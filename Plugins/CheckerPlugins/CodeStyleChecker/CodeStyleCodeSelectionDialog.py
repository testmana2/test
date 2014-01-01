# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to select code style message codes.
"""

from PyQt4.QtCore import QCoreApplication
from PyQt4.QtGui import QDialog, QTreeWidgetItem

from . import pep8
from .NamingStyleChecker import NamingStyleChecker
from .DocStyleChecker import DocStyleChecker

from .Ui_CodeStyleCodeSelectionDialog import Ui_CodeStyleCodeSelectionDialog

import UI.PixmapCache


class CodeStyleCodeSelectionDialog(QDialog, Ui_CodeStyleCodeSelectionDialog):
    """
    Class implementing a dialog to select code style message codes.
    """
    def __init__(self, codes, showFixCodes, parent=None):
        """
        Constructor
        
        @param codes comma separated list of selected codes (string)
        @param showFixCodes flag indicating to show a list of fixable
            issues (boolean)
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        codeList = [code.strip() for code in codes.split(",") if code.strip()]
        
        if showFixCodes:
            from .CodeStyleFixer import FixableCodeStyleIssues
            selectableCodes = FixableCodeStyleIssues
        else:
            selectableCodes = list(pep8.pep8_messages.keys())
            selectableCodes.extend(NamingStyleChecker.Messages.keys())
            selectableCodes.extend(DocStyleChecker.Messages.keys())
        for code in sorted(selectableCodes):
            if code in pep8.pep8_messages_sample_args:
                message = QCoreApplication.translate(
                    "pep8", pep8.pep8_messages[code]).format(
                    *pep8.pep8_messages_sample_args[code])
            elif code in pep8.pep8_messages:
                message = QCoreApplication.translate(
                    "pep8", pep8.pep8_messages[code])
            elif code in NamingStyleChecker.Messages:
                message = QCoreApplication.translate(
                    "NamingStyleChecker",
                    NamingStyleChecker.Messages[code])
            elif code in DocStyleChecker.MessagesSampleArgs:
                message = QCoreApplication.translate(
                    "DocStyleChecker",
                    DocStyleChecker.Messages[code].format(
                        *DocStyleChecker.MessagesSampleArgs[code]))
            elif code in DocStyleChecker.Messages:
                message = QCoreApplication.translate(
                    "DocStyleChecker", DocStyleChecker.Messages[code])
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
