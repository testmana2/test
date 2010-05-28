# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Editor Properties configuration page.
"""

from QScintilla.QsciScintillaCompat import QSCINTILLA_VERSION

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_EditorPropertiesPage import Ui_EditorPropertiesPage

import Preferences

class EditorPropertiesPage(ConfigurationPageBase, Ui_EditorPropertiesPage):
    """
    Class implementing the Editor Properties configuration page.
    """
    def __init__(self, lexers):
        """
        Constructor
        
        @param lexers reference to the lexers dictionary
        """
        ConfigurationPageBase.__init__(self)
        self.setupUi(self)
        self.setObjectName("EditorPropertiesPage")
        
        self.languages = sorted(list(lexers.keys())[:])
        
        # set initial values
        # All
        self.allFoldCompactCheckBox.setChecked(\
            Preferences.getEditor("AllFoldCompact"))
        
        # Bash
        self.foldBashCommentCheckBox.setChecked(\
            Preferences.getEditor("BashFoldComment"))
        
        # CMake
        self.cmakeFoldAtElseCheckBox.setChecked(\
            Preferences.getEditor("CMakeFoldAtElse"))
        
        # C++
        self.foldCppCommentCheckBox.setChecked(\
            Preferences.getEditor("CppFoldComment"))
        self.foldCppPreprocessorCheckBox.setChecked(\
            Preferences.getEditor("CppFoldPreprocessor"))
        self.foldCppAtElseCheckBox.setChecked(\
            Preferences.getEditor("CppFoldAtElse"))
        self.cppIndentOpeningBraceCheckBox.setChecked(\
            Preferences.getEditor("CppIndentOpeningBrace"))
        self.cppIndentClosingBraceCheckBox.setChecked(\
            Preferences.getEditor("CppIndentClosingBrace"))
        self.cppCaseInsensitiveCheckBox.setChecked(\
            Preferences.getEditor("CppCaseInsensitiveKeywords"))
        self.cppDollarAllowedCheckBox.setChecked(
            Preferences.getEditor("CppDollarsAllowed"))
        
        # CSS
        self.foldCssCommentCheckBox.setChecked(\
            Preferences.getEditor("CssFoldComment"))
        
        # D
        self.foldDCommentCheckBox.setChecked(\
            Preferences.getEditor("DFoldComment"))
        self.foldDAtElseCheckBox.setChecked(\
            Preferences.getEditor("DFoldAtElse"))
        self.dIndentOpeningBraceCheckBox.setChecked(\
            Preferences.getEditor("DIndentOpeningBrace"))
        self.dIndentClosingBraceCheckBox.setChecked(\
            Preferences.getEditor("DIndentClosingBrace"))
        
        # HTML
        self.foldHtmlPreprocessorCheckBox.setChecked(\
            Preferences.getEditor("HtmlFoldPreprocessor"))
        self.htmlCaseSensitiveTagsCheckBox.setChecked(\
            Preferences.getEditor("HtmlCaseSensitiveTags"))
        self.foldHtmlScriptCommentsCheckBox.setChecked(
            Preferences.getEditor("HtmlFoldScriptComments"))
        self.foldHtmlScriptHereDocsCheckBox.setChecked(
            Preferences.getEditor("HtmlFoldScriptHeredocs"))
        
        # Pascal
        if "Pascal" in self.languages:
            self.pascalGroup.setEnabled(True)
            self.foldPascalCommentCheckBox.setChecked(\
                Preferences.getEditor("PascalFoldComment"))
            self.foldPascalPreprocessorCheckBox.setChecked(\
                Preferences.getEditor("PascalFoldPreprocessor"))
            if QSCINTILLA_VERSION() >= 0x020400:
                self.pascalSmartHighlightingCheckBox.setChecked(
                    Preferences.getEditor("PascalSmartHighlighting"))
            else:
                self.pascalSmartHighlightingCheckBox.setEnabled(False)
        else:
            self.pascalGroup.setEnabled(False)
        
        # Perl
        self.foldPerlCommentCheckBox.setChecked(\
            Preferences.getEditor("PerlFoldComment"))
        self.foldPerlPackagesCheckBox.setChecked(
            Preferences.getEditor("PerlFoldPackages"))
        self.foldPerlPODBlocksCheckBox.setChecked(
            Preferences.getEditor("PerlFoldPODBlocks"))
        
        # PostScript
        if "PostScript" in self.languages:
            self.postscriptGroup.setEnabled(True)
            self.psFoldAtElseCheckBox.setChecked(\
                Preferences.getEditor("PostScriptFoldAtElse"))
            self.psMarkTokensCheckBox.setChecked(\
                Preferences.getEditor("PostScriptTokenize"))
            self.psLevelSpinBox.setValue(\
                Preferences.getEditor("PostScriptLevel"))
        else:
            self.postscriptGroup.setEnabled(False)
        
        # Povray
        self.foldPovrayCommentCheckBox.setChecked(\
            Preferences.getEditor("PovFoldComment"))
        self.foldPovrayDirectivesCheckBox.setChecked(\
            Preferences.getEditor("PovFoldDirectives"))
        
        # Python
        self.foldPythonCommentCheckBox.setChecked(\
            Preferences.getEditor("PythonFoldComment"))
        self.foldPythonStringCheckBox.setChecked(\
            Preferences.getEditor("PythonFoldString"))
        self.pythonBadIndentationCheckBox.setChecked(\
            Preferences.getEditor("PythonBadIndentation"))
        self.pythonAutoindentCheckBox.setChecked(\
            Preferences.getEditor("PythonAutoIndent"))
        self.pythonV2UnicodeAllowedCheckBox.setChecked(
            Preferences.getEditor("PythonAllowV2Unicode"))
        self.pythonV3BinaryAllowedCheckBox.setChecked(
            Preferences.getEditor("PythonAllowV3Binary"))
        self.pythonV3BytesAllowedCheckBox.setChecked(
            Preferences.getEditor("PythonAllowV3Bytes"))
        
        # SQL
        self.foldSqlCommentCheckBox.setChecked(\
            Preferences.getEditor("SqlFoldComment"))
        self.sqlBackslashEscapesCheckBox.setChecked(\
            Preferences.getEditor("SqlBackslashEscapes"))
        
        # VHDL
        self.vhdlFoldCommentCheckBox.setChecked(\
            Preferences.getEditor("VHDLFoldComment"))
        self.vhdlFoldAtElseCheckBox.setChecked(\
            Preferences.getEditor("VHDLFoldAtElse"))
        self.vhdlFoldAtBeginCheckBox.setChecked(\
            Preferences.getEditor("VHDLFoldAtBegin"))
        self.vhdlFoldAtParenthesisCheckBox.setChecked(\
            Preferences.getEditor("VHDLFoldAtParenthesis"))
        
        # XML
        self.xmlSyleScriptsCheckBox.setChecked(
            Preferences.getEditor("XMLStyleScripts"))
        
        # YAML
        if "YAML" in self.languages:
            self.yamlGroup.setEnabled(True)
            self.foldYamlCommentCheckBox.setChecked(\
                Preferences.getEditor("YAMLFoldComment"))
        else:
            self.yamlGroup.setEnabled(False)
        
    def save(self):
        """
        Public slot to save the Editor Properties (1) configuration.
        """
        # All
        Preferences.setEditor("AllFoldCompact",
            self.allFoldCompactCheckBox.isChecked())
        
        # Bash
        Preferences.setEditor("BashFoldComment",
            self.foldBashCommentCheckBox.isChecked())
        
        # CMake
        Preferences.setEditor("CMakeFoldAtElse",
            self.cmakeFoldAtElseCheckBox.isChecked())
        
        # C++
        Preferences.setEditor("CppFoldComment",
            self.foldCppCommentCheckBox.isChecked())
        Preferences.setEditor("CppFoldPreprocessor",
            self.foldCppPreprocessorCheckBox.isChecked())
        Preferences.setEditor("CppFoldAtElse",
            self.foldCppAtElseCheckBox.isChecked())
        Preferences.setEditor("CppIndentOpeningBrace",
            self.cppIndentOpeningBraceCheckBox.isChecked())
        Preferences.setEditor("CppIndentClosingBrace",
            self.cppIndentClosingBraceCheckBox.isChecked())
        Preferences.setEditor("CppCaseInsensitiveKeywords",
            self.cppCaseInsensitiveCheckBox.isChecked())
        Preferences.setEditor("CppDollarsAllowed",
            self.cppDollarAllowedCheckBox.isChecked())
        
        # CSS
        Preferences.setEditor("CssFoldComment",
            self.foldCssCommentCheckBox.isChecked())
        
        # D
        Preferences.setEditor("DFoldComment",
            self.foldDCommentCheckBox.isChecked())
        Preferences.setEditor("DFoldAtElse",
            self.foldDAtElseCheckBox.isChecked())
        Preferences.setEditor("DIndentOpeningBrace",
            self.dIndentOpeningBraceCheckBox.isChecked())
        Preferences.setEditor("DIndentClosingBrace",
            self.dIndentClosingBraceCheckBox.isChecked())
        
        # HTML
        Preferences.setEditor("HtmlFoldPreprocessor",
            self.foldHtmlPreprocessorCheckBox.isChecked())
        Preferences.setEditor("HtmlCaseSensitiveTags",
            self.htmlCaseSensitiveTagsCheckBox.isChecked())
        Preferences.setEditor("HtmlFoldScriptComments",
            self.foldHtmlScriptCommentsCheckBox.isChecked())
        Preferences.setEditor("HtmlFoldScriptHeredocs",
            self.foldHtmlScriptHereDocsCheckBox.isChecked())
        
        # Pascal
        if "Pascal" in self.languages:
            Preferences.setEditor("PascalFoldComment",
                self.foldPascalCommentCheckBox.isChecked())
            Preferences.setEditor("PascalFoldPreprocessor",
                self.foldPascalPreprocessorCheckBox.isChecked())
            Preferences.setEditor("PascalSmartHighlighting",
                self.pascalSmartHighlightingCheckBox.isChecked())
        
        # Perl
        Preferences.setEditor("PerlFoldComment",
            self.foldPerlCommentCheckBox.isChecked())
        Preferences.setEditor("PerlFoldPackages",
            self.foldPerlPackagesCheckBox.isChecked())
        Preferences.setEditor("PerlFoldPODBlocks",
            self.foldPerlPODBlocksCheckBox.isChecked())
        
        # PostScript
        if "PostScript" in self.languages:
            Preferences.setEditor("PostScriptFoldAtElse",
                self.psFoldAtElseCheckBox.isChecked())
            Preferences.setEditor("PostScriptTokenize",
                self.psMarkTokensCheckBox.isChecked())
            Preferences.setEditor("PostScriptLevel", 
                self.psLevelSpinBox.value())
        
        # Povray
        Preferences.setEditor("PovFoldComment",
            self.foldPovrayCommentCheckBox.isChecked())
        Preferences.setEditor("PovFoldDirectives",
            self.foldPovrayDirectivesCheckBox.isChecked())
        
        # Python
        Preferences.setEditor("PythonFoldComment",
            self.foldPythonCommentCheckBox.isChecked())
        Preferences.setEditor("PythonFoldString",
            self.foldPythonStringCheckBox.isChecked())
        Preferences.setEditor("PythonBadIndentation",
            self.pythonBadIndentationCheckBox.isChecked())
        Preferences.setEditor("PythonAutoIndent",
            self.pythonAutoindentCheckBox.isChecked())
        Preferences.setEditor("PythonAllowV2Unicode",
            self.pythonV2UnicodeAllowedCheckBox.isChecked())
        Preferences.setEditor("PythonAllowV3Binary",
            self.pythonV3BinaryAllowedCheckBox.isChecked())
        Preferences.setEditor("PythonAllowV3Bytes",
            self.pythonV3BytesAllowedCheckBox.isChecked())
        
        # SQL
        Preferences.setEditor("SqlFoldComment",
            self.foldSqlCommentCheckBox.isChecked())
        Preferences.setEditor("SqlBackslashEscapes",
            self.sqlBackslashEscapesCheckBox.isChecked())
        
        # VHDL
        Preferences.setEditor("VHDLFoldComment",
            self.vhdlFoldCommentCheckBox.isChecked())
        Preferences.setEditor("VHDLFoldAtElse",
            self.vhdlFoldAtElseCheckBox.isChecked())
        Preferences.setEditor("VHDLFoldAtBegin",
            self.vhdlFoldAtBeginCheckBox.isChecked())
        Preferences.setEditor("VHDLFoldAtParenthesis",
            self.vhdlFoldAtParenthesisCheckBox.isChecked())
        
        # XML
        Preferences.setEditor("XMLStyleScripts",
            self.xmlSyleScriptsCheckBox.isChecked())
        
        # YAML
        if "YAML" in self.languages:
            Preferences.setEditor("YAMLFoldComment", 
                self.foldYamlCommentCheckBox.isChecked())

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    """
    page = EditorPropertiesPage(dlg.getLexers())
    return page
