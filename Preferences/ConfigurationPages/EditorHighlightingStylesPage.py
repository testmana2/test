# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Editor Highlighting Styles configuration page.
"""

import os

from PyQt4.QtCore import pyqtSlot, QFileInfo
from PyQt4.QtGui import QPalette, QFileDialog, QColorDialog, QFontDialog, \
                        QInputDialog, QMessageBox

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_EditorHighlightingStylesPage import Ui_EditorHighlightingStylesPage

from E4XML.XMLUtilities import make_parser
from E4XML.XMLErrorHandler import XMLErrorHandler, XMLFatalParseError
from E4XML.XMLEntityResolver import XMLEntityResolver
from E4XML.HighlightingStylesWriter import HighlightingStylesWriter
from E4XML.HighlightingStylesHandler import HighlightingStylesHandler

import Preferences

class EditorHighlightingStylesPage(ConfigurationPageBase, 
                                   Ui_EditorHighlightingStylesPage):
    """
    Class implementing the Editor Highlighting Styles configuration page.
    """
    def __init__(self, lexers):
        """
        Constructor
        
        @param lexers reference to the lexers dictionary
        """
        ConfigurationPageBase.__init__(self)
        self.setupUi(self)
        self.setObjectName("EditorHighlightingStylesPage")
        
        self.lexer = None
        self.lexers = lexers
        
        # set initial values
        languages = sorted([''] + list(self.lexers.keys()))
        self.lexerLanguageComboBox.addItems(languages)
        self.on_lexerLanguageComboBox_activated("")
        
    def save(self):
        """
        Public slot to save the Editor Highlighting Styles configuration.
        """
        for lexer in list(self.lexers.values()):
            lexer.writeSettings(Preferences.Prefs.settings, "Scintilla")
        
    @pyqtSlot(str)
    def on_lexerLanguageComboBox_activated(self, language):
        """
        Private slot to fill the style combo of the source page.
        
        @param language The lexer language (string)
        """
        self.styleElementList.clear()
        self.styleGroup.setEnabled(False)
        self.lexer = None
        
        self.exportCurrentButton.setEnabled(language != "")
        self.importCurrentButton.setEnabled(language != "")
        
        if not language:
            return
        
        try:
            self.lexer = self.lexers[language]
        except KeyError:
            return
        
        self.styleGroup.setEnabled(True)
        self.styleElementList.addItems(self.lexer.styles)
        self.styleElementList.setCurrentRow(0)
        
    def on_styleElementList_currentRowChanged(self, index):
        """
        Private method to set up the style element part of the source page.
        
        @param index the style index.
        """
        try:
            self.style = self.lexer.ind2style[index]
        except KeyError:
            return
        
        colour = self.lexer.color(self.style)
        paper = self.lexer.paper(self.style)
        eolfill = self.lexer.eolFill(self.style)
        font = self.lexer.font(self.style)
        
        self.sampleText.setFont(font)
        pl = self.sampleText.palette()
        pl.setColor(QPalette.Text, colour)
        pl.setColor(QPalette.Base, paper)
        self.sampleText.setPalette(pl)
        self.sampleText.repaint()
        self.eolfillCheckBox.setChecked(eolfill)
        
    @pyqtSlot()
    def on_foregroundButton_clicked(self):
        """
        Private method used to select the foreground colour of the selected style 
        and lexer.
        """
        colour = QColorDialog.getColor(self.lexer.color(self.style))
        if colour.isValid():
            pl = self.sampleText.palette()
            pl.setColor(QPalette.Text, colour)
            self.sampleText.setPalette(pl)
            self.sampleText.repaint()
            if len(self.styleElementList.selectedItems()) > 1:
                for selItem in self.styleElementList.selectedItems():
                    style = self.lexer.ind2style[self.styleElementList.row(selItem)]
                    self.lexer.setColor(colour, style)
            else:
                self.lexer.setColor(colour, self.style)
        
    @pyqtSlot()
    def on_backgroundButton_clicked(self):
        """
        Private method used to select the background colour of the selected style 
        and lexer.
        """
        colour = QColorDialog.getColor(self.lexer.paper(self.style))
        if colour.isValid():
            pl = self.sampleText.palette()
            pl.setColor(QPalette.Base, colour)
            self.sampleText.setPalette(pl)
            self.sampleText.repaint()
            if len(self.styleElementList.selectedItems()) > 1:
                for selItem in self.styleElementList.selectedItems():
                    style = self.lexer.ind2style[self.styleElementList.row(selItem)]
                    self.lexer.setPaper(colour, style)
            else:
                self.lexer.setPaper(colour, self.style)
        
    @pyqtSlot()
    def on_allBackgroundColoursButton_clicked(self):
        """
        Private method used to select the background colour of all styles of a 
        selected lexer.
        """
        colour = QColorDialog.getColor(self.lexer.paper(self.style))
        if colour.isValid():
            pl = self.sampleText.palette()
            pl.setColor(QPalette.Base, colour)
            self.sampleText.setPalette(pl)
            self.sampleText.repaint()
            for style in list(self.lexer.ind2style.values()):
                self.lexer.setPaper(colour, style)
        
    @pyqtSlot()
    def on_fontButton_clicked(self):
        """
        Private method used to select the font of the selected style and lexer.
        """
        font, ok = QFontDialog.getFont(self.lexer.font(self.style))
        if ok:
            self.sampleText.setFont(font)
            if len(self.styleElementList.selectedItems()) > 1:
                for selItem in self.styleElementList.selectedItems():
                    style = self.lexer.ind2style[self.styleElementList.row(selItem)]
                    self.lexer.setFont(font, style)
            else:
                self.lexer.setFont(font, self.style)
        
    @pyqtSlot()
    def on_allFontsButton_clicked(self):
        """
        Private method used to change the font of all styles of a selected lexer.
        """
        font, ok = QFontDialog.getFont(self.lexer.font(self.style))
        if ok:
            self.sampleText.setFont(font)
            for style in list(self.lexer.ind2style.values()):
                self.lexer.setFont(font, style)
        
    def on_eolfillCheckBox_toggled(self, b):
        """
        Private method used to set the eolfill for the selected style and lexer.
        
        @param b Flag indicating enabled or disabled state.
        """
        self.lexer.setEolFill(b, self.style)
        
    @pyqtSlot()
    def on_allEolFillButton_clicked(self):
        """
        Private method used to set the eolfill for all styles of a selected lexer.
        """
        on = self.trUtf8("Enabled")
        off = self.trUtf8("Disabled")
        selection, ok = QInputDialog.getItem(\
            self,
            self.trUtf8("Fill to end of line"),
            self.trUtf8("Select fill to end of line for all styles"),
            [on, off], 
            0, False)
        if ok:
            enabled = selection == on
            self.eolfillCheckBox.setChecked(enabled)
            for style in list(self.lexer.ind2style.values()):
                self.lexer.setEolFill(enabled, style)
        
    @pyqtSlot()
    def on_defaultButton_clicked(self):
        """
        Private method to set the current style to it's default values.
        """
        if len(self.styleElementList.selectedItems()) > 1:
            for selItem in self.styleElementList.selectedItems():
                style = self.lexer.ind2style[self.styleElementList.row(selItem)]
                self.__setToDefault(style)
        else:
            self.__setToDefault(self.style)
        self.on_styleElementList_currentRowChanged(self.styleElementList.currentRow())
        
    @pyqtSlot()
    def on_allDefaultButton_clicked(self):
        """
        Private method to set all styles to their default values.
        """
        for style in list(self.lexer.ind2style.values()):
            self.__setToDefault(style)
        self.on_styleElementList_currentRowChanged(self.styleElementList.currentRow())
        
    def __setToDefault(self, style):
        """
        Private method to set a specific style to it's default values.
        
        @param style style to be reset (integer)
        """
        self.lexer.setColor(self.lexer.defaultColor(style), style)
        self.lexer.setPaper(self.lexer.defaultPaper(style), style)
        self.lexer.setFont(self.lexer.defaultFont(style), style)
        self.lexer.setEolFill(self.lexer.defaultEolFill(style), style)
        
    @pyqtSlot()
    def on_importCurrentButton_clicked(self):
        """
        Private slot to import the styles of the current lexer.
        """
        self.__importStyles({self.lexer.language() : self.lexer})
        
    @pyqtSlot()
    def on_exportCurrentButton_clicked(self):
        """
        Private slot to export the styles of the current lexer.
        """
        self.__exportStyles([self.lexer])
        
    @pyqtSlot()
    def on_importAllButton_clicked(self):
        """
        Private slot to import the styles of all lexers.
        """
        self.__importStyles(self.lexers)
        
    @pyqtSlot()
    def on_exportAllButton_clicked(self):
        """
        Private slot to export the styles of all lexers.
        """
        self.__exportStyles(list(self.lexers.values()))
        
    def __exportStyles(self, lexers):
        """
        Private method to export the styles of the given lexers.
        
        @param lexers list of lexer objects for which to export the styles
        """
        fn, selectedFilter = QFileDialog.getSaveFileNameAndFilter(\
            self,
            self.trUtf8("Export Highlighting Styles"),
            "",
            self.trUtf8("Highlighting styles file (*.e4h)"),
            "",
            QFileDialog.Options(QFileDialog.DontConfirmOverwrite))
        
        if not fn:
            return
        
        ext = QFileInfo(fn).suffix()
        if not ext:
            ex = selectedFilter.split("(*")[1].split(")")[0]
            if ex:
                fn += ex
        
        try:
            f = open(fn, "w")
            HighlightingStylesWriter(f, lexers).writeXML()
            f.close()
        except IOError as err:
            QMessageBox.critical(self,
                self.trUtf8("Export Highlighting Styles"),
                self.trUtf8("""<p>The highlighting styles could not be exported"""
                            """ to file <b>{0}</b>.</p><p>Reason: {1}</p>""")\
                    .format(fn, str(err))
            )
        
    def __importStyles(self, lexers):
        """
        Private method to import the styles of the given lexers.
        
        @param lexers dictionary of lexer objects for which to import the styles
        """
        fn = QFileDialog.getOpenFileName(\
            self,
            self.trUtf8("Import Highlighting Styles"),
            "",
            self.trUtf8("Highlighting styles file (*.e4h)"))
        
        if not fn:
            return
        
        try:
            f = open(fn, "r")
            try:
                line = f.readline()
                dtdLine = f.readline()
            finally:
                f.close()
        except IOError as err:
            QMessageBox.critical(self,
                self.trUtf8("Import Highlighting Styles"),
                self.trUtf8("""<p>The highlighting styles could not be read"""
                            """ from file <b>{0}</b>.</p><p>Reason: {1}</p>""")\
                    .format(fn, str(err))
            )
            return
        
        validating = dtdLine.startswith("<!DOCTYPE")
        parser = make_parser(validating)
        handler = HighlightingStylesHandler(lexers)
        er = XMLEntityResolver()
        eh = XMLErrorHandler()
        
        parser.setContentHandler(handler)
        parser.setEntityResolver(er)
        parser.setErrorHandler(eh)
        
        try:
            f = open(fn, "r")
            try:
                try:
                    parser.parse(f)
                except UnicodeEncodeError:
                    f.seek(0)
                    buf = cStringIO.StringIO(f.read())
                    parser.parse(buf)
            finally:
                f.close()
        except IOError as err:
            QMessageBox.critical(self,
                self.trUtf8("Import Highlighting Styles"),
                self.trUtf8("""<p>The highlighting styles could not be read"""
                            """ from file <b>{0}</b>.</p><p>Reason: {1}</p>""")\
                    .format(fn, str(err))
            )
            return
        except XMLFatalParseError:
            QMessageBox.critical(self,
                self.trUtf8("Import Highlighting Styles"),
                self.trUtf8("""<p>The highlighting styles file <b>{0}</b>"""
                            """ has invalid contents.</p>""").format(fn))
            eh.showParseMessages()
            return
        
        eh.showParseMessages()
        
        if self.lexer:
            colour = self.lexer.color(self.style)
            paper = self.lexer.paper(self.style)
            eolfill = self.lexer.eolFill(self.style)
            font = self.lexer.font(self.style)
            
            self.sampleText.setFont(font)
            pl = self.sampleText.palette()
            pl.setColor(QPalette.Text, colour)
            pl.setColor(QPalette.Base, paper)
            self.sampleText.setPalette(pl)
            self.sampleText.repaint()
            self.eolfillCheckBox.setChecked(eolfill)
        
    def saveState(self):
        """
        Public method to save the current state of the widget.
        
        @return array containing the index of the selected lexer language (integer)
            and the index of the selected lexer entry (integer)
        """
        savedState = [
            self.lexerLanguageComboBox.currentIndex(),
            self.styleElementList.currentRow(),
        ]
        return savedState
        
    def setState(self, state):
        """
        Public method to set the state of the widget.
        
        @param state state data generated by saveState
        """
        self.lexerLanguageComboBox.setCurrentIndex(state[0])
        self.on_lexerLanguageComboBox_activated(self.lexerLanguageComboBox.currentText())
        self.styleElementList.setCurrentRow(state[1])

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    """
    page = EditorHighlightingStylesPage(dlg.getLexers())
    return page
