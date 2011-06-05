# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the viewmanager base class.
"""

import os

from PyQt4.QtCore import QSignalMapper, QTimer, QFileInfo, pyqtSignal, QRegExp, \
    QObject, Qt
from PyQt4.QtGui import QColor, QKeySequence, QLineEdit, QToolBar, QWidgetAction, \
    QDialog, QApplication, QMenu, QPalette, QComboBox
from PyQt4.Qsci import QsciScintilla

from E5Gui.E5Application import e5App
from E5Gui import E5FileDialog, E5MessageBox

from Globals import recentNameFiles

import Preferences

from .BookmarkedFilesDialog import BookmarkedFilesDialog

from QScintilla.Editor import Editor
from QScintilla.GotoDialog import GotoDialog
from QScintilla.SearchReplaceWidget import SearchReplaceWidget
from QScintilla.ZoomDialog import ZoomDialog
from QScintilla.APIsManager import APIsManager
from QScintilla.SpellChecker import SpellChecker
import QScintilla.Lexers
import QScintilla.Exporters
from QScintilla.Shell import Shell
from QScintilla.Terminal import Terminal

import Utilities

import UI.PixmapCache
import UI.Config

from E5Gui.E5Action import E5Action, createActionGroup


class QuickSearchLineEdit(QLineEdit):
    """
    Class implementing a line edit that reacts to newline and cancel commands.
    
    @signal escPressed() emitted after the cancel command was activated
    @signal returnPressed() emitted after a newline command was activated
    @signal gotFocus() emitted when the focus is changed to this widget
    """
    escPressed = pyqtSignal()
    gotFocus = pyqtSignal()
    
    def editorCommand(self, cmd):
        """
        Public method to perform an editor command.
        
        @param cmd the scintilla command to be performed
        """
        if cmd == QsciScintilla.SCI_NEWLINE:
            cb = self.parent()
            hasEntry = cb.findText(self.text()) != -1
            if not hasEntry:
                if cb.insertPolicy() == QComboBox.InsertAtTop:
                    cb.insertItem(0, self.text())
                else:
                    cb.addItem(self.text())
            self.returnPressed.emit()
        elif cmd == QsciScintilla.SCI_CANCEL:
            self.escPressed.emit()
    
    def keyPressEvent(self, evt):
        """
        Re-implemented to handle the press of the ESC key.
        
        @param evt key event (QKeyPressEvent)
        """
        if evt.key() == Qt.Key_Escape:
            self.escPressed.emit()
        else:
            QLineEdit.keyPressEvent(self, evt)  # pass it on
    
    def focusInEvent(self, evt):
        """
        Re-implemented to record the current editor widget.
        
        @param evt focus event (QFocusEvent)
        """
        self.gotFocus.emit()
        QLineEdit.focusInEvent(self, evt)   # pass it on


class ViewManager(QObject):
    """
    Base class inherited by all specific viewmanager classes.
    
    It defines the interface to be implemented by specific
    viewmanager classes and all common methods.
    
    @signal lastEditorClosed() emitted after the last editor window was closed
    @signal editorOpened(str) emitted after an editor window was opened
    @signal editorOpenedEd(Editor) emitted after an editor window was opened
    @signal editorClosed(str) emitted just before an editor window gets closed
    @signal editorClosedEd(Editor) emitted just before an editor window gets closed
    @signal editorSaved(str) emitted after an editor window was saved
    @signal checkActions(Editor) emitted when some actions should be checked
            for their status
    @signal cursorChanged(Editor) emitted after the cursor position of the active
            window has changed
    @signal breakpointToggled(Editor) emitted when a breakpoint is toggled.
    @signal bookmarkToggled(Editor) emitted when a bookmark is toggled.
    """
    lastEditorClosed = pyqtSignal()
    editorOpened = pyqtSignal(str)
    editorOpenedEd = pyqtSignal(Editor)
    editorClosed = pyqtSignal(str)
    editorClosedEd = pyqtSignal(Editor)
    editorSaved = pyqtSignal(str)
    checkActions = pyqtSignal(Editor)
    cursorChanged = pyqtSignal(Editor)
    breakpointToggled = pyqtSignal(Editor)
    bookmarkToggled = pyqtSignal(Editor)
    syntaxerrorToggled = pyqtSignal(Editor)
    
    def __init__(self):
        """
        Constructor
        
        @param ui reference to the main user interface
        @param dbs reference to the debug server object
        """
        QObject.__init__(self)
        
        # initialize the instance variables
        self.editors = []
        self.currentEditor = None
        self.untitledCount = 0
        self.srHistory = {
            "search": [],
            "replace": []
        }
        self.editorsCheckFocusIn = True
        
        self.recent = []
        self.__loadRecent()
        
        self.bookmarked = []
        bs = Preferences.Prefs.settings.value("Bookmarked/Sources")
        if bs is not None:
            self.bookmarked = bs
        
        # initialize the autosave timer
        self.autosaveInterval = Preferences.getEditor("AutosaveInterval")
        self.autosaveTimer = QTimer(self)
        self.autosaveTimer.setObjectName("AutosaveTimer")
        self.autosaveTimer.setSingleShot(True)
        self.autosaveTimer.timeout.connect(self.__autosave)
        
        # initialize the APIs manager
        self.apisManager = APIsManager(parent=self)
        
        self.__cooperationClient = None
        
        self.__lastFocusWidget = None
        
    def setReferences(self, ui, dbs):
        """
        Public method to set some references needed later on.
        
        @param ui reference to the main user interface
        @param dbs reference to the debug server object
        """
        self.ui = ui
        self.dbs = dbs
        
        self.searchDlg = SearchReplaceWidget(False, self, ui)
        self.replaceDlg = SearchReplaceWidget(True, self, ui)
        
        self.checkActions.connect(self.searchDlg.updateSelectionCheckBox)
        self.checkActions.connect(self.replaceDlg.updateSelectionCheckBox)
        
    def __loadRecent(self):
        """
        Private method to load the recently opened filenames.
        """
        self.recent = []
        Preferences.Prefs.rsettings.sync()
        rs = Preferences.Prefs.rsettings.value(recentNameFiles)
        if rs is not None:
            for f in Preferences.toList(rs):
                if QFileInfo(f).exists():
                    self.recent.append(f)
        
    def __saveRecent(self):
        """
        Private method to save the list of recently opened filenames.
        """
        Preferences.Prefs.rsettings.setValue(recentNameFiles, self.recent)
        Preferences.Prefs.rsettings.sync()
        
    def getMostRecent(self):
        """
        Public method to get the most recently opened file.
        
        @return path of the most recently opened file (string)
        """
        if len(self.recent):
            return self.recent[0]
        else:
            return None
        
    def setSbInfo(self, sbFile, sbLine, sbPos, sbWritable, sbEncoding, sbLanguage, sbEol):
        """
        Public method to transfer statusbar info from the user interface to viewmanager.
        
        @param sbFile reference to the file part of the statusbar (E5SqueezeLabelPath)
        @param sbLine reference to the line number part of the statusbar (QLabel)
        @param sbPos reference to the character position part of the statusbar (QLabel)
        @param sbWritable reference to the writability indicator part of
            the statusbar (QLabel)
        @param sbEncoding reference to the encoding indicator part of the
            statusbar (QLabel)
        @param sbLanguage reference to the language indicator part of the
            statusbar (QLabel)
        @param sbEol reference to the eol indicator part of the statusbar (QLabel)
        """
        self.sbFile = sbFile
        self.sbLine = sbLine
        self.sbPos = sbPos
        self.sbWritable = sbWritable
        self.sbEnc = sbEncoding
        self.sbLang = sbLanguage
        self.sbEol = sbEol
        self.__setSbFile()
    
    ############################################################################
    ## methods below need to be implemented by a subclass
    ############################################################################
    
    def canCascade(self):
        """
        Public method to signal if cascading of managed windows is available.
        
        @return flag indicating cascading of windows is available
        @exception RuntimeError Not implemented
        """
        raise RuntimeError('Not implemented')
        
    def canTile(self):
        """
        Public method to signal if tiling of managed windows is available.
        
        @return flag indicating tiling of windows is available
        @exception RuntimeError Not implemented
        """
        raise RuntimeError('Not implemented')
        
    def tile(self):
        """
        Public method to tile the managed windows.
        
        @exception RuntimeError Not implemented
        """
        raise RuntimeError('Not implemented')
        
    def cascade(self):
        """
        Public method to cascade the managed windows.
        
        @exception RuntimeError Not implemented
        """
        raise RuntimeError('Not implemented')
        
    def activeWindow(self):
        """
        Public method to return the active (i.e. current) window.
        
        @return reference to the active editor
        @exception RuntimeError Not implemented
        """
        raise RuntimeError('Not implemented')
        
    def _removeAllViews(self):
        """
        Protected method to remove all views (i.e. windows)
        
        @exception RuntimeError Not implemented
        """
        raise RuntimeError('Not implemented')
        
    def _removeView(self, win):
        """
        Protected method to remove a view (i.e. window)
        
        @param win editor window to be removed
        @exception RuntimeError Not implemented
        """
        raise RuntimeError('Not implemented')
        
    def _addView(self, win, fn=None, noName=""):
        """
        Protected method to add a view (i.e. window)
        
        @param win editor window to be added
        @param fn filename of this editor
        @param noName name to be used for an unnamed editor (string)
        @exception RuntimeError Not implemented
        """
        raise RuntimeError('Not implemented')
        
    def _showView(self, win, fn=None):
        """
        Protected method to show a view (i.e. window)
        
        @param win editor window to be shown
        @param fn filename of this editor
        @exception RuntimeError Not implemented
        """
        raise RuntimeError('Not implemented')
        
    def showWindowMenu(self, windowMenu):
        """
        Public method to set up the viewmanager part of the Window menu.
        
        @param windowMenu reference to the window menu
        @exception RuntimeError Not implemented
        """
        raise RuntimeError('Not implemented')
        
    def _initWindowActions(self):
        """
        Protected method to define the user interface actions for window handling.
        
        @exception RuntimeError Not implemented
        """
        raise RuntimeError('Not implemented')
        
    def setEditorName(self, editor, newName):
        """
        Public method to change the displayed name of the editor.
        
        @param editor editor window to be changed
        @param newName new name to be shown (string)
        @exception RuntimeError Not implemented
        """
        raise RuntimeError('Not implemented')
        
    def _modificationStatusChanged(self, m, editor):
        """
        Protected slot to handle the modificationStatusChanged signal.
        
        @param m flag indicating the modification status (boolean)
        @param editor editor window changed
        @exception RuntimeError Not implemented
        """
        raise RuntimeError('Not implemented')
    
    #####################################################################
    ## methods above need to be implemented by a subclass
    #####################################################################
    
    def canSplit(self):
        """
        Public method to signal if splitting of the view is available.
        
        @return flag indicating splitting of the view is available.
        """
        return False
        
    def addSplit(self):
        """
        Public method used to split the current view.
        """
        pass
        
    def removeSplit(self):
        """
        Public method used to remove the current split view.
        
        @return Flag indicating successful deletion
        """
        return False
        
    def setSplitOrientation(self, orientation):
        """
        Public method used to set the orientation of the split view.
        
        @param orientation orientation of the split
                (Qt.Horizontal or Qt.Vertical)
        """
        pass
        
    def nextSplit(self):
        """
        Public slot used to move to the next split.
        """
        pass
        
    def prevSplit(self):
        """
        Public slot used to move to the previous split.
        """
        pass
        
    def eventFilter(self, object, event):
        """
        Public method called to filter an event.
        
        @param object object, that generated the event (QObject)
        @param event the event, that was generated by object (QEvent)
        @return flag indicating if event was filtered out
        """
        return False
    
    #####################################################################
    ## methods above need to be implemented by a subclass, that supports
    ## splitting of the viewmanager area.
    #####################################################################
    
    def initActions(self):
        """
        Public method defining the user interface actions.
        """
        # list containing all edit actions
        self.editActions = []
        
        # list containing all file actions
        self.fileActions = []
        
        # list containing all search actions
        self.searchActions = []
        
        # list containing all view actions
        self.viewActions = []
        
        # list containing all window actions
        self.windowActions = []
        
        # list containing all macro actions
        self.macroActions = []
        
        # list containing all bookmark actions
        self.bookmarkActions = []
        
        # list containing all spell checking actions
        self.spellingActions = []
        
        self.__actions = {
            "bookmark": self.bookmarkActions,
            "edit": self.editActions,
            "file": self.fileActions,
            "macro": self.macroActions,
            "search": self.searchActions,
            "spelling": self.spellingActions,
            "view": self.viewActions,
            "window": self.windowActions,
        }
        
        self._initWindowActions()
        self.__initFileActions()
        self.__initEditActions()
        self.__initSearchActions()
        self.__initViewActions()
        self.__initMacroActions()
        self.__initBookmarkActions()
        self.__initSpellingActions()
        
    ##################################################################
    ## Initialize the file related actions, file menu and toolbar
    ##################################################################
    
    def __initFileActions(self):
        """
        Private method defining the user interface actions for file handling.
        """
        self.newAct = E5Action(QApplication.translate('ViewManager', 'New'),
                UI.PixmapCache.getIcon("new.png"),
                QApplication.translate('ViewManager', '&New'),
                QKeySequence(QApplication.translate('ViewManager', "Ctrl+N", "File|New")),
                0, self, 'vm_file_new')
        self.newAct.setStatusTip(
            QApplication.translate('ViewManager', 'Open an empty editor window'))
        self.newAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>New</b>"""
            """<p>An empty editor window will be created.</p>"""
        ))
        self.newAct.triggered[()].connect(self.newEditor)
        self.fileActions.append(self.newAct)
        
        self.openAct = E5Action(QApplication.translate('ViewManager', 'Open'),
                UI.PixmapCache.getIcon("open.png"),
                QApplication.translate('ViewManager', '&Open...'),
                QKeySequence(
                    QApplication.translate('ViewManager', "Ctrl+O", "File|Open")),
                0, self, 'vm_file_open')
        self.openAct.setStatusTip(QApplication.translate('ViewManager', 'Open a file'))
        self.openAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Open a file</b>"""
            """<p>You will be asked for the name of a file to be opened"""
            """ in an editor window.</p>"""
        ))
        self.openAct.triggered[()].connect(self.openFiles)
        self.fileActions.append(self.openAct)
        
        self.closeActGrp = createActionGroup(self)
        
        self.closeAct = E5Action(QApplication.translate('ViewManager', 'Close'),
                UI.PixmapCache.getIcon("close.png"),
                QApplication.translate('ViewManager', '&Close'),
                QKeySequence(
                    QApplication.translate('ViewManager', "Ctrl+W", "File|Close")),
                0, self.closeActGrp, 'vm_file_close')
        self.closeAct.setStatusTip(
            QApplication.translate('ViewManager', 'Close the current window'))
        self.closeAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Close Window</b>"""
            """<p>Close the current window.</p>"""
        ))
        self.closeAct.triggered[()].connect(self.closeCurrentWindow)
        self.fileActions.append(self.closeAct)
        
        self.closeAllAct = E5Action(QApplication.translate('ViewManager', 'Close All'),
                QApplication.translate('ViewManager', 'Clos&e All'),
                0, 0, self.closeActGrp, 'vm_file_close_all')
        self.closeAllAct.setStatusTip(
            QApplication.translate('ViewManager', 'Close all editor windows'))
        self.closeAllAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Close All Windows</b>"""
            """<p>Close all editor windows.</p>"""
        ))
        self.closeAllAct.triggered[()].connect(self.closeAllWindows)
        self.fileActions.append(self.closeAllAct)
        
        self.closeActGrp.setEnabled(False)
        
        self.saveActGrp = createActionGroup(self)
        
        self.saveAct = E5Action(QApplication.translate('ViewManager', 'Save'),
                UI.PixmapCache.getIcon("fileSave.png"),
                QApplication.translate('ViewManager', '&Save'),
                QKeySequence(
                    QApplication.translate('ViewManager', "Ctrl+S", "File|Save")),
                0, self.saveActGrp, 'vm_file_save')
        self.saveAct.setStatusTip(
            QApplication.translate('ViewManager', 'Save the current file'))
        self.saveAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Save File</b>"""
            """<p>Save the contents of current editor window.</p>"""
        ))
        self.saveAct.triggered[()].connect(self.saveCurrentEditor)
        self.fileActions.append(self.saveAct)
        
        self.saveAsAct = E5Action(QApplication.translate('ViewManager', 'Save as'),
                UI.PixmapCache.getIcon("fileSaveAs.png"),
                QApplication.translate('ViewManager', 'Save &as...'),
                QKeySequence(QApplication.translate('ViewManager',
                    "Shift+Ctrl+S", "File|Save As")),
                0, self.saveActGrp, 'vm_file_save_as')
        self.saveAsAct.setStatusTip(QApplication.translate('ViewManager',
            'Save the current file to a new one'))
        self.saveAsAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Save File as</b>"""
            """<p>Save the contents of current editor window to a new file."""
            """ The file can be entered in a file selection dialog.</p>"""
        ))
        self.saveAsAct.triggered[()].connect(self.saveAsCurrentEditor)
        self.fileActions.append(self.saveAsAct)
        
        self.saveAllAct = E5Action(QApplication.translate('ViewManager', 'Save all'),
                UI.PixmapCache.getIcon("fileSaveAll.png"),
                QApplication.translate('ViewManager', 'Save a&ll...'),
                0, 0, self.saveActGrp, 'vm_file_save_all')
        self.saveAllAct.setStatusTip(QApplication.translate('ViewManager',
            'Save all files'))
        self.saveAllAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Save All Files</b>"""
            """<p>Save the contents of all editor windows.</p>"""
        ))
        self.saveAllAct.triggered[()].connect(self.saveAllEditors)
        self.fileActions.append(self.saveAllAct)
        
        self.saveActGrp.setEnabled(False)

        self.printAct = E5Action(QApplication.translate('ViewManager', 'Print'),
                UI.PixmapCache.getIcon("print.png"),
                QApplication.translate('ViewManager', '&Print'),
                QKeySequence(QApplication.translate('ViewManager',
                    "Ctrl+P", "File|Print")),
                0, self, 'vm_file_print')
        self.printAct.setStatusTip(QApplication.translate('ViewManager',
            'Print the current file'))
        self.printAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Print File</b>"""
            """<p>Print the contents of current editor window.</p>"""
        ))
        self.printAct.triggered[()].connect(self.printCurrentEditor)
        self.printAct.setEnabled(False)
        self.fileActions.append(self.printAct)
        
        self.printPreviewAct = \
            E5Action(QApplication.translate('ViewManager', 'Print Preview'),
                UI.PixmapCache.getIcon("printPreview.png"),
                QApplication.translate('ViewManager', 'Print Preview'),
                0, 0, self, 'vm_file_print_preview')
        self.printPreviewAct.setStatusTip(QApplication.translate('ViewManager',
            'Print preview of the current file'))
        self.printPreviewAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Print Preview</b>"""
            """<p>Print preview of the current editor window.</p>"""
        ))
        self.printPreviewAct.triggered[()].connect(self.printPreviewCurrentEditor)
        self.printPreviewAct.setEnabled(False)
        self.fileActions.append(self.printPreviewAct)
        
        self.findFileNameAct = E5Action(QApplication.translate('ViewManager',
                    'Search File'),
                QApplication.translate('ViewManager', 'Search &File...'),
                QKeySequence(QApplication.translate('ViewManager',
                    "Alt+Ctrl+F", "File|Search File")),
                0, self, 'vm_file_search_file')
        self.findFileNameAct.setStatusTip(QApplication.translate('ViewManager',
            'Search for a file'))
        self.findFileNameAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Search File</b>"""
            """<p>Search for a file.</p>"""
        ))
        self.findFileNameAct.triggered[()].connect(self.__findFileName)
        self.fileActions.append(self.findFileNameAct)
        
    def initFileMenu(self):
        """
        Public method to create the File menu.
        
        @return the generated menu
        """
        menu = QMenu(QApplication.translate('ViewManager', '&File'), self.ui)
        self.recentMenu = QMenu(QApplication.translate('ViewManager',
            'Open &Recent Files'), menu)
        self.bookmarkedMenu = QMenu(QApplication.translate('ViewManager',
            'Open &Bookmarked Files'), menu)
        self.exportersMenu = self.__initContextMenuExporters()
        menu.setTearOffEnabled(True)
        
        menu.addAction(self.newAct)
        menu.addAction(self.openAct)
        self.menuRecentAct = menu.addMenu(self.recentMenu)
        menu.addMenu(self.bookmarkedMenu)
        menu.addSeparator()
        menu.addAction(self.closeAct)
        menu.addAction(self.closeAllAct)
        menu.addSeparator()
        menu.addAction(self.findFileNameAct)
        menu.addSeparator()
        menu.addAction(self.saveAct)
        menu.addAction(self.saveAsAct)
        menu.addAction(self.saveAllAct)
        self.exportersMenuAct = menu.addMenu(self.exportersMenu)
        menu.addSeparator()
        menu.addAction(self.printPreviewAct)
        menu.addAction(self.printAct)
        
        self.recentMenu.aboutToShow.connect(self.__showRecentMenu)
        self.recentMenu.triggered.connect(self.__openSourceFile)
        self.bookmarkedMenu.aboutToShow.connect(self.__showBookmarkedMenu)
        self.bookmarkedMenu.triggered.connect(self.__openSourceFile)
        menu.aboutToShow.connect(self.__showFileMenu)
        
        self.exportersMenuAct.setEnabled(False)
        
        return menu
        
    def initFileToolbar(self, toolbarManager):
        """
        Public method to create the File toolbar.
        
        @param toolbarManager reference to a toolbar manager object (E5ToolBarManager)
        @return the generated toolbar
        """
        tb = QToolBar(QApplication.translate('ViewManager', 'File'), self.ui)
        tb.setIconSize(UI.Config.ToolBarIconSize)
        tb.setObjectName("FileToolbar")
        tb.setToolTip(QApplication.translate('ViewManager', 'File'))
        
        tb.addAction(self.newAct)
        tb.addAction(self.openAct)
        tb.addAction(self.closeAct)
        tb.addSeparator()
        tb.addAction(self.saveAct)
        tb.addAction(self.saveAsAct)
        tb.addAction(self.saveAllAct)
        
        toolbarManager.addToolBar(tb, tb.windowTitle())
        toolbarManager.addAction(self.printPreviewAct, tb.windowTitle())
        toolbarManager.addAction(self.printAct, tb.windowTitle())
        
        return tb
        
    def __initContextMenuExporters(self):
        """
        Private method used to setup the Exporters sub menu.
        """
        menu = QMenu(QApplication.translate('ViewManager', "Export as"))
        
        supportedExporters = QScintilla.Exporters.getSupportedFormats()
        exporters = sorted(list(supportedExporters.keys()))
        for exporter in exporters:
            act = menu.addAction(supportedExporters[exporter])
            act.setData(exporter)
        
        menu.triggered.connect(self.__exportMenuTriggered)
        
        return menu
    
    ##################################################################
    ## Initialize the edit related actions, edit menu and toolbar
    ##################################################################
    
    def __initEditActions(self):
        """
        Private method defining the user interface actions for the edit commands.
        """
        self.editActGrp = createActionGroup(self)
        
        self.undoAct = E5Action(QApplication.translate('ViewManager', 'Undo'),
                UI.PixmapCache.getIcon("editUndo.png"),
                QApplication.translate('ViewManager', '&Undo'),
                QKeySequence(QApplication.translate('ViewManager',
                    "Ctrl+Z", "Edit|Undo")),
                QKeySequence(QApplication.translate('ViewManager',
                    "Alt+Backspace", "Edit|Undo")),
                self.editActGrp, 'vm_edit_undo')
        self.undoAct.setStatusTip(QApplication.translate('ViewManager',
            'Undo the last change'))
        self.undoAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Undo</b>"""
            """<p>Undo the last change done in the current editor.</p>"""
        ))
        self.undoAct.triggered[()].connect(self.__editUndo)
        self.editActions.append(self.undoAct)
        
        self.redoAct = E5Action(QApplication.translate('ViewManager', 'Redo'),
                UI.PixmapCache.getIcon("editRedo.png"),
                QApplication.translate('ViewManager', '&Redo'),
                QKeySequence(QApplication.translate('ViewManager',
                    "Ctrl+Shift+Z", "Edit|Redo")),
                0, self.editActGrp, 'vm_edit_redo')
        self.redoAct.setStatusTip(QApplication.translate('ViewManager',
            'Redo the last change'))
        self.redoAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Redo</b>"""
            """<p>Redo the last change done in the current editor.</p>"""
        ))
        self.redoAct.triggered[()].connect(self.__editRedo)
        self.editActions.append(self.redoAct)
        
        self.revertAct = E5Action(QApplication.translate('ViewManager',
                    'Revert to last saved state'),
                QApplication.translate('ViewManager', 'Re&vert to last saved state'),
                QKeySequence(QApplication.translate('ViewManager',
                    "Ctrl+Y", "Edit|Revert")),
                0,
                self.editActGrp, 'vm_edit_revert')
        self.revertAct.setStatusTip(QApplication.translate('ViewManager',
            'Revert to last saved state'))
        self.revertAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Revert to last saved state</b>"""
            """<p>Undo all changes up to the last saved state"""
            """ of the current editor.</p>"""
        ))
        self.revertAct.triggered[()].connect(self.__editRevert)
        self.editActions.append(self.revertAct)
        
        self.copyActGrp = createActionGroup(self.editActGrp)
        
        self.cutAct = E5Action(QApplication.translate('ViewManager', 'Cut'),
                UI.PixmapCache.getIcon("editCut.png"),
                QApplication.translate('ViewManager', 'Cu&t'),
                QKeySequence(QApplication.translate('ViewManager', "Ctrl+X", "Edit|Cut")),
                QKeySequence(QApplication.translate('ViewManager',
                    "Shift+Del", "Edit|Cut")),
                self.copyActGrp, 'vm_edit_cut')
        self.cutAct.setStatusTip(QApplication.translate('ViewManager',
            'Cut the selection'))
        self.cutAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Cut</b>"""
            """<p>Cut the selected text of the current editor to the clipboard.</p>"""
        ))
        self.cutAct.triggered[()].connect(self.__editCut)
        self.editActions.append(self.cutAct)
        
        self.copyAct = E5Action(QApplication.translate('ViewManager', 'Copy'),
                UI.PixmapCache.getIcon("editCopy.png"),
                QApplication.translate('ViewManager', '&Copy'),
                QKeySequence(QApplication.translate('ViewManager',
                    "Ctrl+C", "Edit|Copy")),
                QKeySequence(QApplication.translate('ViewManager',
                    "Ctrl+Ins", "Edit|Copy")),
                self.copyActGrp, 'vm_edit_copy')
        self.copyAct.setStatusTip(QApplication.translate('ViewManager',
            'Copy the selection'))
        self.copyAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Copy</b>"""
            """<p>Copy the selected text of the current editor to the clipboard.</p>"""
        ))
        self.copyAct.triggered[()].connect(self.__editCopy)
        self.editActions.append(self.copyAct)
        
        self.pasteAct = E5Action(QApplication.translate('ViewManager', 'Paste'),
                UI.PixmapCache.getIcon("editPaste.png"),
                QApplication.translate('ViewManager', '&Paste'),
                QKeySequence(QApplication.translate('ViewManager',
                    "Ctrl+V", "Edit|Paste")),
                QKeySequence(QApplication.translate('ViewManager',
                    "Shift+Ins", "Edit|Paste")),
                self.copyActGrp, 'vm_edit_paste')
        self.pasteAct.setStatusTip(QApplication.translate('ViewManager',
            'Paste the last cut/copied text'))
        self.pasteAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Paste</b>"""
            """<p>Paste the last cut/copied text from the clipboard to"""
            """ the current editor.</p>"""
        ))
        self.pasteAct.triggered[()].connect(self.__editPaste)
        self.editActions.append(self.pasteAct)
        
        self.deleteAct = E5Action(QApplication.translate('ViewManager', 'Clear'),
                UI.PixmapCache.getIcon("editDelete.png"),
                QApplication.translate('ViewManager', 'Cl&ear'),
                QKeySequence(QApplication.translate('ViewManager',
                    "Alt+Shift+C", "Edit|Clear")),
                0,
                self.copyActGrp, 'vm_edit_clear')
        self.deleteAct.setStatusTip(QApplication.translate('ViewManager',
            'Clear all text'))
        self.deleteAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Clear</b>"""
            """<p>Delete all text of the current editor.</p>"""
        ))
        self.deleteAct.triggered[()].connect(self.__editDelete)
        self.editActions.append(self.deleteAct)
        
        self.joinAct = E5Action(QApplication.translate('ViewManager', 'Join Lines'),
                QApplication.translate('ViewManager', 'Join Lines'),
                QKeySequence(QApplication.translate('ViewManager',
                    "Ctrl+J", "Edit|Join Lines")),
                0,
                self.copyActGrp, 'vm_edit_join_lines')
        self.joinAct.setStatusTip(QApplication.translate('ViewManager',
            'Join Lines'))
        self.joinAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Join Lines</b>"""
            """<p>Join the current and the next lines.</p>"""
        ))
        self.joinAct.triggered[()].connect(self.__editJoin)
        self.editActions.append(self.joinAct)
        
        self.indentAct = E5Action(QApplication.translate('ViewManager', 'Indent'),
                UI.PixmapCache.getIcon("editIndent.png"),
                QApplication.translate('ViewManager', '&Indent'),
                QKeySequence(QApplication.translate('ViewManager',
                    "Ctrl+I", "Edit|Indent")),
                0,
                self.editActGrp, 'vm_edit_indent')
        self.indentAct.setStatusTip(QApplication.translate('ViewManager', 'Indent line'))
        self.indentAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Indent</b>"""
            """<p>Indents the current line or the lines of the"""
            """ selection by one level.</p>"""
        ))
        self.indentAct.triggered[()].connect(self.__editIndent)
        self.editActions.append(self.indentAct)
        
        self.unindentAct = E5Action(QApplication.translate('ViewManager', 'Unindent'),
                UI.PixmapCache.getIcon("editUnindent.png"),
                QApplication.translate('ViewManager', 'U&nindent'),
                QKeySequence(QApplication.translate('ViewManager',
                    "Ctrl+Shift+I", "Edit|Unindent")),
                0,
                self.editActGrp, 'vm_edit_unindent')
        self.unindentAct.setStatusTip(QApplication.translate('ViewManager',
            'Unindent line'))
        self.unindentAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Unindent</b>"""
            """<p>Unindents the current line or the lines of the"""
            """ selection by one level.</p>"""
        ))
        self.unindentAct.triggered[()].connect(self.__editUnindent)
        self.editActions.append(self.unindentAct)
        
        self.smartIndentAct = E5Action(QApplication.translate('ViewManager',
                    'Smart indent'),
                UI.PixmapCache.getIcon("editSmartIndent.png"),
                QApplication.translate('ViewManager', 'Smart indent'),
                QKeySequence(QApplication.translate('ViewManager',
                    "Ctrl+Alt+I", "Edit|Smart indent")),
                0,
                self.editActGrp, 'vm_edit_smart_indent')
        self.smartIndentAct.setStatusTip(QApplication.translate('ViewManager',
            'Smart indent Line or Selection'))
        self.smartIndentAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Smart indent</b>"""
            """<p>Indents the current line or the lines of the"""
            """ current selection smartly.</p>"""
        ))
        self.smartIndentAct.triggered[()].connect(self.__editSmartIndent)
        self.editActions.append(self.smartIndentAct)
        
        self.commentAct = E5Action(QApplication.translate('ViewManager', 'Comment'),
                UI.PixmapCache.getIcon("editComment.png"),
                QApplication.translate('ViewManager', 'C&omment'),
                QKeySequence(QApplication.translate('ViewManager',
                    "Ctrl+M", "Edit|Comment")),
                0,
                self.editActGrp, 'vm_edit_comment')
        self.commentAct.setStatusTip(QApplication.translate('ViewManager',
            'Comment Line or Selection'))
        self.commentAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Comment</b>"""
            """<p>Comments the current line or the lines of the"""
            """ current selection.</p>"""
        ))
        self.commentAct.triggered[()].connect(self.__editComment)
        self.editActions.append(self.commentAct)
        
        self.uncommentAct = E5Action(QApplication.translate('ViewManager', 'Uncomment'),
                UI.PixmapCache.getIcon("editUncomment.png"),
                QApplication.translate('ViewManager', 'Unco&mment'),
                QKeySequence(QApplication.translate('ViewManager',
                    "Alt+Ctrl+M", "Edit|Uncomment")),
                0,
                self.editActGrp, 'vm_edit_uncomment')
        self.uncommentAct.setStatusTip(QApplication.translate('ViewManager',
            'Uncomment Line or Selection'))
        self.uncommentAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Uncomment</b>"""
            """<p>Uncomments the current line or the lines of the"""
            """ current selection.</p>"""
        ))
        self.uncommentAct.triggered[()].connect(self.__editUncomment)
        self.editActions.append(self.uncommentAct)
        
        self.streamCommentAct = E5Action(QApplication.translate('ViewManager',
                    'Stream Comment'),
                QApplication.translate('ViewManager', 'Stream Comment'),
                0, 0, self.editActGrp, 'vm_edit_stream_comment')
        self.streamCommentAct.setStatusTip(QApplication.translate('ViewManager',
            'Stream Comment Line or Selection'))
        self.streamCommentAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Stream Comment</b>"""
            """<p>Stream comments the current line or the current selection.</p>"""
        ))
        self.streamCommentAct.triggered[()].connect(self.__editStreamComment)
        self.editActions.append(self.streamCommentAct)
        
        self.boxCommentAct = E5Action(QApplication.translate('ViewManager',
                    'Box Comment'),
                QApplication.translate('ViewManager', 'Box Comment'),
                0, 0, self.editActGrp, 'vm_edit_box_comment')
        self.boxCommentAct.setStatusTip(QApplication.translate('ViewManager',
            'Box Comment Line or Selection'))
        self.boxCommentAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Box Comment</b>"""
            """<p>Box comments the current line or the lines of the"""
            """ current selection.</p>"""
        ))
        self.boxCommentAct.triggered[()].connect(self.__editBoxComment)
        self.editActions.append(self.boxCommentAct)
        
        self.selectBraceAct = E5Action(QApplication.translate('ViewManager',
                    'Select to brace'),
                QApplication.translate('ViewManager', 'Select to &brace'),
                QKeySequence(QApplication.translate('ViewManager',
                    "Ctrl+E", "Edit|Select to brace")),
                0,
                self.editActGrp, 'vm_edit_select_to_brace')
        self.selectBraceAct.setStatusTip(QApplication.translate('ViewManager',
            'Select text to the matching brace'))
        self.selectBraceAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Select to brace</b>"""
            """<p>Select text of the current editor to the matching brace.</p>"""
        ))
        self.selectBraceAct.triggered[()].connect(self.__editSelectBrace)
        self.editActions.append(self.selectBraceAct)
        
        self.selectAllAct = E5Action(QApplication.translate('ViewManager', 'Select all'),
                QApplication.translate('ViewManager', '&Select all'),
                QKeySequence(QApplication.translate('ViewManager',
                    "Ctrl+A", "Edit|Select all")),
                0,
                self.editActGrp, 'vm_edit_select_all')
        self.selectAllAct.setStatusTip(QApplication.translate('ViewManager',
            'Select all text'))
        self.selectAllAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Select All</b>"""
            """<p>Select all text of the current editor.</p>"""
        ))
        self.selectAllAct.triggered[()].connect(self.__editSelectAll)
        self.editActions.append(self.selectAllAct)
        
        self.deselectAllAct = E5Action(QApplication.translate('ViewManager',
                    'Deselect all'),
                QApplication.translate('ViewManager', '&Deselect all'),
                QKeySequence(QApplication.translate('ViewManager',
                    "Alt+Ctrl+A", "Edit|Deselect all")),
                0,
                self.editActGrp, 'vm_edit_deselect_all')
        self.deselectAllAct.setStatusTip(QApplication.translate('ViewManager',
            'Deselect all text'))
        self.deselectAllAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Deselect All</b>"""
            """<p>Deselect all text of the current editor.</p>"""
        ))
        self.deselectAllAct.triggered[()].connect(self.__editDeselectAll)
        self.editActions.append(self.deselectAllAct)
        
        self.convertEOLAct = E5Action(QApplication.translate('ViewManager',
                    'Convert Line End Characters'),
                QApplication.translate('ViewManager', 'Convert &Line End Characters'),
                0, 0, self.editActGrp, 'vm_edit_convert_eol')
        self.convertEOLAct.setStatusTip(QApplication.translate('ViewManager',
            'Convert Line End Characters'))
        self.convertEOLAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Convert Line End Characters</b>"""
            """<p>Convert the line end characters to the currently set type.</p>"""
        ))
        self.convertEOLAct.triggered[()].connect(self.__convertEOL)
        self.editActions.append(self.convertEOLAct)
        
        self.shortenEmptyAct = E5Action(QApplication.translate('ViewManager',
                    'Shorten empty lines'),
                QApplication.translate('ViewManager', 'Shorten empty lines'),
                0, 0, self.editActGrp, 'vm_edit_shorten_empty_lines')
        self.shortenEmptyAct.setStatusTip(QApplication.translate('ViewManager',
            'Shorten empty lines'))
        self.shortenEmptyAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Shorten empty lines</b>"""
            """<p>Shorten lines consisting solely of whitespace characters.</p>"""
        ))
        self.shortenEmptyAct.triggered[()].connect(self.__shortenEmptyLines)
        self.editActions.append(self.shortenEmptyAct)
        
        self.autoCompleteAct = E5Action(QApplication.translate('ViewManager',
                    'Autocomplete'),
                QApplication.translate('ViewManager', '&Autocomplete'),
                QKeySequence(QApplication.translate('ViewManager',
                    "Ctrl+Space", "Edit|Autocomplete")),
                0,
                self.editActGrp, 'vm_edit_autocomplete')
        self.autoCompleteAct.setStatusTip(QApplication.translate('ViewManager',
            'Autocomplete current word'))
        self.autoCompleteAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Autocomplete</b>"""
            """<p>Performs an autocompletion of the word containing the cursor.</p>"""
        ))
        self.autoCompleteAct.triggered[()].connect(self.__editAutoComplete)
        self.editActions.append(self.autoCompleteAct)
        
        self.autoCompleteFromDocAct = E5Action(QApplication.translate('ViewManager',
                    'Autocomplete from Document'),
                QApplication.translate('ViewManager', 'Autocomplete from Document'),
                QKeySequence(QApplication.translate('ViewManager', "Ctrl+Shift+Space",
                             "Edit|Autocomplete from Document")),
                0, self.editActGrp, 'vm_edit_autocomplete_from_document')
        self.autoCompleteFromDocAct.setStatusTip(QApplication.translate('ViewManager',
            'Autocomplete current word from Document'))
        self.autoCompleteFromDocAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Autocomplete from Document</b>"""
            """<p>Performs an autocompletion from document of the word"""
            """ containing the cursor.</p>"""
        ))
        self.autoCompleteFromDocAct.triggered[()].connect(self.__editAutoCompleteFromDoc)
        self.editActions.append(self.autoCompleteFromDocAct)
        
        self.autoCompleteFromAPIsAct = E5Action(QApplication.translate('ViewManager',
                    'Autocomplete from APIs'),
                QApplication.translate('ViewManager', 'Autocomplete from APIs'),
                QKeySequence(QApplication.translate('ViewManager', "Ctrl+Alt+Space",
                             "Edit|Autocomplete from APIs")),
                0, self.editActGrp, 'vm_edit_autocomplete_from_api')
        self.autoCompleteFromAPIsAct.setStatusTip(QApplication.translate('ViewManager',
            'Autocomplete current word from APIs'))
        self.autoCompleteFromAPIsAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Autocomplete from APIs</b>"""
            """<p>Performs an autocompletion from APIs of the word containing"""
            """ the cursor.</p>"""
        ))
        self.autoCompleteFromAPIsAct.triggered[()].connect(self.__editAutoCompleteFromAPIs)
        self.editActions.append(self.autoCompleteFromAPIsAct)
        
        self.autoCompleteFromAllAct = E5Action(
                QApplication.translate('ViewManager',
                    'Autocomplete from Document and APIs'),
                QApplication.translate('ViewManager',
                    'Autocomplete from Document and APIs'),
                QKeySequence(QApplication.translate('ViewManager', "Alt+Shift+Space",
                             "Edit|Autocomplete from Document and APIs")),
                0, self.editActGrp, 'vm_edit_autocomplete_from_all')
        self.autoCompleteFromAllAct.setStatusTip(QApplication.translate('ViewManager',
            'Autocomplete current word from Document and APIs'))
        self.autoCompleteFromAllAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Autocomplete from Document and APIs</b>"""
            """<p>Performs an autocompletion from document and APIs"""
            """ of the word containing the cursor.</p>"""
        ))
        self.autoCompleteFromAllAct.triggered[()].connect(self.__editAutoCompleteFromAll)
        self.editActions.append(self.autoCompleteFromAllAct)
        
        self.calltipsAct = E5Action(QApplication.translate('ViewManager',
                    'Calltip'),
                QApplication.translate('ViewManager', '&Calltip'),
                QKeySequence(QApplication.translate('ViewManager',
                    "Alt+Space", "Edit|Calltip")),
                0,
                self.editActGrp, 'vm_edit_calltip')
        self.calltipsAct.setStatusTip(QApplication.translate('ViewManager',
            'Show Calltips'))
        self.calltipsAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Calltip</b>"""
            """<p>Show calltips based on the characters immediately to the"""
            """ left of the cursor.</p>"""
        ))
        self.calltipsAct.triggered[()].connect(self.__editShowCallTips)
        self.editActions.append(self.calltipsAct)
        
        self.editActGrp.setEnabled(False)
        self.copyActGrp.setEnabled(False)
        
        ####################################################################
        ## Below follow the actions for qscintilla standard commands.
        ####################################################################
        
        self.esm = QSignalMapper(self)
        self.esm.mapped[int].connect(self.__editorCommand)
        
        self.editorActGrp = createActionGroup(self.editActGrp)
        
        act = E5Action(QApplication.translate('ViewManager', 'Move left one character'),
                      QApplication.translate('ViewManager', 'Move left one character'),
                      QKeySequence(QApplication.translate('ViewManager', 'Left')), 0,
                      self.editorActGrp, 'vm_edit_move_left_char')
        self.esm.setMapping(act, QsciScintilla.SCI_CHARLEFT)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager', 'Move right one character'),
                      QApplication.translate('ViewManager', 'Move right one character'),
                      QKeySequence(QApplication.translate('ViewManager', 'Right')), 0,
                      self.editorActGrp, 'vm_edit_move_right_char')
        self.esm.setMapping(act, QsciScintilla.SCI_CHARRIGHT)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager', 'Move up one line'),
                      QApplication.translate('ViewManager', 'Move up one line'),
                      QKeySequence(QApplication.translate('ViewManager', 'Up')), 0,
                      self.editorActGrp, 'vm_edit_move_up_line')
        self.esm.setMapping(act, QsciScintilla.SCI_LINEUP)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager', 'Move down one line'),
                      QApplication.translate('ViewManager', 'Move down one line'),
                      QKeySequence(QApplication.translate('ViewManager', 'Down')), 0,
                      self.editorActGrp, 'vm_edit_move_down_line')
        self.esm.setMapping(act, QsciScintilla.SCI_LINEDOWN)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager', 'Move left one word part'),
                      QApplication.translate('ViewManager', 'Move left one word part'),
                      QKeySequence(QApplication.translate('ViewManager', 'Alt+Left')), 0,
                      self.editorActGrp, 'vm_edit_move_left_word_part')
        self.esm.setMapping(act, QsciScintilla.SCI_WORDPARTLEFT)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager', 'Move right one word part'),
                      QApplication.translate('ViewManager', 'Move right one word part'),
                      QKeySequence(QApplication.translate('ViewManager', 'Alt+Right')), 0,
                      self.editorActGrp, 'vm_edit_move_right_word_part')
        self.esm.setMapping(act, QsciScintilla.SCI_WORDPARTRIGHT)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager', 'Move left one word'),
                      QApplication.translate('ViewManager', 'Move left one word'),
                      QKeySequence(QApplication.translate('ViewManager', 'Ctrl+Left')), 0,
                      self.editorActGrp, 'vm_edit_move_left_word')
        self.esm.setMapping(act, QsciScintilla.SCI_WORDLEFT)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager', 'Move right one word'),
                      QApplication.translate('ViewManager', 'Move right one word'),
                      QKeySequence(QApplication.translate('ViewManager', 'Ctrl+Right')),
                      0,
                      self.editorActGrp, 'vm_edit_move_right_word')
        self.esm.setMapping(act, QsciScintilla.SCI_WORDRIGHT)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Move to first visible character in line'),
                      QApplication.translate('ViewManager',
                        'Move to first visible character in line'),
                      QKeySequence(QApplication.translate('ViewManager', 'Home')), 0,
                      self.editorActGrp, 'vm_edit_move_first_visible_char')
        self.esm.setMapping(act, QsciScintilla.SCI_VCHOME)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Move to start of displayed line'),
                      QApplication.translate('ViewManager',
                        'Move to start of displayed line'),
                      QKeySequence(QApplication.translate('ViewManager', 'Alt+Home')), 0,
                      self.editorActGrp, 'vm_edit_move_start_line')
        self.esm.setMapping(act, QsciScintilla.SCI_HOMEDISPLAY)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager', 'Move to end of line'),
                      QApplication.translate('ViewManager', 'Move to end of line'),
                      QKeySequence(QApplication.translate('ViewManager', 'End')), 0,
                      self.editorActGrp, 'vm_edit_move_end_line')
        self.esm.setMapping(act, QsciScintilla.SCI_LINEEND)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager', 'Scroll view down one line'),
                      QApplication.translate('ViewManager', 'Scroll view down one line'),
                      QKeySequence(QApplication.translate('ViewManager', 'Ctrl+Down')), 0,
                      self.editorActGrp, 'vm_edit_scroll_down_line')
        self.esm.setMapping(act, QsciScintilla.SCI_LINESCROLLDOWN)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager', 'Scroll view up one line'),
                      QApplication.translate('ViewManager', 'Scroll view up one line'),
                      QKeySequence(QApplication.translate('ViewManager', 'Ctrl+Up')), 0,
                      self.editorActGrp, 'vm_edit_scroll_up_line')
        self.esm.setMapping(act, QsciScintilla.SCI_LINESCROLLUP)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager', 'Move up one paragraph'),
                      QApplication.translate('ViewManager', 'Move up one paragraph'),
                      QKeySequence(QApplication.translate('ViewManager', 'Alt+Up')), 0,
                      self.editorActGrp, 'vm_edit_move_up_para')
        self.esm.setMapping(act, QsciScintilla.SCI_PARAUP)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager', 'Move down one paragraph'),
                      QApplication.translate('ViewManager', 'Move down one paragraph'),
                      QKeySequence(QApplication.translate('ViewManager', 'Alt+Down')), 0,
                      self.editorActGrp, 'vm_edit_move_down_para')
        self.esm.setMapping(act, QsciScintilla.SCI_PARADOWN)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager', 'Move up one page'),
                      QApplication.translate('ViewManager', 'Move up one page'),
                      QKeySequence(QApplication.translate('ViewManager', 'PgUp')), 0,
                      self.editorActGrp, 'vm_edit_move_up_page')
        self.esm.setMapping(act, QsciScintilla.SCI_PAGEUP)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager', 'Move down one page'),
                      QApplication.translate('ViewManager', 'Move down one page'),
                      QKeySequence(QApplication.translate('ViewManager', 'PgDown')), 0,
                      self.editorActGrp, 'vm_edit_move_down_page')
        self.esm.setMapping(act, QsciScintilla.SCI_PAGEDOWN)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager', 'Move to start of text'),
                      QApplication.translate('ViewManager', 'Move to start of text'),
                      QKeySequence(QApplication.translate('ViewManager', 'Ctrl+Home')), 0,
                      self.editorActGrp, 'vm_edit_move_start_text')
        self.esm.setMapping(act, QsciScintilla.SCI_DOCUMENTSTART)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager', 'Move to end of text'),
                      QApplication.translate('ViewManager', 'Move to end of text'),
                      QKeySequence(QApplication.translate('ViewManager', 'Ctrl+End')), 0,
                      self.editorActGrp, 'vm_edit_move_end_text')
        self.esm.setMapping(act, QsciScintilla.SCI_DOCUMENTEND)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager', 'Indent one level'),
                      QApplication.translate('ViewManager', 'Indent one level'),
                      QKeySequence(QApplication.translate('ViewManager', 'Tab')), 0,
                      self.editorActGrp, 'vm_edit_indent_one_level')
        self.esm.setMapping(act, QsciScintilla.SCI_TAB)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager', 'Unindent one level'),
                      QApplication.translate('ViewManager', 'Unindent one level'),
                      QKeySequence(QApplication.translate('ViewManager', 'Shift+Tab')), 0,
                      self.editorActGrp, 'vm_edit_unindent_one_level')
        self.esm.setMapping(act, QsciScintilla.SCI_BACKTAB)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Extend selection left one character'),
                      QApplication.translate('ViewManager',
                        'Extend selection left one character'),
                      QKeySequence(QApplication.translate('ViewManager', 'Shift+Left')),
                      0,
                      self.editorActGrp, 'vm_edit_extend_selection_left_char')
        self.esm.setMapping(act, QsciScintilla.SCI_CHARLEFTEXTEND)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Extend selection right one character'),
                      QApplication.translate('ViewManager',
                        'Extend selection right one character'),
                      QKeySequence(QApplication.translate('ViewManager', 'Shift+Right')),
                      0,
                      self.editorActGrp, 'vm_edit_extend_selection_right_char')
        self.esm.setMapping(act, QsciScintilla.SCI_CHARRIGHTEXTEND)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Extend selection up one line'),
                      QApplication.translate('ViewManager',
                        'Extend selection up one line'),
                      QKeySequence(QApplication.translate('ViewManager', 'Shift+Up')), 0,
                      self.editorActGrp, 'vm_edit_extend_selection_up_line')
        self.esm.setMapping(act, QsciScintilla.SCI_LINEUPEXTEND)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Extend selection down one line'),
                      QApplication.translate('ViewManager',
                        'Extend selection down one line'),
                      QKeySequence(QApplication.translate('ViewManager', 'Shift+Down')),
                      0,
                      self.editorActGrp, 'vm_edit_extend_selection_down_line')
        self.esm.setMapping(act, QsciScintilla.SCI_LINEDOWNEXTEND)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Extend selection left one word part'),
                      QApplication.translate('ViewManager',
                        'Extend selection left one word part'),
                      QKeySequence(QApplication.translate('ViewManager',
                        'Alt+Shift+Left')),
                      0,
                      self.editorActGrp, 'vm_edit_extend_selection_left_word_part')
        self.esm.setMapping(act, QsciScintilla.SCI_WORDPARTLEFTEXTEND)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Extend selection right one word part'),
                      QApplication.translate('ViewManager',
                        'Extend selection right one word part'),
                      QKeySequence(QApplication.translate('ViewManager',
                        'Alt+Shift+Right')),
                      0,
                      self.editorActGrp, 'vm_edit_extend_selection_right_word_part')
        self.esm.setMapping(act, QsciScintilla.SCI_WORDPARTRIGHTEXTEND)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Extend selection left one word'),
                      QApplication.translate('ViewManager',
                        'Extend selection left one word'),
                      QKeySequence(QApplication.translate('ViewManager',
                        'Ctrl+Shift+Left')),
                      0,
                      self.editorActGrp, 'vm_edit_extend_selection_left_word')
        self.esm.setMapping(act, QsciScintilla.SCI_WORDLEFTEXTEND)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Extend selection right one word'),
                      QApplication.translate('ViewManager',
                        'Extend selection right one word'),
                      QKeySequence(QApplication.translate('ViewManager',
                        'Ctrl+Shift+Right')),
                      0,
                      self.editorActGrp, 'vm_edit_extend_selection_right_word')
        self.esm.setMapping(act, QsciScintilla.SCI_WORDRIGHTEXTEND)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Extend selection to first visible character in line'),
                      QApplication.translate('ViewManager',
                        'Extend selection to first visible character in line'),
                      QKeySequence(QApplication.translate('ViewManager', 'Shift+Home')),
                      0,
                      self.editorActGrp, 'vm_edit_extend_selection_first_visible_char')
        self.esm.setMapping(act, QsciScintilla.SCI_VCHOMEEXTEND)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Extend selection to start of line'),
                      QApplication.translate('ViewManager',
                        'Extend selection to start of line'),
                      QKeySequence(QApplication.translate('ViewManager',
                        'Alt+Shift+Home')),
                      0,
                      self.editorActGrp, 'vm_edit_extend_selection_start_line')
        self.esm.setMapping(act, QsciScintilla.SCI_HOMEDISPLAYEXTEND)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Extend selection to end of line'),
                      QApplication.translate('ViewManager',
                        'Extend selection to end of line'),
                      QKeySequence(QApplication.translate('ViewManager', 'Shift+End')), 0,
                      self.editorActGrp, 'vm_edit_extend_selection_end_line')
        self.esm.setMapping(act, QsciScintilla.SCI_LINEENDEXTEND)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Extend selection up one paragraph'),
                      QApplication.translate('ViewManager',
                        'Extend selection up one paragraph'),
                      QKeySequence(QApplication.translate('ViewManager', 'Alt+Shift+Up')),
                      0,
                      self.editorActGrp, 'vm_edit_extend_selection_up_para')
        self.esm.setMapping(act, QsciScintilla.SCI_PARAUPEXTEND)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Extend selection down one paragraph'),
                      QApplication.translate('ViewManager',
                        'Extend selection down one paragraph'),
                      QKeySequence(QApplication.translate('ViewManager',
                        'Alt+Shift+Down')),
                      0,
                      self.editorActGrp, 'vm_edit_extend_selection_down_para')
        self.esm.setMapping(act, QsciScintilla.SCI_PARADOWNEXTEND)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Extend selection up one page'),
                      QApplication.translate('ViewManager',
                        'Extend selection up one page'),
                      QKeySequence(QApplication.translate('ViewManager', 'Shift+PgUp')),
                      0,
                      self.editorActGrp, 'vm_edit_extend_selection_up_page')
        self.esm.setMapping(act, QsciScintilla.SCI_PAGEUPEXTEND)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Extend selection down one page'),
                      QApplication.translate('ViewManager',
                        'Extend selection down one page'),
                      QKeySequence(QApplication.translate('ViewManager', 'Shift+PgDown')),
                      0,
                      self.editorActGrp, 'vm_edit_extend_selection_down_page')
        self.esm.setMapping(act, QsciScintilla.SCI_PAGEDOWNEXTEND)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Extend selection to start of text'),
                      QApplication.translate('ViewManager',
                        'Extend selection to start of text'),
                      QKeySequence(QApplication.translate('ViewManager',
                        'Ctrl+Shift+Home')),
                      0,
                      self.editorActGrp, 'vm_edit_extend_selection_start_text')
        self.esm.setMapping(act, QsciScintilla.SCI_DOCUMENTSTARTEXTEND)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Extend selection to end of text'),
                      QApplication.translate('ViewManager',
                        'Extend selection to end of text'),
                      QKeySequence(QApplication.translate('ViewManager',
                        'Ctrl+Shift+End')),
                      0,
                      self.editorActGrp, 'vm_edit_extend_selection_end_text')
        self.esm.setMapping(act, QsciScintilla.SCI_DOCUMENTENDEXTEND)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Delete previous character'),
                      QApplication.translate('ViewManager', 'Delete previous character'),
                      QKeySequence(QApplication.translate('ViewManager', 'Backspace')),
                      QKeySequence(QApplication.translate('ViewManager',
                        'Shift+Backspace')),
                      self.editorActGrp, 'vm_edit_delete_previous_char')
        self.esm.setMapping(act, QsciScintilla.SCI_DELETEBACK)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Delete previous character if not at line start'),
                      QApplication.translate('ViewManager',
                        'Delete previous character if not at line start'),
                      0, 0,
                      self.editorActGrp, 'vm_edit_delet_previous_char_not_line_start')
        self.esm.setMapping(act, QsciScintilla.SCI_DELETEBACKNOTLINE)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager', 'Delete current character'),
                      QApplication.translate('ViewManager', 'Delete current character'),
                      QKeySequence(QApplication.translate('ViewManager', 'Del')), 0,
                      self.editorActGrp, 'vm_edit_delete_current_char')
        self.esm.setMapping(act, QsciScintilla.SCI_CLEAR)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager', 'Delete word to left'),
                      QApplication.translate('ViewManager', 'Delete word to left'),
                      QKeySequence(QApplication.translate('ViewManager',
                        'Ctrl+Backspace')),
                      0,
                      self.editorActGrp, 'vm_edit_delete_word_left')
        self.esm.setMapping(act, QsciScintilla.SCI_DELWORDLEFT)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager', 'Delete word to right'),
                      QApplication.translate('ViewManager', 'Delete word to right'),
                      QKeySequence(QApplication.translate('ViewManager', 'Ctrl+Del')), 0,
                      self.editorActGrp, 'vm_edit_delete_word_right')
        self.esm.setMapping(act, QsciScintilla.SCI_DELWORDRIGHT)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager', 'Delete line to left'),
                      QApplication.translate('ViewManager', 'Delete line to left'),
                      QKeySequence(QApplication.translate('ViewManager',
                        'Ctrl+Shift+Backspace')),
                      0,
                      self.editorActGrp, 'vm_edit_delete_line_left')
        self.esm.setMapping(act, QsciScintilla.SCI_DELLINELEFT)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager', 'Delete line to right'),
                      QApplication.translate('ViewManager', 'Delete line to right'),
                      QKeySequence(QApplication.translate('ViewManager',
                        'Ctrl+Shift+Del')),
                      0,
                      self.editorActGrp, 'vm_edit_delete_line_right')
        self.esm.setMapping(act, QsciScintilla.SCI_DELLINERIGHT)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager', 'Insert new line'),
                      QApplication.translate('ViewManager', 'Insert new line'),
                      QKeySequence(QApplication.translate('ViewManager', 'Return')),
                      QKeySequence(QApplication.translate('ViewManager', 'Enter')),
                      self.editorActGrp, 'vm_edit_insert_line')
        self.esm.setMapping(act, QsciScintilla.SCI_NEWLINE)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                                              'Insert new line below current line'),
                      QApplication.translate('ViewManager',
                                             'Insert new line below current line'),
                      QKeySequence(QApplication.translate('ViewManager', 'Shift+Return')),
                      QKeySequence(QApplication.translate('ViewManager', 'Shift+Enter')),
                      self.editorActGrp, 'vm_edit_insert_line_below')
        act.triggered[()].connect(self.__newLineBelow)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager', 'Delete current line'),
                      QApplication.translate('ViewManager', 'Delete current line'),
                      QKeySequence(QApplication.translate('ViewManager', 'Ctrl+U')),
                      QKeySequence(QApplication.translate('ViewManager', 'Ctrl+Shift+L')),
                      self.editorActGrp, 'vm_edit_delete_current_line')
        self.esm.setMapping(act, QsciScintilla.SCI_LINEDELETE)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager', 'Duplicate current line'),
                      QApplication.translate('ViewManager', 'Duplicate current line'),
                      QKeySequence(QApplication.translate('ViewManager', 'Ctrl+D')), 0,
                      self.editorActGrp, 'vm_edit_duplicate_current_line')
        self.esm.setMapping(act, QsciScintilla.SCI_LINEDUPLICATE)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Swap current and previous lines'),
                      QApplication.translate('ViewManager',
                        'Swap current and previous lines'),
                      QKeySequence(QApplication.translate('ViewManager', 'Ctrl+T')), 0,
                      self.editorActGrp, 'vm_edit_swap_current_previous_line')
        self.esm.setMapping(act, QsciScintilla.SCI_LINETRANSPOSE)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager', 'Cut current line'),
                      QApplication.translate('ViewManager', 'Cut current line'),
                      QKeySequence(QApplication.translate('ViewManager', 'Alt+Shift+L')),
                      0,
                      self.editorActGrp, 'vm_edit_cut_current_line')
        self.esm.setMapping(act, QsciScintilla.SCI_LINECUT)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager', 'Copy current line'),
                      QApplication.translate('ViewManager', 'Copy current line'),
                      QKeySequence(QApplication.translate('ViewManager', 'Ctrl+Shift+T')),
                      0,
                      self.editorActGrp, 'vm_edit_copy_current_line')
        self.esm.setMapping(act, QsciScintilla.SCI_LINECOPY)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager', 'Toggle insert/overtype'),
                      QApplication.translate('ViewManager', 'Toggle insert/overtype'),
                      QKeySequence(QApplication.translate('ViewManager', 'Ins')), 0,
                      self.editorActGrp, 'vm_edit_toggle_insert_overtype')
        self.esm.setMapping(act, QsciScintilla.SCI_EDITTOGGLEOVERTYPE)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Convert selection to lower case'),
                      QApplication.translate('ViewManager',
                        'Convert selection to lower case'),
                      QKeySequence(QApplication.translate('ViewManager', 'Alt+Shift+U')),
                      0,
                      self.editorActGrp, 'vm_edit_convert_selection_lower')
        self.esm.setMapping(act, QsciScintilla.SCI_LOWERCASE)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Convert selection to upper case'),
                      QApplication.translate('ViewManager',
                        'Convert selection to upper case'),
                      QKeySequence(QApplication.translate('ViewManager', 'Ctrl+Shift+U')),
                      0,
                      self.editorActGrp, 'vm_edit_convert_selection_upper')
        self.esm.setMapping(act, QsciScintilla.SCI_UPPERCASE)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Move to end of displayed line'),
                      QApplication.translate('ViewManager',
                        'Move to end of displayed line'),
                      QKeySequence(QApplication.translate('ViewManager', 'Alt+End')), 0,
                      self.editorActGrp, 'vm_edit_move_end_displayed_line')
        self.esm.setMapping(act, QsciScintilla.SCI_LINEENDDISPLAY)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Extend selection to end of displayed line'),
                      QApplication.translate('ViewManager',
                        'Extend selection to end of displayed line'),
                      0, 0,
                      self.editorActGrp, 'vm_edit_extend_selection_end_displayed_line')
        self.esm.setMapping(act, QsciScintilla.SCI_LINEENDDISPLAYEXTEND)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager', 'Formfeed'),
                      QApplication.translate('ViewManager', 'Formfeed'),
                      0, 0,
                      self.editorActGrp, 'vm_edit_formfeed')
        self.esm.setMapping(act, QsciScintilla.SCI_FORMFEED)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager', 'Escape'),
                      QApplication.translate('ViewManager', 'Escape'),
                      QKeySequence(QApplication.translate('ViewManager', 'Esc')), 0,
                      self.editorActGrp, 'vm_edit_escape')
        self.esm.setMapping(act, QsciScintilla.SCI_CANCEL)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Extend rectangular selection down one line'),
                      QApplication.translate('ViewManager',
                        'Extend rectangular selection down one line'),
                      QKeySequence(QApplication.translate('ViewManager',
                        'Alt+Ctrl+Down')),
                      0,
                      self.editorActGrp, 'vm_edit_extend_rect_selection_down_line')
        self.esm.setMapping(act, QsciScintilla.SCI_LINEDOWNRECTEXTEND)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Extend rectangular selection up one line'),
                      QApplication.translate('ViewManager',
                        'Extend rectangular selection up one line'),
                      QKeySequence(QApplication.translate('ViewManager', 'Alt+Ctrl+Up')),
                      0,
                      self.editorActGrp, 'vm_edit_extend_rect_selection_up_line')
        self.esm.setMapping(act, QsciScintilla.SCI_LINEUPRECTEXTEND)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Extend rectangular selection left one character'),
                      QApplication.translate('ViewManager',
                        'Extend rectangular selection left one character'),
                      QKeySequence(QApplication.translate('ViewManager',
                        'Alt+Ctrl+Left')),
                      0,
                      self.editorActGrp, 'vm_edit_extend_rect_selection_left_char')
        self.esm.setMapping(act, QsciScintilla.SCI_CHARLEFTRECTEXTEND)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Extend rectangular selection right one character'),
                      QApplication.translate('ViewManager',
                        'Extend rectangular selection right one character'),
                      QKeySequence(QApplication.translate('ViewManager',
                        'Alt+Ctrl+Right')),
                      0,
                      self.editorActGrp, 'vm_edit_extend_rect_selection_right_char')
        self.esm.setMapping(act, QsciScintilla.SCI_CHARRIGHTRECTEXTEND)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Extend rectangular selection to first'
                        ' visible character in line'),
                      QApplication.translate('ViewManager',
                        'Extend rectangular selection to first'
                        ' visible character in line'),
                      QKeySequence(QApplication.translate('ViewManager',
                        'Alt+Ctrl+Home')),
                      0,
                      self.editorActGrp,
                      'vm_edit_extend_rect_selection_first_visible_char')
        self.esm.setMapping(act, QsciScintilla.SCI_VCHOMERECTEXTEND)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Extend rectangular selection to end of line'),
                      QApplication.translate('ViewManager',
                        'Extend rectangular selection to end of line'),
                      QKeySequence(QApplication.translate('ViewManager', 'Alt+Ctrl+End')),
                      0,
                      self.editorActGrp, 'vm_edit_extend_rect_selection_end_line')
        self.esm.setMapping(act, QsciScintilla.SCI_LINEENDRECTEXTEND)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Extend rectangular selection up one page'),
                      QApplication.translate('ViewManager',
                        'Extend rectangular selection up one page'),
                      QKeySequence(QApplication.translate('ViewManager',
                        'Alt+Ctrl+PgUp')),
                      0,
                      self.editorActGrp, 'vm_edit_extend_rect_selection_up_page')
        self.esm.setMapping(act, QsciScintilla.SCI_PAGEUPRECTEXTEND)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Extend rectangular selection down one page'),
                      QApplication.translate('ViewManager',
                        'Extend rectangular selection down one page'),
                      QKeySequence(QApplication.translate('ViewManager',
                        'Alt+Ctrl+PgDown')),
                      0,
                      self.editorActGrp, 'vm_edit_extend_rect_selection_down_page')
        self.esm.setMapping(act, QsciScintilla.SCI_PAGEDOWNRECTEXTEND)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(QApplication.translate('ViewManager',
                        'Duplicate current selection'),
                      QApplication.translate('ViewManager',
                        'Duplicate current selection'),
                      QKeySequence(QApplication.translate('ViewManager', 'Ctrl+Shift+D')),
                      0,
                      self.editorActGrp, 'vm_edit_duplicate_current_selection')
        self.esm.setMapping(act, QsciScintilla.SCI_SELECTIONDUPLICATE)
        act.triggered[()].connect(self.esm.map)
        self.editActions.append(act)
        
        self.editorActGrp.setEnabled(False)
    
    def initEditMenu(self):
        """
        Public method to create the Edit menu
        
        @return the generated menu
        """
        autocompletionMenu = \
            QMenu(QApplication.translate('ViewManager', '&Autocomplete'), self.ui)
        autocompletionMenu.setTearOffEnabled(True)
        autocompletionMenu.addAction(self.autoCompleteAct)
        autocompletionMenu.addAction(self.autoCompleteFromDocAct)
        autocompletionMenu.addAction(self.autoCompleteFromAPIsAct)
        autocompletionMenu.addAction(self.autoCompleteFromAllAct)
        autocompletionMenu.addSeparator()
        autocompletionMenu.addAction(self.calltipsAct)
        
        searchMenu = \
            QMenu(QApplication.translate('ViewManager', '&Search'), self.ui)
        searchMenu.setTearOffEnabled(True)
        searchMenu.addAction(self.quickSearchAct)
        searchMenu.addAction(self.quickSearchBackAct)
        searchMenu.addAction(self.searchAct)
        searchMenu.addAction(self.searchNextAct)
        searchMenu.addAction(self.searchPrevAct)
        searchMenu.addAction(self.replaceAct)
        searchMenu.addSeparator()
        searchMenu.addAction(self.searchClearMarkersAct)
        searchMenu.addSeparator()
        searchMenu.addAction(self.searchFilesAct)
        searchMenu.addAction(self.replaceFilesAct)
        
        menu = QMenu(QApplication.translate('ViewManager', '&Edit'), self.ui)
        menu.setTearOffEnabled(True)
        menu.addAction(self.undoAct)
        menu.addAction(self.redoAct)
        menu.addAction(self.revertAct)
        menu.addSeparator()
        menu.addAction(self.cutAct)
        menu.addAction(self.copyAct)
        menu.addAction(self.pasteAct)
        menu.addAction(self.deleteAct)
        menu.addSeparator()
        menu.addAction(self.indentAct)
        menu.addAction(self.unindentAct)
        menu.addAction(self.smartIndentAct)
        menu.addSeparator()
        menu.addAction(self.commentAct)
        menu.addAction(self.uncommentAct)
        menu.addAction(self.streamCommentAct)
        menu.addAction(self.boxCommentAct)
        menu.addSeparator()
        menu.addMenu(autocompletionMenu)
        menu.addSeparator()
        menu.addMenu(searchMenu)
        menu.addSeparator()
        menu.addAction(self.gotoAct)
        menu.addAction(self.gotoBraceAct)
        menu.addSeparator()
        menu.addAction(self.selectBraceAct)
        menu.addAction(self.selectAllAct)
        menu.addAction(self.deselectAllAct)
        menu.addSeparator()
        menu.addAction(self.shortenEmptyAct)
        menu.addAction(self.convertEOLAct)
        
        return menu
        
    def initEditToolbar(self, toolbarManager):
        """
        Public method to create the Edit toolbar
        
        @param toolbarManager reference to a toolbar manager object (E5ToolBarManager)
        @return the generated toolbar
        """
        tb = QToolBar(QApplication.translate('ViewManager', 'Edit'), self.ui)
        tb.setIconSize(UI.Config.ToolBarIconSize)
        tb.setObjectName("EditToolbar")
        tb.setToolTip(QApplication.translate('ViewManager', 'Edit'))
        
        tb.addAction(self.undoAct)
        tb.addAction(self.redoAct)
        tb.addSeparator()
        tb.addAction(self.cutAct)
        tb.addAction(self.copyAct)
        tb.addAction(self.pasteAct)
        tb.addAction(self.deleteAct)
        tb.addSeparator()
        tb.addAction(self.indentAct)
        tb.addAction(self.unindentAct)
        tb.addSeparator()
        tb.addAction(self.commentAct)
        tb.addAction(self.uncommentAct)
        
        toolbarManager.addToolBar(tb, tb.windowTitle())
        toolbarManager.addAction(self.smartIndentAct, tb.windowTitle())
        
        return tb
        
    ##################################################################
    ## Initialize the search related actions and the search toolbar
    ##################################################################
    
    def __initSearchActions(self):
        """
        Private method defining the user interface actions for the search commands.
        """
        self.searchActGrp = createActionGroup(self)
        
        self.searchAct = E5Action(QApplication.translate('ViewManager', 'Search'),
                UI.PixmapCache.getIcon("find.png"),
                QApplication.translate('ViewManager', '&Search...'),
                QKeySequence(QApplication.translate('ViewManager',
                    "Ctrl+F", "Search|Search")),
                0,
                self.searchActGrp, 'vm_search')
        self.searchAct.setStatusTip(QApplication.translate('ViewManager',
            'Search for a text'))
        self.searchAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Search</b>"""
            """<p>Search for some text in the current editor. A"""
            """ dialog is shown to enter the searchtext and options"""
            """ for the search.</p>"""
        ))
        self.searchAct.triggered[()].connect(self.__search)
        self.searchActions.append(self.searchAct)
        
        self.searchNextAct = E5Action(QApplication.translate('ViewManager',
                    'Search next'),
                UI.PixmapCache.getIcon("findNext.png"),
                QApplication.translate('ViewManager', 'Search &next'),
                QKeySequence(QApplication.translate('ViewManager',
                    "F3", "Search|Search next")),
                0,
                self.searchActGrp, 'vm_search_next')
        self.searchNextAct.setStatusTip(QApplication.translate('ViewManager',
            'Search next occurrence of text'))
        self.searchNextAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Search next</b>"""
            """<p>Search the next occurrence of some text in the current editor."""
            """ The previously entered searchtext and options are reused.</p>"""
        ))
        self.searchNextAct.triggered[()].connect(self.searchDlg.findNext)
        self.searchActions.append(self.searchNextAct)
        
        self.searchPrevAct = E5Action(QApplication.translate('ViewManager',
                    'Search previous'),
                UI.PixmapCache.getIcon("findPrev.png"),
                QApplication.translate('ViewManager', 'Search &previous'),
                QKeySequence(QApplication.translate('ViewManager',
                    "Shift+F3", "Search|Search previous")),
                0,
                self.searchActGrp, 'vm_search_previous')
        self.searchPrevAct.setStatusTip(QApplication.translate('ViewManager',
            'Search previous occurrence of text'))
        self.searchPrevAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Search previous</b>"""
            """<p>Search the previous occurrence of some text in the current editor."""
            """ The previously entered searchtext and options are reused.</p>"""
        ))
        self.searchPrevAct.triggered[()].connect(self.searchDlg.findPrev)
        self.searchActions.append(self.searchPrevAct)
        
        self.searchClearMarkersAct = E5Action(QApplication.translate('ViewManager',
                    'Clear search markers'),
                UI.PixmapCache.getIcon("findClear.png"),
                QApplication.translate('ViewManager', 'Clear search markers'),
                QKeySequence(QApplication.translate('ViewManager',
                    "Ctrl+3", "Search|Clear search markers")),
                0,
                self.searchActGrp, 'vm_clear_search_markers')
        self.searchClearMarkersAct.setStatusTip(QApplication.translate('ViewManager',
            'Clear all displayed search markers'))
        self.searchClearMarkersAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Clear search markers</b>"""
            """<p>Clear all displayed search markers.</p>"""
        ))
        self.searchClearMarkersAct.triggered[()].connect(self.__searchClearMarkers)
        self.searchActions.append(self.searchClearMarkersAct)
        
        self.replaceAct = E5Action(QApplication.translate('ViewManager', 'Replace'),
                QApplication.translate('ViewManager', '&Replace...'),
                QKeySequence(QApplication.translate('ViewManager',
                    "Ctrl+R", "Search|Replace")),
                0,
                self.searchActGrp, 'vm_search_replace')
        self.replaceAct.setStatusTip(QApplication.translate('ViewManager',
            'Replace some text'))
        self.replaceAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Replace</b>"""
            """<p>Search for some text in the current editor and replace it. A"""
            """ dialog is shown to enter the searchtext, the replacement text"""
            """ and options for the search and replace.</p>"""
        ))
        self.replaceAct.triggered[()].connect(self.__replace)
        self.searchActions.append(self.replaceAct)
        
        self.quickSearchAct = E5Action(QApplication.translate('ViewManager',
                    'Quicksearch'),
                UI.PixmapCache.getIcon("quickFindNext.png"),
                QApplication.translate('ViewManager', '&Quicksearch'),
                QKeySequence(QApplication.translate('ViewManager',
                    "Ctrl+Shift+K", "Search|Quicksearch")),
                0,
                self.searchActGrp, 'vm_quicksearch')
        self.quickSearchAct.setStatusTip(QApplication.translate('ViewManager',
            'Perform a quicksearch'))
        self.quickSearchAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Quicksearch</b>"""
            """<p>This activates the quicksearch function of the IDE by"""
            """ giving focus to the quicksearch entry field. If this field"""
            """ is already active and contains text, it searches for the"""
            """ next occurrence of this text.</p>"""
        ))
        self.quickSearchAct.triggered[()].connect(self.__quickSearch)
        self.searchActions.append(self.quickSearchAct)
        
        self.quickSearchBackAct = E5Action(QApplication.translate('ViewManager',
                    'Quicksearch backwards'),
                UI.PixmapCache.getIcon("quickFindPrev.png"),
                QApplication.translate('ViewManager', 'Quicksearch &backwards'),
                QKeySequence(QApplication.translate('ViewManager',
                    "Ctrl+Shift+J", "Search|Quicksearch backwards")),
                0, self.searchActGrp, 'vm_quicksearch_backwards')
        self.quickSearchBackAct.setStatusTip(QApplication.translate('ViewManager',
            'Perform a quicksearch backwards'))
        self.quickSearchBackAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Quicksearch backwards</b>"""
            """<p>This searches the previous occurrence of the quicksearch text.</p>"""
        ))
        self.quickSearchBackAct.triggered[()].connect(self.__quickSearchPrev)
        self.searchActions.append(self.quickSearchBackAct)
        
        self.quickSearchExtendAct = E5Action(QApplication.translate('ViewManager',
                    'Quicksearch extend'),
                UI.PixmapCache.getIcon("quickFindExtend.png"),
                QApplication.translate('ViewManager', 'Quicksearch e&xtend'),
                QKeySequence(QApplication.translate('ViewManager',
                    "Ctrl+Shift+H", "Search|Quicksearch extend")),
                0,
                self.searchActGrp, 'vm_quicksearch_extend')
        self.quickSearchExtendAct.setStatusTip(QApplication.translate('ViewManager', \
            'Extend the quicksearch to the end of the current word'))
        self.quickSearchExtendAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Quicksearch extend</b>"""
            """<p>This extends the quicksearch text to the end of the word"""
            """ currently found.</p>"""
        ))
        self.quickSearchExtendAct.triggered[()].connect(self.__quickSearchExtend)
        self.searchActions.append(self.quickSearchExtendAct)
        
        self.gotoAct = E5Action(QApplication.translate('ViewManager', 'Goto Line'),
                UI.PixmapCache.getIcon("goto.png"),
                QApplication.translate('ViewManager', '&Goto Line...'),
                QKeySequence(QApplication.translate('ViewManager',
                    "Ctrl+G", "Search|Goto Line")),
                0,
                self.searchActGrp, 'vm_search_goto_line')
        self.gotoAct.setStatusTip(QApplication.translate('ViewManager', 'Goto Line'))
        self.gotoAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Goto Line</b>"""
            """<p>Go to a specific line of text in the current editor."""
            """ A dialog is shown to enter the linenumber.</p>"""
        ))
        self.gotoAct.triggered[()].connect(self.__goto)
        self.searchActions.append(self.gotoAct)
        
        self.gotoBraceAct = E5Action(QApplication.translate('ViewManager', 'Goto Brace'),
                UI.PixmapCache.getIcon("gotoBrace.png"),
                QApplication.translate('ViewManager', 'Goto &Brace'),
                QKeySequence(QApplication.translate('ViewManager',
                    "Ctrl+L", "Search|Goto Brace")),
                0,
                self.searchActGrp, 'vm_search_goto_brace')
        self.gotoBraceAct.setStatusTip(QApplication.translate('ViewManager',
            'Goto Brace'))
        self.gotoBraceAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Goto Brace</b>"""
            """<p>Go to the matching brace in the current editor.</p>"""
        ))
        self.gotoBraceAct.triggered[()].connect(self.__gotoBrace)
        self.searchActions.append(self.gotoBraceAct)
        
        self.searchActGrp.setEnabled(False)
        
        self.searchFilesAct = E5Action(QApplication.translate('ViewManager',
                    'Search in Files'),
                UI.PixmapCache.getIcon("projectFind.png"),
                QApplication.translate('ViewManager', 'Search in &Files...'),
                QKeySequence(QApplication.translate('ViewManager',
                    "Shift+Ctrl+F", "Search|Search Files")),
                0,
                self, 'vm_search_in_files')
        self.searchFilesAct.setStatusTip(QApplication.translate('ViewManager',
            'Search for a text in files'))
        self.searchFilesAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Search in Files</b>"""
            """<p>Search for some text in the files of a directory tree"""
            """ or the project. A dialog is shown to enter the searchtext"""
            """ and options for the search and to display the result.</p>"""
        ))
        self.searchFilesAct.triggered[()].connect(self.__searchFiles)
        self.searchActions.append(self.searchFilesAct)
        
        self.replaceFilesAct = E5Action(QApplication.translate('ViewManager',
                    'Replace in Files'),
                QApplication.translate('ViewManager', 'Replace in F&iles...'),
                QKeySequence(QApplication.translate('ViewManager',
                    "Shift+Ctrl+R", "Search|Replace in Files")),
                0,
                self, 'vm_replace_in_files')
        self.replaceFilesAct.setStatusTip(QApplication.translate('ViewManager',
            'Search for a text in files and replace it'))
        self.replaceFilesAct.setWhatsThis(QApplication.translate('ViewManager',
            """<b>Replace in Files</b>"""
            """<p>Search for some text in the files of a directory tree"""
            """ or the project and replace it. A dialog is shown to enter"""
            """ the searchtext, the replacement text and options for the"""
            """ search and to display the result.</p>"""
        ))
        self.replaceFilesAct.triggered[()].connect(self.__replaceFiles)
        self.searchActions.append(self.replaceFilesAct)
        
    def initSearchToolbars(self, toolbarManager):
        """
        Public method to create the Search toolbars
        
        @param toolbarManager reference to a toolbar manager object (E5ToolBarManager)
        @return a tuple of the generated toolbar (search, quicksearch)
        """
        qtb = QToolBar(QApplication.translate('ViewManager', 'Quicksearch'), self.ui)
        qtb.setIconSize(UI.Config.ToolBarIconSize)
        qtb.setObjectName("QuicksearchToolbar")
        qtb.setToolTip(QApplication.translate('ViewManager', 'Quicksearch'))
        
        self.quickFindLineEdit = QuickSearchLineEdit(self)
        self.quickFindtextCombo = QComboBox(self)
        self.quickFindtextCombo.setEditable(True)
        self.quickFindtextCombo.setLineEdit(self.quickFindLineEdit)
        self.quickFindtextCombo.setDuplicatesEnabled(False)
        self.quickFindtextCombo.setInsertPolicy(QComboBox.InsertAtTop)
        self.quickFindtextCombo.lastActive = None
        self.quickFindtextCombo.lastCursorPos = None
        self.quickFindtextCombo.leForegroundColor = \
            self.quickFindtextCombo.lineEdit().palette().color(QPalette.Text)
        self.quickFindtextCombo.leBackgroundColor = \
            self.quickFindtextCombo.lineEdit().palette().color(QPalette.Base)
        self.quickFindtextCombo.lastSearchText = ""
        self.quickFindtextCombo._editor = self.quickFindtextCombo.lineEdit()
        # this allows us not to jump across searched text
        # just because of autocompletion enabled
        self.quickFindtextCombo.setAutoCompletion(False)
        self.quickFindtextCombo.setMinimumWidth(250)
        self.quickFindtextCombo.setSizeAdjustPolicy(
            QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.quickFindtextCombo.addItem("")
        self.quickFindtextCombo.setWhatsThis(QApplication.translate('ViewManager',
                """<p>Enter the searchtext directly into this field."""
                """ The search will be performed case insensitive."""
                """ The quicksearch function is activated upon activation"""
                """ of the quicksearch next action (default key Ctrl+Shift+K),"""
                """ if this entry field does not have the input focus."""
                """ Otherwise it searches for the next occurrence of the"""
                """ text entered. The quicksearch backwards action"""
                """ (default key Ctrl+Shift+J) searches backward."""
                """ Activating the 'quicksearch extend' action"""
                """ (default key Ctrl+Shift+H) extends the current"""
                """ searchtext to the end of the currently found word."""
                """ The quicksearch can be ended by pressing the Return key"""
                """ while the quicksearch entry has the the input focus.</p>"""
        ))
        self.quickFindtextCombo._editor.returnPressed.connect(self.__quickSearchEnter)
        self.quickFindtextCombo._editor.textChanged.connect(self.__quickSearchText)
        self.quickFindtextCombo._editor.escPressed.connect(self.__quickSearchEscape)
        self.quickFindtextCombo._editor.gotFocus.connect(self.__quickSearchFocusIn)
        self.quickFindtextAction = QWidgetAction(self)
        self.quickFindtextAction.setDefaultWidget(self.quickFindtextCombo)
        self.quickFindtextAction.setObjectName("vm_quickfindtext_action")
        self.quickFindtextAction.setText(self.trUtf8("Quicksearch Textedit"))
        qtb.addAction(self.quickFindtextAction)
        qtb.addAction(self.quickSearchAct)
        qtb.addAction(self.quickSearchBackAct)
        qtb.addAction(self.quickSearchExtendAct)
        self.quickFindtextCombo.setEnabled(False)
        
        tb = QToolBar(QApplication.translate('ViewManager', 'Search'), self.ui)
        tb.setIconSize(UI.Config.ToolBarIconSize)
        tb.setObjectName("SearchToolbar")
        tb.setToolTip(QApplication.translate('ViewManager', 'Search'))
        
        tb.addAction(self.searchAct)
        tb.addAction(self.searchNextAct)
        tb.addAction(self.searchPrevAct)
        tb.addSeparator()
        tb.addAction(self.searchClearMarkersAct)
        tb.addSeparator()
        tb.addAction(self.searchFilesAct)
        
        tb.setAllowedAreas(Qt.ToolBarAreas(Qt.TopToolBarArea | Qt.BottomToolBarArea))
        
        toolbarManager.addToolBar(qtb, qtb.windowTitle())
        toolbarManager.addToolBar(tb, tb.windowTitle())
        toolbarManager.addAction(self.gotoAct, tb.windowTitle())
        toolbarManager.addAction(self.gotoBraceAct, tb.windowTitle())
        
        return tb, qtb
    
    ##################################################################
    ## Initialize the view related actions, view menu and toolbar
    ##################################################################
    
    def __initViewActions(self):
        """
        Private method defining the user interface actions for the view commands.
        """
        self.viewActGrp = createActionGroup(self)
        self.viewFoldActGrp = createActionGroup(self)
        
        self.zoomInAct = E5Action(QApplication.translate('ViewManager', 'Zoom in'),
                            UI.PixmapCache.getIcon("zoomIn.png"),
                            QApplication.translate('ViewManager', 'Zoom &in'),
                            QKeySequence(QApplication.translate('ViewManager',
                                "Ctrl++", "View|Zoom in")),
                            0,
                            self.viewActGrp, 'vm_view_zoom_in')
        self.zoomInAct.setStatusTip(QApplication.translate('ViewManager',
            'Zoom in on the text'))
        self.zoomInAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Zoom in</b>"""
                """<p>Zoom in on the text. This makes the text bigger.</p>"""
                ))
        self.zoomInAct.triggered[()].connect(self.__zoomIn)
        self.viewActions.append(self.zoomInAct)
        
        self.zoomOutAct = E5Action(QApplication.translate('ViewManager', 'Zoom out'),
                            UI.PixmapCache.getIcon("zoomOut.png"),
                            QApplication.translate('ViewManager', 'Zoom &out'),
                            QKeySequence(QApplication.translate('ViewManager',
                                "Ctrl+-", "View|Zoom out")),
                            0,
                            self.viewActGrp, 'vm_view_zoom_out')
        self.zoomOutAct.setStatusTip(QApplication.translate('ViewManager',
            'Zoom out on the text'))
        self.zoomOutAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Zoom out</b>"""
                """<p>Zoom out on the text. This makes the text smaller.</p>"""
                ))
        self.zoomOutAct.triggered[()].connect(self.__zoomOut)
        self.viewActions.append(self.zoomOutAct)
        
        self.zoomToAct = E5Action(QApplication.translate('ViewManager', 'Zoom'),
                            UI.PixmapCache.getIcon("zoomTo.png"),
                            QApplication.translate('ViewManager', '&Zoom'),
                            QKeySequence(QApplication.translate('ViewManager',
                                "Ctrl+#", "View|Zoom")),
                            0,
                            self.viewActGrp, 'vm_view_zoom')
        self.zoomToAct.setStatusTip(QApplication.translate('ViewManager',
            'Zoom the text'))
        self.zoomToAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Zoom</b>"""
                """<p>Zoom the text. This opens a dialog where the"""
                """ desired size can be entered.</p>"""
                ))
        self.zoomToAct.triggered[()].connect(self.__zoom)
        self.viewActions.append(self.zoomToAct)
        
        self.toggleAllAct = E5Action(QApplication.translate('ViewManager',
                                'Toggle all folds'),
                            QApplication.translate('ViewManager', 'Toggle &all folds'),
                            0, 0, self.viewFoldActGrp, 'vm_view_toggle_all_folds')
        self.toggleAllAct.setStatusTip(QApplication.translate('ViewManager',
            'Toggle all folds'))
        self.toggleAllAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Toggle all folds</b>"""
                """<p>Toggle all folds of the current editor.</p>"""
                ))
        self.toggleAllAct.triggered[()].connect(self.__toggleAll)
        self.viewActions.append(self.toggleAllAct)
        
        self.toggleAllChildrenAct = \
                E5Action(QApplication.translate('ViewManager',
                            'Toggle all folds (including children)'),
                        QApplication.translate('ViewManager',
                            'Toggle all &folds (including children)'),
                        0, 0, self.viewFoldActGrp, 'vm_view_toggle_all_folds_children')
        self.toggleAllChildrenAct.setStatusTip(QApplication.translate('ViewManager',
                'Toggle all folds (including children)'))
        self.toggleAllChildrenAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Toggle all folds (including children)</b>"""
                """<p>Toggle all folds of the current editor including"""
                """ all children.</p>"""
                ))
        self.toggleAllChildrenAct.triggered[()].connect(self.__toggleAllChildren)
        self.viewActions.append(self.toggleAllChildrenAct)
        
        self.toggleCurrentAct = E5Action(QApplication.translate('ViewManager',
                                'Toggle current fold'),
                            QApplication.translate('ViewManager', 'Toggle &current fold'),
                            0, 0, self.viewFoldActGrp, 'vm_view_toggle_current_fold')
        self.toggleCurrentAct.setStatusTip(QApplication.translate('ViewManager',
            'Toggle current fold'))
        self.toggleCurrentAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Toggle current fold</b>"""
                """<p>Toggle the folds of the current line of the current editor.</p>"""
                ))
        self.toggleCurrentAct.triggered[()].connect(self.__toggleCurrent)
        self.viewActions.append(self.toggleCurrentAct)
        
        self.unhighlightAct = E5Action(QApplication.translate('ViewManager',
                                'Remove all highlights'),
                            UI.PixmapCache.getIcon("unhighlight.png"),
                            QApplication.translate('ViewManager',
                                'Remove all highlights'),
                            0, 0, self, 'vm_view_unhighlight')
        self.unhighlightAct.setStatusTip(QApplication.translate('ViewManager',
            'Remove all highlights'))
        self.unhighlightAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Remove all highlights</b>"""
                """<p>Remove the highlights of all editors.</p>"""
                ))
        self.unhighlightAct.triggered[()].connect(self.unhighlight)
        self.viewActions.append(self.unhighlightAct)
        
        self.splitViewAct = E5Action(QApplication.translate('ViewManager', 'Split view'),
                            UI.PixmapCache.getIcon("splitVertical.png"),
                            QApplication.translate('ViewManager', '&Split view'),
                            0, 0, self, 'vm_view_split_view')
        self.splitViewAct.setStatusTip(QApplication.translate('ViewManager',
            'Add a split to the view'))
        self.splitViewAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Split view</b>"""
                """<p>Add a split to the view.</p>"""
                ))
        self.splitViewAct.triggered[()].connect(self.__splitView)
        self.viewActions.append(self.splitViewAct)
        
        self.splitOrientationAct = E5Action(QApplication.translate('ViewManager',
                                'Arrange horizontally'),
                            QApplication.translate('ViewManager',
                                'Arrange &horizontally'),
                            0, 0, self, 'vm_view_arrange_horizontally', True)
        self.splitOrientationAct.setStatusTip(QApplication.translate('ViewManager',
                'Arrange the splitted views horizontally'))
        self.splitOrientationAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Arrange horizontally</b>"""
                """<p>Arrange the splitted views horizontally.</p>"""
                ))
        self.splitOrientationAct.setChecked(False)
        self.splitOrientationAct.toggled[bool].connect(self.__splitOrientation)
        self.viewActions.append(self.splitOrientationAct)
        
        self.splitRemoveAct = E5Action(QApplication.translate('ViewManager',
                                'Remove split'),
                            UI.PixmapCache.getIcon("remsplitVertical.png"),
                            QApplication.translate('ViewManager', '&Remove split'),
                            0, 0, self, 'vm_view_remove_split')
        self.splitRemoveAct.setStatusTip(QApplication.translate('ViewManager',
            'Remove the current split'))
        self.splitRemoveAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Remove split</b>"""
                """<p>Remove the current split.</p>"""
                ))
        self.splitRemoveAct.triggered[()].connect(self.removeSplit)
        self.viewActions.append(self.splitRemoveAct)
        
        self.nextSplitAct = E5Action(QApplication.translate('ViewManager', 'Next split'),
                            QApplication.translate('ViewManager', '&Next split'),
                            QKeySequence(QApplication.translate('ViewManager',
                                "Ctrl+Alt+N", "View|Next split")),
                            0,
                            self, 'vm_next_split')
        self.nextSplitAct.setStatusTip(QApplication.translate('ViewManager',
            'Move to the next split'))
        self.nextSplitAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Next split</b>"""
                """<p>Move to the next split.</p>"""
                ))
        self.nextSplitAct.triggered[()].connect(self.nextSplit)
        self.viewActions.append(self.nextSplitAct)
        
        self.prevSplitAct = E5Action(QApplication.translate('ViewManager',
                                'Previous split'),
                            QApplication.translate('ViewManager', '&Previous split'),
                            QKeySequence(QApplication.translate('ViewManager',
                                "Ctrl+Alt+P", "View|Previous split")),
                            0, self, 'vm_previous_split')
        self.prevSplitAct.setStatusTip(QApplication.translate('ViewManager',
            'Move to the previous split'))
        self.prevSplitAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Previous split</b>"""
                """<p>Move to the previous split.</p>"""
                ))
        self.prevSplitAct.triggered[()].connect(self.prevSplit)
        self.viewActions.append(self.prevSplitAct)
        
        self.viewActGrp.setEnabled(False)
        self.viewFoldActGrp.setEnabled(False)
        self.unhighlightAct.setEnabled(False)
        self.splitViewAct.setEnabled(False)
        self.splitOrientationAct.setEnabled(False)
        self.splitRemoveAct.setEnabled(False)
        self.nextSplitAct.setEnabled(False)
        self.prevSplitAct.setEnabled(False)
        
    def initViewMenu(self):
        """
        Public method to create the View menu
        
        @return the generated menu
        """
        menu = QMenu(QApplication.translate('ViewManager', '&View'), self.ui)
        menu.setTearOffEnabled(True)
        menu.addActions(self.viewActGrp.actions())
        menu.addSeparator()
        menu.addActions(self.viewFoldActGrp.actions())
        menu.addSeparator()
        menu.addAction(self.unhighlightAct)
        if self.canSplit():
            menu.addSeparator()
            menu.addAction(self.splitViewAct)
            menu.addAction(self.splitOrientationAct)
            menu.addAction(self.splitRemoveAct)
            menu.addAction(self.nextSplitAct)
            menu.addAction(self.prevSplitAct)
        
        return menu
        
    def initViewToolbar(self, toolbarManager):
        """
        Public method to create the View toolbar
        
        @param toolbarManager reference to a toolbar manager object (E5ToolBarManager)
        @return the generated toolbar
        """
        tb = QToolBar(QApplication.translate('ViewManager', 'View'), self.ui)
        tb.setIconSize(UI.Config.ToolBarIconSize)
        tb.setObjectName("ViewToolbar")
        tb.setToolTip(QApplication.translate('ViewManager', 'View'))
        
        tb.addActions(self.viewActGrp.actions())
        
        toolbarManager.addToolBar(tb, tb.windowTitle())
        toolbarManager.addAction(self.unhighlightAct, tb.windowTitle())
        toolbarManager.addAction(self.splitViewAct, tb.windowTitle())
        toolbarManager.addAction(self.splitRemoveAct, tb.windowTitle())
        
        return tb
    
    ##################################################################
    ## Initialize the macro related actions and macro menu
    ##################################################################
    
    def __initMacroActions(self):
        """
        Private method defining the user interface actions for the macro commands.
        """
        self.macroActGrp = createActionGroup(self)

        self.macroStartRecAct = E5Action(QApplication.translate('ViewManager',
                            'Start Macro Recording'),
                            QApplication.translate('ViewManager',
                            'S&tart Macro Recording'),
                            0, 0, self.macroActGrp, 'vm_macro_start_recording')
        self.macroStartRecAct.setStatusTip(QApplication.translate('ViewManager',
            'Start Macro Recording'))
        self.macroStartRecAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Start Macro Recording</b>"""
                """<p>Start recording editor commands into a new macro.</p>"""
                ))
        self.macroStartRecAct.triggered[()].connect(self.__macroStartRecording)
        self.macroActions.append(self.macroStartRecAct)
        
        self.macroStopRecAct = E5Action(QApplication.translate('ViewManager',
                            'Stop Macro Recording'),
                            QApplication.translate('ViewManager',
                            'Sto&p Macro Recording'),
                            0, 0, self.macroActGrp, 'vm_macro_stop_recording')
        self.macroStopRecAct.setStatusTip(QApplication.translate('ViewManager',
            'Stop Macro Recording'))
        self.macroStopRecAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Stop Macro Recording</b>"""
                """<p>Stop recording editor commands into a new macro.</p>"""
                ))
        self.macroStopRecAct.triggered[()].connect(self.__macroStopRecording)
        self.macroActions.append(self.macroStopRecAct)
        
        self.macroRunAct = E5Action(QApplication.translate('ViewManager', 'Run Macro'),
                            QApplication.translate('ViewManager', '&Run Macro'),
                            0, 0, self.macroActGrp, 'vm_macro_run')
        self.macroRunAct.setStatusTip(QApplication.translate('ViewManager', 'Run Macro'))
        self.macroRunAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Run Macro</b>"""
                """<p>Run a previously recorded editor macro.</p>"""
                ))
        self.macroRunAct.triggered[()].connect(self.__macroRun)
        self.macroActions.append(self.macroRunAct)
        
        self.macroDeleteAct = E5Action(QApplication.translate('ViewManager',
                                'Delete Macro'),
                            QApplication.translate('ViewManager', '&Delete Macro'),
                            0, 0, self.macroActGrp, 'vm_macro_delete')
        self.macroDeleteAct.setStatusTip(QApplication.translate('ViewManager',
            'Delete Macro'))
        self.macroDeleteAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Delete Macro</b>"""
                """<p>Delete a previously recorded editor macro.</p>"""
                ))
        self.macroDeleteAct.triggered[()].connect(self.__macroDelete)
        self.macroActions.append(self.macroDeleteAct)
        
        self.macroLoadAct = E5Action(QApplication.translate('ViewManager', 'Load Macro'),
                            QApplication.translate('ViewManager', '&Load Macro'),
                            0, 0, self.macroActGrp, 'vm_macro_load')
        self.macroLoadAct.setStatusTip(QApplication.translate('ViewManager',
            'Load Macro'))
        self.macroLoadAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Load Macro</b>"""
                """<p>Load an editor macro from a file.</p>"""
                ))
        self.macroLoadAct.triggered[()].connect(self.__macroLoad)
        self.macroActions.append(self.macroLoadAct)
        
        self.macroSaveAct = E5Action(QApplication.translate('ViewManager', 'Save Macro'),
                            QApplication.translate('ViewManager', '&Save Macro'),
                            0, 0, self.macroActGrp, 'vm_macro_save')
        self.macroSaveAct.setStatusTip(QApplication.translate('ViewManager',
            'Save Macro'))
        self.macroSaveAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Save Macro</b>"""
                """<p>Save a previously recorded editor macro to a file.</p>"""
                ))
        self.macroSaveAct.triggered[()].connect(self.__macroSave)
        self.macroActions.append(self.macroSaveAct)
        
        self.macroActGrp.setEnabled(False)
        
    def initMacroMenu(self):
        """
        Public method to create the Macro menu
        
        @return the generated menu
        """
        menu = QMenu(QApplication.translate('ViewManager', "&Macros"), self.ui)
        menu.setTearOffEnabled(True)
        menu.addActions(self.macroActGrp.actions())
        
        return menu
    
    #####################################################################
    ## Initialize the bookmark related actions, bookmark menu and toolbar
    #####################################################################
    
    def __initBookmarkActions(self):
        """
        Private method defining the user interface actions for the bookmarks commands.
        """
        self.bookmarkActGrp = createActionGroup(self)

        self.bookmarkToggleAct = E5Action(QApplication.translate('ViewManager',
                                'Toggle Bookmark'),
                            UI.PixmapCache.getIcon("bookmarkToggle.png"),
                            QApplication.translate('ViewManager', '&Toggle Bookmark'),
                            QKeySequence(QApplication.translate('ViewManager',
                                "Alt+Ctrl+T", "Bookmark|Toggle")), 0,
                            self.bookmarkActGrp, 'vm_bookmark_toggle')
        self.bookmarkToggleAct.setStatusTip(QApplication.translate('ViewManager',
            'Toggle Bookmark'))
        self.bookmarkToggleAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Toggle Bookmark</b>"""
                """<p>Toggle a bookmark at the current line of the current editor.</p>"""
                ))
        self.bookmarkToggleAct.triggered[()].connect(self.__toggleBookmark)
        self.bookmarkActions.append(self.bookmarkToggleAct)
        
        self.bookmarkNextAct = E5Action(QApplication.translate('ViewManager',
                                'Next Bookmark'),
                            UI.PixmapCache.getIcon("bookmarkNext.png"),
                            QApplication.translate('ViewManager', '&Next Bookmark'),
                            QKeySequence(QApplication.translate('ViewManager',
                                "Ctrl+PgDown", "Bookmark|Next")), 0,
                            self.bookmarkActGrp, 'vm_bookmark_next')
        self.bookmarkNextAct.setStatusTip(QApplication.translate('ViewManager',
            'Next Bookmark'))
        self.bookmarkNextAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Next Bookmark</b>"""
                """<p>Go to next bookmark of the current editor.</p>"""
                ))
        self.bookmarkNextAct.triggered[()].connect(self.__nextBookmark)
        self.bookmarkActions.append(self.bookmarkNextAct)
        
        self.bookmarkPreviousAct = E5Action(QApplication.translate('ViewManager',
                                'Previous Bookmark'),
                            UI.PixmapCache.getIcon("bookmarkPrevious.png"),
                            QApplication.translate('ViewManager', '&Previous Bookmark'),
                            QKeySequence(QApplication.translate('ViewManager',
                                "Ctrl+PgUp", "Bookmark|Previous")),
                            0, self.bookmarkActGrp, 'vm_bookmark_previous')
        self.bookmarkPreviousAct.setStatusTip(QApplication.translate('ViewManager',
            'Previous Bookmark'))
        self.bookmarkPreviousAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Previous Bookmark</b>"""
                """<p>Go to previous bookmark of the current editor.</p>"""
                ))
        self.bookmarkPreviousAct.triggered[()].connect(self.__previousBookmark)
        self.bookmarkActions.append(self.bookmarkPreviousAct)
        
        self.bookmarkClearAct = E5Action(QApplication.translate('ViewManager',
                                'Clear Bookmarks'),
                            QApplication.translate('ViewManager', '&Clear Bookmarks'),
                            QKeySequence(QApplication.translate('ViewManager',
                                "Alt+Ctrl+C", "Bookmark|Clear")),
                            0,
                            self.bookmarkActGrp, 'vm_bookmark_clear')
        self.bookmarkClearAct.setStatusTip(QApplication.translate('ViewManager',
            'Clear Bookmarks'))
        self.bookmarkClearAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Clear Bookmarks</b>"""
                """<p>Clear bookmarks of all editors.</p>"""
                ))
        self.bookmarkClearAct.triggered[()].connect(self.__clearAllBookmarks)
        self.bookmarkActions.append(self.bookmarkClearAct)
        
        self.syntaxErrorGotoAct = E5Action(QApplication.translate('ViewManager',
                                'Goto Syntax Error'),
                            UI.PixmapCache.getIcon("syntaxErrorGoto.png"),
                            QApplication.translate('ViewManager', '&Goto Syntax Error'),
                            0, 0,
                            self.bookmarkActGrp, 'vm_syntaxerror_goto')
        self.syntaxErrorGotoAct.setStatusTip(QApplication.translate('ViewManager',
            'Goto Syntax Error'))
        self.syntaxErrorGotoAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Goto Syntax Error</b>"""
                """<p>Go to next syntax error of the current editor.</p>"""
                ))
        self.syntaxErrorGotoAct.triggered[()].connect(self.__gotoSyntaxError)
        self.bookmarkActions.append(self.syntaxErrorGotoAct)
        
        self.syntaxErrorClearAct = E5Action(QApplication.translate('ViewManager',
                                'Clear Syntax Errors'),
                            QApplication.translate('ViewManager', 'Clear &Syntax Errors'),
                            0, 0,
                            self.bookmarkActGrp, 'vm_syntaxerror_clear')
        self.syntaxErrorClearAct.setStatusTip(QApplication.translate('ViewManager',
            'Clear Syntax Errors'))
        self.syntaxErrorClearAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Clear Syntax Errors</b>"""
                """<p>Clear syntax errors of all editors.</p>"""
                ))
        self.syntaxErrorClearAct.triggered[()].connect(self.__clearAllSyntaxErrors)
        self.bookmarkActions.append(self.syntaxErrorClearAct)
        
        self.warningsNextAct = E5Action(QApplication.translate('ViewManager',
                                'Next warning message'),
                            UI.PixmapCache.getIcon("warningNext.png"),
                            QApplication.translate('ViewManager',
                                '&Next warning message'),
                            0, 0,
                            self.bookmarkActGrp, 'vm_warning_next')
        self.warningsNextAct.setStatusTip(QApplication.translate('ViewManager',
            'Next warning message'))
        self.warningsNextAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Next warning message</b>"""
                """<p>Go to next line of the current editor"""
                """ having a py3flakes warning.</p>"""
                ))
        self.warningsNextAct.triggered[()].connect(self.__nextWarning)
        self.bookmarkActions.append(self.warningsNextAct)
        
        self.warningsPreviousAct = E5Action(QApplication.translate('ViewManager',
                                'Previous warning message'),
                            UI.PixmapCache.getIcon("warningPrev.png"),
                            QApplication.translate('ViewManager',
                                '&Previous warning message'),
                            0, 0,
                            self.bookmarkActGrp, 'vm_warning_previous')
        self.warningsPreviousAct.setStatusTip(QApplication.translate('ViewManager',
            'Previous warning message'))
        self.warningsPreviousAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Previous warning message</b>"""
                """<p>Go to previous line of the current editor"""
                """ having a py3flakes warning.</p>"""
                ))
        self.warningsPreviousAct.triggered[()].connect(self.__previousWarning)
        self.bookmarkActions.append(self.warningsPreviousAct)
        
        self.warningsClearAct = E5Action(QApplication.translate('ViewManager',
                                'Clear Warning Messages'),
                            QApplication.translate('ViewManager',
                                'Clear &Warning Messages'),
                            0, 0,
                            self.bookmarkActGrp, 'vm_warnings_clear')
        self.warningsClearAct.setStatusTip(QApplication.translate('ViewManager',
            'Clear Warning Messages'))
        self.warningsClearAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Clear Warning Messages</b>"""
                """<p>Clear py3flakes warning messages of all editors.</p>"""
                ))
        self.warningsClearAct.triggered[()].connect(self.__clearAllWarnings)
        self.bookmarkActions.append(self.warningsClearAct)
        
        self.notcoveredNextAct = E5Action(QApplication.translate('ViewManager',
                                'Next uncovered line'),
                            UI.PixmapCache.getIcon("notcoveredNext.png"),
                            QApplication.translate('ViewManager', '&Next uncovered line'),
                            0, 0,
                            self.bookmarkActGrp, 'vm_uncovered_next')
        self.notcoveredNextAct.setStatusTip(QApplication.translate('ViewManager',
            'Next uncovered line'))
        self.notcoveredNextAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Next uncovered line</b>"""
                """<p>Go to next line of the current editor marked as not covered.</p>"""
                ))
        self.notcoveredNextAct.triggered[()].connect(self.__nextUncovered)
        self.bookmarkActions.append(self.notcoveredNextAct)
        
        self.notcoveredPreviousAct = E5Action(QApplication.translate('ViewManager',
                                'Previous uncovered line'),
                            UI.PixmapCache.getIcon("notcoveredPrev.png"),
                            QApplication.translate('ViewManager',
                                '&Previous uncovered line'),
                            0, 0,
                            self.bookmarkActGrp, 'vm_uncovered_previous')
        self.notcoveredPreviousAct.setStatusTip(QApplication.translate('ViewManager',
            'Previous uncovered line'))
        self.notcoveredPreviousAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Previous uncovered line</b>"""
                """<p>Go to previous line of the current editor marked"""
                """ as not covered.</p>"""
                ))
        self.notcoveredPreviousAct.triggered[()].connect(self.__previousUncovered)
        self.bookmarkActions.append(self.notcoveredPreviousAct)
        
        self.taskNextAct = E5Action(QApplication.translate('ViewManager',
                                'Next Task'),
                            UI.PixmapCache.getIcon("taskNext.png"),
                            QApplication.translate('ViewManager', '&Next Task'),
                            0, 0,
                            self.bookmarkActGrp, 'vm_task_next')
        self.taskNextAct.setStatusTip(QApplication.translate('ViewManager',
            'Next Task'))
        self.taskNextAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Next Task</b>"""
                """<p>Go to next line of the current editor having a task.</p>"""
                ))
        self.taskNextAct.triggered[()].connect(self.__nextTask)
        self.bookmarkActions.append(self.taskNextAct)
        
        self.taskPreviousAct = E5Action(QApplication.translate('ViewManager',
                                'Previous Task'),
                            UI.PixmapCache.getIcon("taskPrev.png"),
                            QApplication.translate('ViewManager',
                                '&Previous Task'),
                            0, 0,
                            self.bookmarkActGrp, 'vm_task_previous')
        self.taskPreviousAct.setStatusTip(QApplication.translate('ViewManager',
            'Previous Task'))
        self.taskPreviousAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Previous Task</b>"""
                """<p>Go to previous line of the current editor having a task.</p>"""
                ))
        self.taskPreviousAct.triggered[()].connect(self.__previousTask)
        self.bookmarkActions.append(self.taskPreviousAct)
        
        self.bookmarkActGrp.setEnabled(False)
        
    def initBookmarkMenu(self):
        """
        Public method to create the Bookmark menu
        
        @return the generated menu
        """
        menu = QMenu(QApplication.translate('ViewManager', '&Bookmarks'), self.ui)
        self.bookmarksMenu = QMenu(QApplication.translate('ViewManager', '&Bookmarks'),
            menu)
        menu.setTearOffEnabled(True)
        
        menu.addAction(self.bookmarkToggleAct)
        menu.addAction(self.bookmarkNextAct)
        menu.addAction(self.bookmarkPreviousAct)
        menu.addAction(self.bookmarkClearAct)
        menu.addSeparator()
        self.menuBookmarksAct = menu.addMenu(self.bookmarksMenu)
        menu.addSeparator()
        menu.addAction(self.syntaxErrorGotoAct)
        menu.addAction(self.syntaxErrorClearAct)
        menu.addSeparator()
        menu.addAction(self.warningsNextAct)
        menu.addAction(self.warningsPreviousAct)
        menu.addAction(self.warningsClearAct)
        menu.addSeparator()
        menu.addAction(self.notcoveredNextAct)
        menu.addAction(self.notcoveredPreviousAct)
        menu.addSeparator()
        menu.addAction(self.taskNextAct)
        menu.addAction(self.taskPreviousAct)
        
        self.bookmarksMenu.aboutToShow.connect(self.__showBookmarksMenu)
        self.bookmarksMenu.triggered.connect(self.__bookmarkSelected)
        menu.aboutToShow.connect(self.__showBookmarkMenu)
        
        return menu
        
    def initBookmarkToolbar(self, toolbarManager):
        """
        Public method to create the Bookmark toolbar
        
        @param toolbarManager reference to a toolbar manager object (E5ToolBarManager)
        @return the generated toolbar
        """
        tb = QToolBar(QApplication.translate('ViewManager', 'Bookmarks'), self.ui)
        tb.setIconSize(UI.Config.ToolBarIconSize)
        tb.setObjectName("BookmarksToolbar")
        tb.setToolTip(QApplication.translate('ViewManager', 'Bookmarks'))
        
        tb.addAction(self.bookmarkToggleAct)
        tb.addAction(self.bookmarkNextAct)
        tb.addAction(self.bookmarkPreviousAct)
        tb.addSeparator()
        tb.addAction(self.syntaxErrorGotoAct)
        tb.addSeparator()
        tb.addAction(self.warningsNextAct)
        tb.addAction(self.warningsPreviousAct)
        tb.addSeparator()
        tb.addAction(self.taskNextAct)
        tb.addAction(self.taskPreviousAct)
        
        toolbarManager.addToolBar(tb, tb.windowTitle())
        toolbarManager.addAction(self.notcoveredNextAct, tb.windowTitle())
        toolbarManager.addAction(self.notcoveredPreviousAct, tb.windowTitle())
        
        return tb
    
    ##################################################################
    ## Initialize the spell checking related actions
    ##################################################################
    
    def __initSpellingActions(self):
        """
        Private method to initialize the spell checking actions.
        """
        self.spellingActGrp = createActionGroup(self)
        
        self.spellCheckAct = E5Action(QApplication.translate('ViewManager',
                                'Spell check'),
                            UI.PixmapCache.getIcon("spellchecking.png"),
                            QApplication.translate('ViewManager',
                                '&Spell Check...'),
                            QKeySequence(QApplication.translate('ViewManager',
                                "Shift+F7", "Spelling|Spell Check")),
                            0,
                            self.spellingActGrp, 'vm_spelling_spellcheck')
        self.spellCheckAct.setStatusTip(QApplication.translate('ViewManager',
            'Perform spell check of current editor'))
        self.spellCheckAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Spell check</b>"""
                """<p>Perform a spell check of the current editor.</p>"""
                ))
        self.spellCheckAct.triggered[()].connect(self.__spellCheck)
        self.spellingActions.append(self.spellCheckAct)
        
        self.autoSpellCheckAct = E5Action(QApplication.translate('ViewManager',
                                'Automatic spell checking'),
                            UI.PixmapCache.getIcon("autospellchecking.png"),
                            QApplication.translate('ViewManager',
                                '&Automatic spell checking'),
                            0, 0,
                            self.spellingActGrp, 'vm_spelling_autospellcheck')
        self.autoSpellCheckAct.setStatusTip(QApplication.translate('ViewManager',
            '(De-)Activate automatic spell checking'))
        self.autoSpellCheckAct.setWhatsThis(QApplication.translate('ViewManager',
                """<b>Automatic spell checking</b>"""
                """<p>Activate or deactivate the automatic spell checking function of"""
                """ all editors.</p>"""
                ))
        self.autoSpellCheckAct.setCheckable(True)
        self.autoSpellCheckAct.setChecked(
            Preferences.getEditor("AutoSpellCheckingEnabled"))
        self.autoSpellCheckAct.triggered[()].connect(self.__setAutoSpellChecking)
        self.spellingActions.append(self.autoSpellCheckAct)
        
        self.__enableSpellingActions()
        
    def __enableSpellingActions(self):
        """
        Private method to set the enabled state of the spelling actions.
        """
        spellingAvailable = SpellChecker.isAvailable()
        
        self.spellCheckAct.setEnabled(len(self.editors) != 0 and spellingAvailable)
        self.autoSpellCheckAct.setEnabled(spellingAvailable)
    
    def addToExtrasMenu(self, menu):
        """
        Public method to add some actions to the extras menu.
        """
        menu.addAction(self.spellCheckAct)
        menu.addAction(self.autoSpellCheckAct)
        menu.addSeparator()
    
    def initSpellingToolbar(self, toolbarManager):
        """
        Public method to create the Spelling toolbar
        
        @param toolbarManager reference to a toolbar manager object (E5ToolBarManager)
        @return the generated toolbar
        """
        tb = QToolBar(QApplication.translate('ViewManager', 'Spelling'), self.ui)
        tb.setIconSize(UI.Config.ToolBarIconSize)
        tb.setObjectName("SpellingToolbar")
        tb.setToolTip(QApplication.translate('ViewManager', 'Spelling'))
        
        tb.addAction(self.spellCheckAct)
        tb.addAction(self.autoSpellCheckAct)
        
        toolbarManager.addToolBar(tb, tb.windowTitle())
        
        return tb
    
    ##################################################################
    ## Methods and slots that deal with file and window handling
    ##################################################################
    
    def openFiles(self, prog=None):
        """
        Public slot to open some files.
        
        @param prog name of file to be opened (string)
        """
        # Get the file name if one wasn't specified.
        if prog is None:
            # set the cwd of the dialog based on the following search criteria:
            #     1: Directory of currently active editor
            #     2: Directory of currently active project
            #     3: CWD
            filter = self._getOpenFileFilter()
            progs = E5FileDialog.getOpenFileNamesAndFilter(
                self.ui,
                QApplication.translate('ViewManager', "Open files"),
                self._getOpenStartDir(),
                QScintilla.Lexers.getOpenFileFiltersList(True, True),
                filter)[0]
        else:
            progs = [prog]
        
        for prog in progs:
            prog = Utilities.normabspath(prog)
            # Open up the new files.
            self.openSourceFile(prog)

    def checkDirty(self, editor, autosave=False):
        """
        Public method to check dirty status and open a message window.
        
        @param editor editor window to check
        @param autosave flag indicating that the file should be saved
            automatically (boolean)
        @return flag indicating successful reset of the dirty flag (boolean)
        """
        if editor.isModified():
            fn = editor.getFileName()
            # ignore the dirty status, if there is more than one open editor
            # for the same file
            if fn and self.getOpenEditorCount(fn) > 1:
                return True
            
            if fn is None:
                fn = editor.getNoName()
                autosave = False
            if autosave:
                res = editor.saveFile()
            else:
                res = E5MessageBox.okToClearData(self.ui,
                    QApplication.translate('ViewManager', "File Modified"),
                    QApplication.translate('ViewManager',
                        """<p>The file <b>{0}</b> has unsaved changes.</p>""")
                        .format(fn),
                    editor.saveFile)
            if res:
                self.setEditorName(editor, editor.getFileName())
            return res
        
        return True
        
    def checkAllDirty(self):
        """
        Public method to check the dirty status of all editors.
        
        @return flag indicating successful reset of all dirty flags (boolean)
        """
        for editor in self.editors:
            if not self.checkDirty(editor):
                return False
        
        return True
        
    def closeEditor(self, editor):
        """
        Public method to close an editor window.
        
        @param editor editor window to be closed
        @return flag indicating success (boolean)
        """
        # save file if necessary
        if not self.checkDirty(editor):
            return False
        
        # get the filename of the editor for later use
        fn = editor.getFileName()
        
        # remove the window
        self._removeView(editor)
        self.editors.remove(editor)
        
        # send a signal, if it was the last editor for this filename
        if fn and self.getOpenEditor(fn) is None:
            self.editorClosed.emit(fn)
        self.editorClosedEd.emit(editor)
        
        # send a signal, if it was the very last editor
        if not len(self.editors):
            self.__lastEditorClosed()
            self.lastEditorClosed.emit()
        
        return True
        
    def closeCurrentWindow(self):
        """
        Public method to close the current window.
        
        @return flag indicating success (boolean)
        """
        aw = self.activeWindow()
        if aw is None:
            return False
        
        res = self.closeEditor(aw)
        if res and aw == self.currentEditor:
            self.currentEditor = None
        
        return res
        
    def closeAllWindows(self):
        """
        Private method to close all editor windows via file menu.
        """
        savedEditors = self.editors[:]
        for editor in savedEditors:
            self.closeEditor(editor)
        
    def closeWindow(self, fn):
        """
        Public method to close an arbitrary source editor.
        
        @param fn filename of editor to be closed
        @return flag indicating success (boolean)
        """
        for editor in self.editors:
            if Utilities.samepath(fn, editor.getFileName()):
                break
        else:
            return True
        
        res = self.closeEditor(editor)
        if res and editor == self.currentEditor:
            self.currentEditor = None
        
        return res
        
    def closeEditorWindow(self, editor):
        """
        Public method to close an arbitrary source editor.
        
        @param editor editor to be closed
        """
        if editor is None:
            return
        
        res = self.closeEditor(editor)
        if res and editor == self.currentEditor:
            self.currentEditor = None
        
    def exit(self):
        """
        Public method to handle the debugged program terminating.
        """
        if self.currentEditor is not None:
            self.currentEditor.highlight()
            self.currentEditor = None
            
        self.__setSbFile()
        
    def openSourceFile(self, fn, lineno=None, filetype="",
                       selStart=0, selEnd=0, pos=0):
        """
        Public slot to display a file in an editor.
        
        @param fn name of file to be opened (string)
        @param lineno line number to place the cursor at (integer)
        @param filetype type of the source file (string)
        @param selStart start of an area to be selected (integer)
        @param selEnd end of an area to be selected (integer)
        """
        try:
            newWin, editor = self.getEditor(fn, filetype=filetype)
        except (IOError, UnicodeDecodeError):
            return
        
        if newWin:
            self._modificationStatusChanged(editor.isModified(), editor)
        self._checkActions(editor)
        
        if lineno is not None and lineno >= 0:
            editor.ensureVisibleTop(lineno)
            editor.gotoLine(lineno, pos)
        
        if selStart != selEnd:
            editor.setSelection(lineno - 1, selStart, lineno - 1, selEnd)
        
        # insert filename into list of recently opened files
        self.addToRecentList(fn)
        
    def __connectEditor(self, editor):
        """
        Private method to establish all editor connections.
        
        @param editor reference to the editor object to be connected
        """
        editor.modificationStatusChanged.connect(self._modificationStatusChanged)
        editor.cursorChanged.connect(self.__cursorChanged)
        editor.editorSaved.connect(self.__editorSaved)
        editor.breakpointToggled.connect(self.__breakpointToggled)
        editor.bookmarkToggled.connect(self.__bookmarkToggled)
        editor.syntaxerrorToggled.connect(self._syntaxErrorToggled)
        editor.coverageMarkersShown.connect(self.__coverageMarkersShown)
        editor.autoCompletionAPIsAvailable.connect(
            self.__editorAutoCompletionAPIsAvailable)
        editor.undoAvailable.connect(self.undoAct.setEnabled)
        editor.redoAvailable.connect(self.redoAct.setEnabled)
        editor.taskMarkersUpdated.connect(self.__taskMarkersUpdated)
        editor.languageChanged.connect(self.__editorConfigChanged)
        editor.eolChanged.connect(self.__editorConfigChanged)
        editor.encodingChanged.connect(self.__editorConfigChanged)
        editor.selectionChanged.connect(self.searchDlg.selectionChanged)
        editor.selectionChanged.connect(self.replaceDlg.selectionChanged)
        
    def newEditorView(self, fn, caller, filetype=""):
        """
        Public method to create a new editor displaying the given document.
        
        @param fn filename of this view
        @param caller reference to the editor calling this method
        @param filetype type of the source file (string)
        """
        editor = self.cloneEditor(caller, filetype, fn)
        
        self._addView(editor, fn, caller.getNoName())
        self._modificationStatusChanged(editor.isModified(), editor)
        self._checkActions(editor)

    def cloneEditor(self, caller, filetype, fn):
        """
        Public method to clone an editor displaying the given document.
        
        @param caller reference to the editor calling this method
        @param filetype type of the source file (string)
        @param fn filename of this view
        @return reference to the new editor object (Editor.Editor)
        """
        editor = Editor(self.dbs, fn, self, filetype=filetype, editor=caller,
                        tv=e5App().getObject("TaskViewer"))
        self.editors.append(editor)
        self.__connectEditor(editor)
        self.__editorOpened()
        self.editorOpened.emit(fn)
        self.editorOpenedEd.emit(editor)

        return editor
        
    def addToRecentList(self, fn):
        """
        Public slot to add a filename to the list of recently opened files.
        
        @param fn name of the file to be added
        """
        for recent in self.recent[:]:
            if Utilities.samepath(fn, recent):
                self.recent.remove(recent)
        self.recent.insert(0, fn)
        maxRecent = Preferences.getUI("RecentNumber")
        if len(self.recent) > maxRecent:
            self.recent = self.recent[:maxRecent]
        self.__saveRecent()
        
    def showDebugSource(self, fn, line):
        """
        Public method to open the given file and highlight the given line in it.
        
        @param fn filename of editor to update (string)
        @param line line number to highlight (int)
        """
        self.openSourceFile(fn, line)
        self.setFileLine(fn, line)
        
    def setFileLine(self, fn, line, error=False, syntaxError=False):
        """
        Public method to update the user interface when the current program
        or line changes.
        
        @param fn filename of editor to update (string)
        @param line line number to highlight (int)
        @param error flag indicating an error highlight (boolean)
        @param syntaxError flag indicating a syntax error
        """
        try:
            newWin, self.currentEditor = self.getEditor(fn)
        except (IOError, UnicodeDecodeError):
            return
        
        enc = self.currentEditor.getEncoding()
        lang = self.currentEditor.getLanguage()
        eol = self.currentEditor.getEolIndicator()
        self.__setSbFile(fn, line, encoding=enc, language=lang, eol=eol)
        
        # Change the highlighted line.
        self.currentEditor.highlight(line, error, syntaxError)
        
        self.currentEditor.highlightVisible()
        self._checkActions(self.currentEditor, False)
        
    def __setSbFile(self, fn=None, line=None, pos=None,
                    encoding=None, language=None, eol=None):
        """
        Private method to set the file info in the status bar.
        
        @param fn filename to display (string)
        @param line line number to display (int)
        @param pos character position to display (int)
        @param encoding encoding name to display (string)
        @param language language to display (string)
        @param eol eol indicator to display (string)
        """
        if fn is None:
            fn = ''
            writ = '   '
        else:
            if QFileInfo(fn).isWritable():
                writ = ' rw'
            else:
                writ = ' ro'
        self.sbWritable.setText(writ)
        self.sbFile.setTextPath(QApplication.translate('ViewManager', 'File: {0}'), fn)
        
        if line is None:
            line = ''
        self.sbLine.setText(QApplication.translate('ViewManager', 'Line: {0:5}')
            .format(line))
        
        if pos is None:
            pos = ''
        self.sbPos.setText(QApplication.translate('ViewManager', 'Pos: {0:5}')
            .format(pos))
        
        if encoding is None:
            encoding = ''
        self.sbEnc.setText(encoding)
        
        if language is None:
            language = ''
        self.sbLang.setText(language)
        
        if eol is None:
            eol = ''
        self.sbEol.setText(eol)
        
    def unhighlight(self, current=False):
        """
        Public method to switch off all highlights.
        
        @param current flag indicating only the current editor should be unhighlighted
                (boolean)
        """
        if current:
            if self.currentEditor is not None:
                self.currentEditor.highlight()
        else:
            for editor in self.editors:
                editor.highlight()
        
    def getOpenFilenames(self):
        """
        Public method returning a list of the filenames of all editors.
        
        @return list of all opened filenames (list of strings)
        """
        filenames = []
        for editor in self.editors:
            fn = editor.getFileName()
            if fn is not None and fn not in filenames:
                filenames.append(fn)
        
        return filenames
        
    def getEditor(self, fn, filetype=""):
        """
        Public method to return the editor displaying the given file.
        
        If there is no editor with the given file, a new editor window is
        created.
        
        @param fn filename to look for
        @param filetype type of the source file (string)
        @return tuple of two values giving a flag indicating a new window creation and
            a reference to the editor displaying this file
        """
        newWin = False
        editor = self.activeWindow()
        if editor is None or not Utilities.samepath(fn, editor.getFileName()):
            for editor in self.editors:
                if Utilities.samepath(fn, editor.getFileName()):
                    break
            else:
                editor = Editor(self.dbs, fn, self, filetype=filetype,
                                tv=e5App().getObject("TaskViewer"))
                self.editors.append(editor)
                self.__connectEditor(editor)
                self.__editorOpened()
                self.editorOpened.emit(fn)
                self.editorOpenedEd.emit(editor)
                newWin = True
        
        if newWin:
            self._addView(editor, fn)
        else:
            self._showView(editor, fn)
        
        return (newWin, editor)
        
    def getOpenEditors(self):
        """
        Public method to get references to all open editors.
        
        @return list of references to all open editors (list of QScintilla.editor)
        """
        return self.editors
        
    def getOpenEditorsCount(self):
        """
        Public method to get the number of open editors.
        
        @return number of open editors (integer)
        """
        return len(self.editors)
        
    def getOpenEditor(self, fn):
        """
        Public method to return the editor displaying the given file.
        
        @param fn filename to look for
        @return a reference to the editor displaying this file or None, if
            no editor was found
        """
        for editor in self.editors:
            if Utilities.samepath(fn, editor.getFileName()):
                return editor
        
        return None
        
    def getOpenEditorCount(self, fn):
        """
        Public method to return the count of editors displaying the given file.
        
        @param fn filename to look for
        @return count of editors displaying this file (integer)
        """
        count = 0
        for editor in self.editors:
            if Utilities.samepath(fn, editor.getFileName()):
                count += 1
        return count
        
    def getActiveName(self):
        """
        Public method to retrieve the filename of the active window.
        
        @return filename of active window (string)
        """
        aw = self.activeWindow()
        if aw:
            return aw.getFileName()
        else:
            return None
        
    def saveEditor(self, fn):
        """
        Public method to save a named editor file.
        
        @param fn filename of editor to be saved (string)
        @return flag indicating success (boolean)
        """
        for editor in self.editors:
            if Utilities.samepath(fn, editor.getFileName()):
                break
        else:
            return True
        
        if not editor.isModified():
            return True
        else:
            ok = editor.saveFile()
            return ok
        
    def saveEditorEd(self, ed):
        """
        Public slot to save the contents of an editor.
        
        @param ed editor to be saved
        @return flag indicating success (boolean)
        """
        if ed:
            if not ed.isModified():
                return True
            else:
                ok = ed.saveFile()
                if ok:
                    self.setEditorName(ed, ed.getFileName())
                return ok
        else:
            return False
        
    def saveCurrentEditor(self):
        """
        Public slot to save the contents of the current editor.
        """
        aw = self.activeWindow()
        self.saveEditorEd(aw)

    def saveAsEditorEd(self, ed):
        """
        Public slot to save the contents of an editor to a new file.
        
        @param ed editor to be saved
        """
        if ed:
            ok = ed.saveFileAs()
            if ok:
                self.setEditorName(ed, ed.getFileName())
        else:
            return
        
    def saveAsCurrentEditor(self):
        """
        Public slot to save the contents of the current editor to a new file.
        """
        aw = self.activeWindow()
        self.saveAsEditorEd(aw)
        
    def saveEditorsList(self, editors):
        """
        Public slot to save a list of editors.
        
        @param editors list of editors to be saved
        """
        for editor in editors:
            ok = editor.saveFile()
            if ok:
                self.setEditorName(editor, editor.getFileName())
        
    def saveAllEditors(self):
        """
        Public slot to save the contents of all editors.
        """
        for editor in self.editors:
            ok = editor.saveFile()
            if ok:
                self.setEditorName(editor, editor.getFileName())
        
        # restart autosave timer
        if self.autosaveInterval > 0:
            self.autosaveTimer.start(self.autosaveInterval * 60000)
        
    def __exportMenuTriggered(self, act):
        """
        Private method to handle the selection of an export format.
        
        @param act reference to the action that was triggered (QAction)
        """
        aw = self.activeWindow()
        if aw:
            exporterFormat = act.data()
            aw.exportFile(exporterFormat)
        
    def newEditor(self):
        """
        Public slot to generate a new empty editor.
        """
        editor = Editor(self.dbs, None, self, tv=e5App().getObject("TaskViewer"))
        self.editors.append(editor)
        self.__connectEditor(editor)
        self._addView(editor, None)
        self.__editorOpened()
        self._checkActions(editor)
        self.editorOpened.emit("")
        self.editorOpenedEd.emit(editor)
        
    def printEditor(self, editor):
        """
        Public slot to print an editor.
        
        @param editor editor to be printed
        """
        if editor:
            editor.printFile()
        else:
            return
        
    def printCurrentEditor(self):
        """
        Public slot to print the contents of the current editor.
        """
        aw = self.activeWindow()
        self.printEditor(aw)
        
    def printPreviewCurrentEditor(self):
        """
        Public slot to show a print preview of the current editor.
        """
        aw = self.activeWindow()
        if aw:
            aw.printPreviewFile()
        
    def __showFileMenu(self):
        """
        Private method to set up the file menu.
        """
        self.menuRecentAct.setEnabled(len(self.recent) > 0)
        
    def __showRecentMenu(self):
        """
        Private method to set up recent files menu.
        """
        self.__loadRecent()
        
        self.recentMenu.clear()
        
        idx = 1
        for rs in self.recent:
            if idx < 10:
                formatStr = '&{0:d}. {1}'
            else:
                formatStr = '{0:d}. {1}'
            act = self.recentMenu.addAction(
                formatStr.format(idx,
                    Utilities.compactPath(rs, self.ui.maxMenuFilePathLen)))
            act.setData(rs)
            act.setEnabled(QFileInfo(rs).exists())
            idx += 1
        
        self.recentMenu.addSeparator()
        self.recentMenu.addAction(
            QApplication.translate('ViewManager', '&Clear'), self.__clearRecent)
        
    def __openSourceFile(self, act):
        """
        Private method to open a file from the list of recently opened files.
        
        @param act reference to the action that triggered (QAction)
        """
        file = act.data()
        if file:
            self.openSourceFile(file)
        
    def __clearRecent(self):
        """
        Private method to clear the recent files menu.
        """
        self.recent = []
        
    def __showBookmarkedMenu(self):
        """
        Private method to set up bookmarked files menu.
        """
        self.bookmarkedMenu.clear()
        
        for rp in self.bookmarked:
            act = self.bookmarkedMenu.addAction(
                Utilities.compactPath(rp, self.ui.maxMenuFilePathLen))
            act.setData(rp)
            act.setEnabled(QFileInfo(rp).exists())
        
        if len(self.bookmarked):
            self.bookmarkedMenu.addSeparator()
        self.bookmarkedMenu.addAction(
            QApplication.translate('ViewManager', '&Add'), self.__addBookmarked)
        self.bookmarkedMenu.addAction(
            QApplication.translate('ViewManager', '&Edit...'), self.__editBookmarked)
        self.bookmarkedMenu.addAction(
            QApplication.translate('ViewManager', '&Clear'), self.__clearBookmarked)
        
    def __addBookmarked(self):
        """
        Private method to add the current file to the list of bookmarked files.
        """
        an = self.getActiveName()
        if an is not None and an not in self.bookmarked:
            self.bookmarked.append(an)
        
    def __editBookmarked(self):
        """
        Private method to edit the list of bookmarked files.
        """
        dlg = BookmarkedFilesDialog(self.bookmarked, self.ui)
        if dlg.exec_() == QDialog.Accepted:
            self.bookmarked = dlg.getBookmarkedFiles()
        
    def __clearBookmarked(self):
        """
        Private method to clear the bookmarked files menu.
        """
        self.bookmarked = []
        
    def projectOpened(self):
        """
        Public slot to handle the projectOpened signal.
        """
        for editor in self.editors:
            editor.setSpellingForProject()
        
    def projectFileRenamed(self, oldfn, newfn):
        """
        Public slot to handle the projectFileRenamed signal.
        
        @param oldfn old filename of the file (string)
        @param newfn new filename of the file (string)
        """
        editor = self.getOpenEditor(oldfn)
        if editor:
            editor.fileRenamed(newfn)
        
    def projectLexerAssociationsChanged(self):
        """
        Public slot to handle changes of the project lexer associations.
        """
        for editor in self.editors:
            editor.projectLexerAssociationsChanged()
        
    def enableEditorsCheckFocusIn(self, enabled):
        """
        Public method to set a flag enabling the editors to perform focus in checks.
        
        @param enabled flag indicating focus in checks should be performed (boolean)
        """
        self.editorsCheckFocusIn = enabled
        
    def editorsCheckFocusInEnabled(self):
        """
        Public method returning the flag indicating editors should perform
        focus in checks.
        
        @return flag indicating focus in checks should be performed (boolean)
        """
        return self.editorsCheckFocusIn

    def __findFileName(self):
        """
        Private method to handle the search for file action.
        """
        self.ui.findFileNameDialog.show()
        self.ui.findFileNameDialog.raise_()
        self.ui.findFileNameDialog.activateWindow()
    
    def appFocusChanged(self, old, now):
        """
        Public method to handle the global change of focus.
        
        @param old reference to the widget loosing focus (QWidget)
        @param now reference to the widget gaining focus (QWidget)
        """
        if not isinstance(now, (Editor, Shell, Terminal)):
            self.editActGrp.setEnabled(False)
            self.copyActGrp.setEnabled(False)
            self.viewActGrp.setEnabled(False)
            self.searchActGrp.setEnabled(False)
        
        if isinstance(old, (Editor, Shell, Terminal)):
            self.__lastFocusWidget = old
    
    ##################################################################
    ## Below are the action methods for the edit menu
    ##################################################################
    
    def __editUndo(self):
        """
        Private method to handle the undo action.
        """
        self.activeWindow().undo()
        
    def __editRedo(self):
        """
        Private method to handle the redo action.
        """
        self.activeWindow().redo()
        
    def __editRevert(self):
        """
        Private method to handle the revert action.
        """
        self.activeWindow().revertToUnmodified()
        
    def __editCut(self):
        """
        Private method to handle the cut action.
        """
        if QApplication.focusWidget() == e5App().getObject("Shell"):
            e5App().getObject("Shell").cut()
        elif QApplication.focusWidget() == e5App().getObject("Terminal"):
            e5App().getObject("Terminal").cut()
        else:
            self.activeWindow().cut()
        
    def __editCopy(self):
        """
        Private method to handle the copy action.
        """
        if QApplication.focusWidget() == e5App().getObject("Shell"):
            e5App().getObject("Shell").copy()
        elif QApplication.focusWidget() == e5App().getObject("Terminal"):
            e5App().getObject("Terminal").copy()
        else:
            self.activeWindow().copy()
        
    def __editPaste(self):
        """
        Private method to handle the paste action.
        """
        if QApplication.focusWidget() == e5App().getObject("Shell"):
            e5App().getObject("Shell").paste()
        elif QApplication.focusWidget() == e5App().getObject("Terminal"):
            e5App().getObject("Terminal").paste()
        else:
            self.activeWindow().paste()
        
    def __editDelete(self):
        """
        Private method to handle the delete action.
        """
        if QApplication.focusWidget() == e5App().getObject("Shell"):
            e5App().getObject("Shell").clear()
        elif QApplication.focusWidget() == e5App().getObject("Terminal"):
            e5App().getObject("Terminal").clear()
        else:
            self.activeWindow().clear()
        
    def __editJoin(self):
        """
        Private method to handle the join action.
        """
        self.activeWindow().joinLines()
        
    def __editIndent(self):
        """
        Private method to handle the indent action.
        """
        self.activeWindow().indentLineOrSelection()
        
    def __editUnindent(self):
        """
        Private method to handle the unindent action.
        """
        self.activeWindow().unindentLineOrSelection()
        
    def __editSmartIndent(self):
        """
        Private method to handle the smart indent action
        """
        self.activeWindow().smartIndentLineOrSelection()
        
    def __editComment(self):
        """
        Private method to handle the comment action.
        """
        self.activeWindow().commentLineOrSelection()
        
    def __editUncomment(self):
        """
        Private method to handle the uncomment action.
        """
        self.activeWindow().uncommentLineOrSelection()
        
    def __editStreamComment(self):
        """
        Private method to handle the stream comment action.
        """
        self.activeWindow().streamCommentLineOrSelection()
        
    def __editBoxComment(self):
        """
        Private method to handle the box comment action.
        """
        self.activeWindow().boxCommentLineOrSelection()
        
    def __editSelectBrace(self):
        """
        Private method to handle the select to brace action.
        """
        self.activeWindow().selectToMatchingBrace()
        
    def __editSelectAll(self):
        """
        Private method to handle the select all action.
        """
        self.activeWindow().selectAll(True)
        
    def __editDeselectAll(self):
        """
        Private method to handle the select all action.
        """
        self.activeWindow().selectAll(False)
        
    def __convertEOL(self):
        """
        Private method to handle the convert line end characters action.
        """
        aw = self.activeWindow()
        aw.convertEols(aw.eolMode())
        
    def __shortenEmptyLines(self):
        """
        Private method to handle the shorten empty lines action.
        """
        self.activeWindow().shortenEmptyLines()
        
    def __editAutoComplete(self):
        """
        Private method to handle the autocomplete action.
        """
        self.activeWindow().autoComplete()
        
    def __editAutoCompleteFromDoc(self):
        """
        Private method to handle the autocomplete from document action.
        """
        self.activeWindow().autoCompleteFromDocument()
        
    def __editAutoCompleteFromAPIs(self):
        """
        Private method to handle the autocomplete from APIs action.
        """
        self.activeWindow().autoCompleteFromAPIs()
        
    def __editAutoCompleteFromAll(self):
        """
        Private method to handle the autocomplete from All action.
        """
        self.activeWindow().autoCompleteFromAll()
        
    def __editorAutoCompletionAPIsAvailable(self, available):
        """
        Private method to handle the availability of API autocompletion signal.
        """
        self.autoCompleteFromAPIsAct.setEnabled(available)
        
    def __editShowCallTips(self):
        """
        Private method to handle the calltips action.
        """
        self.activeWindow().callTip()
    
    ##################################################################
    ## Below are the action and utility methods for the search menu
    ##################################################################

    def textForFind(self, getCurrentWord=True):
        """
        Public method to determine the selection or the current word for the next
        find operation.
        
        @param getCurrentWord flag indicating to return the current word, if no selected
            text was found (boolean)
        @return selection or current word (string)
        """
        aw = self.activeWindow()
        if aw is None:
            return ""
        
        return aw.getSearchText(not getCurrentWord)
        
    def getSRHistory(self, key):
        """
        Public method to get the search or replace history list.
        
        @param key list to return (must be 'search' or 'replace')
        @return the requested history list (list of strings)
        """
        return self.srHistory[key]
        
    def __quickSearch(self):
        """
        Private slot to handle the incremental quick search.
        """
        # first we have to check if quick search is active
        # and try to activate it if not
        if not self.quickFindtextCombo.lineEdit().hasFocus():
            aw = self.activeWindow()
            self.quickFindtextCombo.lastActive = aw
            if aw:
                self.quickFindtextCombo.lastCursorPos = aw.getCursorPosition()
            else:
                self.quickFindtextCombo.lastCursorPos = None
            tff = self.textForFind(False)
            if tff:
                self.quickFindtextCombo.lineEdit().setText(tff)
            self.quickFindtextCombo.lineEdit().setFocus()
            self.quickFindtextCombo.lineEdit().selectAll()
        else:
            self.__quickSearchInEditor(True, False)
        
    def __quickSearchFocusIn(self):
        """
        Private method to handle a focus in signal of the quicksearch lineedit.
        """
        self.quickFindtextCombo.lastActive = self.activeWindow()
        
    def __quickSearchEnter(self):
        """
        Private slot to handle the incremental quick search return pressed
        (jump back to text)
        """
        if self.quickFindtextCombo.lastActive:
            self.quickFindtextCombo.lastActive.setFocus()
        
    def __quickSearchEscape(self):
        """
        Private slot to handle the incremental quick search escape pressed
        (jump back to text)
        """
        if self.quickFindtextCombo.lastActive:
            self.quickFindtextCombo.lastActive.setFocus()
            aw = self.activeWindow()
            if aw and self.quickFindtextCombo.lastCursorPos:
                aw.setCursorPosition(self.quickFindtextCombo.lastCursorPos[0],
                                     self.quickFindtextCombo.lastCursorPos[1])
        
    def __quickSearchText(self):
        """
        Private slot to handle the textChanged signal of the quicksearch edit.
        """
        self.__quickSearchInEditor(False, False)
        
    def __quickSearchPrev(self):
        """
        Private slot to handle the quickFindPrev toolbutton action.
        """
        self.__quickSearchInEditor(True, True)
        
    def __quickSearchMarkOccurrences(self, txt):
        """
        Private method to mark all occurrences of the search text.
        
        @param txt text to search for (string)
        """
        aw = self.activeWindow()
        
        lineFrom = 0
        indexFrom = 0
        lineTo = -1
        indexTo = -1
        
        aw.clearSearchIndicators()
        ok = aw.findFirstTarget(txt, False, False, False,
                                lineFrom, indexFrom, lineTo, indexTo)
        while ok:
            tgtPos, tgtLen = aw.getFoundTarget()
            try:
                aw.setSearchIndicator(tgtPos, tgtLen)
            except AttributeError:
                self.viewmanager.setSearchIndicator(tgtPos, tgtLen)
            ok = aw.findNextTarget()
        
    def __quickSearchInEditor(self, again, back):
        """
        Private slot to perform a quick search.
        
        @param again flag indicating a repeat of the last search (boolean)
        @param back flag indicating a backwards search operation (boolean)
        """
        aw = self.activeWindow()
        if not aw:
            return
        
        text = self.quickFindtextCombo.lineEdit().text()
        if not text:
            text = self.quickFindtextCombo.lastSearchText
        if not text:
            if Preferences.getEditor("QuickSearchMarkersEnabled"):
                aw.clearSearchIndicators()
            return
        else:
            self.quickFindtextCombo.lastSearchText = text
        
        if Preferences.getEditor("QuickSearchMarkersEnabled"):
            self.__quickSearchMarkOccurrences(text)
        
        lineFrom, indexFrom, lineTo, indexTo = aw.getSelection()
        cline, cindex = aw.getCursorPosition()
        if again:
            if back:
                if indexFrom != 0:
                    index = indexFrom - 1
                    line = lineFrom
                elif lineFrom == 0:
                    return
                else:
                    line = lineFrom - 1
                    index = aw.lineLength(line)
                ok = aw.findFirst(text, False, False, False, True, False, line, index)
            else:
                ok = aw.findFirst(text, False, False, False, True, not back,
                                  cline, cindex)
        else:
            ok = aw.findFirst(text, False, False, False, True, not back,
                              lineFrom, indexFrom)
        if not ok:
            palette = self.quickFindtextCombo.lineEdit().palette()
            palette.setColor(QPalette.Base, QColor("red"))
            palette.setColor(QPalette.Text, QColor("white"))
            self.quickFindtextCombo.lineEdit().setPalette(palette)
        else:
            palette = self.quickFindtextCombo.lineEdit().palette()
            palette.setColor(QPalette.Base,
                             self.quickFindtextCombo.palette().color(QPalette.Base))
            palette.setColor(QPalette.Text,
                             self.quickFindtextCombo.palette().color(QPalette.Text))
            self.quickFindtextCombo.lineEdit().setPalette(palette)
        
    def __quickSearchExtend(self):
        """
        Private method to handle the quicksearch extend action.
        """
        aw = self.activeWindow()
        if aw is None:
            return
        
        txt = self.quickFindtextCombo.lineEdit().text()
        if not txt:
            return
        
        line, index = aw.getCursorPosition()
        text = aw.text(line)
        
        re = QRegExp('[^\w_]')
        end = re.indexIn(text, index)
        if end > index:
            ext = text[index:end + 1]
            txt += ext
            self.quickFindtextCombo.lineEdit().setText(txt)
        
    def __search(self):
        """
        Private method to handle the search action.
        """
        self.replaceDlg.close()
        self.searchDlg.show(self.textForFind())
        
    def __replace(self):
        """
        Private method to handle the replace action.
        """
        self.searchDlg.close()
        self.replaceDlg.show(self.textForFind())
        
    def __searchClearMarkers(self):
        """
        Private method to clear the search markers of the active window.
        """
        self.activeWindow().clearSearchIndicators()
        
    def __goto(self):
        """
        Private method to handle the goto action.
        """
        aw = self.activeWindow()
        lines = aw.lines()
        curLine = aw.getCursorPosition()[0] + 1
        dlg = GotoDialog(lines, curLine, self.ui, None, True)
        if dlg.exec_() == QDialog.Accepted:
            aw.gotoLine(dlg.getLinenumber())
        
    def __gotoBrace(self):
        """
        Private method to handle the goto brace action.
        """
        self.activeWindow().moveToMatchingBrace()
        
    def __searchFiles(self):
        """
        Private method to handle the search in files action.
        """
        self.ui.findFilesDialog.show(self.textForFind())
        self.ui.findFilesDialog.raise_()
        self.ui.findFilesDialog.activateWindow()
        
    def __replaceFiles(self):
        """
        Private method to handle the replace in files action.
        """
        self.ui.replaceFilesDialog.show(self.textForFind())
        self.ui.replaceFilesDialog.raise_()
        self.ui.replaceFilesDialog.activateWindow()
    
    ##################################################################
    ## Below are the action methods for the view menu
    ##################################################################
    
    def __zoomIn(self):
        """
        Private method to handle the zoom in action.
        """
        if QApplication.focusWidget() == e5App().getObject("Shell"):
            e5App().getObject("Shell").zoomIn()
        elif QApplication.focusWidget() == e5App().getObject("Terminal"):
            e5App().getObject("Terminal").zoomIn()
        else:
            aw = self.activeWindow()
            if aw:
                aw.zoomIn()
        
    def __zoomOut(self):
        """
        Private method to handle the zoom out action.
        """
        if QApplication.focusWidget() == e5App().getObject("Shell"):
            e5App().getObject("Shell").zoomOut()
        elif QApplication.focusWidget() == e5App().getObject("Terminal"):
            e5App().getObject("Terminal").zoomOut()
        else:
            aw = self.activeWindow()
            if aw:
                aw.zoomOut()
        
    def __zoom(self):
        """
        Private method to handle the zoom action.
        """
        if QApplication.focusWidget() == e5App().getObject("Shell"):
            aw = e5App().getObject("Shell")
        elif QApplication.focusWidget() == e5App().getObject("Terminal"):
            aw = e5App().getObject("Terminal")
        else:
            aw = self.activeWindow()
        if aw:
            dlg = ZoomDialog(aw.getZoom(), self.ui, None, True)
            if dlg.exec_() == QDialog.Accepted:
                aw.zoomTo(dlg.getZoomSize())
        
    def __toggleAll(self):
        """
        Private method to handle the toggle all folds action.
        """
        aw = self.activeWindow()
        if aw:
            aw.foldAll()
        
    def __toggleAllChildren(self):
        """
        Private method to handle the toggle all folds (including children) action.
        """
        aw = self.activeWindow()
        if aw:
            aw.foldAll(True)
        
    def __toggleCurrent(self):
        """
        Private method to handle the toggle current fold action.
        """
        aw = self.activeWindow()
        if aw:
            line, index = aw.getCursorPosition()
            aw.foldLine(line)
        
    def __splitView(self):
        """
        Private method to handle the split view action.
        """
        self.addSplit()
        
    def __splitOrientation(self, checked):
        """
        Private method to handle the split orientation action.
        """
        if checked:
            self.setSplitOrientation(Qt.Horizontal)
            self.splitViewAct.setIcon(
                UI.PixmapCache.getIcon("splitHorizontal.png"))
            self.splitRemoveAct.setIcon(
                UI.PixmapCache.getIcon("remsplitHorizontal.png"))
        else:
            self.setSplitOrientation(Qt.Vertical)
            self.splitViewAct.setIcon(
                UI.PixmapCache.getIcon("splitVertical.png"))
            self.splitRemoveAct.setIcon(
                UI.PixmapCache.getIcon("remsplitVertical.png"))
    
    ##################################################################
    ## Below are the action methods for the macro menu
    ##################################################################
    
    def __macroStartRecording(self):
        """
        Private method to handle the start macro recording action.
        """
        self.activeWindow().macroRecordingStart()
        
    def __macroStopRecording(self):
        """
        Private method to handle the stop macro recording action.
        """
        self.activeWindow().macroRecordingStop()
        
    def __macroRun(self):
        """
        Private method to handle the run macro action.
        """
        self.activeWindow().macroRun()
        
    def __macroDelete(self):
        """
        Private method to handle the delete macro action.
        """
        self.activeWindow().macroDelete()
        
    def __macroLoad(self):
        """
        Private method to handle the load macro action.
        """
        self.activeWindow().macroLoad()
        
    def __macroSave(self):
        """
        Private method to handle the save macro action.
        """
        self.activeWindow().macroSave()
    
    ##################################################################
    ## Below are the action methods for the bookmarks menu
    ##################################################################
    
    def __toggleBookmark(self):
        """
        Private method to handle the toggle bookmark action.
        """
        self.activeWindow().menuToggleBookmark()
        
    def __nextBookmark(self):
        """
        Private method to handle the next bookmark action.
        """
        self.activeWindow().nextBookmark()
    
    def __previousBookmark(self):
        """
        Private method to handle the previous bookmark action.
        """
        self.activeWindow().previousBookmark()
    
    def __clearAllBookmarks(self):
        """
        Private method to handle the clear all bookmarks action.
        """
        for editor in self.editors:
            editor.clearBookmarks()
        
        self.bookmarkNextAct.setEnabled(False)
        self.bookmarkPreviousAct.setEnabled(False)
        self.bookmarkClearAct.setEnabled(False)
    
    def __showBookmarkMenu(self):
        """
        Private method to set up the bookmark menu.
        """
        bookmarksFound = 0
        filenames = self.getOpenFilenames()
        for filename in filenames:
            editor = self.getOpenEditor(filename)
            bookmarksFound = len(editor.getBookmarks()) > 0
            if bookmarksFound:
                self.menuBookmarksAct.setEnabled(True)
                return
        self.menuBookmarksAct.setEnabled(False)
        
    def __showBookmarksMenu(self):
        """
        Private method to handle the show bookmarks menu signal.
        """
        self.bookmarksMenu.clear()
        
        filenames = self.getOpenFilenames()
        for filename in sorted(filenames):
            editor = self.getOpenEditor(filename)
            for bookmark in editor.getBookmarks():
                bmSuffix = " : {0:d}".format(bookmark)
                act = self.bookmarksMenu.addAction(
                    "{0}{1}".format(
                        Utilities.compactPath(
                            filename,
                            self.ui.maxMenuFilePathLen - len(bmSuffix)),
                        bmSuffix))
                act.setData([filename, bookmark])
        
    def __bookmarkSelected(self, act):
        """
        Private method to handle the bookmark selected signal.
        
        @param act reference to the action that triggered (QAction)
        """
        bmList = act.data()
        filename = bmList[0]
        line = bmList[1]
        self.openSourceFile(filename, line)
        
    def __bookmarkToggled(self, editor):
        """
        Private slot to handle the bookmarkToggled signal.
        
        It checks some bookmark actions and reemits the signal.
        
        @param editor editor that sent the signal
        """
        if editor.hasBookmarks():
            self.bookmarkNextAct.setEnabled(True)
            self.bookmarkPreviousAct.setEnabled(True)
            self.bookmarkClearAct.setEnabled(True)
        else:
            self.bookmarkNextAct.setEnabled(False)
            self.bookmarkPreviousAct.setEnabled(False)
            self.bookmarkClearAct.setEnabled(False)
        self.bookmarkToggled.emit(editor)
        
    def __gotoSyntaxError(self):
        """
        Private method to handle the goto syntax error action.
        """
        self.activeWindow().gotoSyntaxError()
        
    def __clearAllSyntaxErrors(self):
        """
        Private method to handle the clear all syntax errors action.
        """
        for editor in self.editors:
            editor.clearSyntaxError()
        
    def _syntaxErrorToggled(self, editor):
        """
        Protected slot to handle the syntaxerrorToggled signal.
        
        It checks some syntax error actions and reemits the signal.
        
        @param editor editor that sent the signal
        """
        if editor.hasSyntaxErrors():
            self.syntaxErrorGotoAct.setEnabled(True)
            self.syntaxErrorClearAct.setEnabled(True)
        else:
            self.syntaxErrorGotoAct.setEnabled(False)
            self.syntaxErrorClearAct.setEnabled(False)
        if editor.hasFlakesWarnings():
            self.warningsNextAct.setEnabled(True)
            self.warningsPreviousAct.setEnabled(True)
            self.warningsClearAct.setEnabled(True)
        else:
            self.warningsNextAct.setEnabled(False)
            self.warningsPreviousAct.setEnabled(False)
            self.warningsClearAct.setEnabled(False)
        self.syntaxerrorToggled.emit(editor)
        
    def __nextWarning(self):
        """
        Private method to handle the next warning action.
        """
        self.activeWindow().nextFlakesWarning()
        
    def __previousWarning(self):
        """
        Private method to handle the previous warning action.
        """
        self.activeWindow().previousFlakesWarning()
        
    def __clearAllWarnings(self):
        """
        Private method to handle the clear all warnings action.
        """
        for editor in self.editors:
            editor.clearFlakesWarnings()
        
    def __nextUncovered(self):
        """
        Private method to handle the next uncovered action.
        """
        self.activeWindow().nextUncovered()
        
    def __previousUncovered(self):
        """
        Private method to handle the previous uncovered action.
        """
        self.activeWindow().previousUncovered()
        
    def __coverageMarkersShown(self, shown):
        """
        Private slot to handle the coverageMarkersShown signal.
        
        @param shown flag indicating whether the markers were shown or cleared
        """
        if shown:
            self.notcoveredNextAct.setEnabled(True)
            self.notcoveredPreviousAct.setEnabled(True)
        else:
            self.notcoveredNextAct.setEnabled(False)
            self.notcoveredPreviousAct.setEnabled(False)
        
    def __taskMarkersUpdated(self, editor):
        """
        Protected slot to handle the taskMarkersUpdated signal.
        
        @param editor editor that sent the signal
        """
        if editor.hasTaskMarkers():
            self.taskNextAct.setEnabled(True)
            self.taskPreviousAct.setEnabled(True)
        else:
            self.taskNextAct.setEnabled(False)
            self.taskPreviousAct.setEnabled(False)
        
    def __nextTask(self):
        """
        Private method to handle the next task action.
        """
        self.activeWindow().nextTask()
        
    def __previousTask(self):
        """
        Private method to handle the previous task action.
        """
        self.activeWindow().previousTask()
    
    ##################################################################
    ## Below are the action methods for the spell checking functions
    ##################################################################
    
    def __setAutoSpellChecking(self):
        """
        Private slot to set the automatic spell checking of all editors.
        """
        enabled = self.autoSpellCheckAct.isChecked()
        Preferences.setEditor("AutoSpellCheckingEnabled", enabled)
        for editor in self.editors:
            editor.setAutoSpellChecking()
    
    def __spellCheck(self):
        """
        Private slot to perform a spell check of the current editor.
        """
        aw = self.activeWindow()
        if aw:
            aw.checkSpelling()
    
    ##################################################################
    ## Below are general utility methods
    ##################################################################
    
    def handleResetUI(self):
        """
        Public slot to handle the resetUI signal.
        """
        editor = self.activeWindow()
        if editor is None:
            self.__setSbFile()
        else:
            line, pos = editor.getCursorPosition()
            enc = editor.getEncoding()
            lang = editor.getLanguage()
            eol = editor.getEolIndicator()
            self.__setSbFile(editor.getFileName(), line + 1, pos, enc, lang, eol)
        
    def closeViewManager(self):
        """
        Public method to shutdown the viewmanager.
        
        If it cannot close all editor windows, it aborts the shutdown process.
        
        @return flag indicating success (boolean)
        """
        self.closeAllWindows()
        
        # save the list of recently opened projects
        self.__saveRecent()
        
        # save the list of recently opened projects
        Preferences.Prefs.settings.setValue('Bookmarked/Sources', self.bookmarked)
        
        if len(self.editors):
            return False
        else:
            return True
        
    def __lastEditorClosed(self):
        """
        Private slot to handle the lastEditorClosed signal.
        """
        self.closeActGrp.setEnabled(False)
        self.saveActGrp.setEnabled(False)
        self.exportersMenuAct.setEnabled(False)
        self.printAct.setEnabled(False)
        if self.printPreviewAct:
            self.printPreviewAct.setEnabled(False)
        self.editActGrp.setEnabled(False)
        self.searchActGrp.setEnabled(False)
        self.quickFindtextCombo.setEnabled(False)
        self.viewActGrp.setEnabled(False)
        self.viewFoldActGrp.setEnabled(False)
        self.unhighlightAct.setEnabled(False)
        self.splitViewAct.setEnabled(False)
        self.splitOrientationAct.setEnabled(False)
        self.macroActGrp.setEnabled(False)
        self.bookmarkActGrp.setEnabled(False)
        self.__enableSpellingActions()
        self.__setSbFile()
        
        # remove all split views, if this is supported
        if self.canSplit():
            while self.removeSplit():
                pass
        
        # stop the autosave timer
        if self.autosaveTimer.isActive():
            self.autosaveTimer.stop()
        
    def __editorOpened(self):
        """
        Private slot to handle the editorOpened signal.
        """
        self.closeActGrp.setEnabled(True)
        self.saveActGrp.setEnabled(True)
        self.exportersMenuAct.setEnabled(True)
        self.printAct.setEnabled(True)
        if self.printPreviewAct:
            self.printPreviewAct.setEnabled(True)
        self.editActGrp.setEnabled(True)
        self.searchActGrp.setEnabled(True)
        self.quickFindtextCombo.setEnabled(True)
        self.viewActGrp.setEnabled(True)
        self.viewFoldActGrp.setEnabled(True)
        self.unhighlightAct.setEnabled(True)
        if self.canSplit():
            self.splitViewAct.setEnabled(True)
            self.splitOrientationAct.setEnabled(True)
        self.macroActGrp.setEnabled(True)
        self.bookmarkActGrp.setEnabled(True)
        self.__enableSpellingActions()
        
        # activate the autosave timer
        if not self.autosaveTimer.isActive() and \
           self.autosaveInterval > 0:
            self.autosaveTimer.start(self.autosaveInterval * 60000)
        
    def __autosave(self):
        """
        Private slot to save the contents of all editors automatically.
        
        Only named editors will be saved by the autosave timer.
        """
        for editor in self.editors:
            if editor.shouldAutosave():
                ok = editor.saveFile()
                if ok:
                    self.setEditorName(editor, editor.getFileName())
        
        # restart autosave timer
        if self.autosaveInterval > 0:
            self.autosaveTimer.start(self.autosaveInterval * 60000)
        
    def _checkActions(self, editor, setSb=True):
        """
        Protected slot to check some actions for their enable/disable status
        and set the statusbar info.
        
        @param editor editor window
        @param setSb flag indicating an update of the status bar is wanted (boolean)
        """
        if editor is not None:
            self.saveAct.setEnabled(editor.isModified())
            self.revertAct.setEnabled(editor.isModified())
            
            self.undoAct.setEnabled(editor.isUndoAvailable())
            self.redoAct.setEnabled(editor.isRedoAvailable())
            
            lex = editor.getLexer()
            if lex is not None:
                self.commentAct.setEnabled(lex.canBlockComment())
                self.uncommentAct.setEnabled(lex.canBlockComment())
                self.streamCommentAct.setEnabled(lex.canStreamComment())
                self.boxCommentAct.setEnabled(lex.canBoxComment())
            else:
                self.commentAct.setEnabled(False)
                self.uncommentAct.setEnabled(False)
                self.streamCommentAct.setEnabled(False)
                self.boxCommentAct.setEnabled(False)
            
            if editor.hasBookmarks():
                self.bookmarkNextAct.setEnabled(True)
                self.bookmarkPreviousAct.setEnabled(True)
                self.bookmarkClearAct.setEnabled(True)
            else:
                self.bookmarkNextAct.setEnabled(False)
                self.bookmarkPreviousAct.setEnabled(False)
                self.bookmarkClearAct.setEnabled(False)
            
            if editor.hasSyntaxErrors():
                self.syntaxErrorGotoAct.setEnabled(True)
                self.syntaxErrorClearAct.setEnabled(True)
            else:
                self.syntaxErrorGotoAct.setEnabled(False)
                self.syntaxErrorClearAct.setEnabled(False)
            
            if editor.hasFlakesWarnings():
                self.warningsNextAct.setEnabled(True)
                self.warningsPreviousAct.setEnabled(True)
                self.warningsClearAct.setEnabled(True)
            else:
                self.warningsNextAct.setEnabled(False)
                self.warningsPreviousAct.setEnabled(False)
                self.warningsClearAct.setEnabled(False)
            
            if editor.hasCoverageMarkers():
                self.notcoveredNextAct.setEnabled(True)
                self.notcoveredPreviousAct.setEnabled(True)
            else:
                self.notcoveredNextAct.setEnabled(False)
                self.notcoveredPreviousAct.setEnabled(False)
            
            if editor.hasTaskMarkers():
                self.taskNextAct.setEnabled(True)
                self.taskPreviousAct.setEnabled(True)
            else:
                self.taskNextAct.setEnabled(False)
                self.taskPreviousAct.setEnabled(False)
            
            if editor.canAutoCompleteFromAPIs():
                self.autoCompleteFromAPIsAct.setEnabled(True)
            else:
                self.autoCompleteFromAPIsAct.setEnabled(False)
            
            if setSb:
                line, pos = editor.getCursorPosition()
                enc = editor.getEncoding()
                lang = editor.getLanguage()
                eol = editor.getEolIndicator()
                self.__setSbFile(editor.getFileName(), line + 1, pos, enc, lang, eol)
            
            self.checkActions.emit(editor)
        
    def preferencesChanged(self):
        """
        Public slot to handle the preferencesChanged signal.
        
        This method performs the following actions
            <ul>
            <li>reread the colours for the syntax highlighting</li>
            <li>reloads the already created API objetcs</li>
            <li>starts or stops the autosave timer</li>
            <li><b>Note</b>: changes in viewmanager type are activated
              on an application restart.</li>
            </ul>
        """
        # reload the APIs
        self.apisManager.reloadAPIs()
        
        # reload editor settings
        for editor in self.editors:
            editor.readSettings()
        
        # reload the autosave timer setting
        self.autosaveInterval = Preferences.getEditor("AutosaveInterval")
        if len(self.editors):
            if self.autosaveTimer.isActive() and \
               self.autosaveInterval == 0:
                self.autosaveTimer.stop()
            elif not self.autosaveTimer.isActive() and \
               self.autosaveInterval > 0:
                self.autosaveTimer.start(self.autosaveInterval * 60000)
        
        self.__enableSpellingActions()
        
    def __editorSaved(self, fn):
        """
        Private slot to handle the editorSaved signal.
        
        It simply reemits the signal.
        
        @param fn filename of the saved editor
        """
        self.editorSaved.emit(fn)
        
    def __cursorChanged(self, fn, line, pos):
        """
        Private slot to handle the cursorChanged signal.
        
        It emits the signal cursorChanged with parameter editor.
        
        @param fn filename (string)
        @param line line number of the cursor (int)
        @param pos position in line of the cursor (int)
        """
        editor = self.getOpenEditor(fn)
        if editor is None:
            editor = self.sender()
        
        if editor is not None:
            enc = editor.getEncoding()
            lang = editor.getLanguage()
            eol = editor.getEolIndicator()
        else:
            enc = None
            lang = None
            eol = None
        self.__setSbFile(fn, line, pos, enc, lang, eol)
        self.cursorChanged.emit(editor)
        
    def __breakpointToggled(self, editor):
        """
        Private slot to handle the breakpointToggled signal.
        
        It simply reemits the signal.
        
        @param editor editor that sent the signal
        """
        self.breakpointToggled.emit(editor)
        
    def getActions(self, type):
        """
        Public method to get a list of all actions.
        
        @param type string denoting the action set to get.
                It must be one of "edit", "file", "search",
                "view", "window", "macro", "bookmark" or
                "spelling".
        @return list of all actions (list of E5Action)
        """
        try:
            return self.__actions[type][:]
        except KeyError:
            return []
        
    def __editorCommand(self, cmd):
        """
        Private method to send an editor command to the active window.
        
        @param cmd the scintilla command to be sent
        """
        focusWidget = QApplication.focusWidget()
        if focusWidget == e5App().getObject("Shell"):
            e5App().getObject("Shell").editorCommand(cmd)
        elif focusWidget == e5App().getObject("Terminal"):
            e5App().getObject("Terminal").editorCommand(cmd)
        elif focusWidget == self.quickFindtextCombo:
            self.quickFindtextCombo._editor.editorCommand(cmd)
        else:
            aw = self.activeWindow()
            if aw:
                aw.editorCommand(cmd)
        
    def __newLineBelow(self):
        """
        Private method to insert a new line below the current one even if
        cursor is not at the end of the line.
        """
        focusWidget = QApplication.focusWidget()
        if focusWidget == e5App().getObject("Shell") or \
           focusWidget == e5App().getObject("Terminal") or \
           focusWidget == self.quickFindtextCombo:
            return
        else:
            aw = self.activeWindow()
            if aw:
                aw.newLineBelow()
        
    def __editorConfigChanged(self):
        """
        Private method to handle changes of an editors configuration (e.g. language).
        """
        editor = self.sender()
        fn = editor.getFileName()
        line, pos = editor.getCursorPosition()
        enc = editor.getEncoding()
        lang = editor.getLanguage()
        eol = editor.getEolIndicator()
        self.__setSbFile(fn, line + 1, pos, encoding=enc, language=lang, eol=eol)
    
    ##################################################################
    ## Below are protected utility methods
    ##################################################################
    
    def _getOpenStartDir(self):
        """
        Protected method to return the starting directory for a file open dialog.
        
        The appropriate starting directory is calculated
        using the following search order, until a match is found:<br />
            1: Directory of currently active editor<br />
            2: Directory of currently active Project<br />
            3: CWD
        
        @return name of directory to start (string)
        """
        # if we have an active source, return its path
        if self.activeWindow() is not None and \
           self.activeWindow().getFileName():
            return os.path.dirname(self.activeWindow().getFileName())
        
        # check, if there is an active project and return its path
        elif e5App().getObject("Project").isOpen():
            return e5App().getObject("Project").ppath
        
        else:
            # None will cause open dialog to start with cwd
            return ""
        
    def _getOpenFileFilter(self):
        """
        Protected method to return the active filename filter for a file open dialog.
        
        The appropriate filename filter is determined by file extension of
        the currently active editor.
        
        @return name of the filename filter (string) or None
        """
        if self.activeWindow() is not None and \
           self.activeWindow().getFileName():
            ext = os.path.splitext(self.activeWindow().getFileName())[1]
            rx = QRegExp(".*\*\.{0}[ )].*".format(ext[1:]))
            filters = QScintilla.Lexers.getOpenFileFiltersList()
            index = -1
            for i in range(len(filters)):
                if rx.exactMatch(filters[i]):
                    index = i
                    break
            if index == -1:
                return Preferences.getEditor("DefaultOpenFilter")
            else:
                return filters[index]
        else:
            return Preferences.getEditor("DefaultOpenFilter")
    
    ##################################################################
    ## Below are API handling methods
    ##################################################################
    
    def getAPIsManager(self):
        """
        Public method to get a reference to the APIs manager.
        @return the APIs manager object (eric5.QScintilla.APIsManager)
        """
        return self.apisManager
    
    #######################################################################
    ## Cooperation related methods
    #######################################################################
    
    def setCooperationClient(self, client):
        """
        Public method to set a reference to the cooperation client.
        
        @param client reference to the cooperation client (CooperationClient)
        """
        self.__cooperationClient = client
    
    def isConnected(self):
        """
        Public method to check the connection status of the IDE.
        
        @return flag indicating the connection status (boolean)
        """
        return self.__cooperationClient.hasConnections()
    
    def send(self, fileName, message):
        """
        Public method to send an editor command to remote editors.
        
        @param fileName file name of the editor (string)
        @param message command message to be sent (string)
        """
        project = e5App().getObject("Project")
        if project.isProjectFile(fileName):
            self.__cooperationClient.sendEditorCommand(
                project.getHash(),
                project.getRelativeUniversalPath(fileName),
                message
            )
    
    def receive(self, hash, fileName, command):
        """
        Public slot to handle received editor commands.
        
        @param hash hash of the project (string)
        @param fileName project relative file name of the editor (string)
        @param command command string (string)
        """
        project = e5App().getObject("Project")
        if hash == project.getHash():
            fn = project.getAbsoluteUniversalPath(fileName)
            editor = self.getOpenEditor(fn)
            if editor:
                editor.receive(command)
    
    def shareConnected(self, connected):
        """
        Public slot to handle a change of the connected state.
        
        @param connected flag indicating the connected state (boolean)
        """
        for editor in self.getOpenEditors():
            editor.shareConnected(connected)
    
    def shareEditor(self, share):
        """
        Public slot to set the shared status of the current editor.
        
        @param share flag indicating the share status (boolean)
        """
        aw = self.activeWindow()
        if aw is not None:
            fn = aw.getFileName()
            if fn and e5App().getObject("Project").isProjectFile(fn):
                aw.shareEditor(share)
    
    def startSharedEdit(self):
        """
        Public slot to start a shared edit session for the current editor.
        """
        aw = self.activeWindow()
        if aw is not None:
            fn = aw.getFileName()
            if fn and e5App().getObject("Project").isProjectFile(fn):
                aw.startSharedEdit()
    
    def sendSharedEdit(self):
        """
        Public slot to end a shared edit session for the current editor and
        send the changes.
        """
        aw = self.activeWindow()
        if aw is not None:
            fn = aw.getFileName()
            if fn and e5App().getObject("Project").isProjectFile(fn):
                aw.sendSharedEdit()
    
    def cancelSharedEdit(self):
        """
        Public slot to cancel a shared edit session for the current editor.
        """
        aw = self.activeWindow()
        if aw is not None:
            fn = aw.getFileName()
            if fn and e5App().getObject("Project").isProjectFile(fn):
                aw.cancelSharedEdit()
    
    #######################################################################
    ## Symbols viewer related methods
    #######################################################################
    
    def insertSymbol(self, txt):
        """
        Private slot to insert a symbol text into the active window.
        
        @param txt text to be inserted (string)
        """
        if self.__lastFocusWidget == e5App().getObject("Shell"):
            e5App().getObject("Shell").insert(txt)
        elif self.__lastFocusWidget == e5App().getObject("Terminal"):
            e5App().getObject("Terminal").insert(txt)
        else:
            aw = self.activeWindow()
            if aw is not None:
                curline, curindex = aw.getCursorPosition()
                aw.insert(txt)
                aw.setCursorPosition(curline, curindex + len(txt))
    
    #######################################################################
    ## Numbers viewer related methods
    #######################################################################
    
    def insertNumber(self, txt):
        """
        Private slot to insert a number text into the active window.
        
        @param txt text to be inserted (string)
        """
        if self.__lastFocusWidget == e5App().getObject("Shell"):
            aw = e5App().getObject("Shell")
            if aw.hasSelectedText():
                aw.removeSelectedText()
            aw.insert(txt)
        elif self.__lastFocusWidget == e5App().getObject("Terminal"):
            aw = e5App().getObject("Terminal")
            if aw.hasSelectedText():
                aw.removeSelectedText()
            aw.insert(txt)
        else:
            aw = self.activeWindow()
            if aw is not None:
                if aw.hasSelectedText():
                    aw.removeSelectedText()
                curline, curindex = aw.getCursorPosition()
                aw.insert(txt)
                aw.setCursorPosition(curline, curindex + len(txt))
    
    def getNumber(self):
        """
        Public method to get a number from the active window.
        
        @return selected text of the active window (string)
        """
        txt = ""
        if self.__lastFocusWidget == e5App().getObject("Shell"):
            aw = e5App().getObject("Shell")
            if aw.hasSelectedText():
                txt = aw.selectedText()
        elif self.__lastFocusWidget == e5App().getObject("Terminal"):
            aw = e5App().getObject("Terminal")
            if aw.hasSelectedText():
                txt = aw.selectedText()
        else:
            aw = self.activeWindow()
            if aw is not None:
                if aw.hasSelectedText():
                    txt = aw.selectedText()
        return txt
