# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog for entering character classes.
"""

from PyQt4.QtCore import QRegExp
from PyQt4.QtGui import QSizePolicy, QSpacerItem, QWidget, QHBoxLayout, \
    QLineEdit, QPushButton, QDialog, QScrollArea, QComboBox, QVBoxLayout, \
    QRegExpValidator, QLabel

from .Ui_QRegExpWizardCharactersDialog import Ui_QRegExpWizardCharactersDialog


class QRegExpWizardCharactersDialog(QDialog, Ui_QRegExpWizardCharactersDialog):
    """
    Class implementing a dialog for entering character classes.
    """
    RegExpMode = 0
    WildcardMode = 1
    W3CMode = 2
    
    def __init__(self, mode=RegExpMode, parent=None):
        """
        Constructor
        
        @param mode mode of the dialog (one of RegExpMode, WildcardMode,
            W3CMode)
        @param parent parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        self.__mode = mode
        
        if mode == QRegExpWizardCharactersDialog.WildcardMode:
            self.predefinedBox.setEnabled(False)
            self.predefinedBox.hide()
        elif mode == QRegExpWizardCharactersDialog.RegExpMode:
            self.w3cInitialIdentifierCheckBox.hide()
            self.w3cNonInitialIdentifierCheckBox.hide()
            self.w3cNmtokenCheckBox.hide()
            self.w3cNonNmtokenCheckBox.hide()
        elif mode == QRegExpWizardCharactersDialog.W3CMode:
            self.__initCharacterSelectors()
        
        self.comboItems = []
        self.singleComboItems = []      # these are in addition to the above
        self.comboItems.append((self.trUtf8("Normal character"), "-c"))
        if mode == QRegExpWizardCharactersDialog.RegExpMode:
            self.comboItems.append((self.trUtf8(
                "Unicode character in hexadecimal notation"), "-h"))
            self.comboItems.append((self.trUtf8(
                "ASCII/Latin1 character in octal notation"), "-o"))
            self.singleComboItems.append(("---", "-i"))
            self.singleComboItems.append(
                (self.trUtf8("Bell character (\\a)"), "\\a"))
            self.singleComboItems.append(
                (self.trUtf8("Page break (\\f)"), "\\f"))
            self.singleComboItems.append(
                (self.trUtf8("Line feed (\\n)"), "\\n"))
            self.singleComboItems.append(
                (self.trUtf8("Carriage return (\\r)"), "\\r"))
            self.singleComboItems.append(
                (self.trUtf8("Horizontal tabulator (\\t)"), "\\t"))
            self.singleComboItems.append(
                (self.trUtf8("Vertical tabulator (\\v)"), "\\v"))
        elif mode == QRegExpWizardCharactersDialog.W3CMode:
            self.comboItems.append((self.trUtf8(
                "Unicode character in hexadecimal notation"), "-h"))
            self.comboItems.append((self.trUtf8(
                "ASCII/Latin1 character in octal notation"), "-o"))
            self.singleComboItems.append(("---", "-i"))
            self.singleComboItems.append(
                (self.trUtf8("Line feed (\\n)"), "\\n"))
            self.singleComboItems.append(
                (self.trUtf8("Carriage return (\\r)"), "\\r"))
            self.singleComboItems.append(
                (self.trUtf8("Horizontal tabulator (\\t)"), "\\t"))
            self.singleComboItems.append(("---", "-i"))
            self.singleComboItems.append(
                (self.trUtf8("Character Category"), "-ccp"))
            self.singleComboItems.append(
                (self.trUtf8("Character Block"), "-cbp"))
            self.singleComboItems.append(
                (self.trUtf8("Not Character Category"), "-ccn"))
            self.singleComboItems.append(
                (self.trUtf8("Not Character Block"), "-cbn"))
        
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
            # display name                              code
            (self.trUtf8("Letter, Any"),                "L"),
            (self.trUtf8("Letter, Uppercase"),          "Lu"),
            (self.trUtf8("Letter, Lowercase"),          "Ll"),
            (self.trUtf8("Letter, Titlecase"),          "Lt"),
            (self.trUtf8("Letter, Modifier"),           "Lm"),
            (self.trUtf8("Letter, Other"),              "Lo"),
            (self.trUtf8("Mark, Any"),                  "M"),
            (self.trUtf8("Mark, Nonspacing"),           "Mn"),
            (self.trUtf8("Mark, Spacing Combining"),    "Mc"),
            (self.trUtf8("Mark, Enclosing"),            "Me"),
            (self.trUtf8("Number, Any"),                "N"),
            (self.trUtf8("Number, Decimal Digit"),      "Nd"),
            (self.trUtf8("Number, Letter"),             "Nl"),
            (self.trUtf8("Number, Other"),              "No"),
            (self.trUtf8("Punctuation, Any"),           "P"),
            (self.trUtf8("Punctuation, Connector"),     "Pc"),
            (self.trUtf8("Punctuation, Dash"),          "Pd"),
            (self.trUtf8("Punctuation, Open"),          "Ps"),
            (self.trUtf8("Punctuation, Close"),         "Pe"),
            (self.trUtf8("Punctuation, Initial Quote"), "Pi"),
            (self.trUtf8("Punctuation, Final Quote"),   "Pf"),
            (self.trUtf8("Punctuation, Other"),         "Po"),
            (self.trUtf8("Symbol, Any"),                "S"),
            (self.trUtf8("Symbol, Math"),               "Sm"),
            (self.trUtf8("Symbol, Currency"),           "Sc"),
            (self.trUtf8("Symbol, Modifier"),           "Sk"),
            (self.trUtf8("Symbol, Other"),              "So"),
            (self.trUtf8("Separator, Any"),             "Z"),
            (self.trUtf8("Separator, Space"),           "Zs"),
            (self.trUtf8("Separator, Line"),            "Zl"),
            (self.trUtf8("Separator, Paragraph"),       "Zp"),
            (self.trUtf8("Other, Any"),                 "C"),
            (self.trUtf8("Other, Control"),             "Cc"),
            (self.trUtf8("Other, Format"),              "Cf"),
            (self.trUtf8("Other, Private Use"),         "Co"),
            (self.trUtf8("Other, Not Assigned"),        "Cn"),
        )
        
        self.__characterBlocks = (
            (self.trUtf8("Basic Latin"),
             "IsBasicLatin"),
            (self.trUtf8("Latin-1 Supplement"),
             "IsLatin-1Supplement"),
            (self.trUtf8("Latin Extended-A"),
             "IsLatinExtended-A"),
            (self.trUtf8("Latin Extended-B"),
             "IsLatinExtended-B"),
            (self.trUtf8("IPA Extensions"),
             "IsIPAExtensions"),
            (self.trUtf8("Spacing Modifier Letters"),
             "IsSpacingModifierLetters"),
            (self.trUtf8("Combining Diacritical Marks"),
             "IsCombiningDiacriticalMarks"),
            (self.trUtf8("Greek"),
             "IsGreek"),
            (self.trUtf8("Cyrillic"),
             "IsCyrillic"),
            (self.trUtf8("Armenian"),
             "IsArmenian"),
            (self.trUtf8("Hebrew"),
             "IsHebrew"),
            (self.trUtf8("Arabic"),
             "IsArabic"),
            (self.trUtf8("Syriac"),
             "IsSyriac"),
            (self.trUtf8("Thaana"),
             "IsThaana"),
            (self.trUtf8("Devanagari"),
             "IsDevanagari"),
            (self.trUtf8("Bengali"),
             "IsBengali"),
            (self.trUtf8("Gurmukhi"),
             "IsBengali"),
            (self.trUtf8("Gujarati"),
             "IsGujarati"),
            (self.trUtf8("Oriya"),
             "IsOriya"),
            (self.trUtf8("Tamil"),
             "IsTamil"),
            (self.trUtf8("Telugu"),
             "IsTelugu"),
            (self.trUtf8("Kannada"),
             "IsKannada"),
            (self.trUtf8("Malayalam"),
             "IsMalayalam"),
            (self.trUtf8("Sinhala"),
             "IsSinhala"),
            (self.trUtf8("Thai"),
             "IsThai"),
            (self.trUtf8("Lao"),
             "IsLao"),
            (self.trUtf8("Tibetan"),
             "IsTibetan"),
            (self.trUtf8("Myanmar"),
             "IsMyanmar"),
            (self.trUtf8("Georgian"),
             "IsGeorgian"),
            (self.trUtf8("Hangul Jamo"),
             "IsHangulJamo"),
            (self.trUtf8("Ethiopic"),
             "IsEthiopic"),
            (self.trUtf8("Cherokee"),
             "IsCherokee"),
            (self.trUtf8("Unified Canadian Aboriginal Syllabics"),
             "IsUnifiedCanadianAboriginalSyllabics"),
            (self.trUtf8("Ogham"),
             "IsOgham"),
            (self.trUtf8("Runic"),
             "IsRunic"),
            (self.trUtf8("Khmer"),
             "IsKhmer"),
            (self.trUtf8("Mongolian"),
             "IsMongolian"),
            (self.trUtf8("Latin Extended Additional"),
             "IsLatinExtendedAdditional"),
            (self.trUtf8("Greek Extended"),
             "IsGreekExtended"),
            (self.trUtf8("General Punctuation"),
             "IsGeneralPunctuation"),
            (self.trUtf8("Superscripts and Subscripts"),
             "IsSuperscriptsandSubscripts"),
            (self.trUtf8("Currency Symbols"),
             "IsCurrencySymbols"),
            (self.trUtf8("Combining Marks for Symbols"),
             "IsCombiningMarksforSymbols"),
            (self.trUtf8("Letterlike Symbols"),
             "IsLetterlikeSymbols"),
            (self.trUtf8("Number Forms"),
             "IsNumberForms"),
            (self.trUtf8("Arrows"),
             "IsArrows"),
            (self.trUtf8("Mathematical Operators"),
             "IsMathematicalOperators"),
            (self.trUtf8("Miscellaneous Technical"),
             "IsMiscellaneousTechnical"),
            (self.trUtf8("Control Pictures"),
             "IsControlPictures"),
            (self.trUtf8("Optical Character Recognition"),
             "IsOpticalCharacterRecognition"),
            (self.trUtf8("Enclosed Alphanumerics"),
             "IsEnclosedAlphanumerics"),
            (self.trUtf8("Box Drawing"),
             "IsBoxDrawing"),
            (self.trUtf8("Block Elements"),
             "IsBlockElements"),
            (self.trUtf8("Geometric Shapes"),
             "IsGeometricShapes"),
            (self.trUtf8("Miscellaneous Symbols"),
             "IsMiscellaneousSymbols"),
            (self.trUtf8("Dingbats"),
             "IsDingbats"),
            (self.trUtf8("Braille Patterns"),
             "IsBraillePatterns"),
            (self.trUtf8("CJK Radicals Supplement"),
             "IsCJKRadicalsSupplement"),
            (self.trUtf8("KangXi Radicals"),
             "IsKangXiRadicals"),
            (self.trUtf8("Ideographic Description Chars"),
             "IsIdeographicDescriptionChars"),
            (self.trUtf8("CJK Symbols and Punctuation"),
             "IsCJKSymbolsandPunctuation"),
            (self.trUtf8("Hiragana"),
             "IsHiragana"),
            (self.trUtf8("Katakana"),
             "IsKatakana"),
            (self.trUtf8("Bopomofo"),
             "IsBopomofo"),
            (self.trUtf8("Hangul Compatibility Jamo"),
             "IsHangulCompatibilityJamo"),
            (self.trUtf8("Kanbun"),
             "IsKanbun"),
            (self.trUtf8("Bopomofo Extended"),
             "IsBopomofoExtended"),
            (self.trUtf8("Enclosed CJK Letters and Months"),
             "IsEnclosedCJKLettersandMonths"),
            (self.trUtf8("CJK Compatibility"),
             "IsCJKCompatibility"),
            (self.trUtf8("CJK Unified Ideographs Extension A"),
             "IsCJKUnifiedIdeographsExtensionA"),
            (self.trUtf8("CJK Unified Ideographs"),
             "IsCJKUnifiedIdeographs"),
            (self.trUtf8("Yi Syllables"),
             "IsYiSyllables"),
            (self.trUtf8("Yi Radicals"),
             "IsYiRadicals"),
            (self.trUtf8("Hangul Syllables"),
             "IsHangulSyllables"),
            (self.trUtf8("Private Use"),
             "IsPrivateUse"),
            (self.trUtf8("CJK Compatibility Ideographs"),
             "IsCJKCompatibilityIdeographs"),
            (self.trUtf8("Alphabetic Presentation Forms"),
             "IsAlphabeticPresentationForms"),
            (self.trUtf8("Arabic Presentation Forms-A"),
             "IsArabicPresentationForms-A"),
            (self.trUtf8("Combining Half Marks"),
             "IsCombiningHalfMarks"),
            (self.trUtf8("CJK Compatibility Forms"),
             "IsCJKCompatibilityForms"),
            (self.trUtf8("Small Form Variants"),
             "IsSmallFormVariants"),
            (self.trUtf8("Arabic Presentation Forms-B"),
             "IsArabicPresentationForms-B"),
            (self.trUtf8("Halfwidth and Fullwidth Forms"),
             "IsHalfwidthandFullwidthForms"),
            (self.trUtf8("Specials"),
             "IsSpecials"),
            (self.trUtf8("Old Italic"),
             "IsOldItalic"),
            (self.trUtf8("Gothic"),
             "IsGothic"),
            (self.trUtf8("Deseret"),
             "IsDeseret"),
            (self.trUtf8("Byzantine Musical Symbols"),
             "IsByzantineMusicalSymbols"),
            (self.trUtf8("Musical Symbols"),
             "IsMusicalSymbols"),
            (self.trUtf8("Mathematical Alphanumeric Symbols"),
             "IsMathematicalAlphanumericSymbols"),
            (self.trUtf8("CJK Unified Ideographic Extension B"),
             "IsCJKUnifiedIdeographicExtensionB"),
            (self.trUtf8("CJK Compatapility Ideographic Supplement"),
             "IsCJKCompatapilityIdeographicSupplement"),
            (self.trUtf8("Tags"),
             "IsTags"),
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
        
    def __populateW3cCharacterCombo(self, combo, format):
        """
        Private method to populate a W3C character selection combo.
        
        @param combo combo box to be populated (QComboBox)
        @param format format identifier (one of "-ccp", "-ccn", "-cbp", "-cbn")
        """
        combo.clear()
        
        if format in ["-ccp", "-ccn"]:
            comboLen = 0
            for txt, code in self.__characterCategories:
                combo.addItem(txt, code)
                comboLen = max(comboLen, len(txt))
            combo.setMinimumContentsLength(comboLen)
        elif format in ["-cbp", "-cbn"]:
            comboLen = 0
            for txt, code in self.__characterBlocks:
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
        elif format in ["-ccp", "-ccn", "-cbp", "-cbn"]:
            lineedit.setEnabled(False)
            lineedit.hide()
            if combo is not None:
                combo.show()
            self.__populateW3cCharacterCombo(combo, format)
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
        
        if self.__mode in [QRegExpWizardCharactersDialog.RegExpMode,
                           QRegExpWizardCharactersDialog.W3CMode]:
            if format == "-h":
                return "\\x{0}".format(char.lower())
            elif format == "-o":
                return "\\0{0}".format(char)
            elif format in ["-ccp", "-cbp"]:
                return "\\p{{{0}}}".format(char)
            elif format in ["-ccn", "-cbn"]:
                return "\\P{{{0}}}".format(char)
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
        if self.whitespaceCheckBox.isChecked():
            regexp += "\\s"
        if self.nonWhitespaceCheckBox.isChecked():
            regexp += "\\S"
        if self.w3cInitialIdentifierCheckBox.isChecked():
            regexp += "\\i"
        if self.w3cNonInitialIdentifierCheckBox.isChecked():
            regexp += "\\I"
        if self.w3cNmtokenCheckBox.isChecked():
            regexp += "\\c"
        if self.w3cNonNmtokenCheckBox.isChecked():
            regexp += "\\C"
            
        # single characters
        for entrieslist in self.singlesEntries:
            format = entrieslist[0].itemData(entrieslist[0].currentIndex())
            if format in ["-ccp", "-ccn", "-cbp", "-cbn"]:
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
            if (regexp.startswith("\\") and
                regexp.count("\\") == 1 and
                "-" not in regexp) or \
               len(regexp) == 1:
                return regexp
            else:
                return "[{0}]".format(regexp)
        else:
            return ""
