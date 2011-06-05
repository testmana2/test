# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog for entering character classes.
"""

from PyQt4.QtCore import QRegExp
from PyQt4.QtGui import QSizePolicy, QSpacerItem, QWidget, QHBoxLayout, QLineEdit, \
    QPushButton, QDialog, QScrollArea, QComboBox, QVBoxLayout, QRegExpValidator, QLabel

from .Ui_QRegExpWizardCharactersDialog import Ui_QRegExpWizardCharactersDialog


class QRegExpWizardCharactersDialog(QDialog, Ui_QRegExpWizardCharactersDialog):
    """
    Class implementing a dialog for entering character classes.
    """
    specialChars = {
        4: "\\a",
        5: "\\f",
        6: "\\n",
        7: "\\r",
        8: "\\t",
        9: "\\v"
    }
    
    predefinedClasses = ["\\s", "\\S", "\\w", "\\W", "\\d", "\\D"]
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent parent widget (QWidget)
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        
        self.comboItems = []
        self.comboItems.append(self.trUtf8("Normal character"))
        self.comboItems.append(self.trUtf8("Unicode character in hexadecimal notation"))
        self.comboItems.append(self.trUtf8("Unicode character in octal notation"))
        self.comboItems.append(self.trUtf8("---"))
        self.comboItems.append(self.trUtf8("Bell character (\\a)"))
        self.comboItems.append(self.trUtf8("Page break (\\f)"))
        self.comboItems.append(self.trUtf8("Line feed (\\n)"))
        self.comboItems.append(self.trUtf8("Carriage return (\\r)"))
        self.comboItems.append(self.trUtf8("Horizontal tabulator (\\t)"))
        self.comboItems.append(self.trUtf8("Vertical tabulator (\\v)"))
        
        self.charValidator = QRegExpValidator(QRegExp(".{0,1}"), self)
        self.hexValidator = QRegExpValidator(QRegExp("[0-9a-fA-F]{0,4}"), self)
        self.octValidator = QRegExpValidator(QRegExp("[0-3]?[0-7]{0,2}"), self)
        
        # generate dialog part for single characters
        self.singlesBoxLayout = QVBoxLayout(self.singlesBox)
        self.singlesBoxLayout.setObjectName("singlesBoxLayout")
        self.singlesBoxLayout.setSpacing(6)
        self.singlesBoxLayout.setMargin(6)
        self.singlesBox.setLayout(self.singlesBoxLayout)
        self.singlesView = QScrollArea(self.singlesBox)
        self.singlesView.setObjectName("singlesView")
        self.singlesBoxLayout.addWidget(self.singlesView)
        
        self.singlesItemsBox = QWidget(self)
        self.singlesView.setWidget(self.singlesItemsBox)
        self.singlesItemsBox.setObjectName("singlesItemsBox")
        self.singlesItemsBoxLayout = QVBoxLayout(self.singlesItemsBox)
        self.singlesItemsBoxLayout.setMargin(6)
        self.singlesItemsBoxLayout.setSpacing(6)
        self.singlesItemsBox.setLayout(self.singlesItemsBoxLayout)
        self.singlesEntries = []
        self.__addSinglesLine()
        
        hlayout0 = QHBoxLayout()
        hlayout0.setMargin(0)
        hlayout0.setSpacing(6)
        hlayout0.setObjectName("hlayout0")
        self.moreSinglesButton = QPushButton(self.trUtf8("Additional Entries"),
            self.singlesBox)
        self.moreSinglesButton.setObjectName("moreSinglesButton")
        hlayout0.addWidget(self.moreSinglesButton)
        hspacer0 = QSpacerItem(30, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        hlayout0.addItem(hspacer0)
        self.singlesBoxLayout.addLayout(hlayout0)
        self.moreSinglesButton.clicked[()].connect(self.__addSinglesLine)
        
        # generate dialog part for character ranges
        self.rangesBoxLayout = QVBoxLayout(self.rangesBox)
        self.rangesBoxLayout.setObjectName("rangesBoxLayout")
        self.rangesBoxLayout.setSpacing(6)
        self.rangesBoxLayout.setMargin(6)
        self.rangesBox.setLayout(self.rangesBoxLayout)
        self.rangesView = QScrollArea(self.rangesBox)
        self.rangesView.setObjectName("rangesView")
        self.rangesBoxLayout.addWidget(self.rangesView)
        
        self.rangesItemsBox = QWidget(self)
        self.rangesView.setWidget(self.rangesItemsBox)
        self.rangesItemsBox.setObjectName("rangesItemsBox")
        self.rangesItemsBoxLayout = QVBoxLayout(self.rangesItemsBox)
        self.rangesItemsBoxLayout.setMargin(6)
        self.rangesItemsBoxLayout.setSpacing(6)
        self.rangesItemsBox.setLayout(self.rangesItemsBoxLayout)
        self.rangesEntries = []
        self.__addRangesLine()
        
        hlayout1 = QHBoxLayout()
        hlayout1.setMargin(0)
        hlayout1.setSpacing(6)
        hlayout1.setObjectName("hlayout1")
        self.moreRangesButton = QPushButton(self.trUtf8("Additional Entries"),
            self.rangesBox)
        self.moreSinglesButton.setObjectName("moreRangesButton")
        hlayout1.addWidget(self.moreRangesButton)
        hspacer1 = QSpacerItem(30, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        hlayout1.addItem(hspacer1)
        self.rangesBoxLayout.addLayout(hlayout1)
        self.moreRangesButton.clicked[()].connect(self.__addRangesLine)
        
    def __addSinglesLine(self):
        """
        Private slot to add a line of entry widgets for single characters.
        """
        hbox = QWidget(self.singlesItemsBox)
        hboxLayout = QHBoxLayout(hbox)
        hboxLayout.setMargin(0)
        hboxLayout.setSpacing(6)
        hbox.setLayout(hboxLayout)
        cb1 = QComboBox(hbox)
        cb1.setEditable(False)
        cb1.addItems(self.comboItems)
        hboxLayout.addWidget(cb1)
        le1 = QLineEdit(hbox)
        le1.setValidator(self.charValidator)
        hboxLayout.addWidget(le1)
        cb2 = QComboBox(hbox)
        cb2.setEditable(False)
        cb2.addItems(self.comboItems)
        hboxLayout.addWidget(cb2)
        le2 = QLineEdit(hbox)
        le2.setValidator(self.charValidator)
        hboxLayout.addWidget(le2)
        self.singlesItemsBoxLayout.addWidget(hbox)
        
        cb1.activated[int].connect(self.__singlesCharTypeSelected)
        cb2.activated[int].connect(self.__singlesCharTypeSelected)
        hbox.show()
        
        self.singlesItemsBox.adjustSize()
        
        self.singlesEntries.append([cb1, le1])
        self.singlesEntries.append([cb2, le2])
        
    def __addRangesLine(self):
        """
        Private slot to add a line of entry widgets for character ranges.
        """
        hbox = QWidget(self.rangesItemsBox)
        hboxLayout = QHBoxLayout(hbox)
        hboxLayout.setMargin(0)
        hboxLayout.setSpacing(6)
        hbox.setLayout(hboxLayout)
        l1 = QLabel(self.trUtf8("Between:"), hbox)
        hboxLayout.addWidget(l1)
        cb1 = QComboBox(hbox)
        cb1.setEditable(False)
        cb1.addItems(self.comboItems)
        hboxLayout.addWidget(cb1)
        le1 = QLineEdit(hbox)
        le1.setValidator(self.charValidator)
        hboxLayout.addWidget(le1)
        l2 = QLabel(self.trUtf8("And:"), hbox)
        hboxLayout.addWidget(l2)
        cb2 = QComboBox(hbox)
        cb2.setEditable(False)
        cb2.addItems(self.comboItems)
        hboxLayout.addWidget(cb2)
        le2 = QLineEdit(hbox)
        le2.setValidator(self.charValidator)
        hboxLayout.addWidget(le2)
        self.rangesItemsBoxLayout.addWidget(hbox)
        
        cb1.activated[int].connect(self.__rangesCharTypeSelected)
        cb2.activated[int].connect(self.__rangesCharTypeSelected)
        hbox.show()
        
        self.rangesItemsBox.adjustSize()
        
        self.rangesEntries.append([cb1, le1, cb2, le2])
        
    def __performSelectedAction(self, index, lineedit):
        """
        Private method performing some actions depending on the input.
        
        @param index selected list index (integer)
        @param lineedit line edit widget to act on (QLineEdit)
        """
        if index < 3:
            lineedit.setEnabled(True)
            if index == 0:
                lineedit.setValidator(self.charValidator)
            elif index == 1:
                lineedit.setValidator(self.hexValidator)
            elif index == 2:
                lineedit.setValidator(self.octValidator)
        elif index > 3:
            lineedit.setEnabled(False)
        lineedit.clear()
        
    def __singlesCharTypeSelected(self, index):
        """
        Private slot to handle the activated(int) signal of the single chars combo boxes.
        
        @param index selected list index (integer)
        """
        combo = self.sender()
        for entriesList in self.singlesEntries:
            if combo == entriesList[0]:
                self.__performSelectedAction(index, entriesList[1])
                break
        
    def __rangesCharTypeSelected(self, index):
        """
        Private slot to handle the activated(int) signal of the char ranges combo boxes.
        
        @param index selected list index (integer)
        """
        combo = self.sender()
        for entriesList in self.rangesEntries:
            if combo == entriesList[0]:
                self.__performSelectedAction(index, entriesList[1])
                break
            elif combo == entriesList[2]:
                self.__performSelectedAction(index, entriesList[3])
                break
        
    def __formatCharacter(self, index, char):
        """
        Private method to format the characters entered into the dialog.
        
        @param index selected list index (integer)
        @param char character string enetered into the dialog (string)
        @return formated character string (string)
        """
        if index == 0:
            return char
        elif index == 1:
            return "\\x{0}".format(char.lower())
        elif index == 2:
            return "\\0{0}".format(char)
        else:
            try:
                return self.specialChars[index]
            except KeyError:
                return ""
        
    def getCharacters(self):
        """
        Public method to return the character string assembled via the dialog.
        
        @return formatted string for character classes (string)
        """
        regexp = ""
        
        # negative character range
        if self.negativeCheckBox.isChecked():
            regexp += "^"
            
        # predefined character ranges
        if self.wordCharCheckBox.isChecked():
            regexp += "\\w"
        if self.nonWordCharCheckBox.isChecked():
            regexp += "\\W"
        if self.digitsCheckBox.isChecked():
            regexp += "\\d"
        if self.nonDigitsCheckBox.isChecked():
            regexp += "\\D"
        if self.whitespaceCheckBox.isChecked():
            regexp += "\\s"
        if self.nonWhitespaceCheckBox.isChecked():
            regexp += "\\S"
            
        # single characters
        for entrieslist in self.singlesEntries:
            index = entrieslist[0].currentIndex()
            char = entrieslist[1].text()
            regexp += self.__formatCharacter(index, char)
        
        # character ranges
        for entrieslist in self.rangesEntries:
            if not entrieslist[1].text() or \
               not entrieslist[3].text():
                continue
            index = entrieslist[0].currentIndex()
            char = entrieslist[1].text()
            regexp += "{0}-".format(self.__formatCharacter(index, char))
            index = entrieslist[2].currentIndex()
            char = entrieslist[3].text()
            regexp += self.__formatCharacter(index, char)
        
        if regexp:
            if len(regexp) == 2 and regexp in self.predefinedClasses:
                return regexp
            else:
                return "[{0}]".format(regexp)
        else:
            return ""
