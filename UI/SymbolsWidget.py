# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a widget to select a symbol in various formats.
"""

from __future__ import unicode_literals    # __IGNORE_WARNING__

import unicodedata
try:  # Py3
    import html.entities as html_entities
except (ImportError):
    chr = unichr
    import htmlentitydefs as html_entities    # __IGNORE_WARNING__

from PyQt4.QtCore import pyqtSlot, pyqtSignal, QAbstractTableModel, QModelIndex, Qt, \
    qVersion
from PyQt4.QtGui import QWidget, QHeaderView, QAbstractItemView, QColor, \
    QItemSelectionModel

from .Ui_SymbolsWidget import Ui_SymbolsWidget

import UI.PixmapCache
import Preferences


class SymbolsModel(QAbstractTableModel):
    """
    Class implementing the model for the symbols widget.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        super(SymbolsModel, self).__init__(parent)
        
        self.__headerData = [
            self.trUtf8("Code"),
            self.trUtf8("Char"),
            self.trUtf8("Hex"),
            self.trUtf8("HTML"),
            self.trUtf8("Name"),
        ]
        
        self.__tables = (
            # first   last     display name
            (0x0,    0x1f,   self.trUtf8("Control Characters")),
            (0x20,   0x7f,   self.trUtf8("Basic Latin")),
            (0x80,   0x100,  self.trUtf8("Latin-1 Supplement")),
            (0x100,  0x180,  self.trUtf8("Latin Extended A")),
            (0x180,  0x24f,  self.trUtf8("Latin Extended B")),
            (0x250,  0x2af,  self.trUtf8("IPA Extensions")),
            (0x2b0,  0x2ff,  self.trUtf8("Spacing Modifier Letters")),
            (0x300,  0x36f,  self.trUtf8("Combining Diacritical Marks")),
            (0x370,  0x3ff,  self.trUtf8("Greek and Coptic")),
            (0x400,  0x4ff,  self.trUtf8("Cyrillic")),
            (0x500,  0x52f,  self.trUtf8("Cyrillic Supplement")),
            (0x530,  0x58f,  self.trUtf8("Armenian")),
            (0x590,  0x5ff,  self.trUtf8("Hebrew")),
            (0x600,  0x6ff,  self.trUtf8("Arabic")),
            (0x700,  0x74f,  self.trUtf8("Syriac")),
            (0x780,  0x7bf,  self.trUtf8("Thaana")),
            (0x900,  0x97f,  self.trUtf8("Devanagari")),
            (0x980,  0x9ff,  self.trUtf8("Bengali")),
            (0xa00,  0xa7f,  self.trUtf8("Gurmukhi")),
            (0xa80,  0xaff,  self.trUtf8("Gujarati")),
            (0xb00,  0xb7f,  self.trUtf8("Oriya")),
            (0xb80,  0xbff,  self.trUtf8("Tamil")),
            (0xc00,  0xc7f,  self.trUtf8("Telugu")),
            (0xc80,  0xcff,  self.trUtf8("Kannada")),
            (0xd00,  0xd7f,  self.trUtf8("Malayalam")),
            (0xd80,  0xdff,  self.trUtf8("Sinhala")),
            (0xe00,  0xe7f,  self.trUtf8("Thai")),
            (0xe80,  0xeff,  self.trUtf8("Lao")),
            (0xf00,  0xfff,  self.trUtf8("Tibetan")),
            (0x1000, 0x109f, self.trUtf8("Myanmar")),
            (0x10a0, 0x10ff, self.trUtf8("Georgian")),
            (0x1100, 0x11ff, self.trUtf8("Hangul Jamo")),
            (0x1200, 0x137f, self.trUtf8("Ethiopic")),
            (0x13a0, 0x13ff, self.trUtf8("Cherokee")),
            (0x1400, 0x167f, self.trUtf8("Canadian Aboriginal Syllabics")),
            (0x1680, 0x169f, self.trUtf8("Ogham")),
            (0x16a0, 0x16ff, self.trUtf8("Runic")),
            (0x1700, 0x171f, self.trUtf8("Tagalog")),
            (0x1720, 0x173f, self.trUtf8("Hanunoo")),
            (0x1740, 0x175f, self.trUtf8("Buhid")),
            (0x1760, 0x177f, self.trUtf8("Tagbanwa")),
            (0x1780, 0x17ff, self.trUtf8("Khmer")),
            (0x1800, 0x18af, self.trUtf8("Mongolian")),
            (0x1900, 0x194f, self.trUtf8("Limbu")),
            (0x1950, 0x197f, self.trUtf8("Tai Le")),
            (0x19e0, 0x19ff, self.trUtf8("Khmer Symbols")),
            (0x1d00, 0x1d7f, self.trUtf8("Phonetic Extensions")),
            (0x1e00, 0x1eff, self.trUtf8("Latin Extended Additional")),
            (0x1f00, 0x1fff, self.trUtf8("Greek Extended")),
            (0x2000, 0x206f, self.trUtf8("General Punctuation")),
            (0x2070, 0x209f, self.trUtf8("Superscripts and Subscripts")),
            (0x20a0, 0x20cf, self.trUtf8("Currency Symbols")),
            (0x20d0, 0x20ff, self.trUtf8("Combining Diacritical Marks")),
            (0x2100, 0x214f, self.trUtf8("Letterlike Symbols")),
            (0x2150, 0x218f, self.trUtf8("Number Forms")),
            (0x2190, 0x21ff, self.trUtf8("Arcolumns")),
            (0x2200, 0x22ff, self.trUtf8("Mathematical Operators")),
            (0x2300, 0x23ff, self.trUtf8("Miscellaneous Technical")),
            (0x2400, 0x243f, self.trUtf8("Control Pictures")),
            (0x2440, 0x245f, self.trUtf8("Optical Character Recognition")),
            (0x2460, 0x24ff, self.trUtf8("Enclosed Alphanumerics")),
            (0x2500, 0x257f, self.trUtf8("Box Drawing")),
            (0x2580, 0x259f, self.trUtf8("Block Elements")),
            (0x25A0, 0x25ff, self.trUtf8("Geometric Shapes")),
            (0x2600, 0x26ff, self.trUtf8("Miscellaneous Symbols")),
            (0x2700, 0x27bf, self.trUtf8("Dingbats")),
            (0x27c0, 0x27ef, self.trUtf8("Miscellaneous Mathematical Symbols-A")),
            (0x27f0, 0x27ff, self.trUtf8("Supplement Arcolumns-A")),
            (0x2800, 0x28ff, self.trUtf8("Braille Patterns")),
            (0x2900, 0x297f, self.trUtf8("Supplement Arcolumns-B")),
            (0x2980, 0x29ff, self.trUtf8("Miscellaneous Mathematical Symbols-B")),
            (0x2a00, 0x2aff, self.trUtf8("Supplemental Mathematical Operators")),
            (0x2b00, 0x2bff, self.trUtf8("Miscellaneous Symbols and Arcolumns")),
            (0x2e80, 0x2eff, self.trUtf8("CJK Radicals Supplement")),
            (0x2f00, 0x2fdf, self.trUtf8("KangXi Radicals")),
            (0x2ff0, 0x2fff, self.trUtf8("Ideographic Description Chars")),
            (0x3000, 0x303f, self.trUtf8("CJK Symbols and Punctuation")),
            (0x3040, 0x309f, self.trUtf8("Hiragana")),
            (0x30a0, 0x30ff, self.trUtf8("Katakana")),
            (0x3100, 0x312f, self.trUtf8("Bopomofo")),
            (0x3130, 0x318f, self.trUtf8("Hangul Compatibility Jamo")),
            (0x3190, 0x319f, self.trUtf8("Kanbun")),
            (0x31a0, 0x31bf, self.trUtf8("Bopomofo Extended")),
            (0x31f0, 0x31ff, self.trUtf8("Katakana Phonetic Extensions")),
            (0x3200, 0x32ff, self.trUtf8("Enclosed CJK Letters and Months")),
            (0x3300, 0x33ff, self.trUtf8("CJK Compatibility")),
            (0x3400, 0x4db5, self.trUtf8("CJK Unified Ideogr. Ext. A")),
            (0x4dc0, 0x4dff, self.trUtf8("Yijing Hexagram Symbols")),
            (0x4e00, 0x9fbb, self.trUtf8("CJK Unified Ideographs")),
            (0xa000, 0xa48f, self.trUtf8("Yi Syllables")),
            (0xa490, 0xa4cf, self.trUtf8("Yi Radicals")),
            (0xac00, 0xd7a3, self.trUtf8("Hangul Syllables")),
            (0xd800, 0xdb7f, self.trUtf8("High Surrogates")),
            (0xdb80, 0xdbff, self.trUtf8("High Private Use Surrogates")),
            (0xdc00, 0xdfff, self.trUtf8("Low Surrogates")),
            (0xe000, 0xf8ff, self.trUtf8("Private Use")),
            (0xf900, 0xfaff, self.trUtf8("CJK Compatibility Ideographs")),
            (0xfb00, 0xfb4f, self.trUtf8("Alphabetic Presentation Forms")),
            (0xfb50, 0xfdff, self.trUtf8("Arabic Presentation Forms-A")),
            (0xfe00, 0xfe0f, self.trUtf8("Variation Selectors")),
            (0xfe20, 0xfe2f, self.trUtf8("Combining Half Marks")),
            (0xfe30, 0xfe4f, self.trUtf8("CJK Compatibility Forms")),
            (0xfe50, 0xfe6f, self.trUtf8("Small Form Variants")),
            (0xfe70, 0xfefe, self.trUtf8("Arabic Presentation Forms-B")),
            (0xfeff, 0xfeff, self.trUtf8("Specials")),
            (0xff00, 0xffef, self.trUtf8("Half- and Fullwidth Forms")),
            (0xfff0, 0xffff, self.trUtf8("Specials")),
            (0x10300, 0x1032f, self.trUtf8("Old Italic")),
            (0x10330, 0x1034f, self.trUtf8("Gothic")),
            (0x10400, 0x1044f, self.trUtf8("Deseret")),
            (0x1d000, 0x1d0ff, self.trUtf8("Byzantine Musical Symbols")),
            (0x1d100, 0x1d1ff, self.trUtf8("Musical Symbols")),
            (0x1d400, 0x1d7ff, self.trUtf8("Mathematical Alphanumeric Symbols")),
            (0x20000, 0x2a6d6, self.trUtf8("CJK Unified Ideogr. Ext. B")),
            (0x2f800, 0x2fa1f, self.trUtf8("CJK Compatapility Ideogr. Suppl.")),
            (0xe0000, 0xe007f, self.trUtf8("Tags")),
        )
        self.__currentTableIndex = 0
    
    def getTableNames(self):
        """
        Public method to get a list of table names.
        
        @return list of table names (list of strings)
        """
        return [table[2] for table in self.__tables]
    
    def getTableBoundaries(self, index):
        """
        Public method to get the first and last character position
        of the given table.
        
        @param index index of the character table (integer)
        @return first and last character position (integer, integer)
        """
        return self.__tables[index][0], self.__tables[index][1]
    
    def getTableIndex(self):
        """
        Private method to get the current table index.
        
        @return current table index (integer)
        """
        return self.__currentTableIndex
    
    def selectTable(self, index):
        """
        Public method to select the shown character table.
        
        @param index index of the character table (integer)
        """
        self.__currentTableIndex = index
        self.reset()
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
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
    
    def data(self, index, role=Qt.DisplayRole):
        """
        Public method to get data from the model.
        
        @param index index to get data for (QModelIndex)
        @param role role of the data to retrieve (integer)
        @return requested data
        """
        id = self.__tables[self.__currentTableIndex][0] + index.row()
        
        if role == Qt.DisplayRole:
            col = index.column()
            if col == 0:
                return str(id)
            elif col == 1:
                try:
                    return chr(id)
                except ValueError:
                    return chr(65533)
            elif col == 2:
                return "0x{0:04x}".format(id)
            elif col == 3:
                if id in html_entities.codepoint2name:
                    return "&{0};".format(html_entities.codepoint2name[id])
            elif col == 4:
                try:
                    return unicodedata.name(chr(id), '').title()
                except ValueError:
                    return self.trUtf8("not possible: narrow Python build")
        
        if role == Qt.BackgroundColorRole:
            if index.column() == 0:
                return QColor(Qt.lightGray)
        
        if role == Qt.TextColorRole:
            try:
                char = chr(id)
            except ValueError:
                char = chr(65533)
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
            first, last = self.__tables[self.__currentTableIndex][:2]
            return last - first + 1
    
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
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(SymbolsWidget, self).__init__(parent)
        self.setupUi(self)
        
        self.setWindowIcon(UI.PixmapCache.getIcon("eric.png"))
        
        self.__model = SymbolsModel(self)
        self.symbolsTable.setModel(self.__model)
        self.symbolsTable.selectionModel().currentRowChanged.connect(
            self.__currentRowChanged)
        
        if qVersion() >= "5.0.0":
            self.symbolsTable.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        else:
            self.symbolsTable.horizontalHeader().setResizeMode(QHeaderView.Fixed)
        fm = self.fontMetrics()
        em = fm.width("M")
        self.symbolsTable.horizontalHeader().resizeSection(0, em * 5)
        self.symbolsTable.horizontalHeader().resizeSection(1, em * 5)
        self.symbolsTable.horizontalHeader().resizeSection(2, em * 6)
        self.symbolsTable.horizontalHeader().resizeSection(3, em * 8)
        self.symbolsTable.horizontalHeader().resizeSection(4, em * 85)
        self.symbolsTable.verticalHeader().setDefaultSectionSize(fm.height() + 4)
        
        tableIndex = int(Preferences.Prefs.settings.value("Symbols/CurrentTable", 1))
        self.tableCombo.addItems(self.__model.getTableNames())
        self.tableCombo.setCurrentIndex(tableIndex)
        
        index = self.__model.index(
            int(Preferences.Prefs.settings.value("Symbols/Top", 0)),
            0)
        self.symbolsTable.scrollTo(index, QAbstractItemView.PositionAtTop)
        self.symbolsTable.selectionModel().setCurrentIndex(index,
            QItemSelectionModel.SelectCurrent | QItemSelectionModel.Rows)
    
    @pyqtSlot(QModelIndex)
    def on_symbolsTable_activated(self, index):
        """
        Private slot to signal the selection of a symbol.
        
        @param index index of the selected symbol (QModelIndex)
        """
        txt = self.__model.data(index)
        if txt:
            self.insertSymbol.emit(txt)
    
    @pyqtSlot()
    def on_symbolSpinBox_editingFinished(self):
        """
        Private slot to move the table to the entered symbol id.
        """
        id = self.symbolSpinBox.value()
        first, last = self.__model.getTableBoundaries(self.__model.getTableIndex())
        row = id - first
        self.symbolsTable.selectRow(row)
        self.symbolsTable.scrollTo(
            self.__model.index(row, 0), QAbstractItemView.PositionAtCenter)
    
    @pyqtSlot(int)
    def on_tableCombo_currentIndexChanged(self, index):
        """
        Private slot to select the current character table.
        
        @param index index of the character table (integer)
        """
        self.symbolsTable.setUpdatesEnabled(False)
        self.__model.selectTable(index)
        self.symbolsTable.setUpdatesEnabled(True)
        
        first, last = self.__model.getTableBoundaries(index)
        self.symbolSpinBox.setMinimum(first)
        self.symbolSpinBox.setMaximum(last)
        
        Preferences.Prefs.settings.setValue("Symbols/CurrentTable", index)
    
    def __currentRowChanged(self, current, previous):
        """
        Private slot recording the currently selected row.
        
        @param current current index (QModelIndex)
        @param previous previous current index (QModelIndex)
        """
        Preferences.Prefs.settings.setValue("Symbols/Top", current.row())
        self.symbolSpinBox.setValue(int(
            self.__model.data(self.__model.index(current.row(), 0))))
