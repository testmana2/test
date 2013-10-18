# -*- coding: utf-8 -*-

# Copyright (c) 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog for entering character classes.
"""

from PyQt4.QtCore import QRegExp
from PyQt4.QtGui import QWidget, QDialog, QVBoxLayout, QHBoxLayout, \
    QScrollArea, QPushButton, QSpacerItem, QSizePolicy, QComboBox, \
    QRegExpValidator, QLineEdit, QLabel

from .Ui_QRegularExpressionWizardCharactersDialog import \
    Ui_QRegularExpressionWizardCharactersDialog


class QRegularExpressionWizardCharactersDialog(
    QDialog, Ui_QRegularExpressionWizardCharactersDialog):
    """
    Class implementing a dialog for entering character classes.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        self.__initCharacterSelectors()
        
        self.comboItems = []
        self.singleComboItems = []      # these are in addition to the above
        self.comboItems.append((self.trUtf8("Normal character"), "-c"))
        self.comboItems.append((self.trUtf8(
            "Unicode character in hexadecimal notation"), "-h"))
        self.comboItems.append((self.trUtf8(
            "ASCII/Latin1 character in octal notation"), "-o"))
        self.singleComboItems.extend([
            ("---", "-i"),
            (self.trUtf8("Bell character (\\a)"), "\\a"),
            (self.trUtf8("Escape character (\\e)"), "\\e"),
            (self.trUtf8("Page break (\\f)"), "\\f"),
            (self.trUtf8("Line feed (\\n)"), "\\n"),
            (self.trUtf8("Carriage return (\\r)"), "\\r"),
            (self.trUtf8("Horizontal tabulator (\\t)"), "\\t"),
            ("---", "-i"),
            (self.trUtf8("Character Category"), "-ccp"),
            (self.trUtf8("Special Character Category"), "-csp"),
            (self.trUtf8("Character Block"), "-cbp"),
            (self.trUtf8("POSIX Named Set"), "-psp"),
            (self.trUtf8("Not Character Category"), "-ccn"),
            (self.trUtf8("Not Character Block"), "-cbn"),
            (self.trUtf8("Not Special Character Category"), "-csn"),
            (self.trUtf8("Not POSIX Named Set"), "-psn"),
        ])
        
        self.charValidator = QRegExpValidator(QRegExp(".{0,1}"), self)
        self.hexValidator = QRegExpValidator(QRegExp("[0-9a-fA-F]{0,4}"), self)
        self.octValidator = QRegExpValidator(QRegExp("[0-3]?[0-7]{0,2}"), self)
        
        # generate dialog part for single characters
        self.singlesBoxLayout = QVBoxLayout(self.singlesBox)
        self.singlesBoxLayout.setObjectName("singlesBoxLayout")
        self.singlesBoxLayout.setSpacing(6)
        self.singlesBoxLayout.setContentsMargins(6, 6, 6, 6)
        self.singlesBox.setLayout(self.singlesBoxLayout)
        self.singlesView = QScrollArea(self.singlesBox)
        self.singlesView.setObjectName("singlesView")
        self.singlesBoxLayout.addWidget(self.singlesView)
        
        self.singlesItemsBox = QWidget(self)
        self.singlesView.setWidget(self.singlesItemsBox)
        self.singlesItemsBox.setObjectName("singlesItemsBox")
        self.singlesItemsBox.setMinimumWidth(1000)
        self.singlesItemsBoxLayout = QVBoxLayout(self.singlesItemsBox)
        self.singlesItemsBoxLayout.setContentsMargins(6, 6, 6, 6)
        self.singlesItemsBoxLayout.setSpacing(6)
        self.singlesItemsBox.setLayout(self.singlesItemsBoxLayout)
        self.singlesEntries = []
        self.__addSinglesLine()
        
        hlayout0 = QHBoxLayout()
        hlayout0.setContentsMargins(0, 0, 0, 0)
        hlayout0.setSpacing(6)
        hlayout0.setObjectName("hlayout0")
        self.moreSinglesButton = QPushButton(
            self.trUtf8("Additional Entries"), self.singlesBox)
        self.moreSinglesButton.setObjectName("moreSinglesButton")
        hlayout0.addWidget(self.moreSinglesButton)
        hspacer0 = QSpacerItem(
            30, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        hlayout0.addItem(hspacer0)
        self.singlesBoxLayout.addLayout(hlayout0)
        self.moreSinglesButton.clicked[()].connect(self.__addSinglesLine)
        
        # generate dialog part for character ranges
        self.rangesBoxLayout = QVBoxLayout(self.rangesBox)
        self.rangesBoxLayout.setObjectName("rangesBoxLayout")
        self.rangesBoxLayout.setSpacing(6)
        self.rangesBoxLayout.setContentsMargins(6, 6, 6, 6)
        self.rangesBox.setLayout(self.rangesBoxLayout)
        self.rangesView = QScrollArea(self.rangesBox)
        self.rangesView.setObjectName("rangesView")
        self.rangesBoxLayout.addWidget(self.rangesView)
        
        self.rangesItemsBox = QWidget(self)
        self.rangesView.setWidget(self.rangesItemsBox)
        self.rangesItemsBox.setObjectName("rangesItemsBox")
        self.rangesItemsBox.setMinimumWidth(1000)
        self.rangesItemsBoxLayout = QVBoxLayout(self.rangesItemsBox)
        self.rangesItemsBoxLayout.setContentsMargins(6, 6, 6, 6)
        self.rangesItemsBoxLayout.setSpacing(6)
        self.rangesItemsBox.setLayout(self.rangesItemsBoxLayout)
        self.rangesEntries = []
        self.__addRangesLine()
        
        hlayout1 = QHBoxLayout()
        hlayout1.setContentsMargins(0, 0, 0, 0)
        hlayout1.setSpacing(6)
        hlayout1.setObjectName("hlayout1")
        self.moreRangesButton = QPushButton(
            self.trUtf8("Additional Entries"), self.rangesBox)
        self.moreSinglesButton.setObjectName("moreRangesButton")
        hlayout1.addWidget(self.moreRangesButton)
        hspacer1 = QSpacerItem(
            30, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        hlayout1.addItem(hspacer1)
        self.rangesBoxLayout.addLayout(hlayout1)
        self.moreRangesButton.clicked[()].connect(self.__addRangesLine)
    
    def __initCharacterSelectors(self):
        """
        Private method to initialize the W3C character selector entries.
        """
        self.__characterCategories = (
            # display name                                  code
            (self.trUtf8("Letter, Any"),                    "L"),
            (self.trUtf8("Letter, Lower case"),             "Ll"),
            (self.trUtf8("Letter, Modifier"),               "Lm"),
            (self.trUtf8("Letter, Other"),                  "Lo"),
            (self.trUtf8("Letter, Title case"),             "Lt"),
            (self.trUtf8("Letter, Upper case"),             "Lu"),
            (self.trUtf8("Letter, Lower, Upper or Title"),  "L&"),
            (self.trUtf8("Mark, Any"),                      "M"),
            (self.trUtf8("Mark, Spacing"),                  "Mc"),
            (self.trUtf8("Mark, Enclosing"),                "Me"),
            (self.trUtf8("Mark, Non-spacing"),              "Mn"),
            (self.trUtf8("Number, Any"),                    "N"),
            (self.trUtf8("Number, Decimal"),                "Nd"),
            (self.trUtf8("Number, Letter"),                 "Nl"),
            (self.trUtf8("Number, Other"),                  "No"),
            (self.trUtf8("Punctuation, Any"),               "P"),
            (self.trUtf8("Punctuation, Connector"),         "Pc"),
            (self.trUtf8("Punctuation, Dash"),              "Pd"),
            (self.trUtf8("Punctuation, Close"),             "Pe"),
            (self.trUtf8("Punctuation, Final"),             "Pf"),
            (self.trUtf8("Punctuation, Initial"),           "Pi"),
            (self.trUtf8("Punctuation, Other"),             "Po"),
            (self.trUtf8("Punctuation, Open"),              "Ps"),
            (self.trUtf8("Symbol, Any"),                    "S"),
            (self.trUtf8("Symbol, Currency"),               "Sc"),
            (self.trUtf8("Symbol, Modifier"),               "Sk"),
            (self.trUtf8("Symbol, Mathematical"),           "Sm"),
            (self.trUtf8("Symbol, Other"),                  "So"),
            (self.trUtf8("Separator, Any"),                 "Z"),
            (self.trUtf8("Separator, Line"),                "Zl"),
            (self.trUtf8("Separator, Paragraph"),           "Zp"),
            (self.trUtf8("Separator, Space"),               "Zs"),
            (self.trUtf8("Other, Any"),                     "C"),
            (self.trUtf8("Other, Control"),                 "Cc"),
            (self.trUtf8("Other, Format"),                  "Cf"),
            (self.trUtf8("Other, Unassigned"),              "Cn"),
            (self.trUtf8("Other, Private Use"),             "Co"),
            (self.trUtf8("Other, Surrogat"),                "Cn"),
        )
        
        self.__specialCharacterCategories = (
            # display name                           code
            (self.trUtf8("Alphanumeric"),            "Xan"),
            (self.trUtf8("POSIX Space"),             "Xps"),
            (self.trUtf8("Perl Space"),              "Xsp"),
            (self.trUtf8("Universal Character"),     "Xuc"),
            (self.trUtf8("Perl Word"),               "Xan"),
        )
        
        self.__characterBlocks = (
            # display name                           code
            (self.trUtf8("Arabic"),                  "Arabic"),
            (self.trUtf8("Armenian"),                "Armenian"),
            (self.trUtf8("Avestan"),                 "Avestan"),
            (self.trUtf8("Balinese"),                "Balinese"),
            (self.trUtf8("Bamum"),                   "Bamum"),
            (self.trUtf8("Batak"),                   "Batak"),
            (self.trUtf8("Bengali"),                 "Bengali"),
            (self.trUtf8("Bopomofo"),                "Bopomofo"),
            (self.trUtf8("Brahmi"),                  "Brahmi"),
            (self.trUtf8("Braille"),                 "Braille"),
            (self.trUtf8("Buginese"),                "Buginese"),
            (self.trUtf8("Buhid"),                   "Buhid"),
            (self.trUtf8("Canadian Aboriginal"),     "Canadian_Aboriginal"),
            (self.trUtf8("Carian"),                  "Carian"),
            (self.trUtf8("Chakma"),                  "Chakma"),
            (self.trUtf8("Cham"),                    "Cham"),
            (self.trUtf8("Cherokee"),                "Cherokee"),
            (self.trUtf8("Common"),                  "Common"),
            (self.trUtf8("Coptic"),                  "Coptic"),
            (self.trUtf8("Cuneiform"),               "Cuneiform"),
            (self.trUtf8("Cypriot"),                 "Cypriot"),
            (self.trUtf8("Cyrillic"),                "Cyrillic"),
            (self.trUtf8("Deseret"),                 "Deseret,"),
            (self.trUtf8("Devanagari"),              "Devanagari"),
            (self.trUtf8("Egyptian Hieroglyphs"),    "Egyptian_Hieroglyphs"),
            (self.trUtf8("Ethiopic"),                "Ethiopic"),
            (self.trUtf8("Georgian"),                "Georgian"),
            (self.trUtf8("Glagolitic"),              "Glagolitic"),
            (self.trUtf8("Gothic"),                  "Gothic"),
            (self.trUtf8("Greek"),                   "Greek"),
            (self.trUtf8("Gujarati"),                "Gujarati"),
            (self.trUtf8("Gurmukhi"),                "Gurmukhi"),
            (self.trUtf8("Han"),                     "Han"),
            (self.trUtf8("Hangul"),                  "Hangul"),
            (self.trUtf8("Hanunoo"),                 "Hanunoo"),
            (self.trUtf8("Hebrew"),                  "Hebrew"),
            (self.trUtf8("Hiragana"),                "Hiragana"),
            (self.trUtf8("Imperial Aramaic"),        "Imperial_Aramaic"),
            (self.trUtf8("Inherited"),               "Inherited"),
            (self.trUtf8("Inscriptional Pahlavi"),   "Inscriptional_Pahlavi"),
            (self.trUtf8("Inscriptional Parthian"),  "Inscriptional_Parthian"),
            (self.trUtf8("Javanese"),                "Javanese"),
            (self.trUtf8("Kaithi"),                  "Kaithi"),
            (self.trUtf8("Kannada"),                 "Kannada"),
            (self.trUtf8("Katakana"),                "Katakana"),
            (self.trUtf8("Kayah Li"),                "Kayah_Li"),
            (self.trUtf8("Kharoshthi"),              "Kharoshthi"),
            (self.trUtf8("Khmer"),                   "Khmer"),
            (self.trUtf8("Lao"),                     "Lao"),
            (self.trUtf8("Latin"),                   "Latin"),
            (self.trUtf8("Lepcha"),                  "Lepcha"),
            (self.trUtf8("Limbu"),                   "Limbu"),
            (self.trUtf8("Linear B"),                "Linear_B"),
            (self.trUtf8("Lisu"),                    "Lisu"),
            (self.trUtf8("Lycian"),                  "Lycian"),
            (self.trUtf8("Lydian"),                  "Lydian"),
            (self.trUtf8("Malayalam"),               "Malayalam"),
            (self.trUtf8("Mandaic"),                 "Mandaic"),
            (self.trUtf8("Meetei Mayek"),            "Meetei_Mayek"),
            (self.trUtf8("Meroitic Cursive"),        "Meroitic_Cursive"),
            (self.trUtf8("Meroitic Hieroglyphs"),    "Meroitic_Hieroglyphs"),
            (self.trUtf8("Miao"),                    "Miao"),
            (self.trUtf8("Mongolian"),               "Mongolian"),
            (self.trUtf8("Myanmar"),                 "Myanmar"),
            (self.trUtf8("New Tai Lue"),             "New_Tai_Lue"),
            (self.trUtf8("N'Ko"),                    "Nko"),
            (self.trUtf8("Ogham"),                   "Ogham"),
            (self.trUtf8("Old Italic"),              "Old_Italic"),
            (self.trUtf8("Old Persian"),             "Old_Persian"),
            (self.trUtf8("Old South Arabian"),       "Old_South_Arabian"),
            (self.trUtf8("Old Turkic"),              "Old_Turkic,"),
            (self.trUtf8("Ol Chiki"),                "Ol_Chiki"),
            (self.trUtf8("Oriya"),                   "Oriya"),
            (self.trUtf8("Osmanya"),                 "Osmanya"),
            (self.trUtf8("Phags-pa"),                "Phags_Pa"),
            (self.trUtf8("Phoenician"),              "Phoenician"),
            (self.trUtf8("Rejang"),                  "Rejang"),
            (self.trUtf8("Runic"),                   "Runic"),
            (self.trUtf8("Samaritan"),               "Samaritan"),
            (self.trUtf8("Saurashtra"),              "Saurashtra"),
            (self.trUtf8("Sharada"),                 "Sharada"),
            (self.trUtf8("Shavian"),                 "Shavian"),
            (self.trUtf8("Sinhala"),                 "Sinhala"),
            (self.trUtf8("Sora Sompeng"),            "Sora_Sompeng"),
            (self.trUtf8("Sundanese"),               "Sundanese"),
            (self.trUtf8("Syloti Nagri"),            "Syloti_Nagri"),
            (self.trUtf8("Syriac"),                  "Syriac"),
            (self.trUtf8("Tagalog"),                 "Tagalog"),
            (self.trUtf8("Tagbanwa"),                "Tagbanwa"),
            (self.trUtf8("Tai Le"),                  "Tai_Le"),
            (self.trUtf8("Tai Tham"),                "Tai_Tham"),
            (self.trUtf8("Tai Viet"),                "Tai_Viet"),
            (self.trUtf8("Takri"),                   "Takri"),
            (self.trUtf8("Tamil"),                   "Tamil"),
            (self.trUtf8("Telugu"),                  "Telugu"),
            (self.trUtf8("Thaana"),                  "Thaana"),
            (self.trUtf8("Thai"),                    "Thai"),
            (self.trUtf8("Tibetan"),                 "Tibetan"),
            (self.trUtf8("Tifinagh"),                "Tifinagh"),
            (self.trUtf8("Ugaritic"),                "Ugaritic"),
            (self.trUtf8("Vai"),                     "Vai"),
            (self.trUtf8("Yi"),                      "Yi"),
        )
        
        self.__posixNamedSets = (
            # display name                                  code
            (self.trUtf8("Alphanumeric"),                   "alnum"),
            (self.trUtf8("Alphabetic"),                     "alpha"),
            (self.trUtf8("ASCII"),                          "ascii"),
            (self.trUtf8("Word Letter"),                    "word"),
            (self.trUtf8("Lower Case Letter"),              "lower"),
            (self.trUtf8("Upper Case Letter"),              "upper"),
            (self.trUtf8("Decimal Digit"),                  "digit"),
            (self.trUtf8("Hexadecimal Digit"),              "xdigit"),
            (self.trUtf8("Space or Tab"),                   "blank"),
            (self.trUtf8("White Space"),                    "space"),
            (self.trUtf8("Printing (excl. space)"),         "graph"),
            (self.trUtf8("Printing (incl. space)"),         "print"),
            (self.trUtf8("Printing (excl. alphanumeric)"),  "punct"),
            (self.trUtf8("Control Character"),              "cntrl"),
        )
    
    def __populateCharTypeCombo(self, combo, isSingle):
        """
        Private method to populate a given character type selection combo box.
        
        @param combo reference to the combo box to be populated (QComboBox)
        @param isSingle flag indicating a singles combo (boolean)
        """
        for txt, value in self.comboItems:
            combo.addItem(txt, value)
        if isSingle:
            for txt, value in self.singleComboItems:
                combo.addItem(txt, value)

    def __addSinglesLine(self):
        """
        Private slot to add a line of entry widgets for single characters.
        """
        hbox = QWidget(self.singlesItemsBox)
        hboxLayout = QHBoxLayout(hbox)
        hboxLayout.setContentsMargins(0, 0, 0, 0)
        hboxLayout.setSpacing(6)
        hbox.setLayout(hboxLayout)
        cb1 = QComboBox(hbox)
        cb1.setEditable(False)
        self.__populateCharTypeCombo(cb1, True)
        hboxLayout.addWidget(cb1)
        le1 = QLineEdit(hbox)
        le1.setValidator(self.charValidator)
        hboxLayout.addWidget(le1)
        cb1a = QComboBox(hbox)
        cb1a.setEditable(False)
        cb1a.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        hboxLayout.addWidget(cb1a)
        cb1a.hide()
        cb2 = QComboBox(hbox)
        cb2.setEditable(False)
        self.__populateCharTypeCombo(cb2, True)
        hboxLayout.addWidget(cb2)
        le2 = QLineEdit(hbox)
        le2.setValidator(self.charValidator)
        hboxLayout.addWidget(le2)
        cb2a = QComboBox(hbox)
        cb2a.setEditable(False)
        cb2a.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        hboxLayout.addWidget(cb2a)
        cb2a.hide()
        self.singlesItemsBoxLayout.addWidget(hbox)
        
        cb1.activated[int].connect(self.__singlesCharTypeSelected)
        cb2.activated[int].connect(self.__singlesCharTypeSelected)
        hbox.show()
        
        self.singlesItemsBox.adjustSize()
        
        self.singlesEntries.append([cb1, le1, cb1a])
        self.singlesEntries.append([cb2, le2, cb2a])
    
    def __addRangesLine(self):
        """
        Private slot to add a line of entry widgets for character ranges.
        """
        hbox = QWidget(self.rangesItemsBox)
        hboxLayout = QHBoxLayout(hbox)
        hboxLayout.setContentsMargins(0, 0, 0, 0)
        hboxLayout.setSpacing(6)
        hbox.setLayout(hboxLayout)
        cb1 = QComboBox(hbox)
        cb1.setEditable(False)
        self.__populateCharTypeCombo(cb1, False)
        hboxLayout.addWidget(cb1)
        l1 = QLabel(self.trUtf8("Between:"), hbox)
        hboxLayout.addWidget(l1)
        le1 = QLineEdit(hbox)
        le1.setValidator(self.charValidator)
        hboxLayout.addWidget(le1)
        l2 = QLabel(self.trUtf8("And:"), hbox)
        hboxLayout.addWidget(l2)
        le2 = QLineEdit(hbox)
        le2.setValidator(self.charValidator)
        hboxLayout.addWidget(le2)
        self.rangesItemsBoxLayout.addWidget(hbox)
        
        cb1.activated[int].connect(self.__rangesCharTypeSelected)
        hbox.show()
        
        self.rangesItemsBox.adjustSize()
        
        self.rangesEntries.append([cb1, le1, le2])
    
    def __populateCharacterCombo(self, combo, format):
        """
        Private method to populate a character selection combo.
        
        @param combo combo box to be populated (QComboBox)
        @param format format identifier (one of "-ccp", "-ccn",
            "-cbp", "-cbn", "-csp", "-csn", "-psp", "-psn")
        """
        combo.clear()
        
        if format in ["-ccp", "-ccn"]:
            items = self.__characterCategories
        elif format in ["-csp", "-csn"]:
            items = self.__specialCharacterCategories
        elif format in ["-cbp", "-cbn"]:
            items = self.__characterBlocks
        elif format in ["-psp", "-psn"]:
            items = self.__posixNamedSets
        
        comboLen = 0
        for txt, code in items:
            combo.addItem(txt, code)
            comboLen = max(comboLen, len(txt))
        combo.setMinimumContentsLength(comboLen)
    
    def __performSelectedAction(self, format, lineedit, combo):
        """
        Private method performing some actions depending on the input.
        
        @param format format of the selected entry (string)
        @param lineedit line edit widget to act on (QLineEdit)
        @param combo combo box widget to act on (QComboBox)
        """
        if format == "-i":
            return
        
        if format in ["-c", "-h", "-o"]:
            lineedit.show()
            lineedit.setEnabled(True)
            if combo is not None:
                combo.hide()
            if format == "-c":
                lineedit.setValidator(self.charValidator)
            elif format == "-h":
                lineedit.setValidator(self.hexValidator)
            elif format == "-o":
                lineedit.setValidator(self.octValidator)
        elif format in ["-ccp", "-ccn", "-cbp", "-cbn", "-csp", "-csn",
                        "-psp", "-psn"]:
            lineedit.setEnabled(False)
            lineedit.hide()
            if combo is not None:
                combo.show()
            self.__populateCharacterCombo(combo, format)
        else:
            lineedit.setEnabled(False)
            lineedit.hide()
            if combo is not None:
                combo.hide()
        lineedit.clear()
    
    def __singlesCharTypeSelected(self, index):
        """
        Private slot to handle the activated(int) signal of the single chars
        combo boxes.
        
        @param index selected list index (integer)
        """
        combo = self.sender()
        for entriesList in self.singlesEntries:
            if combo == entriesList[0]:
                format = combo.itemData(index)
                self.__performSelectedAction(
                    format, entriesList[1], entriesList[2])
                break
    
    def __rangesCharTypeSelected(self, index):
        """
        Private slot to handle the activated(int) signal of the char ranges
        combo boxes.
        
        @param index selected list index (integer)
        """
        combo = self.sender()
        for entriesList in self.rangesEntries:
            if combo == entriesList[0]:
                format = combo.itemData(index)
                self.__performSelectedAction(format, entriesList[1], None)
                self.__performSelectedAction(format, entriesList[2], None)
                break
    
    def __formatCharacter(self, char, format):
        """
        Private method to format the characters entered into the dialog.
        
        @param char character string entered into the dialog (string)
        @param format string giving a special format (-c, -h, -i or -o) or
            the already formatted character (string)
        @return formatted character string (string)
        """
        if format == "-c":
            return char
        elif format == "-i":
            return ""
        
        if format == "-h":
            while len(char) < 2:
                char = "0" + char
            if len(char) > 2:
                return "\\x{{{0}}}".format(char.lower())
            else:
                return "\\x{0}".format(char.lower())
        elif format == "-o":
            while len(char) < 3:
                char = "0" + char
            if len(char) > 3:
                char = char[:3]
            return "\\{0}".format(char)
        elif format in ["-ccp", "-cbp", "-csp"]:
            return "\\p{{{0}}}".format(char)
        elif format in ["-ccn", "-cbn", "-csn"]:
            return "\\P{{{0}}}".format(char)
        elif format == "-psp":
            return "[:{0}:]".format(char)
        elif format == "-psn":
            return "[:^{0}:]".format(char)
        else:
            return format
    
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
        if self.newlineCheckBox.isChecked():
            regexp += "\\R"
        if self.nonNewlineCheckBox.isChecked():
            regexp += "\\N"
        if self.whitespaceCheckBox.isChecked():
            regexp += "\\s"
        if self.nonWhitespaceCheckBox.isChecked():
            regexp += "\\S"
        if self.horizontalWhitespaceCheckBox.isChecked():
            regexp += "\\h"
        if self.nonHorizontalWhitespaceCheckBox.isChecked():
            regexp += "\\H"
        if self.verticalWhitespaceCheckBox.isChecked():
            regexp += "\\v"
        if self.nonVerticalWhitespaceCheckBox.isChecked():
            regexp += "\\V"
        
        # single characters
        for entrieslist in self.singlesEntries:
            format = entrieslist[0].itemData(entrieslist[0].currentIndex())
            if format in ["-ccp", "-ccn", "-cbp", "-cbn", "-csp", "-csn",
                          "-psp", "-psn"]:
                char = entrieslist[2].itemData(entrieslist[2].currentIndex())
            else:
                char = entrieslist[1].text()
            regexp += self.__formatCharacter(char, format)
        
        # character ranges
        for entrieslist in self.rangesEntries:
            if not entrieslist[1].text() or \
               not entrieslist[2].text():
                continue
            format = entrieslist[0].itemData(entrieslist[0].currentIndex())
            char1 = entrieslist[1].text()
            char2 = entrieslist[2].text()
            regexp += "{0}-{1}".format(
                self.__formatCharacter(char1, format),
                self.__formatCharacter(char2, format))
        
        if regexp:
            if (regexp.startswith("\\") and \
                regexp.count("\\") == 1 and \
                "-" not in regexp) or \
               len(regexp) == 1:
                return regexp
            else:
                return "[{0}]".format(regexp)
        else:
            return ""
