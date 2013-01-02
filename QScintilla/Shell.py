# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a graphical Python shell.
"""

import sys
import re

from PyQt4.QtCore import QFileInfo, Qt, QEvent
from PyQt4.QtGui import QDialog, QInputDialog, QApplication, QClipboard, QMenu, \
    QPalette, QFont
from PyQt4.Qsci import QsciScintilla

from E5Gui.E5Application import e5App
from E5Gui import E5MessageBox

from . import Lexers
from .QsciScintillaCompat import QsciScintillaCompat

import Preferences
import UI.PixmapCache

from Debugger.DebugClientCapabilities import HasCompleter

from .ShellHistoryDialog import ShellHistoryDialog


class Shell(QsciScintillaCompat):
    """
    Class implementing a graphical Python shell.
    
    A user can enter commands that are executed in the remote
    Python interpreter.
    """
    def __init__(self, dbs, vm, parent=None):
        """
        Constructor
        
        @param dbs reference to the debug server object
        @param vm reference to the viewmanager object
        @param parent parent widget (QWidget)
        """
        super().__init__(parent)
        self.setUtf8(True)
        
        self.vm = vm
        
        self.linesepRegExp = r"\r\n|\n|\r"
        
        self.passive = Preferences.getDebugger("PassiveDbgEnabled")
        if self.passive:
            self.setWindowTitle(self.trUtf8('Shell - Passive'))
        else:
            self.setWindowTitle(self.trUtf8('Shell'))
        
        self.setWhatsThis(self.trUtf8(
            """<b>The Shell Window</b>"""
            """<p>This is simply an interpreter running in a window. The"""
            """ interpreter is the one that is used to run the program being debugged."""
            """ This means that you can execute any command while the program"""
            """ being debugged is running.</p>"""
            """<p>You can use the cursor keys while entering commands. There is also a"""
            """ history of commands that can be recalled using the up and down cursor"""
            """ keys. Pressing the up or down key after some text has been entered will"""
            """ start an incremental search.</p>"""
            """<p>The shell has some special commands. 'reset' kills the shell"""
            """ and starts a new one. 'clear' clears the display of the shell window."""
            """ 'start' is used to switch the shell language and must be followed by"""
            """ a supported language. Supported languages are listed by the 'languages'"""
            """ command. These commands (except 'languages') are available through the"""
            """ context menu as well.</p>"""
            """<p>Pressing the Tab key after some text has been entered will show"""
            """ a list of possible commandline completions. The relevant entry may"""
            """ be selected from this list. If only one entry is available, this will"""
            """ inserted automatically.</p>"""
            """<p>In passive debugging mode the shell is only available after the"""
            """ program to be debugged has connected to the IDE until it has finished."""
            """ This is indicated by a different prompt and by an indication in the"""
            """ window caption.</p>"""
        ))
        
        self.userListActivated.connect(self.__completionListSelected)
        
        self.__showStdOutErr = Preferences.getShell("ShowStdOutErr")
        if self.__showStdOutErr:
            dbs.clientProcessStdout.connect(self.__writeStdOut)
            dbs.clientProcessStderr.connect(self.__writeStdErr)
        dbs.clientOutput.connect(self.__write)
        dbs.clientStatement.connect(self.__clientStatement)
        dbs.clientGone.connect(self.__initialise)
        dbs.clientRawInput.connect(self.__raw_input)
        dbs.clientBanner.connect(self.__writeBanner)
        dbs.clientCompletionList.connect(self.__showCompletions)
        dbs.clientCapabilities.connect(self.__clientCapabilities)
        dbs.clientException.connect(self.__clientError)
        dbs.clientSyntaxError.connect(self.__clientError)
        self.dbs = dbs
        
        # Initialise instance variables.
        self.__initialise()
        self.prline = 0
        self.prcol = 0
        self.inDragDrop = False
        self.lexer_ = None
        self.completionText = ""
        
        # Initialize history
        self.historyLists = {}
        self.maxHistoryEntries = Preferences.getShell("MaxHistoryEntries")
        self.history = []
        self.histidx = -1
        
        self.clientType = ''
        
        # clear QScintilla defined keyboard commands
        # we do our own handling through the view manager
        self.clearAlternateKeys()
        self.clearKeys()
        self.__actionsAdded = False
        
        # Make sure we have prompts.
        if self.passive:
            sys.ps1 = self.trUtf8("Passive >>> ")
        else:
            try:
                sys.ps1
            except AttributeError:
                sys.ps1 = ">>> "
        try:
            sys.ps2
        except AttributeError:
            sys.ps2 = "... "
        
        if self.passive:
            self.__getBanner()
        
        # Create a little language context menu
        self.lmenu = QMenu(self.trUtf8('Start'))
        self.clientLanguages = self.dbs.getSupportedLanguages(shellOnly=True)
        self.clientLanguages.sort()
        for language in self.clientLanguages:
            act = self.lmenu.addAction(language)
            act.setData(language)
        self.lmenu.triggered.connect(self.__startDebugClient)
        
        # Create the history context menu
        self.hmenu = QMenu(self.trUtf8('History'))
        self.hmenu.addAction(self.trUtf8('Select entry'), self.__selectHistory)
        self.hmenu.addAction(self.trUtf8('Show'), self.__showHistory)
        self.hmenu.addAction(self.trUtf8('Clear'), self.__clearHistory)
        
        # Create a little context menu
        self.menu = QMenu(self)
        self.menu.addAction(self.trUtf8('Cut'), self.cut)
        self.menu.addAction(self.trUtf8('Copy'), self.copy)
        self.menu.addAction(self.trUtf8('Paste'), self.paste)
        self.menu.addMenu(self.hmenu)
        self.menu.addSeparator()
        self.menu.addAction(self.trUtf8('Clear'), self.clear)
        self.menu.addAction(self.trUtf8('Reset'), self.__reset)
        self.menu.addAction(self.trUtf8('Reset and Clear'),
            self.__resetAndClear)
        self.menu.addSeparator()
        self.menu.addMenu(self.lmenu)
        self.menu.addSeparator()
        self.menu.addAction(self.trUtf8("Configure..."), self.__configure)
        
        self.__bindLexer()
        self.__setTextDisplay()
        self.__setMargin0()
        
        # set the autocompletion and calltips function
        self.__setAutoCompletion()
        self.__setCallTips()
        
        self.setWindowIcon(UI.PixmapCache.getIcon("eric.png"))
        
        self.incrementalSearchString = ""
        self.incrementalSearchActive = False
        
        self.supportedEditorCommands = {
            QsciScintilla.SCI_LINEDELETE: self.__clearCurrentLine,
            QsciScintilla.SCI_TAB: self.__QScintillaTab,
            QsciScintilla.SCI_NEWLINE: self.__QScintillaNewline,
            
            QsciScintilla.SCI_DELETEBACK: self.__QScintillaDeleteBack,
            QsciScintilla.SCI_CLEAR: self.__QScintillaDelete,
            QsciScintilla.SCI_DELWORDLEFT: self.__QScintillaDeleteWordLeft,
            QsciScintilla.SCI_DELWORDRIGHT: self.__QScintillaDeleteWordRight,
            QsciScintilla.SCI_DELLINELEFT: self.__QScintillaDeleteLineLeft,
            QsciScintilla.SCI_DELLINERIGHT: self.__QScintillaDeleteLineRight,
            
            QsciScintilla.SCI_CHARLEFT: self.__QScintillaCharLeft,
            QsciScintilla.SCI_CHARRIGHT: self.__QScintillaCharRight,
            QsciScintilla.SCI_WORDLEFT: self.__QScintillaWordLeft,
            QsciScintilla.SCI_WORDRIGHT: self.__QScintillaWordRight,
            QsciScintilla.SCI_VCHOME: self.__QScintillaVCHome,
            QsciScintilla.SCI_LINEEND: self.__QScintillaLineEnd,
            QsciScintilla.SCI_LINEUP: self.__QScintillaLineUp,
            QsciScintilla.SCI_LINEDOWN: self.__QScintillaLineDown,
            
            QsciScintilla.SCI_PAGEUP: self.__QScintillaAutoCompletionCommand,
            QsciScintilla.SCI_PAGEDOWN: self.__QScintillaAutoCompletionCommand,
            QsciScintilla.SCI_CANCEL: self.__QScintillaAutoCompletionCommand,
            
            QsciScintilla.SCI_CHARLEFTEXTEND: self.__QScintillaCharLeftExtend,
            QsciScintilla.SCI_CHARRIGHTEXTEND: self.extendSelectionRight,
            QsciScintilla.SCI_WORDLEFTEXTEND: self.__QScintillaWordLeftExtend,
            QsciScintilla.SCI_WORDRIGHTEXTEND: self.extendSelectionWordRight,
            QsciScintilla.SCI_VCHOMEEXTEND: self.__QScintillaVCHomeExtend,
            QsciScintilla.SCI_LINEENDEXTEND: self.extendSelectionToEOL,
        }
        
        self.grabGesture(Qt.PinchGesture)
        
    def closeShell(self):
        """
        Public method to shutdown the shell.
        """
        for key in list(self.historyLists.keys()):
            self.saveHistory(key)
        
    def __bindLexer(self, language='Python3'):
        """
        Private slot to set the lexer.
        
        @param language lexer language to set (string)
        """
        self.language = language
        if Preferences.getShell("SyntaxHighlightingEnabled"):
            self.lexer_ = Lexers.getLexer(self.language, self)
        else:
            self.lexer_ = None
        
        if self.lexer_ is None:
            self.setLexer(None)
            font = Preferences.getShell("MonospacedFont")
            self.monospacedStyles(font)
            return
        
        # get the font for style 0 and set it as the default font
        key = 'Scintilla/{0}/style0/font'.format(self.lexer_.language())
        fdesc = Preferences.Prefs.settings.value(key)
        if fdesc is not None:
            font = QFont(fdesc[0], int(fdesc[1]))
            self.lexer_.setDefaultFont(font)
        self.setLexer(self.lexer_)
        self.lexer_.readSettings(Preferences.Prefs.settings, "Scintilla")
        
        # initialize the lexer APIs settings
        api = self.vm.getAPIsManager().getAPIs(self.language)
        if api is not None:
            api = api.getQsciAPIs()
            if api is not None:
                self.lexer_.setAPIs(api)
        
        self.lexer_.setDefaultColor(self.lexer_.color(0))
        self.lexer_.setDefaultPaper(self.lexer_.paper(0))
        
    def __setMargin0(self):
        """
        Private method to configure margin 0.
        """
        # set the settings for all margins
        self.setMarginsFont(Preferences.getShell("MarginsFont"))
        self.setMarginsForegroundColor(Preferences.getEditorColour("MarginsForeground"))
        self.setMarginsBackgroundColor(Preferences.getEditorColour("MarginsBackground"))
        
        # set margin 0 settings
        linenoMargin = Preferences.getShell("LinenoMargin")
        self.setMarginLineNumbers(0, linenoMargin)
        if linenoMargin:
            self.setMarginWidth(0, ' ' + '8' * Preferences.getShell("LinenoWidth"))
        else:
            self.setMarginWidth(0, 0)
        
        # disable margins 1 and 2
        self.setMarginWidth(1, 0)
        self.setMarginWidth(2, 0)
        
    def __setTextDisplay(self):
        """
        Private method to configure the text display.
        """
        self.setTabWidth(Preferences.getEditor("TabWidth"))
        if Preferences.getEditor("ShowWhitespace"):
            self.setWhitespaceVisibility(QsciScintilla.WsVisible)
            try:
                self.setWhitespaceForegroundColor(
                    Preferences.getEditorColour("WhitespaceForeground"))
                self.setWhitespaceBackgroundColor(
                    Preferences.getEditorColour("WhitespaceBackground"))
                self.setWhitespaceSize(
                    Preferences.getEditor("WhitespaceSize"))
            except AttributeError:
                # QScintilla before 2.5 doesn't support this
                pass
        else:
            self.setWhitespaceVisibility(QsciScintilla.WsInvisible)
        self.setEolVisibility(Preferences.getEditor("ShowEOL"))
        if Preferences.getEditor("BraceHighlighting"):
            self.setBraceMatching(QsciScintilla.SloppyBraceMatch)
        else:
            self.setBraceMatching(QsciScintilla.NoBraceMatch)
        self.setMatchedBraceForegroundColor(
            Preferences.getEditorColour("MatchingBrace"))
        self.setMatchedBraceBackgroundColor(
            Preferences.getEditorColour("MatchingBraceBack"))
        self.setUnmatchedBraceForegroundColor(
            Preferences.getEditorColour("NonmatchingBrace"))
        self.setUnmatchedBraceBackgroundColor(
            Preferences.getEditorColour("NonmatchingBraceBack"))
        if Preferences.getEditor("CustomSelectionColours"):
            self.setSelectionBackgroundColor(
                Preferences.getEditorColour("SelectionBackground"))
        else:
            self.setSelectionBackgroundColor(
                QApplication.palette().color(QPalette.Highlight))
        if Preferences.getEditor("ColourizeSelText"):
            self.resetSelectionForegroundColor()
        elif Preferences.getEditor("CustomSelectionColours"):
            self.setSelectionForegroundColor(
                Preferences.getEditorColour("SelectionForeground"))
        else:
            self.setSelectionForegroundColor(
                QApplication.palette().color(QPalette.HighlightedText))
        self.setSelectionToEol(Preferences.getEditor("ExtendSelectionToEol"))
        self.setCaretForegroundColor(
            Preferences.getEditorColour("CaretForeground"))
        self.setCaretLineBackgroundColor(
            Preferences.getEditorColour("CaretLineBackground"))
        self.setCaretLineVisible(Preferences.getEditor("CaretLineVisible"))
        self.caretWidth = Preferences.getEditor("CaretWidth")
        self.setCaretWidth(self.caretWidth)
        if Preferences.getShell("WrapEnabled"):
            self.setWrapMode(QsciScintilla.WrapWord)
        else:
            self.setWrapMode(QsciScintilla.WrapNone)
        self.useMonospaced = Preferences.getShell("UseMonospacedFont")
        self.__setMonospaced(self.useMonospaced)
        
        self.setCursorFlashTime(QApplication.cursorFlashTime())
        
    def __setMonospaced(self, on):
        """
        Private method to set/reset a monospaced font.
        
        @param on flag to indicate usage of a monospace font (boolean)
        """
        if on:
            f = Preferences.getShell("MonospacedFont")
            self.monospacedStyles(f)
        else:
            if not self.lexer_:
                self.clearStyles()
                self.__setMargin0()
            self.setFont(Preferences.getShell("MonospacedFont"))
        
        self.useMonospaced = on
        
    def __setAutoCompletion(self, language='Python'):
        """
        Private method to configure the autocompletion function.
        
        @param language of the autocompletion set to set (string)
        """
        self.setAutoCompletionCaseSensitivity(
            Preferences.getEditor("AutoCompletionCaseSensitivity"))
        self.setAutoCompletionThreshold(-1)
        
        self.racEnabled = Preferences.getShell("AutoCompletionEnabled")
        
    def __setCallTips(self, language='Python'):
        """
        Private method to configure the calltips function.
        
        @param language of the calltips set to set (string)
        """
        if Preferences.getShell("CallTipsEnabled"):
            self.setCallTipsBackgroundColor(
                Preferences.getEditorColour("CallTipsBackground"))
            self.setCallTipsVisible(Preferences.getEditor("CallTipsVisible"))
            calltipsStyle = Preferences.getEditor("CallTipsStyle")
            if calltipsStyle == QsciScintilla.CallTipsNoContext:
                self.setCallTipsStyle(QsciScintilla.CallTipsNoContext)
            elif calltipsStyle == QsciScintilla.CallTipsNoAutoCompletionContext:
                self.setCallTipsStyle(QsciScintilla.CallTipsNoAutoCompletionContext)
            else:
                self.setCallTipsStyle(QsciScintilla.CallTipsContext)
        else:
            self.setCallTipsStyle(QsciScintilla.CallTipsNone)
        
    def setDebuggerUI(self, ui):
        """
        Public method to set the debugger UI.
        
        @param ui reference to the debugger UI object (DebugUI)
        """
        ui.exceptionInterrupt.connect(self.__writePrompt)
        
    def __initialise(self):
        """
        Private method to get ready for a new remote interpreter.
        """
        self.buff = ""
        self.inContinue = False
        self.inRawMode = False
        self.echoInput = True
        self.clientCapabilities = 0
        self.inCommandExecution = False
        self.interruptCommandExecution = False
        
    def __clientCapabilities(self, cap, clType):
        """
        Private slot to handle the reporting of the clients capabilities.
        
        @param cap client capabilities (integer)
        @param clType type of the debug client (string)
        """
        self.clientCapabilities = cap
        if clType != self.clientType:
            self.clientType = clType
            self.__bindLexer(clType)
            self.__setTextDisplay()
            self.__setMargin0()
            self.__setAutoCompletion(clType)
            self.__setCallTips(clType)
            self.racEnabled = Preferences.getShell("AutoCompletionEnabled") and \
                              (cap & HasCompleter) > 0
            
            if clType not in self.historyLists:
                # load history list
                self.loadHistory(clType)
            self.history = self.historyLists[clType]
            self.histidx = -1
        
    def loadHistory(self, clientType):
        """
        Public method to load the history for the given client type.
        
        @param clientType type of the debug client (string)
        """
        hl = Preferences.Prefs.settings.value("Shell/Histories/" + clientType)
        if hl is not None:
            self.historyLists[clientType] = hl[-self.maxHistoryEntries:]
        else:
            self.historyLists[clientType] = []
        
    def reloadHistory(self):
        """
        Public method to reload the history of the currently selected client type.
        """
        self.loadHistory(self.clientType)
        self.history = self.historyLists[self.clientType]
        self.histidx = -1
        
    def saveHistory(self, clientType):
        """
        Public method to save the history for the given client type.
        
        @param clientType type of the debug client (string)
        """
        if clientType in self.historyLists:
            Preferences.Prefs.settings.setValue(
                "Shell/Histories/" + clientType, self.historyLists[clientType])
        
    def getHistory(self, clientType):
        """
        Public method to get the history for the given client type.
        
        @param clientType type of the debug client (string).
            If it is None, the current history is returned.
        @return reference to the history list (list of strings)
        """
        if clientType is None:
            return self.history
        elif clientType in self.historyLists:
            return self.historyLists[clientType]
        else:
            return []
        
    def __clearHistory(self):
        """
        Private slot to clear the current history.
        """
        self.history = []
        
    def __selectHistory(self):
        """
        Private slot to select a history entry to execute.
        """
        cmd, ok = QInputDialog.getItem(
            self,
            self.trUtf8("Select History"),
            self.trUtf8("Select the history entry to execute (most recent shown last)."),
            self.history,
            0, False)
        if ok:
            self.__insertHistory(cmd)
        
    def __showHistory(self):
        """
        Private slot to show the shell history dialog.
        """
        dlg = ShellHistoryDialog(self.history, self.vm, self)
        if dlg.exec_() == QDialog.Accepted:
            self.historyLists[self.clientType] = dlg.getHistory()
            self.history = self.historyLists[self.clientType]
            self.histidx = -1
        
    def getClientType(self):
        """
        Public slot to get the clients type.
        
        @return client type (string)
        """
        return self.clientType
        
    def __getBanner(self):
        """
        Private method to get the banner for the remote interpreter.
        
        It requests the interpreter version and platform running on the
        debug client side.
        """
        if self.passive:
            self.__writeBanner('', '', '')
        else:
            self.dbs.remoteBanner()
        
    def __writeBanner(self, version, platform, dbgclient):
        """
        Private method to write a banner with info from the debug client.
        
        @param version interpreter version string (string)
        @param platform platform of the remote interpreter (string)
        @param dbgclient debug client variant used (string)
        """
        super().clear()
        if self.passive and not self.dbs.isConnected():
            self.__write(self.trUtf8('Passive Debug Mode'))
            self.__write(self.trUtf8('\nNot connected'))
        else:
            version = version.replace("#", self.trUtf8("No."))
            if platform != "" and dbgclient != "":
                self.__write(self.trUtf8('{0} on {1}, {2}')
                    .format(version, platform, dbgclient))
            else:
                self.__write(version)
        self.__write('\n')
        
        self.__write(sys.ps1)
        
    def __writePrompt(self):
        """
        Private method to write the prompt.
        """
        self.__write(self.inContinue and sys.ps2 or sys.ps1)
        
    def __clientStatement(self, more):
        """
        Private method to handle the response from the debugger client.
        
        @param more flag indicating that more user input is required (boolean)
        """
        if not self.inRawMode:
            self.inContinue = more
            self.__writePrompt()
        self.inCommandExecution = False
        
    def __clientError(self):
        """
        Private method to handle an error in the client.
        """
        self.inCommandExecution = False
        self.interruptCommandExecution = True
        self.inContinue = False
        
    def __getEndPos(self):
        """
        Private method to return the line and column of the last character.
        
        @return tuple of two values (int, int) giving the line and column
        """
        line = self.lines() - 1
        return (line, len(self.text(line)))
        
    def __write(self, s):
        """
        Private method to display some text.
        
        @param s text to be displayed (string)
        """
        line, col = self.__getEndPos()
        self.setCursorPosition(line, col)
        self.insert(s)
        self.prline, self.prcol = self.getCursorPosition()
        self.ensureCursorVisible()
        self.ensureLineVisible(self.prline)
        
    def __writeStdOut(self, s):
        """
        Private method to display some text with StdOut label.
        
        @param s text to be displayed (string)
        """
        self.__write(self.trUtf8("StdOut: {0}").format(s))
        
    def __writeStdErr(self, s):
        """
        Private method to display some text with StdErr label.
        
        @param s text to be displayed (string)
        """
        self.__write(self.trUtf8("StdErr: {0}").format(s))
        
    def __raw_input(self, s, echo):
        """
        Private method to handle raw input.
        
        @param s prompt to be displayed (string)
        @param echo Flag indicating echoing of the input (boolean)
        """
        self.setFocus()
        self.inRawMode = True
        self.echoInput = echo
        self.__write(s)
        line, col = self.__getEndPos()
        self.setCursorPosition(line, col)
        self.prompt = self.text(line)\
                      .replace(sys.ps1, "").replace(sys.ps2, "")
        # move cursor to end of line
        self.moveCursorToEOL()
        
    def paste(self):
        """
        Reimplemented slot to handle the paste action.
        """
        lines = QApplication.clipboard().text()
        self.executeLines(lines)
        
    def __middleMouseButton(self):
        """
        Private method to handle the middle mouse button press.
        """
        lines = QApplication.clipboard().text(QClipboard.Selection)
        self.executeLines(lines)
        
    def executeLines(self, lines):
        """
        Public method to execute a set of lines as multiple commands.
        
        @param lines multiple lines of text to be executed as single
            commands (string)
        """
        for line in lines.splitlines(True):
            if line.endswith("\r\n"):
                fullline = True
                cmd = line[:-2]
            elif line.endswith("\r") or line.endswith("\n"):
                fullline = True
                cmd = line[:-1]
            else:
                fullline = False
            
            self.__insertTextAtEnd(line)
            if fullline:
                self.__executeCommand(cmd)
                if self.interruptCommandExecution:
                    self.__executeCommand("")
                    break
        
    def __clearCurrentLine(self):
        """
        Private method to clear the line containing the cursor.
        """
        line, col = self.getCursorPosition()
        if self.text(line).startswith(sys.ps1):
            col = len(sys.ps1)
        elif self.text(line).startswith(sys.ps2):
            col = len(sys.ps2)
        else:
            col = 0
        self.setCursorPosition(line, col)
        self.deleteLineRight()
        
    def __insertText(self, s):
        """
        Private method to insert some text at the current cursor position.
        
        @param s text to be inserted (string)
        """
        line, col = self.getCursorPosition()
        self.insertAt(s, line, col)
        self.setCursorPosition(line, col + len(s))
        
    def __insertTextAtEnd(self, s):
        """
        Private method to insert some text at the end of the command line.
        
        @param s text to be inserted (string)
        """
        line, col = self.__getEndPos()
        self.setCursorPosition(line, col)
        self.insert(s)
        self.prline, self.prcol = self.getCursorPosition()
        
    def __insertTextNoEcho(self, s):
        """
        Private method to insert some text at the end of the buffer without echoing it.
        
        @param s text to be inserted (string)
        """
        self.buff += s
        self.prline, self.prcol = self.getCursorPosition()
        
    def mousePressEvent(self, event):
        """
        Protected method to handle the mouse press event.
        
        @param event the mouse press event (QMouseEvent)
        """
        self.setFocus()
        if event.button() == Qt.MidButton:
            self.__middleMouseButton()
        else:
            super().mousePressEvent(event)
        
    def wheelEvent(self, evt):
        """
        Protected method to handle wheel events.
        
        @param evt reference to the wheel event (QWheelEvent)
        """
        if evt.modifiers() & Qt.ControlModifier:
            if evt.delta() < 0:
                self.zoomOut()
            else:
                self.zoomIn()
            evt.accept()
            return
        
        super().wheelEvent(evt)
    
    def event(self, evt):
        """
        Protected method handling events.
        
        @param evt reference to the event (QEvent)
        @return flag indicating, if the event was handled (boolean)
        """
        if evt.type() == QEvent.Gesture:
            self.gestureEvent(evt)
            return True
        
        return super().event(evt)
    
    def gestureEvent(self, evt):
        """
        Protected method handling gesture events.
        
        @param evt reference to the gesture event (QGestureEvent
        """
        pinch = evt.gesture(Qt.PinchGesture)
        if pinch:
            if pinch.state() == Qt.GestureStarted:
                zoom = (self.getZoom() + 10) / 10.0
                pinch.setScaleFactor(zoom)
            else:
                zoom = int(pinch.scaleFactor() * 10) - 10
                if zoom <= -9:
                    zoom = -9
                    pinch.setScaleFactor(0.1)
                elif zoom >= 20:
                    zoom = 20
                    pinch.setScaleFactor(3.0)
                self.zoomTo(zoom)
            evt.accept()
    
    def editorCommand(self, cmd):
        """
        Public method to perform an editor command.
        
        @param cmd the scintilla command to be performed
        """
        try:
            self.supportedEditorCommands[cmd]()
        except TypeError:
            self.supportedEditorCommands[cmd](cmd)
        except KeyError:
            pass
        
    def __isCursorOnLastLine(self):
        """
        Private method to check, if the cursor is on the last line.
        """
        cline, ccol = self.getCursorPosition()
        return cline == self.lines() - 1
        
    def keyPressEvent(self, ev):
        """
        Re-implemented to handle the user input a key at a time.
        
        @param ev key event (QKeyEvent)
        """
        txt = ev.text()
        
        # See it is text to insert.
        if len(txt) and txt >= " ":
            if not self.__isCursorOnLastLine():
                line, col = self.__getEndPos()
                self.setCursorPosition(line, col)
                self.prline, self.prcol = self.getCursorPosition()
            if self.echoInput:
                ac = self.isListActive()
                super().keyPressEvent(ev)
                self.incrementalSearchActive = True
                if ac and \
                   self.racEnabled:
                    self.dbs.remoteCompletion(self.completionText + txt)
            else:
                self.__insertTextNoEcho(txt)
        else:
            ev.ignore()
        
    def __QScintillaTab(self, cmd):
        """
        Private method to handle the Tab key.
        
        @param cmd QScintilla command
        """
        if self.isListActive():
            self.SendScintilla(cmd)
        elif self.__isCursorOnLastLine():
            line, index = self.getCursorPosition()
            buf = self.text(line).replace(sys.ps1, "").replace(sys.ps2, "")
            if self.inContinue and not buf[:index - len(sys.ps2)].strip():
                self.SendScintilla(cmd)
            elif self.racEnabled:
                self.dbs.remoteCompletion(buf)
        
    def __QScintillaLeftDeleteCommand(self, method):
        """
        Private method to handle a QScintilla delete command working to the left.
        
        @param method shell method to execute
        """
        if self.__isCursorOnLastLine():
            line, col = self.getCursorPosition()
            db = 0
            ac = self.isListActive()
            oldLength = len(self.text(line))
            
            if self.text(line).startswith(sys.ps1):
                if col > len(sys.ps1):
                    method()
                    db = 1
            elif self.text(line).startswith(sys.ps2):
                if col > len(sys.ps2):
                    method()
                    db = 1
            elif col > 0:
                method()
                db = 1
            if db and ac and self.racEnabled and self.completionText:
                delta = len(self.text(line)) - oldLength
                self.dbs.remoteCompletion(self.completionText[:delta])
        
    def __QScintillaDeleteBack(self):
        """
        Private method to handle the Backspace key.
        """
        self.__QScintillaLeftDeleteCommand(self.deleteBack)
        
    def __QScintillaDeleteWordLeft(self):
        """
        Private method to handle the Delete Word Left command.
        """
        self.__QScintillaLeftDeleteCommand(self.deleteWordLeft)
        
    def __QScintillaDelete(self):
        """
        Private method to handle the delete command.
        """
        if self.__isCursorOnLastLine():
            if self.hasSelectedText():
                lineFrom, indexFrom, lineTo, indexTo = self.getSelection()
                if self.text(lineFrom).startswith(sys.ps1):
                    if indexFrom >= len(sys.ps1):
                        self.delete()
                elif self.text(lineFrom).startswith(sys.ps2):
                    if indexFrom >= len(sys.ps2):
                        self.delete()
                elif indexFrom >= 0:
                    self.delete()
            else:
                self.delete()
        
    def __QScintillaDeleteLineLeft(self):
        """
        Private method to handle the Delete Line Left command.
        """
        if self.__isCursorOnLastLine():
            if self.isListActive():
                self.cancelList()
            
            line, col = self.getCursorPosition()
            if self.text(line).startswith(sys.ps1):
                prompt = sys.ps1
            elif self.text(line).startswith(sys.ps2):
                prompt = sys.ps2
            else:
                prompt = ""
            
            self.deleteLineLeft()
            self.insertAt(prompt, line, 0)
            self.setCursorPosition(line, len(prompt))
        
    def __QScintillaNewline(self, cmd):
        """
        Private method to handle the Return key.
        
        @param cmd QScintilla command
        """
        if self.__isCursorOnLastLine():
            if self.isListActive():
                self.SendScintilla(cmd)
            else:
                self.incrementalSearchString = ""
                self.incrementalSearchActive = False
                line, col = self.__getEndPos()
                self.setCursorPosition(line, col)
                buf = self.text(line).replace(sys.ps1, "").replace(sys.ps2, "")
                self.insert('\n')
                self.__executeCommand(buf)
        
    def __QScintillaLeftCommand(self, method, allLinesAllowed=False):
        """
        Private method to handle a QScintilla command working to the left.
        
        @param method shell method to execute
        @param allLinesAllowed flag indicating that the command may be executed
            on any line (boolean)
        """
        if self.__isCursorOnLastLine() or allLinesAllowed:
            line, col = self.getCursorPosition()
            if self.text(line).startswith(sys.ps1):
                if col > len(sys.ps1):
                    method()
            elif self.text(line).startswith(sys.ps2):
                if col > len(sys.ps2):
                    method()
            elif col > 0:
                method()
        
    def __QScintillaCharLeft(self):
        """
        Private method to handle the Cursor Left command.
        """
        self.__QScintillaLeftCommand(self.moveCursorLeft)
        
    def __QScintillaWordLeft(self):
        """
        Private method to handle the Cursor Word Left command.
        """
        self.__QScintillaLeftCommand(self.moveCursorWordLeft)
        
    def __QScintillaRightCommand(self, method):
        """
        Private method to handle a QScintilla command working to the right.
        
        @param method shell method to execute
        """
        if self.__isCursorOnLastLine():
            method()
        
    def __QScintillaCharRight(self):
        """
        Private method to handle the Cursor Right command.
        """
        self.__QScintillaRightCommand(self.moveCursorRight)
        
    def __QScintillaWordRight(self):
        """
        Private method to handle the Cursor Word Right command.
        """
        self.__QScintillaRightCommand(self.moveCursorWordRight)
        
    def __QScintillaDeleteWordRight(self):
        """
        Private method to handle the Delete Word Right command.
        """
        self.__QScintillaRightCommand(self.deleteWordRight)
        
    def __QScintillaDeleteLineRight(self):
        """
        Private method to handle the Delete Line Right command.
        """
        self.__QScintillaRightCommand(self.deleteLineRight)
        
    def __QScintillaVCHome(self, cmd):
        """
        Private method to handle the Home key.
        
        @param cmd QScintilla command
        """
        if self.isListActive():
            self.SendScintilla(cmd)
        elif self.__isCursorOnLastLine():
            line, col = self.getCursorPosition()
            if self.text(line).startswith(sys.ps1):
                col = len(sys.ps1)
            elif self.text(line).startswith(sys.ps2):
                col = len(sys.ps2)
            else:
                col = 0
            self.setCursorPosition(line, col)
        
    def __QScintillaLineEnd(self, cmd):
        """
        Private method to handle the End key.
        
        @param cmd QScintilla command
        """
        if self.isListActive():
            self.SendScintilla(cmd)
        elif self.__isCursorOnLastLine():
            self.moveCursorToEOL()
        
    def __QScintillaLineUp(self, cmd):
        """
        Private method to handle the Up key.
        
        @param cmd QScintilla command
        """
        if self.isListActive():
            self.SendScintilla(cmd)
        else:
            line, col = self.__getEndPos()
            buf = self.text(line).replace(sys.ps1, "").replace(sys.ps2, "")
            if buf and self.incrementalSearchActive:
                if self.incrementalSearchString:
                    idx = self.__rsearchHistory(self.incrementalSearchString,
                                                self.histidx)
                    if idx >= 0:
                        self.histidx = idx
                        self.__useHistory()
                else:
                    idx = self.__rsearchHistory(buf)
                    if idx >= 0:
                        self.histidx = idx
                        self.incrementalSearchString = buf
                        self.__useHistory()
            else:
                if self.histidx < 0:
                    self.histidx = len(self.history)
                if self.histidx > 0:
                    self.histidx = self.histidx - 1
                    self.__useHistory()
        
    def __QScintillaLineDown(self, cmd):
        """
        Private method to handle the Down key.
        
        @param cmd QScintilla command
        """
        if self.isListActive():
            self.SendScintilla(cmd)
        else:
            line, col = self.__getEndPos()
            buf = self.text(line).replace(sys.ps1, "").replace(sys.ps2, "")
            if buf and self.incrementalSearchActive:
                if self.incrementalSearchString:
                    idx = self.__searchHistory(self.incrementalSearchString, self.histidx)
                    if idx >= 0:
                        self.histidx = idx
                        self.__useHistory()
                else:
                    idx = self.__searchHistory(buf)
                    if idx >= 0:
                        self.histidx = idx
                        self.incrementalSearchString = buf
                        self.__useHistory()
            else:
                if self.histidx >= 0 and self.histidx < len(self.history):
                    self.histidx += 1
                    self.__useHistory()
        
    def __QScintillaCharLeftExtend(self):
        """
        Private method to handle the Extend Selection Left command.
        """
        self.__QScintillaLeftCommand(self.extendSelectionLeft, True)
        
    def __QScintillaWordLeftExtend(self):
        """
        Private method to handle the Extend Selection Left one word command.
        """
        self.__QScintillaLeftCommand(self.extendSelectionWordLeft, True)
        
    def __QScintillaVCHomeExtend(self):
        """
        Private method to handle the Extend Selection to start of line command.
        """
        line, col = self.getCursorPosition()
        if self.text(line).startswith(sys.ps1):
            col = len(sys.ps1)
        elif self.text(line).startswith(sys.ps2):
            col = len(sys.ps2)
        else:
            col = 0
        
        self.extendSelectionToBOL()
        while col > 0:
            self.extendSelectionRight()
            col -= 1
        
    def __QScintillaAutoCompletionCommand(self, cmd):
        """
        Private method to handle a command for autocompletion only.
        
        @param cmd QScintilla command
        """
        if self.isListActive() or self.isCallTipActive():
            self.SendScintilla(cmd)
        
    def __executeCommand(self, cmd):
        """
        Private slot to execute a command.
        
        @param cmd command to be executed by debug client (string)
        """
        if not self.inRawMode:
            self.inCommandExecution = True
            self.interruptCommandExecution = False
            if not cmd:
                cmd = ''
            if len(self.history) == 0 or self.history[-1] != cmd:
                if len(self.history) == self.maxHistoryEntries:
                    del self.history[0]
                self.history.append(cmd)
            self.histidx = -1
            if cmd.startswith('start '):
                if not self.passive:
                    cmdList = cmd.split(None, 1)
                    if len(cmdList) < 2:
                        self.dbs.startClient(False)  # same as reset
                    else:
                        language = cmdList[1]
                        if not language in self.clientLanguages:
                            language = cmdList[1].capitalize()
                            if not language in self.clientLanguages:
                                language = ""
                        if language:
                            self.dbs.startClient(False, language)
                        else:
                            # language not supported or typo
                            self.__write(
                                self.trUtf8('Shell language "{0}" not supported.\n')\
                                    .format(cmdList[1]))
                            self.__clientStatement(False)
                        return
                    cmd = ''
            elif cmd == 'languages':
                s = '{0}\n'.format(', '.join(self.clientLanguages))
                self.__write(s)
                self.__clientStatement(False)
                return
            elif cmd == 'clear':
                # Display the banner.
                self.__getBanner()
                if not self.passive:
                    return
                else:
                    cmd = ''
            elif cmd == 'reset':
                self.dbs.startClient(False)
                if self.passive:
                    return
                else:
                    cmd = ''
            
            self.dbs.remoteStatement(cmd)
            while self.inCommandExecution:
                QApplication.processEvents()
        else:
            if not self.echoInput:
                cmd = self.buff
            self.inRawMode = False
            self.echoInput = True
            if not cmd:
                cmd = ''
            else:
                cmd = cmd.replace(self.prompt, "")
            self.dbs.remoteRawInput(cmd)
        
    def __useHistory(self):
        """
        Private method to display a command from the history.
        """
        if self.histidx < len(self.history):
            cmd = self.history[self.histidx]
        else:
            cmd = ""
            self.incrementalSearchString = ""
            self.incrementalSearchActive = False
        
        self.__insertHistory(cmd)

    def __insertHistory(self, cmd):
        """
        Private method to insert a command selected from the history.
        
        @param cmd history entry to be inserted (string)
        """
        self.setCursorPosition(self.prline, self.prcol)
        self.setSelection(self.prline, self.prcol,\
                          self.prline, self.lineLength(self.prline))
        self.removeSelectedText()
        self.__insertText(cmd)
        
    def __searchHistory(self, txt, startIdx=-1):
        """
        Private method used to search the history.
        
        @param txt text to match at the beginning (string)
        @param startIdx index to start search from (integer)
        @return index of found entry (integer)
        """
        if startIdx == -1:
            idx = 0
        else:
            idx = startIdx + 1
        while idx < len(self.history) and \
              not self.history[idx].startswith(txt):
            idx += 1
        return idx
        
    def __rsearchHistory(self, txt, startIdx=-1):
        """
        Private method used to reverse search the history.
        
        @param txt text to match at the beginning (string)
        @param startIdx index to start search from (integer)
        @return index of found entry (integer)
        """
        if startIdx == -1:
            idx = len(self.history) - 1
        else:
            idx = startIdx - 1
        while idx >= 0 and \
              not self.history[idx].startswith(txt):
            idx -= 1
        return idx
        
    def focusNextPrevChild(self, next):
        """
        Reimplemented to stop Tab moving to the next window.
        
        While the user is entering a multi-line command, the movement to
        the next window by the Tab key being pressed is suppressed.
        
        @param next next window
        @return flag indicating the movement
        """
        if next and self.inContinue:
            return False
        
        return QsciScintillaCompat.focusNextPrevChild(self, next)
        
    def contextMenuEvent(self, ev):
        """
        Reimplemented to show our own context menu.
        
        @param ev context menu event (QContextMenuEvent)
        """
        self.menu.popup(ev.globalPos())
        ev.accept()
        
    def clear(self):
        """
        Public slot to clear the display.
        """
        # Display the banner.
        self.__getBanner()
        
    def __resetAndClear(self):
        """
        Private slot to handle the 'reset and clear' context menu entry.
        """
        self.__reset()
        self.clear()
        
    def __reset(self):
        """
        Private slot to handle the 'reset' context menu entry.
        """
        self.dbs.startClient(False)
        
    def __startDebugClient(self, action):
        """
        Private slot to start a debug client accoding to the action triggered[()].
        
        @param action context menu action that was triggered (QAction)
        """
        language = action.data()
        self.dbs.startClient(False, language)
        
    def handlePreferencesChanged(self):
        """
        Public slot to handle the preferencesChanged signal.
        """
        # rebind the lexer
        self.__bindLexer(self.language)
        self.recolor()
        
        # set margin 0 configuration
        self.__setTextDisplay()
        self.__setMargin0()
        
        # set the autocompletion and calltips function
        self.__setAutoCompletion()
        self.__setCallTips()
        
        # do the history related stuff
        self.maxHistoryEntries = Preferences.getShell("MaxHistoryEntries")
        for key in list(self.historyLists.keys()):
            self.historyLists[key] = \
                self.historyLists[key][-self.maxHistoryEntries:]
        
        # do stdout /stderr stuff
        showStdOutErr = Preferences.getShell("ShowStdOutErr")
        if self.__showStdOutErr != showStdOutErr:
            if showStdOutErr:
                self.dbs.clientProcessStdout.connect(self.__writeStdOut)
                self.dbs.clientProcessStderr.connect(self.__writeStdErr)
            else:
                self.dbs.clientProcessStdout.disconnect(self.__writeStdOut)
                self.dbs.clientProcessStderr.disconnect(self.__writeStdErr)
            self.__showStdOutErr = showStdOutErr
        
    def __showCompletions(self, completions, text):
        """
        Private method to display the possible completions.
        
        @param completions list of possible completions (list of strings)
        @param text text that is about to be completed (string)
        """
        if len(completions) == 0:
            return
        
        if len(completions) > 1:
            completions.sort()
            self.showUserList(1, completions)
            self.completionText = text
        else:
            txt = completions[0]
            if text != "":
                txt = txt.replace(text, "")
            self.__insertText(txt)
            self.completionText = ""
        
    def __completionListSelected(self, id, txt):
        """
        Private slot to handle the selection from the completion list.
        
        @param id the ID of the user list (should be 1) (integer)
        @param txt the selected text (string)
        """
        if id == 1:
            if self.completionText != "":
                txt = txt.replace(self.completionText, "")
            self.__insertText(txt)
            self.completionText = ""
    
    #################################################################
    ## Drag and Drop Support
    #################################################################
    
    def dragEnterEvent(self, event):
        """
        Protected method to handle the drag enter event.
        
        @param event the drag enter event (QDragEnterEvent)
        """
        self.inDragDrop = event.mimeData().hasUrls() or event.mimeData().hasText()
        if self.inDragDrop:
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)
        
    def dragMoveEvent(self, event):
        """
        Protected method to handle the drag move event.
        
        @param event the drag move event (QDragMoveEvent)
        """
        if self.inDragDrop:
            event.accept()
        else:
            super().dragMoveEvent(event)
        
    def dragLeaveEvent(self, event):
        """
        Protected method to handle the drag leave event.
        
        @param event the drag leave event (QDragLeaveEvent)
        """
        if self.inDragDrop:
            self.inDragDrop = False
            event.accept()
        else:
            super().dragLeaveEvent(event)
        
    def dropEvent(self, event):
        """
        Protected method to handle the drop event.
        
        @param event the drop event (QDropEvent)
        """
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                fname = url.toLocalFile()
                if fname:
                    if not QFileInfo(fname).isDir():
                        self.vm.openSourceFile(fname)
                    else:
                        E5MessageBox.information(self,
                            self.trUtf8("Drop Error"),
                            self.trUtf8("""<p><b>{0}</b> is not a file.</p>""")
                                .format(fname))
            event.acceptProposedAction()
        elif event.mimeData().hasText():
            s = event.mimeData().text()
            if s:
                event.acceptProposedAction()
                self.executeLines(s)
            del s
        else:
            super().dropEvent(event)
        
        self.inDragDrop = False
        
    def focusInEvent(self, event):
        """
        Public method called when the shell receives focus.
        
        @param event the event object (QFocusEvent)
        """
        if not self.__actionsAdded:
            self.addActions(self.vm.editorActGrp.actions())
            self.addActions(self.vm.copyActGrp.actions())
            self.addActions(self.vm.viewActGrp.actions())
        
        try:
            self.vm.editActGrp.setEnabled(False)
            self.vm.editorActGrp.setEnabled(True)
            self.vm.copyActGrp.setEnabled(True)
            self.vm.viewActGrp.setEnabled(True)
            self.vm.searchActGrp.setEnabled(False)
        except AttributeError:
            pass
        self.setCaretWidth(self.caretWidth)
        self.setCursorFlashTime(QApplication.cursorFlashTime())
        
        super().focusInEvent(event)
        
    def focusOutEvent(self, event):
        """
        Public method called when the shell loses focus.
        
        @param event the event object (QFocusEvent)
        """
        try:
            self.vm.editorActGrp.setEnabled(False)
        except AttributeError:
            pass
        self.setCaretWidth(0)
        super().focusOutEvent(event)
        
    def insert(self, txt):
        """
        Public slot to insert text at the current cursor position.
        
        The cursor is advanced to the end of the inserted text.
        
        @param txt text to be inserted (string)
        """
        l = len(txt)
        line, col = self.getCursorPosition()
        self.insertAt(txt, line, col)
        if re.search(self.linesepRegExp, txt) is not None:
            line += 1
        self.setCursorPosition(line, col + l)
        
    def __configure(self):
        """
        Private method to open the configuration dialog.
        """
        e5App().getObject("UserInterface").showPreferences("shellPage")
