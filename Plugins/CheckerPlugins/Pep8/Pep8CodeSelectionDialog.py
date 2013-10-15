# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to select PEP 8 message codes.
"""

from __future__ import unicode_literals    # __IGNORE_WARNING__

from PyQt4.QtCore import QCoreApplication
from PyQt4.QtGui import QDialog, QTreeWidgetItem

from . import pep8
from .Pep8NamingChecker import Pep8NamingChecker
from .Pep257Checker import Pep257Checker

from .Ui_Pep8CodeSelectionDialog import Ui_Pep8CodeSelectionDialog

import UI.PixmapCache


class Pep8CodeSelectionDialog(QDialog, Ui_Pep8CodeSelectionDialog):
    """
    Class implementing a dialog to select PEP 8 message codes.
    """
    def __init__(self, codes, showFixCodes, parent=None):
        """
        Constructor
        
        @param codes comma separated list of selected codes (string)
        @param showFixCodes flag indicating to show a list of fixable
            issues (boolean)
        @param parent reference to the parent widget (QWidget)
        """
        super(Pep8CodeSelectionDialog, self).__init__(parent)
        self.setupUi(self)
        
        codeList = [code.strip() for code in codes.split(",") if code.strip()]
        
        if showFixCodes:
            from .Pep8Fixer import Pep8FixableIssues
            selectableCodes = Pep8FixableIssues
        else:
            selectableCodes = list(pep8.pep8_messages.keys())
            selectableCodes.extend(Pep8NamingChecker.Messages.keys())
            selectableCodes.extend(Pep257Checker.Messages.keys())
        for code in sorted(selectableCodes):
            if code in pep8.pep8_messages_sample_args:
                message = QCoreApplication.translate(
                    "pep8", pep8.pep8_messages[code]).format(
                    *pep8.pep8_messages_sample_args[code])
            elif code in pep8.pep8_messages:
                message = QCoreApplication.translate(
                    "pep8", pep8.pep8_messages[code])
            elif code in Pep8NamingChecker.Messages:
                message = QCoreApplication.translate(
                    "Pep8NamingChecker",
                    Pep8NamingChecker.Messages[code])
            elif code in Pep257Checker.Messages:
                message = QCoreApplication.translate(
                    "Pep257Checker", Pep257Checker.Messages[code])
            else:
                continue
            itm = QTreeWidgetItem(self.codeTable, [code, message])
            if code.startswith("W"):
                itm.setIcon(0, UI.PixmapCache.getIcon("warning.png"))
            elif code.startswith("E"):
                itm.setIcon(0, UI.PixmapCache.getIcon("syntaxError.png"))
            elif code.startswith("N"):
                itm.setIcon(0, UI.PixmapCache.getIcon("namingError.png"))
            elif code.startswith("D"):
                itm.setIcon(0, UI.PixmapCache.getIcon("docstringError.png"))
            if code in codeList:
                itm.setSelected(True)
                codeList.remove(code)
        
        self.__extraCodes = codeList[:]
    
    def getSelectedCodes(self):
        """
        Public method to get a comma separated list of codes selected.
        
        @return comma separated list of selected codes (string)
        """
        selectedCodes = []
        
        for itm in self.codeTable.selectedItems():
            selectedCodes.append(itm.text(0))
        
        return ", ".join(self.__extraCodes + selectedCodes)
