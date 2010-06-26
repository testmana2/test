# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a widget to select a symbol in various formats.
"""

import unicodedata
import html.entities

from PyQt4.QtCore import pyqtSlot, pyqtSignal, QAbstractTableModel, QModelIndex, Qt
from PyQt4.QtGui import QWidget, QHeaderView, QAbstractItemView, QColor

from .Ui_SymbolsWidget import Ui_SymbolsWidget

class SymbolsModel(QAbstractTableModel):
    """
    Class implementing the model for the symbols widget.
    """
    def __init__(self, parent = None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        QAbstractTableModel.__init__(self, parent)
        
        self.__headerData = [
            self.trUtf8("Code"), 
            self.trUtf8("Char"), 
            self.trUtf8("Hex"), 
            self.trUtf8("HTML"), 
        ]
        
        self.__unicode = True
    
    def setUnicode(self, u):
        """
        Public method to set the mode of the model.
        
        @param u flag indicating unicode mode (boolean)
        """
        self.__unicode = u
        self.reset()
    
    def headerData(self, section, orientation, role = Qt.DisplayRole):
        """
        Public method to get header data from the model.
        
        @param section section number (integer)
        @param orientation orientation (Qt.Orientation)
        @param role role of the data to retrieve (integer)
        @return requested data
        """
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.__headerData[section]
        
        return QAbstractTableModel.headerData(self, section, orientation, role)
    
    def data(self, index, role = Qt.DisplayRole):
        """
        Public method to get data from the model.
        
        @param index index to get data for (QModelIndex)
        @param role role of the data to retrieve (integer)
        @return requested data
        """
        id = index.row()
        
        if role == Qt.DisplayRole:
            col = index.column()
            if col == 0:
                return str(id)
            elif col == 1:
                return chr(id)
            elif col == 2:
                return "0x{0:04x}".format(id)
            elif col == 3:
                if id in html.entities.codepoint2name:
                    return "&{0};".format(html.entities.codepoint2name[id])
        
        if role == Qt.BackgroundColorRole:
            if index.column() == 0:
                return QColor(Qt.lightGray)
        
        if role == Qt.TextColorRole:
            char = chr(id)
            if self.__isDigit(char):
                return QColor(Qt.darkBlue)
            elif self.__isLetter(char):
                return QColor(Qt.darkGreen)
            elif self.__isMark(char):
                return QColor(Qt.darkRed)
            elif self.__isSymbol(char):
                return QColor(Qt.black)
            elif self.__isPunct(char):
                return QColor(Qt.darkMagenta)
            else:
                return QColor(Qt.darkGray)
        
        if role == Qt.TextAlignmentRole:
            if index.column() in [0, 1, 3]:
                return Qt.AlignHCenter
        
        return None
    
    def columnCount(self, parent):
        """
        Public method to get the number of columns of the model.
        
        @param parent parent index (QModelIndex)
        @return number of columns (integer)
        """
        if parent.column() > 0:
            return 0
        else:
            return len(self.__headerData)
    
    def rowCount(self, parent):
        """
        Public method to get the number of rows of the model.
        
        @param parent parent index (QModelIndex)
        @return number of columns (integer)
        """
        if parent.isValid():
            return 0
        else:
            if self.__unicode:
                return 65536
            else:
                return 256
    
    def __isDigit(self, char):
        """
        Private method to check, if a character is a digit.
        
        @param char character to test (one character string)
        @return flag indicating a digit (boolean)
        """
        return unicodedata.category(char) == "Nd"
    
    def __isLetter(self, char):
        """
        Private method to check, if a character is a letter.
        
        @param char character to test (one character string)
        @return flag indicating a letter (boolean)
        """
        return unicodedata.category(char) in ["Lu", "Ll", "Lt", "Lm", "Lo"]
    
    def __isMark(self, char):
        """
        Private method to check, if a character is a mark character.
        
        @param char character to test (one character string)
        @return flag indicating a mark character (boolean)
        """
        return unicodedata.category(char) in ["Mn", "Mc", "Me"]
    
    def __isSymbol(self, char):
        """
        Private method to check, if a character is a symbol.
        
        @param char character to test (one character string)
        @return flag indicating a symbol (boolean)
        """
        return unicodedata.category(char) in ["Sm", "Sc", "Sk", "So"]
    
    def __isPunct(self, char):
        """
        Private method to check, if a character is a punctuation character.
        
        @param char character to test (one character string)
        @return flag indicating a punctuation character (boolean)
        """
        return unicodedata.category(char) in ["Pc", "Pd", "Ps", "Pe", "Pi", "Pf", "Po"]

class SymbolsWidget(QWidget, Ui_SymbolsWidget):
    """
    Class implementing a widget to select a symbol in various formats.
    
    @signal insertSymbol(str) emitted after the user has selected a symbol
    """
    insertSymbol = pyqtSignal(str)
    
    def __init__(self, parent = None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        QWidget.__init__(self, parent)
        self.setupUi(self)
        
        self.__model = SymbolsModel(self)
        self.symbolsTable.setModel(self.__model)
        self.symbolsTable.horizontalHeader().setResizeMode(QHeaderView.Fixed)
        
        fm = self.fontMetrics()
        em = fm.width("M")
        self.symbolsTable.horizontalHeader().resizeSection(0, em * 5)
        self.symbolsTable.horizontalHeader().resizeSection(1, em * 5)
        self.symbolsTable.horizontalHeader().resizeSection(2, em * 6)
        self.symbolsTable.horizontalHeader().resizeSection(3, em * 8)
        self.symbolsTable.verticalHeader().setDefaultSectionSize(fm.height() + 4)
    
    @pyqtSlot(QModelIndex)
    def on_symbolsTable_activated(self, index):
        """
        Private slot to signal the selection of a symbol.
        
        @param index index of the selected symbol (QModelIndex)
        """
        txt = self.__model.data(index)
        if txt:
            self.insertSymbol.emit(txt)
    
    @pyqtSlot(bool)
    def on_unicodeButton_toggled(self, checked):
        """
        Private slot to switch unicode mode.
        
        @param checked flag indicating that the button is pressed (boolean)
        """
        self.symbolsTable.setUpdatesEnabled(False)
        self.__model.setUnicode(checked)
        self.symbolsTable.setUpdatesEnabled(True)
    
    @pyqtSlot()
    def on_symbolSpinBox_editingFinished(self):
        """
        Private slot to move the table to the entered symbol id.
        """
        id = self.symbolSpinBox.value()
        self.symbolsTable.selectRow(id)
        self.symbolsTable.scrollTo(
            self.__model.index(id, 0), QAbstractItemView.PositionAtCenter)
