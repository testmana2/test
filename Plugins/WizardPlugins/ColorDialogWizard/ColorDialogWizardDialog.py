# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the color dialog wizard dialog.
"""

from __future__ import unicode_literals    # __IGNORE_WARNING__

import os

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QColor, QColorDialog, QDialog, QDialogButtonBox

from E5Gui import E5MessageBox

from .Ui_ColorDialogWizardDialog import Ui_ColorDialogWizardDialog


class ColorDialogWizardDialog(QDialog, Ui_ColorDialogWizardDialog):
    """
    Class implementing the color dialog wizard dialog.
    
    It displays a dialog for entering the parameters
    for the QColorDialog code generator.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent parent widget (QWidget)
        """
        super(ColorDialogWizardDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.bTest = self.buttonBox.addButton(
            self.trUtf8("Test"), QDialogButtonBox.ActionRole)
    
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.bTest:
            self.on_bTest_clicked()
    
    @pyqtSlot()
    def on_bTest_clicked(self):
        """
        Private method to test the selected options.
        """
        if self.rColor.isChecked():
            if not self.eColor.currentText():
                QColorDialog.getColor()
            else:
                coStr = self.eColor.currentText()
                if coStr.startswith('#'):
                    coStr = "QColor('{0}')".format(coStr)
                else:
                    coStr = "QColor({0})".format(coStr)
                try:
                    exec('from PyQt4.QtCore import Qt;'
                         ' QColorDialog.getColor({0}, None, "{1}")'.format(
                        coStr, self.eTitle.text()))
                except:
                    E5MessageBox.critical(
                        self,
                        self.trUtf8("QColorDialog Wizard Error"),
                        self.trUtf8(
                            """<p>The colour <b>{0}</b> is not valid.</p>""")
                            .format(coStr))
            
        elif self.rRGBA.isChecked():
            QColorDialog.getColor(
                QColor(self.sRed.value(), self.sGreen.value(),
                       self.sBlue.value(), self.sAlpha.value()),
                None, self.eTitle.text(),
                QColorDialog.ColorDialogOptions(QColorDialog.ShowAlphaChannel))
        
    def on_eRGB_textChanged(self, text):
        """
        Private slot to handle the textChanged signal of eRGB.
        
        @param text the new text (string)
        """
        if not text:
            self.sRed.setEnabled(True)
            self.sGreen.setEnabled(True)
            self.sBlue.setEnabled(True)
            self.sAlpha.setEnabled(True)
            self.bTest.setEnabled(True)
        else:
            self.sRed.setEnabled(False)
            self.sGreen.setEnabled(False)
            self.sBlue.setEnabled(False)
            self.sAlpha.setEnabled(False)
            self.bTest.setEnabled(False)

    def on_eColor_editTextChanged(self, text):
        """
        Private slot to handle the editTextChanged signal of eColor.
        
        @param text the new text (string)
        """
        if not text or text.startswith('Qt.') or text.startswith('#'):
            self.bTest.setEnabled(True)
        else:
            self.bTest.setEnabled(False)
    
    def getCode(self, indLevel, indString):
        """
        Public method to get the source code.
        
        @param indLevel indentation level (int)
        @param indString string used for indentation (space or tab) (string)
        @return generated code (string)
        """
        # calculate our indentation level and the indentation string
        il = indLevel + 1
        istring = il * indString
        estring = os.linesep + indLevel * indString
        
        # now generate the code
        code = 'QColorDialog.'
        if self.rColor.isChecked():
            code += 'getColor('
            if self.eColor.currentText():
                col = self.eColor.currentText()
                if col.startswith('#'):
                    code += 'QColor("{0}")'.format(col)
                else:
                    code += 'QColor({0})'.format(col)
            code += ', None,{0}'.format(os.linesep)
            code += '{0}self.trUtf8("{1}"),{2}'.format(
                istring, self.eTitle.text(), os.linesep)
            code += '{0}QColorDialog.ColorDialogOptions(' \
                'QColorDialog.ShowAlphaChannel)'.format(istring)
            code += '){0}'.format(estring)
        elif self.rRGBA.isChecked():
            code += 'getColor('
            if not self.eRGB.text():
                code += 'QColor({0:d}, {1:d}, {2:d}, {3:d}),{4}'.format(
                    self.sRed.value(), self.sGreen.value(), self.sBlue.value(),
                    self.sAlpha.value(), os.linesep)
            else:
                code += '{0},{1}'.format(self.eRGB.text(), os.linesep)
            code += '{0}None,{1}'.format(istring, os.linesep)
            code += '{0}self.trUtf8("{1}"),{2}'.format(
                istring, self.eTitle.text(), os.linesep)
            code += '{0}QColorDialog.ColorDialogOptions(' \
                'QColorDialog.ShowAlphaChannel)'.format(istring)
            code += '){0}'.format(estring)
        
        return code
