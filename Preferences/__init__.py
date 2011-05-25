# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Package implementing the preferences interface.

The preferences interface consists of a class, which defines the default
values for all configuration items and stores the actual values. These
values are read and written to the eric5 preferences file by module
functions. The data is stored in a file in a subdirectory of the users home
directory. The individual configuration data is accessed by accessor functions
defined on the module level. The module is simply imported wherever it is needed
with the statement 'import Preferences'. Do not use 'from Preferences import *'
to import it.
"""

import os
import fnmatch
import shutil

from PyQt4 import QtCore, QtGui, QtNetwork
from PyQt4 import Qsci
from PyQt4.QtWebKit import QWebSettings

from E5Gui import E5FileDialog

import QScintilla.Lexers

from Globals import settingsNameOrganization, settingsNameGlobal, settingsNameRecent, \
    isWindowsPlatform, isLinuxPlatform

from Project.ProjectBrowserFlags import SourcesBrowserFlag, FormsBrowserFlag, \
    ResourcesBrowserFlag, TranslationsBrowserFlag, InterfacesBrowserFlag, \
    OthersBrowserFlag, AllBrowsersFlag


class Prefs(object):
    """
    A class to hold all configuration items for the application.
    """
    # defaults for the variables window
    varDefaults = {
        "LocalsFilter": "[]",
        "GlobalsFilter": "[]"
    }
    
    # defaults for the debugger
    debuggerDefaults = {
        "RemoteDbgEnabled": False,
        "RemoteHost": "",
        "RemoteExecution": "",
        "PassiveDbgEnabled": False,
        "PassiveDbgPort": 42424,
        "PassiveDbgType": "Python",
        "AutomaticReset": False,
        "Autosave": False,
        "ThreeStateBreakPoints": False,
        "SuppressClientExit": False,
        "BreakAlways": False,
        "PythonInterpreter": "",
        "Python3Interpreter": "",
        "CustomPython3Interpreter": False,
        "RubyInterpreter": "/usr/bin/ruby",
        "DebugClientType": "standard",     # supported "standard", "threaded", "custom"
        "DebugClient": "",
        "DebugClientType3": "standard",    # supported "standard", "threaded", "custom"
        "DebugClient3": "",
        "PythonExtensions": ".py2 .pyw2 .ptl",
                                            # space separated list of Python extensions
        "Python3Extensions": ".py .pyw .py3 .pyw3",
                                            # space separated list of Python3 extensions
        "DebugEnvironmentReplace": False,
        "DebugEnvironment": "",
        "PythonRedirect": True,
        "PythonNoEncoding": False,
        "Python3Redirect": True,
        "Python3NoEncoding": False,
        "RubyRedirect": True,
        "ConsoleDbgEnabled": False,
        "ConsoleDbgCommand": "",
        "PathTranslation": False,
        "PathTranslationRemote": "",
        "PathTranslationLocal": "",
        "NetworkInterface": "127.0.0.1",
    }
    debuggerDefaults["AllowedHosts"] = ["127.0.0.1", "::1%0"]
    
    # defaults for the UI settings
    uiDefaults = {
        "Language": "System",
        "Style": "System",
        "StyleSheet": "",
        "ViewManager": "tabview",
        "LayoutType": "Sidebars",
        # allowed values are "DockWindows", "FloatingWindows", "Toolboxes" and "Sidebars"
        "LayoutShellEmbedded": 0,          # 0 = separate
                                            # 1 = embedded in debug browser
        "LayoutFileBrowserEmbedded": 1,    # 0 = separate
                                            # 1 = embedded in debug browser
                                            # 2 = embedded in project browser
        "BrowsersListFoldersFirst": True,
        "BrowsersHideNonPublic": False,
        "BrowsersListContentsByOccurrence": False,
        "BrowsersListHiddenFiles": False,
        "BrowsersFileFilters": "*.py[co];*.so;*.dll",
        "LogViewerAutoRaise": True,
        "SingleApplicationMode": False,
        "CaptionShowsFilename": True,
        "CaptionFilenameLength": 100,
        "RecentNumber": 9,
        "TopLeftByLeft": True,
        "BottomLeftByLeft": False,
        "TopRightByRight": True,
        "BottomRightByRight": False,
        "TabViewManagerFilenameLength": 40,
        "TabViewManagerFilenameOnly": True,
        # the order in ViewProfiles is Project-Viewer, File-Browser,
        # Debug-Viewer, Python-Shell, Log-Viewer, Task-Viewer,
        # Templates-Viewer, Multiproject-Viewer, Terminal, Chat, Symbols,
        # Numbers
        "ViewProfiles": {
            "edit": [
                    # visibility (0)
                    [True, False, False, True, True, True, True,  True,
                     True, True,  True,  True],
                    # saved state main window with dock windows (1)
                    b"",
                    # saved states floating windows (2)
                    [b"", b"", b"", b"", b"", b"", b"", b"", b"", b"", b"", b""],
                    # saved state main window with floating windows (3)
                    b"",
                    # saved state main window with toolbox windows (4)
                    b"",
                    # visibility of the toolboxes/sidebars (5)
                    [True,  True],
                    # saved states of the splitters and sidebars of the
                    # sidebars layout (6)
                    [b"", b"", b"", b""],
                ],
            "debug": [
                    # visibility (0)
                    [False, False, True,  True, True, True, False, False,
                     True,  False, False, False],
                    # saved state main window with dock windows (1)
                    b"",
                    # saved states floating windows (2)
                    [b"", b"", b"", b"", b"", b"", b"", b"", b"", b"", b"", b""],
                    # saved state main window with floating windows (3)
                    b"",
                    # saved state main window with toolbox windows (4)
                    b"",
                    # visibility of the toolboxes/sidebars (5)
                    [False,  True],
                    # saved states of the splitters and sidebars of the
                    # sidebars layout (6)
                    [b"", b"", b"", b""],
                ],
        },
        "ToolbarManagerState": QtCore.QByteArray(),
        "ShowSplash": True,
        "SingleCloseButton": False,
        
        "PerformVersionCheck": 4,      # 0 = off
                                        # 1 = at startup
                                        # 2 = daily
                                        # 3 = weekly
                                        # 4 = monthly
        "UseProxy": False,
        "UseSystemProxy": True,
        "UseHttpProxyForAll": False,
        "ProxyHost/Http": "",
        "ProxyHost/Https": "",
        "ProxyHost/Ftp": "",
        "ProxyPort/Http": 80,
        "ProxyPort/Https": 443,
        "ProxyPort/Ftp": 21,
        "ProxyUser/Http": "",
        "ProxyUser/Https": "",
        "ProxyUser/Ftp": "",
        "ProxyPassword/Http": "",
        "ProxyPassword/Https": "",
        "ProxyPassword/Ftp": "",
        
        "PluginRepositoryUrl5": \
            "http://die-offenbachs.homelinux.org/eric/plugins5/repository.xml",
        "VersionsUrls5": [
            "http://die-offenbachs.homelinux.org/eric/snapshots5/versions",
            "http://eric-ide.python-projects.org/snapshots5/versions",
        ],
        
        "OpenOnStartup": 0,        # 0 = nothing
                                   # 1 = last file
                                   # 2 = last project
                                   # 3 = last multiproject
                                   # 4 = last global session
        
        "DownloadPath": "",
        "RequestDownloadFilename": True,
        "CheckErrorLog": True,
        
        "LogStdErrColour": QtGui.QColor(QtCore.Qt.red),
    }
    viewProfilesLength = len(uiDefaults["ViewProfiles"]["edit"][2])
    
    iconsDefaults = {
        "Path": [],
    }
    
    # defaults for the cooperation settings
    cooperationDefaults = {
        "ServerPort": 42000,
        "AutoStartServer": False,
        "TryOtherPorts": True,
        "MaxPortsToTry": 100,
        "AutoAcceptConnections": False,
        "BannedUsers": [],
    }
    
    # defaults for the editor settings
    editorDefaults = {
        "AutosaveInterval": 0,
        "TabWidth": 4,
        "IndentWidth": 4,
        "LinenoWidth": 4,
        "IndentationGuides": True,
        "UnifiedMargins": False,
        "LinenoMargin": True,
        "FoldingMargin": True,
        "FoldingStyle": 1,
        "TabForIndentation": False,
        "TabIndents": True,
        "ConvertTabsOnLoad": False,
        "AutomaticEOLConversion": True,
        "ShowWhitespace": False,
        "WhitespaceSize": 1,
        "ShowEOL": False,
        "UseMonospacedFont": False,
        "WrapLongLines": False,
        "WarnFilesize": 512,
        "ClearBreaksOnClose": True,
        "StripTrailingWhitespace": False,
        "CommentColumn0": True,
        
        "EdgeMode": Qsci.QsciScintilla.EdgeNone,
        "EdgeColumn": 80,
        
        "AutoIndentation": True,
        "BraceHighlighting": True,
        "CreateBackupFile": False,
        "CaretLineVisible": False,
        "CaretWidth": 1,
        "ColourizeSelText": False,
        "CustomSelectionColours": False,
        "ExtendSelectionToEol": False,
        
        "AutoPrepareAPIs": False,
        
        "AutoCompletionEnabled": False,
        "AutoCompletionCaseSensitivity": True,
        "AutoCompletionReplaceWord": False,
        "AutoCompletionShowSingle": False,
        "AutoCompletionSource": Qsci.QsciScintilla.AcsDocument,
        "AutoCompletionThreshold": 2,
        "AutoCompletionFillups": False,
        
        "CallTipsEnabled": False,
        "CallTipsVisible": 0,
        "CallTipsStyle": Qsci.QsciScintilla.CallTipsNoContext,
        "CallTipsScintillaOnFail": False,
        # show QScintilla calltips, if plugin fails
        
        "AutoCheckSyntax": True,
        "AutoReopen": False,
        
        "AnnotationsEnabled": True,
        
        "MiniContextMenu": False,
        
        "SearchMarkersEnabled": True,
        "QuickSearchMarkersEnabled": True,
        "MarkOccurrencesEnabled": True,
        "MarkOccurrencesTimeout": 500,     # 500 milliseconds
        "AdvancedEncodingDetection": True,
        
        "SpellCheckingEnabled": True,
        "AutoSpellCheckingEnabled": True,
        "AutoSpellCheckChunkSize": 30,
        "SpellCheckStringsOnly": True,
        "SpellCheckingMinWordSize": 3,
        "SpellCheckingDefaultLanguage": "en",
        "SpellCheckingPersonalWordList": "",
        "SpellCheckingPersonalExcludeList": "",
        
        "DefaultEncoding": "utf-8",
        "DefaultOpenFilter": "",
        "DefaultSaveFilter": "",
        "AdditionalOpenFilters": [],
        "AdditionalSaveFilters": [],
        
        "ZoomFactor": 0,
        
        # All (most) lexers
        "AllFoldCompact": True,
        
        # Bash specifics
        "BashFoldComment": True,
        
        # CMake specifics
        "CMakeFoldAtElse": False,
        
        # C++ specifics
        "CppCaseInsensitiveKeywords": False,
        "CppFoldComment": True,
        "CppFoldPreprocessor": False,
        "CppFoldAtElse": False,
        "CppIndentOpeningBrace": False,
        "CppIndentClosingBrace": False,
        "CppDollarsAllowed": True,
        "CppStylePreprocessor": False,
        
        # CSS specifics
        "CssFoldComment": True,
        
        # D specifics
        "DFoldComment": True,
        "DFoldAtElse": False,
        "DIndentOpeningBrace": False,
        "DIndentClosingBrace": False,
        
        # HTML specifics
        "HtmlFoldPreprocessor": False,
        "HtmlFoldScriptComments": False,
        "HtmlFoldScriptHeredocs": False,
        "HtmlCaseSensitiveTags": False,
        "HtmlDjangoTemplates": False,
        "HtmlMakoTemplates": False,
        
        # Pascal specifics
        "PascalFoldComment": True,
        "PascalFoldPreprocessor": False,
        "PascalSmartHighlighting": True,
        
        # Perl specifics
        "PerlFoldComment": True,
        "PerlFoldPackages": True,
        "PerlFoldPODBlocks": True,
        
        # PostScript specifics
        "PostScriptTokenize": False,
        "PostScriptLevel": 3,
        "PostScriptFoldAtElse": False,
        
        # Povray specifics
        "PovFoldComment": True,
        "PovFoldDirectives": False,
        
        # Properties specifics
        "PropertiesInitialSpaces": True,
        
        # Python specifics
        "PythonBadIndentation": True,
        "PythonFoldComment": True,
        "PythonFoldString": True,
        "PythonAutoIndent": True,
        "PythonAllowV2Unicode": True,
        "PythonAllowV3Binary": True,
        "PythonAllowV3Bytes": True,
        "PythonFoldQuotes": False,
        "PythonStringsOverNewLineAllowed": False,
        
        # Ruby specifics
        "RubyFoldComment": False,
        
        # SQL specifics
        "SqlFoldComment": True,
        "SqlBackslashEscapes": False,
        "SqlDottedWords": False,
        "SqlFoldAtElse": False,
        "SqlFoldOnlyBegin": False,
        "SqlHashComments": False,
        "SqlQuotedIdentifiers": False,
        
        # TCL specifics
        "TclFoldComment": False,
        
        # TeX specifics
        "TexFoldComment": False,
        "TexProcessComments": False,
        "TexProcessIf": True,
        
        # VHDL specifics
        "VHDLFoldComment": True,
        "VHDLFoldAtElse": True,
        "VHDLFoldAtBegin": True,
        "VHDLFoldAtParenthesis": True,
        
        # XML specifics
        "XMLStyleScripts": True,
        
        # YAML specifics
        "YAMLFoldComment": False,
    }
    
    if isWindowsPlatform():
        editorDefaults["EOLMode"] = Qsci.QsciScintilla.EolWindows
    else:
        editorDefaults["EOLMode"] = Qsci.QsciScintilla.EolUnix
    
    editorColourDefaults = {
        "CurrentMarker": QtGui.QColor(QtCore.Qt.yellow),
        "ErrorMarker": QtGui.QColor(QtCore.Qt.red),
        "MatchingBrace": QtGui.QColor(QtCore.Qt.green),
        "MatchingBraceBack": QtGui.QColor(QtCore.Qt.white),
        "NonmatchingBrace": QtGui.QColor(QtCore.Qt.red),
        "NonmatchingBraceBack": QtGui.QColor(QtCore.Qt.white),
        "CallTipsBackground": QtGui.QColor(QtCore.Qt.white),
        "CaretForeground": QtGui.QColor(QtCore.Qt.black),
        "CaretLineBackground": QtGui.QColor(QtCore.Qt.white),
        "Edge": QtGui.QColor(QtCore.Qt.lightGray),
        "SelectionBackground": QtGui.QColor(QtCore.Qt.black),
        "SelectionForeground": QtGui.QColor(QtCore.Qt.white),
        "SearchMarkers": QtGui.QColor(QtCore.Qt.blue),
        "MarginsBackground": QtGui.QColor(QtCore.Qt.lightGray),
        "MarginsForeground": QtGui.QColor(QtCore.Qt.black),
        "FoldmarginBackground": QtGui.QColor("#e6e6e6"),
        "FoldMarkersForeground": QtGui.QColor(QtCore.Qt.white),
        "FoldMarkersBackground": QtGui.QColor(QtCore.Qt.black),
        "SpellingMarkers": QtGui.QColor(QtCore.Qt.red),
        "AnnotationsWarningForeground": QtGui.QColor("#606000"),
        "AnnotationsWarningBackground": QtGui.QColor("#ffffd0"),
        "AnnotationsErrorForeground": QtGui.QColor("#600000"),
        "AnnotationsErrorBackground": QtGui.QColor("#ffd0d0"),
        "WhitespaceForeground": QtGui.QColor(QtCore.Qt.darkGray),
        "WhitespaceBackground": QtGui.QColor(QtCore.Qt.white),
    }
    
    editorOtherFontsDefaults = {
        "MarginsFont": "Sans Serif,10,-1,5,50,0,0,0,0,0",
        "DefaultFont": "Sans Serif,10,-1,5,50,0,0,0,0,0",
        "MonospacedFont": "Courier,10,-1,5,50,0,0,0,0,0",
    }
    
    editorTypingDefaults = {
        "Python/EnabledTypingAids": True,
        "Python/InsertClosingBrace": True,
        "Python/IndentBrace": True,
        "Python/SkipBrace": True,
        "Python/InsertQuote": True,
        "Python/DedentElse": True,
        "Python/DedentExcept": True,
        "Python/Py24StyleTry": True,
        "Python/InsertImport": True,
        "Python/InsertSelf": True,
        "Python/InsertBlank": True,
        "Python/ColonDetection": True,
        "Python/DedentDef": False,
        
        "Ruby/EnabledTypingAids": True,
        "Ruby/InsertClosingBrace": True,
        "Ruby/IndentBrace": True,
        "Ruby/SkipBrace": True,
        "Ruby/InsertQuote": True,
        "Ruby/InsertBlank": True,
        "Ruby/InsertHereDoc": True,
        "Ruby/InsertInlineDoc": True,
    }
    
    editorExporterDefaults = {
        "HTML/WYSIWYG": True,
        "HTML/Folding": False,
        "HTML/OnlyStylesUsed": False,
        "HTML/FullPathAsTitle": False,
        "HTML/UseTabs": False,
        
        "RTF/WYSIWYG": True,
        "RTF/UseTabs": False,
        "RTF/Font": "Courier New,10,-1,5,50,0,0,0,0,0",
        
        "PDF/Magnification": 0,
        "PDF/Font": "Helvetica",  # must be Courier, Helvetica or Times
        "PDF/PageSize": "A4",         # must be A4 or Letter
        "PDF/MarginLeft": 36,
        "PDF/MarginRight": 36,
        "PDF/MarginTop": 36,
        "PDF/MarginBottom": 36,
        
        "TeX/OnlyStylesUsed": False,
        "TeX/FullPathAsTitle": False,
        
        "ODT/WYSIWYG": True,
        "ODT/OnlyStylesUsed": False,
        "ODT/UseTabs": False,
    }
    
    # defaults for the printer settings
    printerDefaults = {
        "PrinterName": "",
        "ColorMode": True,
        "FirstPageFirst": True,
        "Magnification": -3,
        "Orientation": 0,
        "PageSize": 0,
        "HeaderFont": "Serif,10,-1,5,50,0,0,0,0,0",
        "LeftMargin": 1.0,
        "RightMargin": 1.0,
        "TopMargin": 1.0,
        "BottomMargin": 1.0,
    }
    
    # defaults for the project settings
    projectDefaults = {
        "SearchNewFiles": False,
        "SearchNewFilesRecursively": False,
        "AutoIncludeNewFiles": False,
        "AutoLoadSession": False,
        "AutoSaveSession": False,
        "SessionAllBreakpoints": False,
        "XMLTimestamp": True,
        "AutoCompileForms": False,
        "AutoCompileResources": False,
        "AutoLoadDbgProperties": False,
        "AutoSaveDbgProperties": False,
        "HideGeneratedForms": False,
        "FollowEditor": True,
        "RecentNumber": 9,
        "DeterminePyFromProject": True,
    }
    
    # defaults for the multi project settings
    multiProjectDefaults = {
        "OpenMasterAutomatically": True,
        "XMLTimestamp": True,
        "RecentNumber": 9,
    }
    
    # defaults for the project browser flags settings
    projectBrowserFlagsDefaults = {
        "Qt4":
            SourcesBrowserFlag | \
            FormsBrowserFlag | \
            ResourcesBrowserFlag | \
            TranslationsBrowserFlag | \
            InterfacesBrowserFlag | \
            OthersBrowserFlag,
        "Qt4C":
            SourcesBrowserFlag | \
            ResourcesBrowserFlag | \
            TranslationsBrowserFlag | \
            InterfacesBrowserFlag | \
            OthersBrowserFlag,
        "E4Plugin":
            SourcesBrowserFlag | \
            FormsBrowserFlag | \
            ResourcesBrowserFlag | \
            TranslationsBrowserFlag | \
            InterfacesBrowserFlag | \
            OthersBrowserFlag,
        "Console":
            SourcesBrowserFlag | \
            InterfacesBrowserFlag | \
            OthersBrowserFlag,
        "Other":
            SourcesBrowserFlag | \
            InterfacesBrowserFlag | \
            OthersBrowserFlag,
        "PySide":
            SourcesBrowserFlag | \
            FormsBrowserFlag | \
            ResourcesBrowserFlag | \
            TranslationsBrowserFlag | \
            InterfacesBrowserFlag | \
            OthersBrowserFlag,
        "PySideC":
            SourcesBrowserFlag | \
            ResourcesBrowserFlag | \
            TranslationsBrowserFlag | \
            InterfacesBrowserFlag | \
            OthersBrowserFlag,
    }
    
    # defaults for the project browser colour settings
    projectBrowserColourDefaults = {
        "Highlighted": QtGui.QColor(QtCore.Qt.red),
        
        "VcsAdded": QtGui.QColor(QtCore.Qt.blue),
        "VcsConflict": QtGui.QColor(QtCore.Qt.red),
        "VcsModified": QtGui.QColor(QtCore.Qt.yellow),
        "VcsReplaced": QtGui.QColor(QtCore.Qt.cyan),
        "VcsUpdate": QtGui.QColor(QtCore.Qt.green),
        "VcsRemoved": QtGui.QColor(QtCore.Qt.magenta)
    }
    
    # defaults for the help settings
    helpDefaults = {
        "HelpViewerType": 1,      # this coresponds with the radio button id
        "CustomViewer": "",
        "PythonDocDir": "",
        "Python2DocDir": "",
        "QtDocDir": "",
        "Qt4DocDir": "",
        "PyQt4DocDir": "",
        "PySideDocDir": "",
        "SingleHelpWindow": True,
        "SaveGeometry": True,
        "HelpViewerState": QtCore.QByteArray(),
        "WebSearchSuggestions": True,
        "WebSearchEngine": "Google",
        "WebSearchKeywords": [],   # array of two tuples (keyword, search engine name)
        "DiskCacheEnabled": True,
        "DiskCacheSize": 50,       # 50 MB
        "CachePolicy": QtNetwork.QNetworkRequest.PreferNetwork,
        "AcceptCookies": 2,        # CookieJar.AcceptOnlyFromSitesNavigatedTo
        "KeepCookiesUntil": 0,     # CookieJar.KeepUntilExpire
        "FilterTrackingCookies": True,
        "PrintBackgrounds": False,
        "StartupBehavior": 0,      # show home page
        "HomePage": "pyrc:home",
        "HistoryLimit": 30,
        "DefaultScheme": "file://",
        "SavePasswords": False,
        "AdBlockEnabled": False,
        "AdBlockSubscriptions": [],
        "OfflineStorageDatabaseQuota": 50,     # 50 MB
        "UserAgent": "",
        "ShowPreview": True,
        "DownloadManagerRemovePolicy": 0,      # never delete downloads
        "DownloadManagerSize": QtCore.QSize(400, 300),
        "DownloadManagerPosition": QtCore.QPoint(),
        "DownloadManagerDownloads": [],
        "AccessKeysEnabled": True,
        "VirusTotalEnabled": False,
        "VirusTotalServiceKey": "",
        "VirusTotalSecure": False,
    }
    
    websettings = QWebSettings.globalSettings()
    fontFamily = websettings.fontFamily(QWebSettings.StandardFont)
    fontSize = websettings.fontSize(QWebSettings.DefaultFontSize)
    helpDefaults["StandardFont"] = QtGui.QFont(fontFamily, fontSize).toString()
    fontFamily = websettings.fontFamily(QWebSettings.FixedFont)
    fontSize = websettings.fontSize(QWebSettings.DefaultFixedFontSize)
    helpDefaults["FixedFont"] = QtGui.QFont(fontFamily, fontSize).toString()
    helpDefaults.update({
        "AutoLoadImages":
            websettings.testAttribute(QWebSettings.AutoLoadImages),
        "UserStyleSheet": "",
        "SaveUrlColor": QtGui.QColor(248, 248, 210),
        "JavaEnabled":
            websettings.testAttribute(QWebSettings.JavaEnabled),
        "JavaScriptEnabled":
            websettings.testAttribute(QWebSettings.JavascriptEnabled),
        "JavaScriptCanOpenWindows":
            websettings.testAttribute(QWebSettings.JavascriptCanOpenWindows),
        "JavaScriptCanAccessClipboard":
            websettings.testAttribute(QWebSettings.JavascriptCanAccessClipboard),
        "PluginsEnabled":
            websettings.testAttribute(QWebSettings.PluginsEnabled),
        "OfflineStorageDatabaseEnabled":
            websettings.testAttribute(QWebSettings.OfflineStorageDatabaseEnabled),
    })
    if hasattr(QWebSettings, "OfflineWebApplicationCacheEnabled"):
        helpDefaults.update({
            "OfflineWebApplicationCacheEnabled":
                websettings.testAttribute(QWebSettings.OfflineWebApplicationCacheEnabled),
            "OfflineWebApplicationCacheQuota": 50,     # 50 MB
        })
    if hasattr(QWebSettings, "LocalStorageEnabled"):
        helpDefaults["LocalStorageEnabled"] = \
            websettings.testAttribute(QWebSettings.LocalStorageEnabled)
    if hasattr(QWebSettings, "DnsPrefetchEnabled"):
        helpDefaults["DnsPrefetchEnabled"] = \
            websettings.testAttribute(QWebSettings.DnsPrefetchEnabled)
    if hasattr(QWebSettings, "defaultTextEncoding"):
        helpDefaults["DefaultTextEncoding"] = \
            websettings.defaultTextEncoding()

    # defaults for system settings
    sysDefaults = {
        "StringEncoding": "utf-8",
        "IOEncoding": "utf-8",
    }
    
    # defaults for the shell settings
    shellDefaults = {
        "LinenoWidth": 4,
        "LinenoMargin": True,
        "AutoCompletionEnabled": True,
        "CallTipsEnabled": True,
        "WrapEnabled": True,
        "MaxHistoryEntries": 100,
        "SyntaxHighlightingEnabled": True,
        "ShowStdOutErr": True,
        "UseMonospacedFont": False,
        "MonospacedFont": "Courier,10,-1,5,50,0,0,0,0,0",
        "MarginsFont": "Sans Serif,10,-1,5,50,0,0,0,0,0",
    }

    # defaults for the terminal settings
    terminalDefaults = {
        "LinenoWidth": 4,
        "LinenoMargin": True,
        "MaxHistoryEntries": 100,
        "SyntaxHighlightingEnabled": True,
        "Shell": "",
        "ShellInteractive": True,
        "UseMonospacedFont": False,
        "MonospacedFont": "Courier,10,-1,5,50,0,0,0,0,0",
        "MarginsFont": "Sans Serif,10,-1,5,50,0,0,0,0,0",
    }
    if isLinuxPlatform():
        terminalDefaults["Shell"] = "bash"

    # defaults for Qt related stuff
    qtDefaults = {
        "Qt4TranslationsDir": "",
        "QtToolsPrefix4": "",
        "QtToolsPostfix4": "",
        "Qt4Dir": "",
    }
    
    # defaults for corba related stuff
    corbaDefaults = {
        "omniidl": "omniidl"
    }
    
    # defaults for user related stuff
    userDefaults = {
        "Email": "",
        "MailServer": "",
        "Signature": "",
        "MailServerAuthentication": False,
        "MailServerUser": "",
        "MailServerPassword": "",
        "MailServerUseTLS": False,
        "MailServerPort": 25,
        "UseSystemEmailClient": False,
    }
    
    # defaults for vcs related stuff
    vcsDefaults = {
        "AutoClose": False,
        "AutoSaveFiles": True,
        "AutoSaveProject": True,
        "AutoUpdate": False,
        "StatusMonitorInterval": 30,
        "MonitorLocalStatus": False,
    }
    
    # defaults for tasks related stuff
    tasksDefaults = {
        "TasksMarkers": "TO" + "DO:",
        "TasksMarkersBugfix": "FIX" + "ME:",
        # needed to keep it from being recognized as a task
        "TasksColour": QtGui.QColor(QtCore.Qt.black),
        "TasksBugfixColour": QtGui.QColor(QtCore.Qt.red),
        "TasksBgColour": QtGui.QColor(QtCore.Qt.white),
        "TasksProjectBgColour": QtGui.QColor(QtCore.Qt.lightGray),
    }
    
    # defaults for templates related stuff
    templatesDefaults = {
        "AutoOpenGroups": True,
        "SingleDialog": False,
        "ShowTooltip": False,
        "SeparatorChar": "$",
    }
    
    # defaults for plugin manager related stuff
    pluginManagerDefaults = {
        "ActivateExternal": True,
        "DownloadPath": ""
    }
    
    # defaults for the printer settings
    graphicsDefaults = {
        "Font": "SansSerif,10,-1,5,50,0,0,0,0,0"
    }
    
    # defaults for the icon editor
    iconEditorDefaults = {
        "IconEditorState": QtCore.QByteArray(),
    }
    
    # defaults for py3flakes
    py3flakesDefaults = {
        "IncludeInSyntaxCheck": True,
        "IgnoreStarImportWarnings": True,
    }
    
    # defaults for tray starter
    trayStarterDefaults = {
        "TrayStarterIcon": "erict.png",
        # valid values are: erict.png, erict-hc.png,
        #                   erict-bw.png, erict-bwi.png
    }
    
    # defaults for geometry
    geometryDefaults = {
        "HelpViewerGeometry": QtCore.QByteArray(),
        "IconEditorGeometry": QtCore.QByteArray(),
        "MainGeometry": QtCore.QByteArray(),
        "MainMaximized": False,
    }

    # if true, revert layouts to factory defaults
    resetLayout = False


def readToolGroups(prefClass=Prefs):
    """
    Module function to read the tool groups configuration.
    
    @param prefClass preferences class used as the storage area
    @return list of tuples defing the tool groups
    """
    toolGroups = []
    groups = int(prefClass.settings.value("Toolgroups/Groups", 0))
    for groupIndex in range(groups):
        groupName = \
            prefClass.settings.value("Toolgroups/{0:02d}/Name".format(groupIndex))
        group = [groupName, []]
        items = int(prefClass.settings.value(
            "Toolgroups/{0:02d}/Items".format(groupIndex), 0))
        for ind in range(items):
            menutext = prefClass.settings.value(
                "Toolgroups/{0:02d}/{1:02d}/Menutext".format(groupIndex, ind))
            icon = prefClass.settings.value(
                "Toolgroups/{0:02d}/{1:02d}/Icon".format(groupIndex, ind))
            executable = prefClass.settings.value(
                "Toolgroups/{0:02d}/{1:02d}/Executable".format(groupIndex, ind))
            arguments = prefClass.settings.value(
                "Toolgroups/{0:02d}/{1:02d}/Arguments".format(groupIndex, ind))
            redirect = prefClass.settings.value(
                "Toolgroups/{0:02d}/{1:02d}/Redirect".format(groupIndex, ind))
            
            if menutext:
                if menutext == '--':
                    tool = {
                        'menutext': '--',
                        'icon': '',
                        'executable': '',
                        'arguments': '',
                        'redirect': 'no',
                    }
                    group[1].append(tool)
                elif executable:
                    tool = {
                        'menutext': menutext,
                        'icon': icon,
                        'executable': executable,
                        'arguments': arguments,
                        'redirect': redirect,
                    }
                    group[1].append(tool)
        toolGroups.append(group)
    currentGroup = int(prefClass.settings.value("Toolgroups/Current Group", -1))
    return toolGroups, currentGroup
    

def saveToolGroups(toolGroups, currentGroup, prefClass=Prefs):
    """
    Module function to write the tool groups configuration.
    
    @param toolGroups reference to the list of tool groups
    @param currentGroup index of the currently selected tool group (integer)
    @param prefClass preferences class used as the storage area
    """
    # first step, remove all tool group entries
    prefClass.settings.remove("Toolgroups")
    
    # second step, write the tool group entries
    prefClass.settings.setValue("Toolgroups/Groups", len(toolGroups))
    groupIndex = 0
    for group in toolGroups:
        prefClass.settings.setValue(
            "Toolgroups/{0:02d}/Name".format(groupIndex), group[0])
        prefClass.settings.setValue(
            "Toolgroups/{0:02d}/Items".format(groupIndex), len(group[1]))
        ind = 0
        for tool in group[1]:
            prefClass.settings.setValue(
                "Toolgroups/{0:02d}/{1:02d}/Menutext".format(groupIndex, ind),
                tool['menutext'])
            prefClass.settings.setValue(
                "Toolgroups/{0:02d}/{1:02d}/Icon".format(groupIndex, ind),
                tool['icon'])
            prefClass.settings.setValue(
                "Toolgroups/{0:02d}/{1:02d}/Executable".format(groupIndex, ind),
                tool['executable'])
            prefClass.settings.setValue(
                "Toolgroups/{0:02d}/{1:02d}/Arguments".format(groupIndex, ind),
                tool['arguments'])
            prefClass.settings.setValue(
                "Toolgroups/{0:02d}/{1:02d}/Redirect".format(groupIndex, ind),
                tool['redirect'])
            ind += 1
        groupIndex += 1
    prefClass.settings.setValue("Toolgroups/Current Group", currentGroup)
    

def initPreferences():
    """
    Module function to initialize the central configuration store.
    """
    Prefs.settings = QtCore.QSettings(
        QtCore.QSettings.IniFormat, QtCore.QSettings.UserScope,
        settingsNameOrganization, settingsNameGlobal)
    if not isWindowsPlatform():
        hp = QtCore.QDir.homePath()
        dn = QtCore.QDir(hp)
        dn.mkdir(".eric5")
    QtCore.QCoreApplication.setOrganizationName(settingsNameOrganization)
    QtCore.QCoreApplication.setApplicationName(settingsNameGlobal)
    

def syncPreferences(prefClass=Prefs):
    """
    Module function to sync the preferences to disk.
    
    In addition to syncing, the central configuration store is reinitialized as well.
    
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("General/Configured", True)
    prefClass.settings.sync()
    

def exportPreferences(prefClass=Prefs):
    """
    Module function to export the current preferences.
    
    @param prefClass preferences class used as the storage area
    """
    filename, selectedFilter = E5FileDialog.getSaveFileNameAndFilter(
        None,
        QtCore.QCoreApplication.translate("Preferences", "Export Preferences"),
        "",
        QtCore.QCoreApplication.translate("Preferences",
            "Properties File (*.ini);;All Files (*)"),
        None,
        E5FileDialog.Options(E5FileDialog.DontConfirmOverwrite))
    if filename:
        ext = QtCore.QFileInfo(filename).suffix()
        if not ext:
            ex = selectedFilter.split("(*")[1].split(")")[0]
            if ex:
                filename += ex
        settingsFile = prefClass.settings.fileName()
        prefClass.settings = None
        shutil.copy(settingsFile, filename)
        initPreferences()


def importPreferences(prefClass=Prefs):
    """
    Module function to import preferences from a file previously saved by
    the export function.
    
    @param prefClass preferences class used as the storage area
    """
    filename = E5FileDialog.getOpenFileName(
        None,
        QtCore.QCoreApplication.translate("Preferences", "Import Preferences"),
        "",
        QtCore.QCoreApplication.translate("Preferences",
            "Properties File (*.ini);;All Files (*)"))
    if filename:
        settingsFile = prefClass.settings.fileName()
        shutil.copy(filename, settingsFile)
        initPreferences()


def isConfigured(prefClass=Prefs):
    """
    Module function to check, if the the application has been configured.
    
    @param prefClass preferences class used as the storage area
    @return flag indicating the configured status (boolean)
    """
    return toBool(prefClass.settings.value("General/Configured", False))
    

def initRecentSettings():
    """
    Module function to initialize the central configuration store for recently
    opened files and projects.
    
    This function is called once upon import of the module.
    """
    Prefs.rsettings = QtCore.QSettings(
        QtCore.QSettings.IniFormat, QtCore.QSettings.UserScope,
        settingsNameOrganization, settingsNameRecent)
    

def getVarFilters(prefClass=Prefs):
    """
    Module function to retrieve the variables filter settings.
    
    @param prefClass preferences class used as the storage area
    @return a tuple defing the variables filter
    """
    localsFilter = eval(prefClass.settings.value("Variables/LocalsFilter",
        prefClass.varDefaults["LocalsFilter"]))
    globalsFilter = eval(prefClass.settings.value("Variables/GlobalsFilter",
        prefClass.varDefaults["GlobalsFilter"]))
    return (localsFilter, globalsFilter)
    

def setVarFilters(filters, prefClass=Prefs):
    """
    Module function to store the variables filter settings.
    
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("Variables/LocalsFilter", str(filters[0]))
    prefClass.settings.setValue("Variables/GlobalsFilter", str(filters[1]))
    

def getDebugger(key, prefClass=Prefs):
    """
    Module function to retrieve the debugger settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested debugger setting
    """
    if key in ["RemoteDbgEnabled", "PassiveDbgEnabled",
                "CustomPython3Interpreter",
                "AutomaticReset", "DebugEnvironmentReplace",
                "PythonRedirect", "PythonNoEncoding",
                "Python3Redirect", "Python3NoEncoding",
                "RubyRedirect",
                "ConsoleDbgEnabled", "PathTranslation",
                "Autosave", "ThreeStateBreakPoints",
                "SuppressClientExit", "BreakAlways",
              ]:
        return toBool(prefClass.settings.value("Debugger/" + key,
            prefClass.debuggerDefaults[key]))
    elif key in ["PassiveDbgPort"]:
        return int(
            prefClass.settings.value("Debugger/" + key, prefClass.debuggerDefaults[key]))
    elif key in ["AllowedHosts"]:
        return toList(
            prefClass.settings.value("Debugger/" + key, prefClass.debuggerDefaults[key]))
    else:
        return \
            prefClass.settings.value("Debugger/" + key, prefClass.debuggerDefaults[key])
    

def setDebugger(key, value, prefClass=Prefs):
    """
    Module function to store the debugger settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("Debugger/" + key, value)


def getPython(key, prefClass=Prefs):
    """
    Module function to retrieve the Python settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested debugger setting
    """
    if key in ["PythonExtensions", "Python3Extensions"]:
        exts = []
        for ext in getDebugger(key, prefClass).split():
            if ext.startswith("."):
                exts.append(ext)
            else:
                exts.append(".{0}".format(ext))
        return exts


def setPython(key, value, prefClass=Prefs):
    """
    Module function to store the Python settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    if key in ["PythonExtensions", "Python3Extensions"]:
        setDebugger(key, value, prefClass)


def getUILanguage(prefClass=Prefs):
    """
    Module function to retrieve the language for the user interface.
    
    @param prefClass preferences class used as the storage area
    @return the language for the UI
    """
    lang = \
        prefClass.settings.value("UI/Language", prefClass.uiDefaults["Language"])
    if lang == "None" or lang == "" or lang is None:
        return None
    else:
        return lang
    

def setUILanguage(lang, prefClass=Prefs):
    """
    Module function to store the language for the user interface.
    
    @param lang the language
    @param prefClass preferences class used as the storage area
    """
    if lang is None:
        prefClass.settings.setValue("UI/Language", "None")
    else:
        prefClass.settings.setValue("UI/Language", lang)


def getUILayout(prefClass=Prefs):
    """
    Module function to retrieve the layout for the user interface.
    
    @param prefClass preferences class used as the storage area
    @return the UI layout as a tuple of main layout, flag for
        an embedded shell and a value for an embedded file browser
    """
    layout = (
        prefClass.settings.value("UI/LayoutType",
            prefClass.uiDefaults["LayoutType"]),
        int(prefClass.settings.value("UI/LayoutShellEmbedded",
            prefClass.uiDefaults["LayoutShellEmbedded"])),
        int(prefClass.settings.value("UI/LayoutFileBrowserEmbedded",
            prefClass.uiDefaults["LayoutFileBrowserEmbedded"])),
    )
    return layout
    

def setUILayout(layout, prefClass=Prefs):
    """
    Module function to store the layout for the user interface.
    
    @param layout the layout type
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("UI/LayoutType", layout[0])
    prefClass.settings.setValue("UI/LayoutShellEmbedded", layout[1])
    prefClass.settings.setValue("UI/LayoutFileBrowserEmbedded", layout[2])


def getViewManager(prefClass=Prefs):
    """
    Module function to retrieve the selected viewmanager type.
    
    @param prefClass preferences class used as the storage area
    @return the viewmanager type
    """
    return prefClass.settings.value("UI/ViewManager",
        prefClass.uiDefaults["ViewManager"])
    

def setViewManager(vm, prefClass=Prefs):
    """
    Module function to store the selected viewmanager type.
    
    @param vm the viewmanager type
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("UI/ViewManager", vm)


def getUI(key, prefClass=Prefs):
    """
    Module function to retrieve the various UI settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested UI setting
    """
    if key in ["BrowsersListFoldersFirst", "BrowsersHideNonPublic",
                "BrowsersListContentsByOccurrence", "BrowsersListHiddenFiles",
                "LogViewerAutoRaise",
                "SingleApplicationMode", "TabViewManagerFilenameOnly",
                "CaptionShowsFilename", "ShowSplash",
                "SingleCloseButton",
                "UseProxy", "UseSystemProxy", "UseHttpProxyForAll",
                "TopLeftByLeft", "BottomLeftByLeft",
                "TopRightByRight", "BottomRightByRight",
                "RequestDownloadFilename",
                "LayoutShellEmbedded", "LayoutFileBrowserEmbedded",
                "CheckErrorLog"]:
        return toBool(prefClass.settings.value("UI/" + key,
            prefClass.uiDefaults[key]))
    elif key in ["TabViewManagerFilenameLength", "CaptionFilenameLength",
                 "ProxyPort/Http", "ProxyPort/Https", "ProxyPort/Ftp",
                 "OpenOnStartup",
                 "PerformVersionCheck", "RecentNumber", ]:
        return int(prefClass.settings.value("UI/" + key,
            prefClass.uiDefaults[key]))
    elif key in ["ProxyPassword/Http", "ProxyPassword/Https",
                 "ProxyPassword/Ftp", ]:
        from Utilities import pwDecode
        return pwDecode(prefClass.settings.value("UI/" + key, prefClass.uiDefaults[key]))
    elif key in ["LogStdErrColour"]:
        col = prefClass.settings.value("UI/" + key)
        if col is not None:
            return QtGui.QColor(col)
        else:
            return prefClass.uiDefaults[key]
    elif key == "ViewProfiles":
        profiles = prefClass.settings.value("UI/ViewProfiles")
        if profiles is not None:
            if isinstance(profiles, str):
                # just in case of an old structure
                viewProfiles = eval(profiles)
            else:
                viewProfiles = profiles
            for name in ["edit", "debug"]:
                # adjust entries for individual windows
                vpLength = len(viewProfiles[name][0])
                if vpLength < prefClass.viewProfilesLength:
                    viewProfiles[name][0].extend(
                        prefClass.uiDefaults["ViewProfiles"][name][0][vpLength:])
                
                vpLength = len(viewProfiles[name][2])
                if vpLength < prefClass.viewProfilesLength:
                    viewProfiles[name][2].extend(
                        prefClass.uiDefaults["ViewProfiles"][name][2][vpLength:])
                
                # adjust profile
                vpLength = len(viewProfiles[name])
                if vpLength < len(prefClass.uiDefaults["ViewProfiles"][name]):
                    viewProfiles[name].extend(
                        prefClass.uiDefaults["ViewProfiles"][name][vpLength:])
                
                # adjust entries for toolboxes and sidebars
                vpLength = len(viewProfiles[name][5])
                if vpLength < len(prefClass.uiDefaults["ViewProfiles"][name][5]):
                    viewProfiles[name][5].extend(
                        prefClass.uiDefaults["ViewProfiles"][name][5][vpLength:])
                vpLength = len(viewProfiles[name][6])
                if vpLength < len(prefClass.uiDefaults["ViewProfiles"][name][6]):
                    viewProfiles[name][6].extend(
                        prefClass.uiDefaults["ViewProfiles"][name][6][vpLength:])
        else:
            viewProfiles = prefClass.uiDefaults["ViewProfiles"]
        return viewProfiles
    elif key == "ToolbarManagerState":
        toolbarManagerState = prefClass.settings.value("UI/ToolbarManagerState")
        if toolbarManagerState is not None:
            return toolbarManagerState
        else:
            return prefClass.uiDefaults["ToolbarManagerState"]
    elif key in ["VersionsUrls5"]:
        urls = toList(prefClass.settings.value("UI/" + key, prefClass.uiDefaults[key]))
        if len(urls) == 0:
            return prefClass.uiDefaults[key]
        else:
            return urls
    else:
        return prefClass.settings.value("UI/" + key, prefClass.uiDefaults[key])
    

def setUI(key, value, prefClass=Prefs):
    """
    Module function to store the various UI settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    if key == "ViewProfiles":
        prefClass.settings.setValue("UI/" + key, value)
    elif key == "LogStdErrColour":
        prefClass.settings.setValue("UI/" + key, value.name())
    elif key in ["ProxyPassword/Http", "ProxyPassword/Https",
                 "ProxyPassword/Ftp", ]:
        from Utilities import pwEncode
        prefClass.settings.setValue("UI/" + key, pwEncode(value))
    else:
        prefClass.settings.setValue("UI/" + key, value)
    

def getIcons(key, prefClass=Prefs):
    """
    Module function to retrieve the various Icons settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested Icons setting
    """
    dirlist = prefClass.settings.value("UI/Icons/" + key)
    if dirlist is not None:
        return dirlist
    else:
        return prefClass.iconsDefaults[key]
    

def setIcons(key, value, prefClass=Prefs):
    """
    Module function to store the various Icons settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("UI/Icons/" + key, value)
    

def getCooperation(key, prefClass=Prefs):
    """
    Module function to retrieve the various Cooperation settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested UI setting
    """
    if key in ["AutoStartServer", "TryOtherPorts", "AutoAcceptConnections"]:
        return toBool(prefClass.settings.value("Cooperation/" + key,
            prefClass.cooperationDefaults[key]))
    elif key in ["ServerPort", "MaxPortsToTry"]:
        return int(prefClass.settings.value("Cooperation/" + key,
            prefClass.cooperationDefaults[key]))
    elif key in ["BannedUsers"]:
        return toList(prefClass.settings.value("Cooperation/" + key,
            prefClass.cooperationDefaults[key]))
    else:
        return prefClass.settings.value("Cooperation/" + key,
            prefClass.cooperationDefaults[key])
    

def setCooperation(key, value, prefClass=Prefs):
    """
    Module function to store the various Cooperation settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("Cooperation/" + key, value)


def getEditor(key, prefClass=Prefs):
    """
    Module function to retrieve the various editor settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested editor setting
    """
    if key in ["DefaultEncoding", "DefaultOpenFilter", "DefaultSaveFilter",
               "SpellCheckingDefaultLanguage", "SpellCheckingPersonalWordList",
               "SpellCheckingPersonalExcludeList"]:
        return prefClass.settings.value("Editor/" + key, prefClass.editorDefaults[key])
    elif key in ["AutosaveInterval", "TabWidth", "IndentWidth", "LinenoWidth",
                 "FoldingStyle", "WarnFilesize", "EdgeMode", "EdgeColumn",
                 "CaretWidth", "AutoCompletionSource", "AutoCompletionThreshold",
                 "CallTipsVisible", "CallTipsStyle", "MarkOccurrencesTimeout",
                 "AutoSpellCheckChunkSize", "SpellCheckingMinWordSize",
                 "PostScriptLevel", "EOLMode", "ZoomFactor", "WhitespaceSize"]:
        return int(prefClass.settings.value("Editor/" + key,
            prefClass.editorDefaults[key]))
    elif key in ["AdditionalOpenFilters", "AdditionalSaveFilters"]:
        return toList(prefClass.settings.value("Editor/" + key,
            prefClass.editorDefaults[key]))
    else:
        return toBool(prefClass.settings.value("Editor/" + key,
            prefClass.editorDefaults[key]))
    

def setEditor(key, value, prefClass=Prefs):
    """
    Module function to store the various editor settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("Editor/" + key, value)
    

def getEditorColour(key, prefClass=Prefs):
    """
    Module function to retrieve the various editor marker colours.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested editor colour
    """
    col = prefClass.settings.value("Editor/Colour/" + key)
    if col is not None:
        if len(col) == 9:
            # color string with alpha
            return QtGui.QColor.fromRgba(int(col[1:], 16))
        else:
            return QtGui.QColor(col)
    else:
        return prefClass.editorColourDefaults[key]
    

def setEditorColour(key, value, prefClass=Prefs):
    """
    Module function to store the various editor marker colours.
    
    @param key the key of the colour to be set
    @param value the colour to be set
    @param prefClass preferences class used as the storage area
    """
    if value.alpha() < 255:
        val = "#{0:8x}".format(value.rgba())
    else:
        val = value.name()
    prefClass.settings.setValue("Editor/Colour/" + key, val)
    

def getEditorOtherFonts(key, prefClass=Prefs):
    """
    Module function to retrieve the various editor fonts except the lexer fonts.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested editor font (QFont)
    """
    f = QtGui.QFont()
    f.fromString(prefClass.settings.value("Editor/Other Fonts/" + key,
        prefClass.editorOtherFontsDefaults[key]))
    return f
    

def setEditorOtherFonts(key, font, prefClass=Prefs):
    """
    Module function to store the various editor fonts except the lexer fonts.
    
    @param key the key of the font to be set
    @param font the font to be set (QFont)
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("Editor/Other Fonts/" + key, font.toString())
    

def getEditorAPI(key, prefClass=Prefs):
    """
    Module function to retrieve the various lists of api files.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested list of api files (list of strings)
    """
    apis = prefClass.settings.value("Editor/APIs/" + key)
    if apis is not None:
        if len(apis) and apis[0] == "":
            return []
        else:
            return apis
    else:
        return []
    

def setEditorAPI(key, apilist, prefClass=Prefs):
    """
    Module function to store the various lists of api files.
    
    @param key the key of the api to be set
    @param apilist the list of api files (list of strings)
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("Editor/APIs/" + key, apilist)
    

def getEditorKeywords(key, prefClass=Prefs):
    """
    Module function to retrieve the various lists of language keywords.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested list of language keywords (list of strings)
    """
    keywords = prefClass.settings.value("Editor/Keywords/" + key)
    if keywords is not None:
        return keywords
    else:
        return []
    

def setEditorKeywords(key, keywordsLists, prefClass=Prefs):
    """
    Module function to store the various lists of language keywords.
    
    @param key the key of the api to be set
    @param keywordsLists the list of language keywords (list of strings)
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("Editor/Keywords/" + key, keywordsLists)
    

def getEditorLexerAssocs(prefClass=Prefs):
    """
    Module function to retrieve all lexer associations.
    
    @param prefClass preferences class used as the storage area
    @return a reference to the list of lexer associations
        (dictionary of strings)
    """
    editorLexerAssoc = {}
    prefClass.settings.beginGroup("Editor/LexerAssociations")
    keyList = prefClass.settings.childKeys()
    prefClass.settings.endGroup()
    editorLexerAssocDefaults = QScintilla.Lexers.getDefaultLexerAssociations()
    
    if len(keyList) == 0:
        # build from scratch
        for key in list(editorLexerAssocDefaults.keys()):
            editorLexerAssoc[key] = editorLexerAssocDefaults[key]
    else:
        for key in keyList:
            if key in editorLexerAssocDefaults:
                defaultValue = editorLexerAssocDefaults[key]
            else:
                defaultValue = ""
            editorLexerAssoc[key] = \
                prefClass.settings.value("Editor/LexerAssociations/" + key, defaultValue)
        
        # check for new default lexer associations
        for key in list(editorLexerAssocDefaults.keys()):
            if key not in editorLexerAssoc:
                editorLexerAssoc[key] = editorLexerAssocDefaults[key]
    return editorLexerAssoc
    

def setEditorLexerAssocs(assocs, prefClass=Prefs):
    """
    Module function to retrieve all lexer associations.
    
    @param assocs dictionary of lexer associations to be set
    @param prefClass preferences class used as the storage area
    """
    # first remove lexer associations that no longer exist, than save the rest
    prefClass.settings.beginGroup("Editor/LexerAssociations")
    keyList = prefClass.settings.childKeys()
    prefClass.settings.endGroup()
    for key in keyList:
        if key not in assocs:
            prefClass.settings.remove("Editor/LexerAssociations/" + key)
    for key in assocs:
        prefClass.settings.setValue("Editor/LexerAssociations/" + key, assocs[key])
    

def getEditorLexerAssoc(filename, prefClass=Prefs):
    """
    Module function to retrieve a lexer association.
    
    @param filename filename used to determine the associated lexer language (string)
    @param prefClass preferences class used as the storage area
    @return the requested lexer language (string)
    """
    for pattern, language in list(getEditorLexerAssocs().items()):
        if fnmatch.fnmatch(filename, pattern):
            return language
    
    return ""
    

def getEditorTyping(key, prefClass=Prefs):
    """
    Module function to retrieve the various editor typing settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested editor setting
    """
    return toBool(prefClass.settings.value("Editor/Typing/" + key,
        prefClass.editorTypingDefaults[key]))
    

def setEditorTyping(key, value, prefClass=Prefs):
    """
    Module function to store the various editor typing settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("Editor/Typing/" + key, value)
    

def getEditorExporter(key, prefClass=Prefs):
    """
    Module function to retrieve the various editor exporters settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested editor setting
    """
    if key in ["RTF/Font"]:
        f = QtGui.QFont()
        f.fromString(prefClass.settings.value("Editor/Exporters/" + key,
            prefClass.editorExporterDefaults[key]))
        return f
    elif key in ["HTML/WYSIWYG", "HTML/Folding", "HTML/OnlyStylesUsed",
                 "HTML/FullPathAsTitle", "HTML/UseTabs", "RTF/WYSIWYG",
                 "RTF/UseTabs", "TeX/OnlyStylesUsed", "TeX/FullPathAsTitle",
                 "ODT/WYSIWYG", "ODT/OnlyStylesUsed", "ODT/UseTabs"]:
        return toBool(prefClass.settings.value("Editor/Exporters/" + key,
            prefClass.editorExporterDefaults[key]))
    elif key in ["PDF/Magnification", "PDF/MarginLeft", "PDF/MarginRight",
                 "PDF/MarginTop", "PDF/MarginBottom"]:
        return int(prefClass.settings.value("Editor/Exporters/" + key,
            prefClass.editorExporterDefaults[key]))
    else:
        return prefClass.settings.value("Editor/Exporters/" + key,
            prefClass.editorExporterDefaults[key])


def setEditorExporter(key, value, prefClass=Prefs):
    """
    Module function to store the various editor exporters settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    if key in ["RTF/Font"]:
        prefClass.settings.setValue("Editor/Exporters/" + key, value.toString())
    else:
        prefClass.settings.setValue("Editor/Exporters/" + key, value)
    

def getPrinter(key, prefClass=Prefs):
    """
    Module function to retrieve the various printer settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested printer setting
    """
    if key in ["ColorMode", "FirstPageFirst"]:
        return toBool(prefClass.settings.value("Printer/" + key,
            prefClass.printerDefaults[key]))
    elif key in ["Magnification", "Orientation", "PageSize"]:
        return int(prefClass.settings.value("Printer/" + key,
            prefClass.printerDefaults[key]))
    elif key in ["LeftMargin", "RightMargin", "TopMargin", "BottomMargin"]:
        return float(prefClass.settings.value("Printer/" + key,
            prefClass.printerDefaults[key]))
    elif key in ["HeaderFont"]:
        f = QtGui.QFont()
        f.fromString(prefClass.settings.value("Printer/" + key,
            prefClass.printerDefaults[key]))
        return f
    else:
        return prefClass.settings.value("Printer/" + key,
            prefClass.printerDefaults[key])


def setPrinter(key, value, prefClass=Prefs):
    """
    Module function to store the various printer settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    if key in ["HeaderFont"]:
        prefClass.settings.setValue("Printer/" + key, value.toString())
    else:
        prefClass.settings.setValue("Printer/" + key, value)


def getShell(key, prefClass=Prefs):
    """
    Module function to retrieve the various shell settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested shell setting
    """
    if key in ["MonospacedFont", "MarginsFont"]:
        f = QtGui.QFont()
        f.fromString(prefClass.settings.value("Shell/" + key,
            prefClass.shellDefaults[key]))
        return f
    elif key in ["LinenoWidth", "MaxHistoryEntries"]:
        return int(prefClass.settings.value("Shell/" + key,
            prefClass.shellDefaults[key]))
    else:
        return toBool(prefClass.settings.value("Shell/" + key,
            prefClass.shellDefaults[key]))


def setShell(key, value, prefClass=Prefs):
    """
    Module function to store the various shell settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    if key in ["MonospacedFont", "MarginsFont"]:
        prefClass.settings.setValue("Shell/" + key, value.toString())
    else:
        prefClass.settings.setValue("Shell/" + key, value)


def getTerminal(key, prefClass=Prefs):
    """
    Module function to retrieve the various terminal settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested shell setting
    """
    if key in ["Shell"]:
        return prefClass.settings.value("Terminal/" + key,
            prefClass.terminalDefaults[key])
    elif key in ["MonospacedFont", "MarginsFont"]:
        f = QtGui.QFont()
        f.fromString(prefClass.settings.value("Terminal/" + key,
            prefClass.terminalDefaults[key]))
        return f
    elif key in ["LinenoWidth", "MaxHistoryEntries"]:
        return int(prefClass.settings.value("Terminal/" + key,
            prefClass.terminalDefaults[key]))
    else:
        return toBool(prefClass.settings.value("Terminal/" + key,
            prefClass.terminalDefaults[key]))


def setTerminal(key, value, prefClass=Prefs):
    """
    Module function to store the various terminal settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    if key in ["MonospacedFont", "MarginsFont"]:
        prefClass.settings.setValue("Terminal/" + key, value.toString())
    else:
        prefClass.settings.setValue("Terminal/" + key, value)


def getProject(key, prefClass=Prefs):
    """
    Module function to retrieve the various project handling settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested project setting
    """
    if key in ["RecentNumber"]:
        return int(prefClass.settings.value("Project/" + key,
            prefClass.projectDefaults[key]))
    else:
        return toBool(prefClass.settings.value("Project/" + key,
            prefClass.projectDefaults[key]))
    

def setProject(key, value, prefClass=Prefs):
    """
    Module function to store the various project handling settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("Project/" + key, value)
    

def getProjectBrowserFlags(key, prefClass=Prefs):
    """
    Module function to retrieve the various project browser flags settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested project setting
    """
    try:
        default = prefClass.projectBrowserFlagsDefaults[key]
    except KeyError:
        default = AllBrowsersFlag
    
    return int(prefClass.settings.value("Project/BrowserFlags/" + key, default))
    

def setProjectBrowserFlags(key, value, prefClass=Prefs):
    """
    Module function to store the various project browser flags settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("Project/BrowserFlags/" + key, value)
    

def setProjectBrowserFlagsDefault(key, value, prefClass=Prefs):
    """
    Module function to store the various project browser flags settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.projectBrowserFlagsDefaults[key] = value
    

def removeProjectBrowserFlags(key, prefClass=Prefs):
    """
    Module function to remove a project browser flags setting.
    
    @param key the key of the setting to be removed
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.remove("Project/BrowserFlags/" + key)
    

def getProjectBrowserColour(key, prefClass=Prefs):
    """
    Module function to retrieve the various project browser colours.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested project browser colour
    """
    col = prefClass.settings.value("Project/Colour/" + key)
    if col is not None:
        return QtGui.QColor(col)
    else:
        return prefClass.projectBrowserColourDefaults[key]
    

def setProjectBrowserColour(key, value, prefClass=Prefs):
    """
    Module function to store the various project browser colours.
    
    @param key the key of the colour to be set
    @param value the colour to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("Project/Colour/" + key, value.name())
    

def getMultiProject(key, prefClass=Prefs):
    """
    Module function to retrieve the various project handling settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested project setting
    """
    if key in ["RecentNumber"]:
        return int(prefClass.settings.value("MultiProject/" + key,
            prefClass.multiProjectDefaults[key]))
    else:
        return toBool(prefClass.settings.value("MultiProject/" + key,
            prefClass.multiProjectDefaults[key]))
    

def setMultiProject(key, value, prefClass=Prefs):
    """
    Module function to store the various project handling settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("MultiProject/" + key, value)
    

def getQt4DocDir(prefClass=Prefs):
    """
    Module function to retrieve the Qt4DocDir setting.
    
    @param prefClass preferences class used as the storage area
    @return the requested Qt4DocDir setting (string)
    """
    s = prefClass.settings.value("Help/Qt4DocDir",
        prefClass.helpDefaults["Qt4DocDir"])
    if s == "":
        return os.getenv("QT4DOCDIR", "")
    else:
        return s
    

def getHelp(key, prefClass=Prefs):
    """
    Module function to retrieve the various help settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested help setting
    """
    if key in ["StandardFont", "FixedFont"]:
        f = QtGui.QFont()
        f.fromString(prefClass.settings.value("Help/" + key,
            prefClass.helpDefaults[key]))
        return f
    elif key in ["SaveUrlColor"]:
        col = prefClass.settings.value("Help/" + key)
        if col is not None:
            return QtGui.QColor(col)
        else:
            return prefClass.helpDefaults[key]
    elif key in ["WebSearchKeywords"]:
        # return a list of tuples of (keyword, engine name)
        keywords = []
        size = prefClass.settings.beginReadArray("Help/" + key)
        for index in range(size):
            prefClass.settings.setArrayIndex(index)
            keyword = prefClass.settings.value("Keyword")
            engineName = prefClass.settings.value("Engine")
            keywords.append((keyword, engineName))
        prefClass.settings.endArray()
        return keywords
    elif key in ["DownloadManagerDownloads"]:
        # return a list of tuples of (URL, save location, done flag)
        downloads = []
        length = prefClass.settings.beginReadArray("Help/" + key)
        for index in range(length):
            prefClass.settings.setArrayIndex(index)
            url = prefClass.settings.value("URL")
            location = prefClass.settings.value("Location")
            done = toBool(prefClass.settings.value("Done"))
            pageUrl = prefClass.settings.value("PageURL")
            if pageUrl is None:
                pageUrl = QtCore.QUrl()
            downloads.append((url, location, done, pageUrl))
        prefClass.settings.endArray()
        return downloads
    elif key in ["HelpViewerType", "DiskCacheSize", "AcceptCookies",
                 "KeepCookiesUntil", "StartupBehavior", "HistoryLimit",
                 "OfflineStorageDatabaseQuota", "OfflineWebApplicationCacheQuota",
                 "CachePolicy", "DownloadManagerRemovePolicy"]:
        return int(prefClass.settings.value("Help/" + key,
            prefClass.helpDefaults[key]))
    elif key in ["SingleHelpWindow", "SaveGeometry", "WebSearchSuggestions",
                 "DiskCacheEnabled", "FilterTrackingCookies", "PrintBackgrounds",
                 "SavePasswords", "AdBlockEnabled", "AutoLoadImages",
                 "JavaEnabled", "JavaScriptEnabled", "JavaScriptCanOpenWindows",
                 "JavaScriptCanAccessClipboard", "PluginsEnabled", "DnsPrefetchEnabled",
                 "OfflineStorageDatabaseEnabled", "OfflineWebApplicationCacheEnabled",
                 "LocalStorageEnabled", "ShowPreview", "AccessKeysEnabled",
                 "VirusTotalEnabled", "VirusTotalSecure"]:
        return toBool(prefClass.settings.value("Help/" + key,
            prefClass.helpDefaults[key]))
    elif key in ["AdBlockSubscriptions"]:
        return toList(prefClass.settings.value("Help/" + key,
            prefClass.helpDefaults[key]))
    else:
        return prefClass.settings.value("Help/" + key, prefClass.helpDefaults[key])
    

def setHelp(key, value, prefClass=Prefs):
    """
    Module function to store the various help settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    if key in ["StandardFont", "FixedFont"]:
        prefClass.settings.setValue("Help/" + key, value.toString())
    elif key == "SaveUrlColor":
        prefClass.settings.setValue("Help/" + key, value.name())
    elif key == "WebSearchKeywords":
        # value is list of tuples of (keyword, engine name)
        prefClass.settings.remove("Help/" + key)
        prefClass.settings.beginWriteArray("Help/" + key, len(value))
        index = 0
        for v in value:
            prefClass.settings.setArrayIndex(index)
            prefClass.settings.setValue("Keyword", v[0])
            prefClass.settings.setValue("Engine", v[1])
            index += 1
        prefClass.settings.endArray()
    elif key == "DownloadManagerDownloads":
        # value is list of tuples of (URL, save location, done flag, page url)
        prefClass.settings.remove("Help/" + key)
        prefClass.settings.beginWriteArray("Help/" + key, len(value))
        index = 0
        for v in value:
            prefClass.settings.setArrayIndex(index)
            prefClass.settings.setValue("URL", v[0])
            prefClass.settings.setValue("Location", v[1])
            prefClass.settings.setValue("Done", v[2])
            prefClass.settings.setValue("PageURL", v[3])
            index += 1
        prefClass.settings.endArray()
    else:
        prefClass.settings.setValue("Help/" + key, value)
    

def getSystem(key, prefClass=Prefs):
    """
    Module function to retrieve the various system settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested system setting
    """
    from Utilities import supportedCodecs
    if key in ["StringEncoding", "IOEncoding"]:
        encoding = prefClass.settings.value("System/" + key,
            prefClass.sysDefaults[key])
        if encoding not in supportedCodecs:
            encoding = prefClass.sysDefaults[key]
        return encoding
    

def setSystem(key, value, prefClass=Prefs):
    """
    Module function to store the various system settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("System/" + key, value)
    

def getQt4TranslationsDir(prefClass=Prefs):
    """
    Module function to retrieve the Qt4TranslationsDir setting.
    
    @param prefClass preferences class used as the storage area
    @return the requested Qt4TranslationsDir setting (string)
    """
    s = prefClass.settings.value("Qt/Qt4TranslationsDir",
        prefClass.qtDefaults["Qt4TranslationsDir"])
    if s == "":
        s = os.getenv("QT4TRANSLATIONSDIR", "")
    if s == "" and isWindowsPlatform():
        from PyQt4 import pyqtconfig
        transPath = os.path.join(pyqtconfig._pkg_config["pyqt_mod_dir"], "translations")
        if os.path.exists(transPath):
            s = transPath
    return s
    

def getQt(key, prefClass=Prefs):
    """
    Module function to retrieve the various Qt settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested Qt setting
    """
    if key == "Qt4TranslationsDir":
        return getQt4TranslationsDir(prefClass)
    else:
        return prefClass.settings.value("Qt/" + key, prefClass.qtDefaults[key])
    

def setQt(key, value, prefClass=Prefs):
    """
    Module function to store the various Qt settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("Qt/" + key, value)
    

def getCorba(key, prefClass=Prefs):
    """
    Module function to retrieve the various corba settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested corba setting
    """
    return prefClass.settings.value("Corba/" + key, prefClass.corbaDefaults[key])
    

def setCorba(key, value, prefClass=Prefs):
    """
    Module function to store the various corba settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("Corba/" + key, value)
    

def getUser(key, prefClass=Prefs):
    """
    Module function to retrieve the various user settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested user setting
    """
    if key == "MailServerPassword":
        from Utilities import pwDecode
        return pwDecode(prefClass.settings.value("User/" + key,
            prefClass.userDefaults[key]))
    elif key in ["MailServerPort"]:
        return int(prefClass.settings.value("User/" + key,
            prefClass.userDefaults[key]))
    elif key in ["MailServerAuthentication", "MailServerUseTLS",
                 "UseSystemEmailClient"]:
        return toBool(prefClass.settings.value("User/" + key,
            prefClass.userDefaults[key]))
    else:
        return prefClass.settings.value("User/" + key, prefClass.userDefaults[key])
    

def setUser(key, value, prefClass=Prefs):
    """
    Module function to store the various user settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    if key == "MailServerPassword":
        from Utilities import pwEncode
        prefClass.settings.setValue(
            "User/" + key, pwEncode(value))
    else:
        prefClass.settings.setValue("User/" + key, value)
    

def getVCS(key, prefClass=Prefs):
    """
    Module function to retrieve the VCS related settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested user setting
    """
    if key in ["StatusMonitorInterval"]:
        return int(prefClass.settings.value("VCS/" + key, prefClass.vcsDefaults[key]))
    else:
        return toBool(prefClass.settings.value("VCS/" + key, prefClass.vcsDefaults[key]))
    

def setVCS(key, value, prefClass=Prefs):
    """
    Module function to store the VCS related settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("VCS/" + key, value)
    

def getTasks(key, prefClass=Prefs):
    """
    Module function to retrieve the Tasks related settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested user setting
    """
    if key in ["TasksColour", "TasksBugfixColour",
               "TasksBgColour", "TasksProjectBgColour"]:
        col = prefClass.settings.value("Tasks/" + key)
        if col is not None:
            return QtGui.QColor(col)
        else:
            return prefClass.tasksDefaults[key]
    else:
        return prefClass.settings.value("Tasks/" + key,
            prefClass.tasksDefaults[key])
    

def setTasks(key, value, prefClass=Prefs):
    """
    Module function to store the Tasks related settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    if key in ["TasksColour", "TasksBugfixColour",
               "TasksBgColour", "TasksProjectBgColour"]:
        prefClass.settings.setValue("Tasks/" + key, value.name())
    else:
        prefClass.settings.setValue("Tasks/" + key, value)
    

def getTemplates(key, prefClass=Prefs):
    """
    Module function to retrieve the Templates related settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested user setting
    """
    if key in ["SeparatorChar"]:
        return prefClass.settings.value("Templates/" + key,
            prefClass.templatesDefaults[key])
    else:
        return toBool(prefClass.settings.value("Templates/" + key,
            prefClass.templatesDefaults[key]))
    

def setTemplates(key, value, prefClass=Prefs):
    """
    Module function to store the Templates related settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("Templates/" + key, value)
    

def getPluginManager(key, prefClass=Prefs):
    """
    Module function to retrieve the plugin manager related settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested user setting
    """
    if key in ["DownloadPath"]:
        return prefClass.settings.value("PluginManager/" + key,
            prefClass.pluginManagerDefaults[key])
    else:
        return toBool(prefClass.settings.value("PluginManager/" + key,
            prefClass.pluginManagerDefaults[key]))
    

def setPluginManager(key, value, prefClass=Prefs):
    """
    Module function to store the plugin manager related settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("PluginManager/" + key, value)
    

def getGraphics(key, prefClass=Prefs):
    """
    Module function to retrieve the Graphics related settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested user setting
    """
    if key in ["Font"]:
        font = prefClass.settings.value("Graphics/" + key,
            prefClass.graphicsDefaults[key])
        if isinstance(font, QtGui.QFont):
            # workaround for an old bug in eric < 4.4
            return font
        else:
            f = QtGui.QFont()
            f.fromString(font)
            return f
    else:
        return prefClass.settings.value("Graphics/" + key,
            prefClass.graphicsDefaults[key])
    

def setGraphics(key, value, prefClass=Prefs):
    """
    Module function to store the Graphics related settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    if key in ["Font"]:
        prefClass.settings.setValue("Graphics/" + key, value.toString())
    else:
        prefClass.settings.setValue("Graphics/" + key, value)
    

def getIconEditor(key, prefClass=Prefs):
    """
    Module function to retrieve the Icon Editor related settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested user setting
    """
    return prefClass.settings.value("IconEditor/" + key,
        prefClass.iconEditorDefaults[key])
    

def setIconEditor(key, value, prefClass=Prefs):
    """
    Module function to store the Icon Editor related settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("IconEditor/" + key, value)


def getFlakes(key, prefClass=Prefs):
    """
    Module function to retrieve the py3flakes related settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested user setting
    """
    if key in ["IncludeInSyntaxCheck", "IgnoreStarImportWarnings"]:
        return toBool(prefClass.settings.value("Py3Flakes/" + key,
            prefClass.py3flakesDefaults[key]))
    else:
        return prefClass.settings.value("Py3Flakes/" + key,
            prefClass.py3flakesDefaults[key])
    

def setFlakes(key, value, prefClass=Prefs):
    """
    Module function to store the py3flakes related settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("Py3Flakes/" + key, value)


def getTrayStarter(key, prefClass=Prefs):
    """
    Module function to retrieve the tray starter related settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested user setting
    """
    return prefClass.settings.value("TrayStarter/" + key,
            prefClass.trayStarterDefaults[key])
    

def setTrayStarter(key, value, prefClass=Prefs):
    """
    Module function to store the tray starter related settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("TrayStarter/" + key, value)
    

def getGeometry(key, prefClass=Prefs):
    """
    Module function to retrieve the display geometry.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested geometry setting
    """
    if key in ["MainMaximized"]:
        return toBool(prefClass.settings.value("Geometry/" + key,
            prefClass.geometryDefaults[key]))
    else:
        v = prefClass.settings.value("Geometry/" + key)
        if v is not None:
            return v
        else:
            return prefClass.geometryDefaults[key]


def setGeometry(key, value, prefClass=Prefs):
    """
    Module function to store the display geometry.
    
    @param key the key of the setting to be set
    @param value the geometry to be set
    @param prefClass preferences class used as the storage area
    """
    if key in ["MainMaximized"]:
        prefClass.settings.setValue("Geometry/" + key, value)
    else:
        if prefClass.resetLayout:
            v = prefClass.geometryDefaults[key]
        else:
            v = value
        prefClass.settings.setValue("Geometry/" + key, v)


def resetLayout(prefClass=Prefs):
    """
    Module function to set a flag not storing the current layout.
    
    @param prefClass preferences class used as the storage area
    """
    prefClass.resetLayout = True


def shouldResetLayout(prefClass=Prefs):
    """
    Module function to indicate a reset of the layout.
    
    @param prefClass preferences class used as the storage area
    @return flag indicating a reset of the layout (boolean)
    """
    return prefClass.resetLayout
    

def saveResetLayout(prefClass=Prefs):
    """
    Module function to save the reset layout.
    """
    if prefClass.resetLayout:
        for key in list(prefClass.geometryDefaults.keys()):
            prefClass.settings.setValue("Geometry/" + key,
                prefClass.geometryDefaults[key])


def toBool(value):
    """
    Module function to convert a value to bool.
    
    @param value value to be converted
    @return converted data
    """
    if value in ["true", "1", "True"]:
        return True
    elif value in ["false", "0", "False"]:
        return False
    else:
        return bool(value)


def toList(value):
    """
    Module function to convert a value to a list.
    
    @param value value to be converted
    @return converted data
    """
    if value is None:
        return []
    elif not isinstance(value, list):
        return [value]
    else:
        return value


def toByteArray(value):
    """
    Module function to convert a value to a byte array.
    
    @param value value to be converted
    @return converted data
    """
    if value is None:
        return QtCore.QByteArray()
    else:
        return value


def toDict(value):
    """
    Module function to convert a value to a dictionary.
    
    @param value value to be converted
    @return converted data
    """
    if value is None:
        return {}
    else:
        return value
    
initPreferences()
initRecentSettings()
