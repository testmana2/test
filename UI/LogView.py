# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the log viewer widget and the log widget.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QTextCursor, QTextDocument
from PyQt5.QtWidgets import QTextEdit, QApplication, QMenu, QWidget, \
    QHBoxLayout

from E5Gui.E5Application import e5App

import UI.PixmapCache
import Preferences


class LogViewer(QWidget):
    """
    Class implementing the containing widget for the log viewer.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(LogViewer, self).__init__(parent)
        
        self.setWindowIcon(UI.PixmapCache.getIcon("eric.png"))
        
        self.__logViewer = LogViewerEdit(self)
        from .SearchWidget import SearchWidget
        self.__searchWidget = SearchWidget(self.__logViewer, self)
        self.__searchWidget.hide()
        
        self.__layout = QHBoxLayout(self)
        self.__layout.setContentsMargins(1, 1, 1, 1)
        self.__layout.addWidget(self.__logViewer)
        self.__layout.addWidget(self.__searchWidget)
        
        self.__searchWidget.searchNext.connect(self.__logViewer.searchNext)
        self.__searchWidget.searchPrevious.connect(self.__logViewer.searchPrev)
        self.__logViewer.searchStringFound.connect(
            self.__searchWidget.searchStringFound)
        
    def appendToStdout(self, txt):
        """
        Public slot to appand text to the "stdout" tab.
        
        @param txt text to be appended (string)
        """
        self.__logViewer.appendToStdout(txt)
        
    def appendToStderr(self, txt):
        """
        Public slot to appand text to the "stderr" tab.
        
        @param txt text to be appended (string)
        """
        self.__logViewer.appendToStderr(txt)
        
    def preferencesChanged(self):
        """
        Public slot to handle a change of the preferences.
        """
        self.__logViewer.preferencesChanged()
        
    def showFind(self, txt=""):
        """
        Public method to display the search widget.
        
        @param txt text to be shown in the combo (string)
        """
        self.__searchWidget.showFind(txt)


class LogViewerEdit(QTextEdit):
    """
    Class providing a specialized text edit for displaying logging information.
    
    @signal searchStringFound(found) emitted to indicate the search result
        (boolean)
    """
    searchStringFound = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(LogViewerEdit, self).__init__(parent)
        self.setAcceptRichText(False)
        self.setLineWrapMode(QTextEdit.NoWrap)
        self.setReadOnly(True)
        
        self.__mainWindow = parent
        self.__lastSearch = ()
        
        # create the context menu
        self.__menu = QMenu(self)
        self.__menu.addAction(self.tr('Clear'), self.clear)
        self.__menu.addAction(self.tr('Copy'), self.copy)
        self.__menu.addSeparator()
        self.__menu.addAction(self.tr('Find'), self.__find)
        self.__menu.addSeparator()
        self.__menu.addAction(self.tr('Select All'), self.selectAll)
        self.__menu.addSeparator()
        self.__menu.addAction(self.tr("Configure..."), self.__configure)
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__handleShowContextMenu)
        
        self.cNormalFormat = self.currentCharFormat()
        self.cErrorFormat = self.currentCharFormat()
        self.cErrorFormat.setForeground(
            QBrush(Preferences.getUI("LogStdErrColour")))
        
    def __handleShowContextMenu(self, coord):
        """
        Private slot to show the context menu.
        
        @param coord the position of the mouse pointer (QPoint)
        """
        coord = self.mapToGlobal(coord)
        self.__menu.popup(coord)
        
    def __appendText(self, txt, error=False):
        """
        Private method to append text to the end.
        
        @param txt text to insert (string)
        @param error flag indicating to insert error text (boolean)
        """
        tc = self.textCursor()
        tc.movePosition(QTextCursor.End)
        self.setTextCursor(tc)
        if error:
            self.setCurrentCharFormat(self.cErrorFormat)
        else:
            self.setCurrentCharFormat(self.cNormalFormat)
        self.insertPlainText(txt)
        self.ensureCursorVisible()
        
    def appendToStdout(self, txt):
        """
        Public slot to appand text to the "stdout" tab.
        
        @param txt text to be appended (string)
        """
        self.__appendText(txt, error=False)
        QApplication.processEvents()
        
    def appendToStderr(self, txt):
        """
        Public slot to appand text to the "stderr" tab.
        
        @param txt text to be appended (string)
        """
        self.__appendText(txt, error=True)
        QApplication.processEvents()
        
    def preferencesChanged(self):
        """
        Public slot to handle a change of the preferences.
        """
        self.cErrorFormat.setForeground(
            QBrush(Preferences.getUI("LogStdErrColour")))
        
    def __configure(self):
        """
        Private method to open the configuration dialog.
        """
        e5App().getObject("UserInterface").showPreferences("interfacePage")
        
    def __find(self):
        """
        Private slot to show the find widget.
        """
        txt = self.textCursor().selectedText()
        self.__mainWindow.showFind(txt)
        
    def searchNext(self, txt, caseSensitive, wholeWord):
        """
        Public method to search the next occurrence of the given text.
        
        @param txt text to search for (string)
        @param caseSensitive flag indicating case sensitivity (boolean)
        @param wholeWord flag indicating a search for the whole word (boolean)
        """
        self.__lastSearch = (txt, caseSensitive, wholeWord)
        flags = QTextDocument.FindFlags()
        if caseSensitive:
            flags |= QTextDocument.FindCaseSensitively
        if wholeWord:
            flags |= QTextDocument.FindWholeWords
        ok = self.find(txt, flags)
        self.searchStringFound.emit(ok)
        
    def searchPrev(self, txt, caseSensitive, wholeWord):
        """
        Public method to search the previous occurrence of the given text.
        
        @param txt text to search for (string)
        @param caseSensitive flag indicating case sensitivity (boolean)
        @param wholeWord flag indicating a search for the whole word (boolean)
        """
        self.__lastSearch = (txt, caseSensitive, wholeWord)
        flags = QTextDocument.FindFlags(QTextDocument.FindBackward)
        if caseSensitive:
            flags |= QTextDocument.FindCaseSensitively
        if wholeWord:
            flags |= QTextDocument.FindWholeWords
        ok = self.find(txt, flags)
        self.searchStringFound.emit(ok)
        
    def keyPressEvent(self, evt):
        """
        Protected method handling key press events.
        
        @param evt key press event (QKeyEvent)
        """
        if evt.modifiers() == Qt.ControlModifier:
            if evt.key() == Qt.Key_F:
                self.__find()
                evt.accept()
                return
            elif evt.key() == Qt.Key_C:
                self.copy()
                evt.accept()
                return
            elif evt.key() == Qt.Key_A:
                self.selectAll()
                evt.accept()
                return
        elif evt.modifiers() == Qt.NoModifier:
            if evt.key() == Qt.Key_F3 and self.__lastSearch:
                self.searchNext(*self.__lastSearch)
                evt.accept()
                return
        elif evt.modifiers() == Qt.ShiftModifier and self.__lastSearch:
            if evt.key() == Qt.Key_F3 and self.__lastSearch:
                self.searchPrev(*self.__lastSearch)
                evt.accept()
                return
