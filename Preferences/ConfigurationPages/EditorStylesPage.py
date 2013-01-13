# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Editor Styles configuration page.
"""

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QColor, QPalette, QColorDialog
from PyQt4.Qsci import QsciScintilla

from QScintilla.QsciScintillaCompat import QsciScintillaCompat, QSCINTILLA_VERSION

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_EditorStylesPage import Ui_EditorStylesPage

import Preferences


class EditorStylesPage(ConfigurationPageBase, Ui_EditorStylesPage):
    """
    Class implementing the Editor Styles configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super().__init__()
        self.setupUi(self)
        self.setObjectName("EditorStylesPage")
        
        self.foldStyles = [
            QsciScintilla.PlainFoldStyle,
            QsciScintilla.CircledFoldStyle,
            QsciScintilla.BoxedFoldStyle,
            QsciScintilla.CircledTreeFoldStyle,
            QsciScintilla.BoxedTreeFoldStyle,
            QsciScintillaCompat.ArrowFoldStyle,
            QsciScintillaCompat.ArrowTreeFoldStyle,
        ]
        
        self.edgeModes = [
            QsciScintilla.EdgeNone,
            QsciScintilla.EdgeLine,
            QsciScintilla.EdgeBackground
        ]
        
        self.wrapModeComboBox.addItem(self.trUtf8("Disabled"),
            QsciScintilla.WrapNone)
        self.wrapModeComboBox.addItem(self.trUtf8("Word Boundary"),
            QsciScintilla.WrapWord)
        self.wrapModeComboBox.addItem(self.trUtf8("Character Boundary"),
            QsciScintilla.WrapCharacter)
        self.wrapVisualComboBox.addItem(self.trUtf8("No Indicator"),
            QsciScintilla.WrapFlagNone)
        self.wrapVisualComboBox.addItem(self.trUtf8("Indicator by Text"),
            QsciScintilla.WrapFlagByText)
        self.wrapVisualComboBox.addItem(self.trUtf8("Indicator by Margin"),
            QsciScintilla.WrapFlagByBorder)
        if QSCINTILLA_VERSION() >= 0x020700:
            self.wrapVisualComboBox.addItem(
                self.trUtf8("Indicator in Line Number Margin"),
                QsciScintilla.WrapFlagInMargin)
        
        # set initial values
        try:
            self.foldingStyleComboBox.setCurrentIndex(
                self.foldStyles.index(Preferences.getEditor("FoldingStyle")))
        except ValueError:
            self.foldingStyleComboBox.setCurrentIndex(0)
        self.marginsFont = Preferences.getEditorOtherFonts("MarginsFont")
        self.marginsFontSample.setFont(self.marginsFont)
        self.defaultFont = Preferences.getEditorOtherFonts("DefaultFont")
        self.defaultFontSample.setFont(self.defaultFont)
        self.monospacedFont = Preferences.getEditorOtherFonts("MonospacedFont")
        self.monospacedFontSample.setFont(self.monospacedFont)
        self.monospacedCheckBox.setChecked(
            Preferences.getEditor("UseMonospacedFont"))
        self.linenowidthSlider.setValue(
            Preferences.getEditor("LinenoWidth"))
        self.linenoCheckBox.setChecked(
            Preferences.getEditor("LinenoMargin"))
        self.foldingCheckBox.setChecked(
            Preferences.getEditor("FoldingMargin"))
        self.unifiedMarginsCheckBox.setChecked(
            Preferences.getEditor("UnifiedMargins"))
        
        self.caretlineVisibleCheckBox.setChecked(
            Preferences.getEditor("CaretLineVisible"))
        self.caretWidthSpinBox.setValue(
            Preferences.getEditor("CaretWidth"))
        self.colourizeSelTextCheckBox.setChecked(
            Preferences.getEditor("ColourizeSelText"))
        self.customSelColourCheckBox.setChecked(
            Preferences.getEditor("CustomSelectionColours"))
        self.extentSelEolCheckBox.setChecked(
            Preferences.getEditor("ExtendSelectionToEol"))
        
        self.initColour("CaretForeground", self.caretForegroundButton,
            Preferences.getEditorColour)
        self.initColour("CaretLineBackground", self.caretlineBackgroundButton,
            Preferences.getEditorColour, hasAlpha=True)
        self.initColour("SelectionForeground", self.selectionForegroundButton,
            Preferences.getEditorColour)
        self.initColour("SelectionBackground", self.selectionBackgroundButton,
            Preferences.getEditorColour, hasAlpha=True)
        self.initColour("CurrentMarker", self.currentLineMarkerButton,
            Preferences.getEditorColour, hasAlpha=True)
        self.initColour("ErrorMarker", self.errorMarkerButton,
            Preferences.getEditorColour, hasAlpha=True)
        self.initColour("MarginsForeground", self.marginsForegroundButton,
            Preferences.getEditorColour)
        self.initColour("MarginsBackground", self.marginsBackgroundButton,
            Preferences.getEditorColour)
        self.initColour("FoldmarginBackground", self.foldmarginBackgroundButton,
            Preferences.getEditorColour)
        self.initColour("FoldMarkersForeground", self.foldmarkersForegroundButton,
            Preferences.getEditorColour)
        self.initColour("FoldMarkersBackground", self.foldmarkersBackgroundButton,
            Preferences.getEditorColour)
        
        self.editorColours = {}
        self.editorColours["AnnotationsWarningForeground"] = \
            QColor(Preferences.getEditorColour("AnnotationsWarningForeground"))
        self.editorColours["AnnotationsWarningBackground"] = \
            QColor(Preferences.getEditorColour("AnnotationsWarningBackground"))
        self.editorColours["AnnotationsErrorForeground"] = \
            QColor(Preferences.getEditorColour("AnnotationsErrorForeground"))
        self.editorColours["AnnotationsErrorBackground"] = \
            QColor(Preferences.getEditorColour("AnnotationsErrorBackground"))
        
        self.eolCheckBox.setChecked(Preferences.getEditor("ShowEOL"))
        self.wrapModeComboBox.setCurrentIndex(self.wrapModeComboBox.findData(
            Preferences.getEditor("WrapLongLinesMode")))
        self.wrapVisualComboBox.setCurrentIndex(self.wrapVisualComboBox.findData(
            Preferences.getEditor("WrapVisualFlag")))
        
        self.edgeModeCombo.setCurrentIndex(
            self.edgeModes.index(Preferences.getEditor("EdgeMode")))
        self.edgeLineColumnSlider.setValue(
            Preferences.getEditor("EdgeColumn"))
        self.initColour("Edge", self.edgeBackgroundColorButton,
            Preferences.getEditorColour)
        
        self.bracehighlightingCheckBox.setChecked(
            Preferences.getEditor("BraceHighlighting"))
        self.initColour("MatchingBrace", self.matchingBracesButton,
            Preferences.getEditorColour)
        self.initColour("MatchingBraceBack", self.matchingBracesBackButton,
            Preferences.getEditorColour)
        self.initColour("NonmatchingBrace", self.nonmatchingBracesButton,
            Preferences.getEditorColour)
        self.initColour("NonmatchingBraceBack", self.nonmatchingBracesBackButton,
            Preferences.getEditorColour)
        
        self.zoomfactorSlider.setValue(
            Preferences.getEditor("ZoomFactor"))
        
        self.whitespaceCheckBox.setChecked(
            Preferences.getEditor("ShowWhitespace"))
        self.whitespaceSizeSpinBox.setValue(
            Preferences.getEditor("WhitespaceSize"))
        self.initColour("WhitespaceForeground", self.whitespaceForegroundButton,
            Preferences.getEditorColour)
        self.initColour("WhitespaceBackground", self.whitespaceBackgroundButton,
            Preferences.getEditorColour)
        if not hasattr(QsciScintilla, "setWhitespaceForegroundColor"):
            self.whitespaceSizeSpinBox.setEnabled(False)
            self.whitespaceForegroundButton.setEnabled(False)
            self.whitespaceBackgroundButton.setEnabled(False)
        
        self.miniMenuCheckBox.setChecked(
            Preferences.getEditor("MiniContextMenu"))
        
        self.enableAnnotationsCheckBox.setChecked(
            Preferences.getEditor("AnnotationsEnabled"))
        
        self.editAreaOverrideCheckBox.setChecked(
            Preferences.getEditor("OverrideEditAreaColours"))
        self.initColour("EditAreaForeground", self.editAreaForegroundButton,
            Preferences.getEditorColour)
        self.initColour("EditAreaBackground", self.editAreaBackgroundButton,
            Preferences.getEditorColour)
        
        self.enableChangeTraceCheckBox.setChecked(
            Preferences.getEditor("OnlineChangeTrace"))
        self.changeTraceTimeoutSpinBox.setValue(
            Preferences.getEditor("OnlineChangeTraceInterval"))
        self.initColour("OnlineChangeTraceMarkerUnsaved",
            self.changeMarkerUnsavedColorButton,
            Preferences.getEditorColour)
        self.initColour("OnlineChangeTraceMarkerSaved",
            self.changeMarkerSavedColorButton,
            Preferences.getEditorColour)
    
    def save(self):
        """
        Public slot to save the Editor Styles configuration.
        """
        Preferences.setEditor("FoldingStyle",
            self.foldStyles[self.foldingStyleComboBox.currentIndex()])
        Preferences.setEditorOtherFonts("MarginsFont", self.marginsFont)
        Preferences.setEditorOtherFonts("DefaultFont", self.defaultFont)
        Preferences.setEditorOtherFonts("MonospacedFont", self.monospacedFont)
        Preferences.setEditor("UseMonospacedFont",
            self.monospacedCheckBox.isChecked())
        
        Preferences.setEditor("LinenoWidth",
            self.linenowidthSlider.value())
        Preferences.setEditor("LinenoMargin",
            self.linenoCheckBox.isChecked())
        Preferences.setEditor("FoldingMargin",
            self.foldingCheckBox.isChecked())
        Preferences.setEditor("UnifiedMargins",
            self.unifiedMarginsCheckBox.isChecked())
        
        Preferences.setEditor("CaretLineVisible",
            self.caretlineVisibleCheckBox.isChecked())
        Preferences.setEditor("ColourizeSelText",
            self.colourizeSelTextCheckBox.isChecked())
        Preferences.setEditor("CustomSelectionColours",
            self.customSelColourCheckBox.isChecked())
        Preferences.setEditor("ExtendSelectionToEol",
            self.extentSelEolCheckBox.isChecked())
        
        Preferences.setEditor("CaretWidth",
            self.caretWidthSpinBox.value())
        
        Preferences.setEditor("ShowEOL",
            self.eolCheckBox.isChecked())
        Preferences.setEditor("WrapLongLinesMode",
            self.wrapModeComboBox.itemData(self.wrapModeComboBox.currentIndex()))
        Preferences.setEditor("WrapVisualFlag",
            self.wrapVisualComboBox.itemData(self.wrapVisualComboBox.currentIndex()))
        Preferences.setEditor("EdgeMode",
            self.edgeModes[self.edgeModeCombo.currentIndex()])
        Preferences.setEditor("EdgeColumn",
            self.edgeLineColumnSlider.value())
        
        Preferences.setEditor("BraceHighlighting",
            self.bracehighlightingCheckBox.isChecked())
        
        Preferences.setEditor("ZoomFactor",
            self.zoomfactorSlider.value())
        
        Preferences.setEditor("ShowWhitespace",
            self.whitespaceCheckBox.isChecked())
        Preferences.setEditor("WhitespaceSize",
            self.whitespaceSizeSpinBox.value())
        
        Preferences.setEditor("MiniContextMenu",
            self.miniMenuCheckBox.isChecked())
        
        Preferences.setEditor("AnnotationsEnabled",
            self.enableAnnotationsCheckBox.isChecked())
        
        Preferences.setEditor("OverrideEditAreaColours",
            self.editAreaOverrideCheckBox.isChecked())
        
        Preferences.setEditor("OnlineChangeTrace",
            self.enableChangeTraceCheckBox.isChecked())
        Preferences.setEditor("OnlineChangeTraceInterval",
            self.changeTraceTimeoutSpinBox.value())
        
        self.saveColours(Preferences.setEditorColour)
        for key in list(self.editorColours.keys()):
            Preferences.setEditorColour(key, self.editorColours[key])
        
    @pyqtSlot()
    def on_linenumbersFontButton_clicked(self):
        """
        Private method used to select the font for the editor margins.
        """
        self.marginsFont = self.selectFont(self.marginsFontSample, self.marginsFont)
        
    @pyqtSlot()
    def on_defaultFontButton_clicked(self):
        """
        Private method used to select the default font for the editor.
        """
        self.defaultFont = self.selectFont(self.defaultFontSample, self.defaultFont)
        
    @pyqtSlot()
    def on_monospacedFontButton_clicked(self):
        """
        Private method used to select the font to be used as the monospaced font.
        """
        self.monospacedFont = \
            self.selectFont(self.monospacedFontSample, self.monospacedFont)
        
    def polishPage(self):
        """
        Public slot to perform some polishing actions.
        """
        self.marginsFontSample.setFont(self.marginsFont)
        self.defaultFontSample.setFont(self.defaultFont)
        self.monospacedFontSample.setFont(self.monospacedFont)
        
        pl = self.annotationsWarningSample.palette()
        pl.setColor(QPalette.Text, self.editorColours["AnnotationsWarningForeground"])
        pl.setColor(QPalette.Base, self.editorColours["AnnotationsWarningBackground"])
        self.annotationsWarningSample.setPalette(pl)
        self.annotationsWarningSample.repaint()
        
        pl = self.annotationsErrorSample.palette()
        pl.setColor(QPalette.Text, self.editorColours["AnnotationsErrorForeground"])
        pl.setColor(QPalette.Base, self.editorColours["AnnotationsErrorBackground"])
        self.annotationsErrorSample.setPalette(pl)
        self.annotationsErrorSample.repaint()
    
    @pyqtSlot()
    def on_annotationsWarningFgButton_clicked(self):
        """
        Private slot to set the foreground colour of the warning annotations.
        """
        colour = QColorDialog.getColor(self.editorColours["AnnotationsWarningForeground"])
        if colour.isValid():
            pl = self.annotationsWarningSample.palette()
            pl.setColor(QPalette.Text, colour)
            self.annotationsWarningSample.setPalette(pl)
            self.annotationsWarningSample.repaint()
            self.editorColours["AnnotationsWarningForeground"] = colour
    
    @pyqtSlot()
    def on_annotationsWarningBgButton_clicked(self):
        """
        Private slot to set the background colour of the warning annotations.
        """
        colour = QColorDialog.getColor(self.editorColours["AnnotationsWarningBackground"])
        if colour.isValid():
            pl = self.annotationsWarningSample.palette()
            pl.setColor(QPalette.Base, colour)
            self.annotationsWarningSample.setPalette(pl)
            self.annotationsWarningSample.repaint()
            self.editorColours["AnnotationsWarningBackground"] = colour
    
    @pyqtSlot()
    def on_annotationsErrorFgButton_clicked(self):
        """
        Private slot to set the foreground colour of the error annotations.
        """
        colour = QColorDialog.getColor(self.editorColours["AnnotationsErrorForeground"])
        if colour.isValid():
            pl = self.annotationsErrorSample.palette()
            pl.setColor(QPalette.Text, colour)
            self.annotationsErrorSample.setPalette(pl)
            self.annotationsErrorSample.repaint()
            self.editorColours["AnnotationsErrorForeground"] = colour
    
    @pyqtSlot()
    def on_annotationsErrorBgButton_clicked(self):
        """
        Private slot to set the background colour of the error annotations.
        """
        colour = QColorDialog.getColor(self.editorColours["AnnotationsErrorBackground"])
        if colour.isValid():
            pl = self.annotationsErrorSample.palette()
            pl.setColor(QPalette.Base, colour)
            self.annotationsErrorSample.setPalette(pl)
            self.annotationsErrorSample.repaint()
            self.editorColours["AnnotationsErrorBackground"] = colour


def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    """
    page = EditorStylesPage()
    return page
