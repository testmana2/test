# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a minimalistic editor for simple editing tasks.
"""

import os
import re

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.Qsci import QsciScintilla

from E5Gui.E5Action import E5Action, createActionGroup
from E5Gui import E5MessageBox, E5FileDialog

from . import Lexers
from .QsciScintillaCompat import QsciScintillaCompat
from .SearchReplaceWidget import SearchReplaceWidget

import UI.PixmapCache
import UI.Config

from .Printer import Printer

import Utilities
import Preferences

class MiniScintilla(QsciScintillaCompat):
    """
    Class implementing a QsciScintillaCompat subclass for handling focus events.
    """
    def __init__(self, parent = None):
        """
        Constructor
        
        @param parent parent widget (QWidget)
        @param name name of this instance (string)
        @param flags window flags
        """
        QsciScintillaCompat.__init__(self, parent)
        
        self.mw = parent
    
    def getFileName(self):
        """
        Public method to return the name of the file being displayed.
        
        @return filename of the displayed file (string)
        """
        return self.mw.getFileName()
    
    def focusInEvent(self, event):
        """
        Protected method called when the editor receives focus.
        
        This method checks for modifications of the current file and
        rereads it upon request. The cursor is placed at the current position
        assuming, that it is in the vicinity of the old position after the reread.
        
        @param event the event object (QFocusEvent)
        """
        self.mw.editorActGrp.setEnabled(True)
        try:
            self.setCaretWidth(self.mw.caretWidth)
        except AttributeError:
            pass
        
        self.setCursorFlashTime(QApplication.cursorFlashTime())
        
        QsciScintillaCompat.focusInEvent(self, event)
    
    def focusOutEvent(self, event):
        """
        Public method called when the editor loses focus.
        
        @param event the event object (QFocusEvent)
        """
        self.mw.editorActGrp.setEnabled(False)
        self.setCaretWidth(0)
        
        QsciScintillaCompat.focusOutEvent(self, event)

class MiniEditor(QMainWindow):
    """
    Class implementing a minimalistic editor for simple editing tasks.
    
    @signal editorSaved() emitted after the file has been saved
    """
    editorSaved = pyqtSignal()
    
    def __init__(self, filename = "", filetype = "", parent = None, name = None):
        """
        Constructor
        
        @param filename name of the file to open (string)
        @param filetype type of the source file (string)
        @param parent reference to the parent widget (QWidget)
        @param name object name of the window (string)
        """
        QMainWindow.__init__(self, parent)
        if name is not None:
            self.setObjectName(name)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowIcon(UI.PixmapCache.getIcon("editor.png"))
        
        self.__textEdit = MiniScintilla(self)
        self.__textEdit.clearSearchIndicators = self.clearSearchIndicators
        self.__textEdit.setSearchIndicator = self.setSearchIndicator
        self.__textEdit.setUtf8(True)
        self.encoding = Preferences.getEditor("DefaultEncoding")
        
        self.srHistory = {
            "search" : [], 
            "replace" : []
        }
        self.searchDlg = SearchReplaceWidget(False, self, self)
        self.replaceDlg = SearchReplaceWidget(True, self, self)
        
        centralWidget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(1, 1, 1, 1)
        layout.addWidget(self.__textEdit)
        layout.addWidget(self.searchDlg)
        layout.addWidget(self.replaceDlg)
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)
        self.searchDlg.hide()
        self.replaceDlg.hide()
        
        self.lexer_ = None
        self.apiLanguage = ""
        self.filetype = ""
        
        self.__createActions()
        self.__createMenus()
        self.__createToolBars()
        self.__createStatusBar()
        
        self.__setTextDisplay()
        self.__setMargins()
        self.__setEolMode()
        
        self.__readSettings()
        
        # clear QScintilla defined keyboard commands
        # we do our own handling through the view manager
        self.__textEdit.clearAlternateKeys()
        self.__textEdit.clearKeys()
        
        # initialise the mark occurrences timer
        self.__markOccurrencesTimer = QTimer(self)
        self.__markOccurrencesTimer.setSingleShot(True)
        self.__markOccurrencesTimer.setInterval(
            Preferences.getEditor("MarkOccurrencesTimeout"))
        self.__markOccurrencesTimer.timeout.connect(self.__markOccurrences)
        self.__markedText = ""
        
        self.__textEdit.textChanged.connect(self.__documentWasModified)
        self.__textEdit.modificationChanged.connect(self.__modificationChanged)
        self.__textEdit.cursorPositionChanged.connect(self.__cursorPositionChanged)
        
        self.__textEdit.setContextMenuPolicy(Qt.CustomContextMenu)
        self.__textEdit.customContextMenuRequested.connect(self.__contextMenuRequested)
        
        self.__textEdit.selectionChanged.connect(self.searchDlg.selectionChanged)
        self.__textEdit.selectionChanged.connect(self.replaceDlg.selectionChanged)
        
        self.__setCurrentFile("")
        if filename:
            self.__loadFile(filename, filetype)
        
        self.__checkActions()

    def closeEvent(self, event):
        """
        Public method to handle the close event.
        
        @param event close event (QCloseEvent)
        """
        if self.__maybeSave():
            self.__writeSettings()
            event.accept()
        else:
            event.ignore()
    
    def __newFile(self):
        """
        Private slot to create a new file.
        """
        if self.__maybeSave():
            self.__textEdit.clear()
            self.__setCurrentFile("")
        
        self.__checkActions()
    
    def __open(self):
        """
        Private slot to open a file.
        """
        if self.__maybeSave():
            fileName = E5FileDialog.getOpenFileName(self)
            if fileName:
                self.__loadFile(fileName)
        self.__checkActions()
    
    def __save(self):
        """
        Private slot to save a file.
        """
        if not self.__curFile:
            return self.__saveAs()
        else:
            return self.__saveFile(self.__curFile)
    
    def __saveAs(self):
        """
        Private slot to save a file with a new name.
        """
        fileName = E5FileDialog.getSaveFileName(self)
        if not fileName:
            return False
        
        return self.__saveFile(fileName)
    
    def __about(self):
        """
        Private slot to show a little About message.
        """
        E5MessageBox.about(self, self.trUtf8("About eric5 Mini Editor"),
            self.trUtf8("The eric5 Mini Editor is an editor component"
                " based on QScintilla. It may be used for simple"
                " editing tasks, that don't need the power of"
                " a full blown editor."))
    
    def __aboutQt(self):
        """
        Private slot to handle the About Qt dialog.
        """
        E5MessageBox.aboutQt(self, "eric5 Mini Editor")
    
    def __whatsThis(self):
        """
        Private slot called in to enter Whats This mode.
        """
        QWhatsThis.enterWhatsThisMode()
    
    def __documentWasModified(self):
        """
        Private slot to handle a change in the documents modification status.
        """
        self.setWindowModified(self.__textEdit.isModified())
    
    def __checkActions(self, setSb = True):
        """
        Private slot to check some actions for their enable/disable status
        and set the statusbar info.
        
        @param setSb flag indicating an update of the status bar is wanted (boolean)
        """
        self.saveAct.setEnabled(self.__textEdit.isModified())
        
        self.undoAct.setEnabled(self.__textEdit.isUndoAvailable())
        self.redoAct.setEnabled(self.__textEdit.isRedoAvailable())
        
        if setSb:
            line, pos = self.__textEdit.getCursorPosition()
            self.__setSbFile(line + 1, pos)
    
    def __setSbFile(self, line = None, pos = None):
        """
        Private method to set the file info in the status bar.
        
        @param line line number to display (int)
        @param pos character position to display (int)
        """
        if not self.__curFile:
            writ = '   '
        else:
            if QFileInfo(self.__curFile).isWritable():
                writ = ' rw'
            else:
                writ = ' ro'
        
        self.sbWritable.setText(writ)
        
        if line is None:
            line = ''
        self.sbLine.setText(self.trUtf8('Line: {0:5}').format(line))
        
        if pos is None:
            pos = ''
        self.sbPos.setText(self.trUtf8('Pos: {0:5}').format(pos))
    
    def __readShortcut(self, act, category):
        """
        Private function to read a single keyboard shortcut from the settings.
        
        @param act reference to the action object (E5Action)
        @param category category the action belongs to (string)
        @param prefClass preferences class used as the storage area
        """
        if act.objectName():
            accel = Preferences.Prefs.settings.value(
                "Shortcuts/{0}/{1}/Accel".format(category, act.objectName()))
            if accel is not None:
                act.setShortcut(QKeySequence(accel))
            accel = Preferences.Prefs.settings.value(
                "Shortcuts/{0}/{1}/AltAccel".format(category, act.objectName()))
            if accel is not None:
                act.setAlternateShortcut(QKeySequence(accel))
    
    def __createActions(self):
        """
        Private method to create the actions.
        """
        self.fileActions = []
        self.editActions = []
        self.helpActions = []
        self.searchActions = []
        
        self.__createFileActions()
        self.__createEditActions()
        self.__createHelpActions()
        self.__createSearchActions()
        
        # read the keyboard shortcuts and make them identical to the main
        # eric5 shortcuts
        for act in self.helpActions:
            self.__readShortcut(act, "General")
        for act in self.editActions:
            self.__readShortcut(act, "Edit")
        for act in self.fileActions:
            self.__readShortcut(act, "File")
        for act in self.searchActions:
            self.__readShortcut(act, "Search")
    
    def __createFileActions(self):
        """
        Private method to create the File actions.
        """
        self.newAct = E5Action(self.trUtf8('New'),
                UI.PixmapCache.getIcon("new.png"),
                self.trUtf8('&New'),
                QKeySequence(self.trUtf8("Ctrl+N", "File|New")),
                0, self, 'vm_file_new')
        self.newAct.setStatusTip(self.trUtf8('Open an empty editor window'))
        self.newAct.setWhatsThis(self.trUtf8(
            """<b>New</b>"""
            """<p>An empty editor window will be created.</p>"""
        ))
        self.newAct.triggered[()].connect(self.__newFile)
        self.fileActions.append(self.newAct)
        
        self.openAct = E5Action(self.trUtf8('Open'),
                UI.PixmapCache.getIcon("open.png"),
                self.trUtf8('&Open...'),
                QKeySequence(self.trUtf8("Ctrl+O", "File|Open")), 
                0, self, 'vm_file_open')
        self.openAct.setStatusTip(self.trUtf8('Open a file'))
        self.openAct.setWhatsThis(self.trUtf8(
            """<b>Open a file</b>"""
            """<p>You will be asked for the name of a file to be opened.</p>"""
        ))
        self.openAct.triggered[()].connect(self.__open)
        self.fileActions.append(self.openAct)
        
        self.saveAct = E5Action(self.trUtf8('Save'),
                UI.PixmapCache.getIcon("fileSave.png"),
                self.trUtf8('&Save'),
                QKeySequence(self.trUtf8("Ctrl+S", "File|Save")), 
                0, self, 'vm_file_save')
        self.saveAct.setStatusTip(self.trUtf8('Save the current file'))
        self.saveAct.setWhatsThis(self.trUtf8(
            """<b>Save File</b>"""
            """<p>Save the contents of current editor window.</p>"""
        ))
        self.saveAct.triggered[()].connect(self.__save)
        self.fileActions.append(self.saveAct)
        
        self.saveAsAct = E5Action(self.trUtf8('Save as'),
                UI.PixmapCache.getIcon("fileSaveAs.png"),
                self.trUtf8('Save &as...'),
                QKeySequence(self.trUtf8("Shift+Ctrl+S", "File|Save As")), 
                0, self, 'vm_file_save_as')
        self.saveAsAct.setStatusTip(self.trUtf8('Save the current file to a new one'))
        self.saveAsAct.setWhatsThis(self.trUtf8(
            """<b>Save File as</b>"""
            """<p>Save the contents of current editor window to a new file."""
            """ The file can be entered in a file selection dialog.</p>"""
        ))
        self.saveAsAct.triggered[()].connect(self.__saveAs)
        self.fileActions.append(self.saveAsAct)
        
        self.closeAct = E5Action(self.trUtf8('Close'),
                UI.PixmapCache.getIcon("close.png"),
                self.trUtf8('&Close'),
                QKeySequence(self.trUtf8("Ctrl+W", "File|Close")), 
                0, self, 'vm_file_close')
        self.closeAct.setStatusTip(self.trUtf8('Close the editor window'))
        self.closeAct.setWhatsThis(self.trUtf8(
            """<b>Close Window</b>"""
            """<p>Close the current window.</p>"""
        ))
        self.closeAct.triggered[()].connect(self.close)
        self.fileActions.append(self.closeAct)
        
        self.printAct = E5Action(self.trUtf8('Print'),
                UI.PixmapCache.getIcon("print.png"),
                self.trUtf8('&Print'),
                QKeySequence(self.trUtf8("Ctrl+P", "File|Print")), 
                0, self, 'vm_file_print')
        self.printAct.setStatusTip(self.trUtf8('Print the current file'))
        self.printAct.setWhatsThis(self.trUtf8( 
            """<b>Print File</b>"""
            """<p>Print the contents of the current file.</p>"""
        ))
        self.printAct.triggered[()].connect(self.__printFile)
        self.fileActions.append(self.printAct)
        
        self.printPreviewAct = \
            E5Action(self.trUtf8('Print Preview'),
                UI.PixmapCache.getIcon("printPreview.png"),
                QApplication.translate('ViewManager', 'Print Preview'),
                0, 0, self, 'vm_file_print_preview')
        self.printPreviewAct.setStatusTip(self.trUtf8(
            'Print preview of the current file'))
        self.printPreviewAct.setWhatsThis(self.trUtf8(
            """<b>Print Preview</b>"""
            """<p>Print preview of the current file.</p>"""
        ))
        self.printPreviewAct.triggered[()].connect(self.__printPreviewFile)
        self.fileActions.append(self.printPreviewAct)
    
    def __createEditActions(self):
        """
        Private method to create the Edit actions.
        """
        self.undoAct = E5Action(self.trUtf8('Undo'),
                UI.PixmapCache.getIcon("editUndo.png"),
                self.trUtf8('&Undo'),
                QKeySequence(self.trUtf8("Ctrl+Z", "Edit|Undo")), 
                QKeySequence(self.trUtf8("Alt+Backspace", "Edit|Undo")), 
                self, 'vm_edit_undo')
        self.undoAct.setStatusTip(self.trUtf8('Undo the last change'))
        self.undoAct.setWhatsThis(self.trUtf8(
            """<b>Undo</b>"""
            """<p>Undo the last change done in the current editor.</p>"""
        ))
        self.undoAct.triggered[()].connect(self.__undo)
        self.editActions.append(self.undoAct)
        
        self.redoAct = E5Action(self.trUtf8('Redo'),
                UI.PixmapCache.getIcon("editRedo.png"),
                self.trUtf8('&Redo'),
                QKeySequence(self.trUtf8("Ctrl+Shift+Z", "Edit|Redo")), 
                0, self, 'vm_edit_redo')
        self.redoAct.setStatusTip(self.trUtf8('Redo the last change'))
        self.redoAct.setWhatsThis(self.trUtf8(
            """<b>Redo</b>"""
            """<p>Redo the last change done in the current editor.</p>"""
        ))
        self.redoAct.triggered[()].connect(self.__redo)
        self.editActions.append(self.redoAct)
        
        self.cutAct = E5Action(self.trUtf8('Cut'),
                UI.PixmapCache.getIcon("editCut.png"),
                self.trUtf8('Cu&t'),
                QKeySequence(self.trUtf8("Ctrl+X", "Edit|Cut")),
                QKeySequence(self.trUtf8("Shift+Del", "Edit|Cut")),
                self, 'vm_edit_cut')
        self.cutAct.setStatusTip(self.trUtf8('Cut the selection'))
        self.cutAct.setWhatsThis(self.trUtf8(
            """<b>Cut</b>"""
            """<p>Cut the selected text of the current editor to the clipboard.</p>"""
        ))
        self.cutAct.triggered[()].connect(self.__textEdit.cut)
        self.editActions.append(self.cutAct)
        
        self.copyAct = E5Action(self.trUtf8('Copy'),
                UI.PixmapCache.getIcon("editCopy.png"),
                self.trUtf8('&Copy'),
                QKeySequence(self.trUtf8("Ctrl+C", "Edit|Copy")), 
                QKeySequence(self.trUtf8("Ctrl+Ins", "Edit|Copy")), 
                self, 'vm_edit_copy')
        self.copyAct.setStatusTip(self.trUtf8('Copy the selection'))
        self.copyAct.setWhatsThis(self.trUtf8(
            """<b>Copy</b>"""
            """<p>Copy the selected text of the current editor to the clipboard.</p>"""
        ))
        self.copyAct.triggered[()].connect(self.__textEdit.copy)
        self.editActions.append(self.copyAct)
        
        self.pasteAct = E5Action(self.trUtf8('Paste'),
                UI.PixmapCache.getIcon("editPaste.png"),
                self.trUtf8('&Paste'),
                QKeySequence(self.trUtf8("Ctrl+V", "Edit|Paste")), 
                QKeySequence(self.trUtf8("Shift+Ins", "Edit|Paste")), 
                self, 'vm_edit_paste')
        self.pasteAct.setStatusTip(self.trUtf8('Paste the last cut/copied text'))
        self.pasteAct.setWhatsThis(self.trUtf8(
            """<b>Paste</b>"""
            """<p>Paste the last cut/copied text from the clipboard to"""
            """ the current editor.</p>"""
        ))
        self.pasteAct.triggered[()].connect(self.__textEdit.paste)
        self.editActions.append(self.pasteAct)
        
        self.deleteAct = E5Action(self.trUtf8('Clear'),
                UI.PixmapCache.getIcon("editDelete.png"),
                self.trUtf8('Cl&ear'),
                QKeySequence(self.trUtf8("Alt+Shift+C", "Edit|Clear")), 
                0,
                self, 'vm_edit_clear')
        self.deleteAct.setStatusTip(self.trUtf8('Clear all text'))
        self.deleteAct.setWhatsThis(self.trUtf8(
            """<b>Clear</b>"""
            """<p>Delete all text of the current editor.</p>"""
        ))
        self.deleteAct.triggered[()].connect(self.__textEdit.clear)
        self.editActions.append(self.deleteAct)
        
        self.cutAct.setEnabled(False)
        self.copyAct.setEnabled(False)
        self.__textEdit.copyAvailable.connect(self.cutAct.setEnabled)
        self.__textEdit.copyAvailable.connect(self.copyAct.setEnabled)
        
        ####################################################################
        ## Below follow the actions for qscintilla standard commands.
        ####################################################################
        
        self.esm = QSignalMapper(self)
        self.esm.mapped[int].connect(self.__textEdit.editorCommand)
        
        self.editorActGrp = createActionGroup(self)
        
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
        act.triggered[()].connect(self.__textEdit.newLineBelow)
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
        
        self.__textEdit.addActions(self.editorActGrp.actions())
    
    def __createSearchActions(self):
        """
        Private method defining the user interface actions for the search commands.
        """
        self.searchAct = E5Action(QApplication.translate('ViewManager', 'Search'),
                UI.PixmapCache.getIcon("find.png"),
                QApplication.translate('ViewManager', '&Search...'),
                QKeySequence(QApplication.translate('ViewManager', 
                    "Ctrl+F", "Search|Search")), 
                0,
                self, 'vm_search')
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
                self, 'vm_search_next')
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
                self, 'vm_search_previous')
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
                self, 'vm_clear_search_markers')
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
                self, 'vm_search_replace')
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
    
    def __createHelpActions(self):
        """
        Private method to create the Help actions.
        """
        self.aboutAct = E5Action(self.trUtf8('About'),
                self.trUtf8('&About'),
                0, 0, self, 'about_eric')
        self.aboutAct.setStatusTip(self.trUtf8('Display information about this software'))
        self.aboutAct.setWhatsThis(self.trUtf8(
            """<b>About</b>"""
            """<p>Display some information about this software.</p>"""))
        self.aboutAct.triggered[()].connect(self.__about)
        self.helpActions.append(self.aboutAct)
        
        self.aboutQtAct = E5Action(self.trUtf8('About Qt'),
                self.trUtf8('About &Qt'), 0, 0, self, 'about_qt')
        self.aboutQtAct.setStatusTip(
            self.trUtf8('Display information about the Qt toolkit'))
        self.aboutQtAct.setWhatsThis(self.trUtf8(
            """<b>About Qt</b>"""
            """<p>Display some information about the Qt toolkit.</p>"""
        ))
        self.aboutQtAct.triggered[()].connect(self.__aboutQt)
        self.helpActions.append(self.aboutQtAct)
        
        self.whatsThisAct = E5Action(self.trUtf8('What\'s This?'), 
            UI.PixmapCache.getIcon("whatsThis.png"),
            self.trUtf8('&What\'s This?'), 
            QKeySequence(self.trUtf8("Shift+F1","Help|What's This?'")), 
            0, self, 'help_help_whats_this')
        self.whatsThisAct.setStatusTip(self.trUtf8('Context sensitive help'))
        self.whatsThisAct.setWhatsThis(self.trUtf8(
                """<b>Display context sensitive help</b>"""
                """<p>In What's This? mode, the mouse cursor shows an arrow with a"""
                """ question mark, and you can click on the interface elements to get"""
                """ a short description of what they do and how to use them. In"""
                """ dialogs, this feature can be accessed using the context help button"""
                """ in the titlebar.</p>"""
        ))
        self.whatsThisAct.triggered[()].connect(self.__whatsThis)
        self.helpActions.append(self.whatsThisAct)
    
    def __createMenus(self):
        """
        Private method to create the menus of the menu bar.
        """
        self.fileMenu = self.menuBar().addMenu(self.trUtf8("&File"))
        self.fileMenu.addAction(self.newAct)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.saveAct)
        self.fileMenu.addAction(self.saveAsAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.printPreviewAct)
        self.fileMenu.addAction(self.printAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.closeAct)
        
        self.editMenu = self.menuBar().addMenu(self.trUtf8("&Edit"))
        self.editMenu.addAction(self.undoAct)
        self.editMenu.addAction(self.redoAct)
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.cutAct)
        self.editMenu.addAction(self.copyAct)
        self.editMenu.addAction(self.pasteAct)
        self.editMenu.addAction(self.deleteAct)
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.searchAct)
        self.editMenu.addAction(self.searchNextAct)
        self.editMenu.addAction(self.searchPrevAct)
        self.editMenu.addAction(self.searchClearMarkersAct)
        self.editMenu.addAction(self.replaceAct)
        
        self.menuBar().addSeparator()
        
        self.helpMenu = self.menuBar().addMenu(self.trUtf8("&Help"))
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)
        self.helpMenu.addSeparator()
        self.helpMenu.addAction(self.whatsThisAct)
        
        self.__initContextMenu()
    
    def __createToolBars(self):
        """
        Private method to create the various toolbars.
        """
        filetb = self.addToolBar(self.trUtf8("File"))
        filetb.setIconSize(UI.Config.ToolBarIconSize)
        filetb.addAction(self.newAct)
        filetb.addAction(self.openAct)
        filetb.addAction(self.saveAct)
        filetb.addAction(self.saveAsAct)
        filetb.addSeparator()
        filetb.addAction(self.printPreviewAct)
        filetb.addAction(self.printAct)
        filetb.addSeparator()
        filetb.addAction(self.closeAct)
        
        edittb = self.addToolBar(self.trUtf8("Edit"))
        edittb.setIconSize(UI.Config.ToolBarIconSize)
        edittb.addAction(self.undoAct)
        edittb.addAction(self.redoAct)
        edittb.addSeparator()
        edittb.addAction(self.cutAct)
        edittb.addAction(self.copyAct)
        edittb.addAction(self.pasteAct)
        edittb.addAction(self.deleteAct)
        
        findtb = self.addToolBar(self.trUtf8("Find"))
        findtb.setIconSize(UI.Config.ToolBarIconSize)
        findtb.addAction(self.searchAct)
        findtb.addAction(self.searchNextAct)
        findtb.addAction(self.searchPrevAct)
        findtb.addAction(self.searchClearMarkersAct)
        
        helptb = self.addToolBar(self.trUtf8("Help"))
        helptb.setIconSize(UI.Config.ToolBarIconSize)
        helptb.addAction(self.whatsThisAct)
    
    def __createStatusBar(self):
        """
        Private method to initialize the status bar.
        """
        self.__statusBar = self.statusBar()
        self.__statusBar.setSizeGripEnabled(True)

        self.sbWritable = QLabel(self.__statusBar)
        self.__statusBar.addPermanentWidget(self.sbWritable)
        self.sbWritable.setWhatsThis(self.trUtf8(
            """<p>This part of the status bar displays an indication of the"""
            """ editors files writability.</p>"""
        ))

        self.sbLine = QLabel(self.__statusBar)
        self.__statusBar.addPermanentWidget(self.sbLine)
        self.sbLine.setWhatsThis(self.trUtf8(
            """<p>This part of the status bar displays the line number of the"""
            """ editor.</p>"""
        ))

        self.sbPos = QLabel(self.__statusBar)
        self.__statusBar.addPermanentWidget(self.sbPos)
        self.sbPos.setWhatsThis(self.trUtf8(
            """<p>This part of the status bar displays the cursor position of"""
            """ the editor.</p>"""
        ))
        
        self.__statusBar.showMessage(self.trUtf8("Ready"))
    
    def __readSettings(self):
        """
        Private method to read the settings remembered last time.
        """
        settings = Preferences.Prefs.settings
        pos = settings.value("MiniEditor/Position", QPoint(0, 0))
        size = settings.value("MiniEditor/Size", QSize(800, 600))
        self.resize(size)
        self.move(pos)
    
    def __writeSettings(self):
        """
        Private method to write the settings for reuse.
        """
        settings = Preferences.Prefs.settings
        settings.setValue("MiniEditor/Position", self.pos())
        settings.setValue("MiniEditor/Size", self.size())
    
    def __maybeSave(self):
        """
        Private method to ask the user to save the file, if it was modified.
        
        @return flag indicating, if it is ok to continue (boolean)
        """
        if self.__textEdit.isModified():
            ret = E5MessageBox.okToClearData(self, 
                    self.trUtf8("eric5 Mini Editor"),
                    self.trUtf8("The document has unsaved changes."),
                    self.__save)
            return ret
        return True
    
    def __loadFile(self, fileName, filetype = None):
        """
        Private method to load the given file.
        
        @param fileName name of the file to load (string)
        @param filetype type of the source file (string)
        """
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        
        try:
            txt, self.encoding = Utilities.readEncodedFile(fileName)
        except (UnicodeDecodeError, IOError) as why:
            QApplication.restoreOverrideCursor()
            E5MessageBox.critical(self, self.trUtf8('Open File'),
                self.trUtf8('<p>The file <b>{0}</b> could not be opened.</p>'
                            '<p>Reason: {1}</p>')
                    .format(fileName, str(why)))
            QApplication.restoreOverrideCursor()
            return
        
        self.__textEdit.setText(txt)
        QApplication.restoreOverrideCursor()
        
        if filetype is None:
            self.filetype = ""
        else:
            self.filetype = filetype
        self.__setCurrentFile(fileName)
        
        fileEol = self.__textEdit.detectEolString(txt)
        self.__textEdit.setEolModeByEolString(fileEol)
        
        self.__statusBar.showMessage(self.trUtf8("File loaded"), 2000)

    def __saveFile(self, fileName):
        """
        Private method to save to the given file.
        
        @param fileName name of the file to save to (string)
        @return flag indicating success (boolean)
        """
        QApplication.setOverrideCursor(Qt.WaitCursor)
        txt = self.__textEdit.text()
        try:
            self.encoding = Utilities.writeEncodedFile(fileName, txt, self.encoding)
        except (IOError, Utilities.CodingError, UnicodeError) as why:
            E5MessageBox.critical(self, self.trUtf8('Save File'),
                self.trUtf8('<p>The file <b>{0}</b> could not be saved.<br/>'
                            'Reason: {1}</p>')
                    .format(fileName, str(why)))
            QApplication.restoreOverrideCursor()
        
            self.__checkActions()
            
            return False
        
        QApplication.restoreOverrideCursor()
        self.editorSaved.emit()
        
        self.__setCurrentFile(fileName)
        self.__statusBar.showMessage(self.trUtf8("File saved"), 2000)
        
        self.__checkActions()
        
        return True

    def __setCurrentFile(self, fileName):
        """
        Private method to register the file name of the current file.
        
        @param fileName name of the file to register (string)
        """
        self.__curFile = fileName
        
        if not self.__curFile:
            shownName = self.trUtf8("Untitled")
        else:
            shownName = self.__strippedName(self.__curFile)
        
        self.setWindowTitle(self.trUtf8("{0}[*] - {1}")\
                            .format(shownName, self.trUtf8("Mini Editor")))
        
        self.__textEdit.setModified(False)
        self.setWindowModified(False)
        
        self.setLanguage(self.__bindName(self.__textEdit.text(0)))

    def getFileName(self):
        """
        Public method to return the name of the file being displayed.
        
        @return filename of the displayed file (string)
        """
        return self.__curFile
    
    def __strippedName(self, fullFileName):
        """
        Private method to return the filename part of the given path.
        
        @param fullFileName full pathname of the given file (string)
        @return filename part (string)
        """
        return QFileInfo(fullFileName).fileName()

    def __modificationChanged(self, m):
        """
        Private slot to handle the modificationChanged signal. 
        
        @param m modification status
        """
        self.setWindowModified(m)
        self.__checkActions()
    
    def __cursorPositionChanged(self, line, pos):
        """
        Private slot to handle the cursorPositionChanged signal. 
        
        @param line line number of the cursor
        @param pos position in line of the cursor
        """
        self.__setSbFile(line + 1, pos)
        
        if Preferences.getEditor("MarkOccurrencesEnabled"):
            self.__markOccurrencesTimer.stop()
            self.__markOccurrencesTimer.start()
    
    def __undo(self):
        """
        Public method to undo the last recorded change.
        """
        self.__textEdit.undo()
        self.__checkActions()
    
    def __redo(self):
        """
        Public method to redo the last recorded change.
        """
        self.__textEdit.redo()
        self.__checkActions()
    
    def __selectAll(self):
        """
        Private slot handling the select all context menu action.
        """
        self.__textEdit.selectAll(True)
    
    def __deselectAll(self):
        """
        Private slot handling the deselect all context menu action.
        """
        self.__textEdit.selectAll(False)
    
    def __setMargins(self):
        """
        Private method to configure the margins.
        """
        # set the settings for all margins
        self.__textEdit.setMarginsFont(Preferences.getEditorOtherFonts("MarginsFont"))
        self.__textEdit.setMarginsForegroundColor(
            Preferences.getEditorColour("MarginsForeground"))
        self.__textEdit.setMarginsBackgroundColor(
            Preferences.getEditorColour("MarginsBackground"))
        
        # set margin 0 settings
        linenoMargin = Preferences.getEditor("LinenoMargin")
        self.__textEdit.setMarginLineNumbers(0, linenoMargin)
        if linenoMargin:
            self.__textEdit.setMarginWidth(0, 
                ' ' + '8' * Preferences.getEditor("LinenoWidth"))
        else:
            self.__textEdit.setMarginWidth(0, 16)
        
        # set margin 1 settings
        self.__textEdit.setMarginWidth(1, 0)
        
        # set margin 2 settings
        self.__textEdit.setMarginWidth(2, 16)
        if Preferences.getEditor("FoldingMargin"):
            folding = Preferences.getEditor("FoldingStyle")
            try:
                folding = QsciScintilla.FoldStyle(folding)
            except AttributeError:
                pass
            self.__textEdit.setFolding(folding)
            self.__textEdit.setFoldMarginColors(
                Preferences.getEditorColour("FoldmarginBackground"), 
                Preferences.getEditorColour("FoldmarginBackground"))
            self.__textEdit.setFoldMarkersColors(
                Preferences.getEditorColour("FoldMarkersForeground"),
                Preferences.getEditorColour("FoldMarkersBackground"))
        else:
            self.__textEdit.setFolding(QsciScintilla.NoFoldStyle)
    
    def __setTextDisplay(self):
        """
        Private method to configure the text display.
        """
        self.__textEdit.setTabWidth(Preferences.getEditor("TabWidth"))
        self.__textEdit.setIndentationWidth(Preferences.getEditor("IndentWidth"))
        if self.lexer_ and self.lexer_.alwaysKeepTabs():
            self.__textEdit.setIndentationsUseTabs(True)
        else:
            self.__textEdit.setIndentationsUseTabs(
                Preferences.getEditor("TabForIndentation"))
        self.__textEdit.setTabIndents(Preferences.getEditor("TabIndents"))
        self.__textEdit.setBackspaceUnindents(Preferences.getEditor("TabIndents"))
        self.__textEdit.setIndentationGuides(Preferences.getEditor("IndentationGuides"))
        if Preferences.getEditor("ShowWhitespace"):
            self.__textEdit.setWhitespaceVisibility(QsciScintilla.WsVisible)
        else:
            self.__textEdit.setWhitespaceVisibility(QsciScintilla.WsInvisible)
        self.__textEdit.setEolVisibility(Preferences.getEditor("ShowEOL"))
        self.__textEdit.setAutoIndent(Preferences.getEditor("AutoIndentation"))
        if Preferences.getEditor("BraceHighlighting"):
            self.__textEdit.setBraceMatching(QsciScintilla.SloppyBraceMatch)
        else:
            self.__textEdit.setBraceMatching(QsciScintilla.NoBraceMatch)
        self.__textEdit.setMatchedBraceForegroundColor(
            Preferences.getEditorColour("MatchingBrace"))
        self.__textEdit.setMatchedBraceBackgroundColor(
            Preferences.getEditorColour("MatchingBraceBack"))
        self.__textEdit.setUnmatchedBraceForegroundColor(
            Preferences.getEditorColour("NonmatchingBrace"))
        self.__textEdit.setUnmatchedBraceBackgroundColor(
            Preferences.getEditorColour("NonmatchingBraceBack"))
        if Preferences.getEditor("CustomSelectionColours"):
            self.__textEdit.setSelectionBackgroundColor(
                Preferences.getEditorColour("SelectionBackground"))
        else:
            self.__textEdit.setSelectionBackgroundColor(
                QApplication.palette().color(QPalette.Highlight))
        if Preferences.getEditor("ColourizeSelText"):
            self.__textEdit.resetSelectionForegroundColor()
        elif Preferences.getEditor("CustomSelectionColours"):
            self.__textEdit.setSelectionForegroundColor(
                Preferences.getEditorColour("SelectionForeground"))
        else:
            self.__textEdit.setSelectionForegroundColor(
                QApplication.palette().color(QPalette.HighlightedText))
        self.__textEdit.setSelectionToEol(Preferences.getEditor("ExtendSelectionToEol"))
        self.__textEdit.setCaretForegroundColor(
            Preferences.getEditorColour("CaretForeground"))
        self.__textEdit.setCaretLineBackgroundColor(
            Preferences.getEditorColour("CaretLineBackground"))
        self.__textEdit.setCaretLineVisible(Preferences.getEditor("CaretLineVisible"))
        self.caretWidth = Preferences.getEditor("CaretWidth")
        self.__textEdit.setCaretWidth(self.caretWidth)
        self.useMonospaced = Preferences.getEditor("UseMonospacedFont")
        self.__setMonospaced(self.useMonospaced)
        edgeMode = Preferences.getEditor("EdgeMode")
        edge = QsciScintilla.EdgeMode(edgeMode)
        self.__textEdit.setEdgeMode(edge)
        if edgeMode:
            self.__textEdit.setEdgeColumn(Preferences.getEditor("EdgeColumn"))
            self.__textEdit.setEdgeColor(Preferences.getEditorColour("Edge"))
        
        if Preferences.getEditor("WrapLongLines"):
            self.__textEdit.setWrapMode(QsciScintilla.WrapWord)
            self.__textEdit.setWrapVisualFlags(
                QsciScintilla.WrapFlagByBorder, QsciScintilla.WrapFlagByBorder)
        else:
            self.__textEdit.setWrapMode(QsciScintilla.WrapNone)
            self.__textEdit.setWrapVisualFlags(
                QsciScintilla.WrapFlagNone, QsciScintilla.WrapFlagNone)
        
        self.searchIndicator = QsciScintilla.INDIC_CONTAINER
        self.__textEdit.indicatorDefine(self.searchIndicator, QsciScintilla.INDIC_BOX, 
            Preferences.getEditorColour("SearchMarkers"))
        
        self.__textEdit.setCursorFlashTime(QApplication.cursorFlashTime())
    
    def __setEolMode(self):
        """
        Private method to configure the eol mode of the editor.
        """
        eolMode = Preferences.getEditor("EOLMode")
        eolMode = QsciScintilla.EolMode(eolMode)
        self.__textEdit.setEolMode(eolMode)
        
    def __setMonospaced(self, on):
        """
        Private method to set/reset a monospaced font.
        
        @param on flag to indicate usage of a monospace font (boolean)
        """
        if on:
            f = Preferences.getEditorOtherFonts("MonospacedFont")
            self.__textEdit.monospacedStyles(f)
        else:
            if not self.lexer_:
                self.__textEdit.clearStyles()
                self.__setMargins()
            self.__textEdit.setFont(Preferences.getEditorOtherFonts("DefaultFont"))
        
        self.useMonospaced = on
    
    def __printFile(self):
        """
        Private slot to print the text.
        """
        printer = Printer(mode = QPrinter.HighResolution)
        sb = self.statusBar()
        printDialog = QPrintDialog(printer, self)
        if self.__textEdit.hasSelectedText():
            printDialog.addEnabledOption(QAbstractPrintDialog.PrintSelection)
        if printDialog.exec_() == QDialog.Accepted:
            sb.showMessage(self.trUtf8('Printing...'))
            QApplication.processEvents()
            if self.__curFile:
                printer.setDocName(QFileInfo(self.__curFile).fileName())
            else:
                printer.setDocName(self.trUtf8("Untitled"))
            if printDialog.printRange() == QAbstractPrintDialog.Selection:
                # get the selection
                fromLine, fromIndex, toLine, toIndex = self.__textEdit.getSelection()
                if toIndex == 0:
                    toLine -= 1
                # Qscintilla seems to print one line more than told
                res = printer.printRange(self.__textEdit, fromLine, toLine-1)
            else:
                res = printer.printRange(self.__textEdit)
            if res:
                sb.showMessage(self.trUtf8('Printing completed'), 2000)
            else:
                sb.showMessage(self.trUtf8('Error while printing'), 2000)
            QApplication.processEvents()
        else:
            sb.showMessage(self.trUtf8('Printing aborted'), 2000)
            QApplication.processEvents()
    
    def __printPreviewFile(self):
        """
        Private slot to show a print preview of the text.
        """
        from PyQt4.QtGui import QPrintPreviewDialog
        
        printer = Printer(mode = QPrinter.HighResolution)
        if self.__curFile:
            printer.setDocName(QFileInfo(self.__curFile).fileName())
        else:
            printer.setDocName(self.trUtf8("Untitled"))
        preview = QPrintPreviewDialog(printer, self)
        preview.paintRequested.connect(self.__printPreview)
        preview.exec_()
    
    def __printPreview(self, printer):
        """
        Private slot to generate a print preview.
        
        @param printer reference to the printer object (QScintilla.Printer.Printer)
        """
        printer.printRange(self.__textEdit)
    
    #########################################################
    ## Methods needed by the context menu
    #########################################################
    
    def __contextMenuRequested(self, coord):
        """
        Private slot to show the context menu.
        
        @param coord the position of the mouse pointer (QPoint)
        """
        self.contextMenu.popup(self.mapToGlobal(coord))
    
    def __initContextMenu(self):
        """
        Private method used to setup the context menu
        """
        self.contextMenu = QMenu()
        
        self.languagesMenu = self.__initContextMenuLanguages()
        
        self.contextMenu.addAction(self.undoAct)
        self.contextMenu.addAction(self.redoAct)
        self.contextMenu.addSeparator()
        self.contextMenu.addAction(self.cutAct)
        self.contextMenu.addAction(self.copyAct)
        self.contextMenu.addAction(self.pasteAct)
        self.contextMenu.addSeparator()
        self.contextMenu.addAction(self.trUtf8('Select all'), self.__selectAll)
        self.contextMenu.addAction(self.trUtf8('Deselect all'), self.__deselectAll)
        self.contextMenu.addSeparator()
        self.languagesMenuAct = self.contextMenu.addMenu(self.languagesMenu)
        self.contextMenu.addSeparator()
        self.contextMenu.addAction(self.printPreviewAct)
        self.contextMenu.addAction(self.printAct)
    
    def __initContextMenuLanguages(self):
        """
        Private method used to setup the Languages context sub menu.
        """
        menu = QMenu(self.trUtf8("Languages"))
        
        self.languagesActGrp = QActionGroup(self)
        self.noLanguageAct = menu.addAction(self.trUtf8("No Language"))
        self.noLanguageAct.setCheckable(True)
        self.noLanguageAct.setData("None")
        self.languagesActGrp.addAction(self.noLanguageAct)
        menu.addSeparator()
        
        self.supportedLanguages = {}
        supportedLanguages = Lexers.getSupportedLanguages()
        languages = sorted(list(supportedLanguages.keys()))
        for language in languages:
            if language != "Guessed":
                self.supportedLanguages[language] = supportedLanguages[language][:]
                act = menu.addAction(self.supportedLanguages[language][0])
                act.setCheckable(True)
                act.setData(language)
                self.supportedLanguages[language].append(act)
                self.languagesActGrp.addAction(act)
        
        menu.addSeparator()
        self.pygmentsAct = menu.addAction(self.trUtf8("Guessed"))
        self.pygmentsAct.setCheckable(True)
        self.pygmentsAct.setData("Guessed")
        self.languagesActGrp.addAction(self.pygmentsAct)
        self.pygmentsSelAct = menu.addAction(self.trUtf8("Alternatives"))
        self.pygmentsSelAct.setData("Alternatives")
        
        menu.triggered.connect(self.__languageMenuTriggered)
        menu.aboutToShow.connect(self.__showContextMenuLanguages)
        
        return menu
    
    def __showContextMenuLanguages(self):
        """
        Private slot handling the aboutToShow signal of the languages context menu.
        """
        if self.apiLanguage.startswith("Pygments|"):
            self.pygmentsSelAct.setText(
                self.trUtf8("Alternatives ({0})").format(self.getLanguage()))
        else:
            self.pygmentsSelAct.setText(self.trUtf8("Alternatives"))
    
    def __selectPygmentsLexer(self):
        """
        Private method to select a specific pygments lexer.
        
        @return name of the selected pygments lexer (string)
        """
        from pygments.lexers import get_all_lexers
        lexerList = sorted([l[0] for l in get_all_lexers()])
        try:
            lexerSel = lexerList.index(self.getLanguage())
        except ValueError:
            lexerSel = 0
        lexerName, ok = QInputDialog.getItem(
            self,
            self.trUtf8("Pygments Lexer"),
            self.trUtf8("Select the Pygments lexer to apply."),
            lexerList,
            lexerSel, 
            False)
        if ok and lexerName:
            return lexerName
        else:
            return ""
    
    def __languageMenuTriggered(self, act):
        """
        Private method to handle the selection of a lexer language.
        
        @param act reference to the action that was triggered (QAction)
        """
        if act == self.noLanguageAct:
            self.__resetLanguage()
        elif act == self.pygmentsAct:
            self.setLanguage("dummy.pygments")
        elif act == self.pygmentsSelAct:
            language = self.__selectPygmentsLexer()
            if language:
                self.setLanguage("dummy.pygments", pyname = language)
        else:
            language = act.data()
            if language:
                self.setLanguage(self.supportedLanguages[language][1])
        
    def __resetLanguage(self):
        """
        Private method used to reset the language selection.
        """
        if self.lexer_ is not None and \
           (self.lexer_.lexer() == "container" or self.lexer_.lexer() is None):
            self.__textEdit.SCN_STYLENEEDED.disconnect(self.__styleNeeded)
        
        self.apiLanguage = ""
        self.lexer_ = None
        self.__textEdit.setLexer()
        self.__setMonospaced(self.useMonospaced)
        
    def setLanguage(self, filename, initTextDisplay = True, pyname = ""):
        """
        Public method to set a lexer language.
        
        @param filename filename used to determine the associated lexer language (string)
        @param initTextDisplay flag indicating an initialization of the text display
            is required as well (boolean)
        @keyparam pyname name of the pygments lexer to use (string)
        """
        self.__bindLexer(filename, pyname = pyname)
        self.__textEdit.recolor()
        self.__checkLanguage()
        
        # set the text display
        if initTextDisplay:
            self.__setTextDisplay()
            self.__setMargins()

    def getLanguage(self):
        """
        Public method to retrieve the language of the editor.
        
        @return language of the editor (string)
        """
        if self.apiLanguage == "Guessed" or self.apiLanguage.startswith("Pygments|"):
            return self.lexer_.name()
        else:
            return self.apiLanguage
    
    def __checkLanguage(self):
        """
        Private method to check the selected language of the language submenu.
        """
        if self.apiLanguage == "":
            self.noLanguageAct.setChecked(True)
        elif self.apiLanguage == "Guessed":
            self.pygmentsAct.setChecked(True)
        elif self.apiLanguage.startswith("Pygments|"):
            act = self.languagesActGrp.checkedAction()
            if act:
                act.setChecked(False)
        else:
            self.supportedLanguages[self.apiLanguage][2].setChecked(True)
    
    def __bindLexer(self, filename, pyname = ""):
        """
        Private slot to set the correct lexer depending on language.
        
        @param filename filename used to determine the associated lexer language (string)
        @keyparam pyname name of the pygments lexer to use (string)
        """
        if self.lexer_ is not None and \
           (self.lexer_.lexer() == "container" or self.lexer_.lexer() is None):
            self.__textEdit.SCN_STYLENEEDED.disconnect(self.__styleNeeded)
        
        filename = os.path.basename(filename)
        language = Preferences.getEditorLexerAssoc(filename)
        if language == "Python":
            if self.__isPy2File():
                language = "Python2"
            else:
                language = "Python3"
        if language.startswith("Pygments|"):
            pyname = language.split("|", 1)[1]
            language = ""
        
        self.lexer_ = Lexers.getLexer(language, self.__textEdit, pyname = pyname)
        if self.lexer_ is None:
            self.__textEdit.setLexer()
            self.apiLanguage = ""
            return
        
        if pyname:
            self.apiLanguage = "Pygments|{0}".format(pyname)
        else:
            self.apiLanguage = self.lexer_.language()
        self.__textEdit.setLexer(self.lexer_)
        if self.lexer_.lexer() == "container" or self.lexer_.lexer() is None:
            self.__textEdit.setStyleBits(self.lexer_.styleBitsNeeded())
            self.__textEdit.SCN_STYLENEEDED.connect(self.__styleNeeded)
        
        # get the font for style 0 and set it as the default font
        key = 'Scintilla/{0}/style0/font'.format(self.lexer_.language())
        fdesc = Preferences.Prefs.settings.value(key)
        if fdesc is not None:
            font = QFont(fdesc[0], int(fdesc[1]))
            self.lexer_.setDefaultFont(font)
        self.lexer_.readSettings(Preferences.Prefs.settings, "Scintilla")
        
        # now set the lexer properties
        self.lexer_.initProperties()
        
    def __isPy2File(self):
        """
        Private method to return a flag indicating a Python 2 file.
        
        @return flag indicating a Python 2 file (boolean)
        """
        if self.filetype in ["Python", "Python2"]:
            return True
        
        if self.filetype == "":
            line0 = self.__textEdit.text(0)
            if line0.startswith("#!") and \
               ("python2" in line0 or \
                ("python" in line0 and not "python3" in line0)):
                return True
            
            if self.__curFile is not None:
                exts = []
                for ext in Preferences.getDebugger("PythonExtensions").split():
                    if ext.startswith("."):
                        exts.append(ext)
                    else:
                        exts.append(".{0}".format(ext))
                
                ext = os.path.splitext(self.__curFile)[1]
                if ext in exts:
                    return True
        
        return False
        
    def __styleNeeded(self, position):
        """
        Private slot to handle the need for more styling.
        
        @param position end position, that needs styling (integer)
        """
        self.lexer_.styleText(self.__textEdit.getEndStyled(), position)
    
    def __bindName(self, line0):
        """
        Private method to generate a dummy filename for binding a lexer.
        
        @param line0 first line of text to use in the generation process (string)
        """
        bindName = self.__curFile
        
        if line0.startswith("<?xml"):
            # override extension for XML files
            bindName = "dummy.xml"
        
        # check filetype
        if self.filetype in ["Python", "Python2", "Python3"]:
            bindName = "dummy.py"
        elif self.filetype == "Ruby":
            bindName = "dummy.rb"
        elif self.filetype == "D":
            bindName = "dummy.d"
        elif self.filetype == "Properties":
            bindName = "dummy.ini"
        
        # #! marker detection
        if line0.startswith("#!"):
            if "python3" in line0:
                bindName = "dummy.py"
                self.filetype = "Python3"
            elif "python2" in line0:
                bindName = "dummy.py"
                self.filetype = "Python2"
            elif "python" in line0:
                bindName = "dummy.py"
                self.filetype = "Python2"
            elif ("/bash" in line0 or "/sh" in line0):
                bindName = "dummy.sh"
            elif "ruby" in line0:
                bindName = "dummy.rb"
                self.filetype = "Ruby"
            elif "perl" in line0:
                bindName = "dummy.pl"
            elif "lua" in line0:
                bindName = "dummy.lua"
            elif "dmd" in line0:
                bindName = "dummy.d"
                self.filetype = "D"
        return bindName
    
    ##########################################################
    ## Methods needed for the search functionality
    ##########################################################
    
    def getSRHistory(self, key):
        """
        Public method to get the search or replace history list.
        
        @param key list to return (must be 'search' or 'replace')
        @return the requested history list (list of strings)
        """
        return self.srHistory[key][:]
    
    def textForFind(self):
        """
        Public method to determine the selection or the current word for the next 
        find operation.
        
        @return selection or current word (string)
        """
        if self.__textEdit.hasSelectedText():
            text = self.__textEdit.selectedText()
            if '\r' in text or '\n' in text:
                # the selection contains at least a newline, it is
                # unlikely to be the expression to search for
                return ''
            
            return text
        
        # no selected text, determine the word at the current position
        return self.__getCurrentWord()
    
    def __getWord(self, line, index):
        """
        Private method to get the word at a position.
        
        @param line number of line to look at (int)
        @param index position to look at (int)
        @return the word at that position (string)
        """
        text = self.__textEdit.text(line)
        if self.__textEdit.caseSensitive():
            cs = Qt.CaseSensitive
        else:
            cs = Qt.CaseInsensitive
        wc = self.__textEdit.wordCharacters()
        if wc is None:
            regExp = QRegExp('[^\w_]', cs)
        else:
            wc = re.sub('\w', "", wc)
            regExp = QRegExp('[^\w{0}]'.format(re.escape(wc)), cs)
        start = regExp.lastIndexIn(text, index) + 1
        end = regExp.indexIn(text, index)
        if start == end + 1 and index > 0:
            # we are on a word boundary, try again
            start = regExp.lastIndexIn(text, index - 1) + 1
        if start == -1:
            start = 0
        if end == -1:
            end = len(text)
        if end > start:
            word = text[start:end]
        else:
            word = ''
        return word
    
    def __getCurrentWord(self):
        """
        Private method to get the word at the current position.
        
        @return the word at that current position
        """
        line, index = self.__textEdit.getCursorPosition()
        return self.__getWord(line, index)
    
    def __search(self):
        """
        Private method to handle the search action.
        """
        self.replaceDlg.close()
        self.searchDlg.show(self.textForFind())
    
    def __searchClearMarkers(self):
        """
        Private method to clear the search markers of the active window.
        """
        self.clearSearchIndicators()
    
    def __replace(self):
        """
        Private method to handle the replace action.
        """
        self.searchDlg.close()
        self.replaceDlg.show(self.textForFind())
    
    def activeWindow(self):
        """
        Public method to fulfill the ViewManager interface.
        
        @return reference to the text edit component (QsciScintillaCompat)
        """
        return self.__textEdit
    
    def setSearchIndicator(self, startPos, indicLength):
        """
        Public method to set a search indicator for the given range.
        
        @param startPos start position of the indicator (integer)
        @param indicLength length of the indicator (integer)
        """
        self.__textEdit.setIndicatorRange(self.searchIndicator, startPos, indicLength)
    
    def clearSearchIndicators(self):
        """
        Public method to clear all search indicators.
        """
        self.__textEdit.clearAllIndicators(self.searchIndicator)
        self.__markedText = ""
    
    def __markOccurrences(self):
        """
        Private method to mark all occurrences of the current word.
        """
        word = self.__getCurrentWord()
        if not word:
            self.clearSearchIndicators()
            return
        
        if self.__markedText == word:
            return
        
        self.clearSearchIndicators()
        ok = self.__textEdit.findFirstTarget(word, 
            False, self.__textEdit.caseSensitive(), True, 
            0, 0)
        while ok:
            tgtPos, tgtLen = self.__textEdit.getFoundTarget()
            self.setSearchIndicator(tgtPos, tgtLen)
            ok = self.__textEdit.findNextTarget()
        self.__markedText = word
    
    ##########################################################
    ## Methods exhibiting some QScintilla API methods
    ##########################################################
    
    def setText(self, txt, filetype = None):
        """
        Public method to set the text programatically.
        
        @param txt text to be set (string)
        @param filetype type of the source file (string)
        """
        self.__textEdit.setText(txt)
        
        if filetype is None:
            self.filetype = ""
        else:
            self.filetype = filetype
        
        fileEol = self.__textEdit.detectEolString(txt)
        self.__textEdit.setEolModeByEolString(fileEol)
        
        self.__textEdit.setModified(False)
