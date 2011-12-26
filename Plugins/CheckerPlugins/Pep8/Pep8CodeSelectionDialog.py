# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to select PEP 8 message codes.
"""

from PyQt4.QtCore import QCoreApplication
from PyQt4.QtGui import QDialog, QTreeWidgetItem

from . import pep8
from .Pep8Fixer import Pep8FixableIssues

from .Ui_Pep8CodeSelectionDialog import Ui_Pep8CodeSelectionDialog

class Pep8CodeSelectionDialog(QDialog, Ui_Pep8CodeSelectionDialog):
    """
    Class implementing a dialog to select PEP 8 message codes.
    """
    def __init__(self, codes, showFixCodes, parent = None):
        """
        Constructor
        
        @param codes comma separated list of selected codes (string)
        @param showFixCodes flag indicating to show a list of fixable
            issues (boolean)
        @param parent reference to the parent widget (QWidget)
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        
        codeList = [code.strip() for code in codes.split(",") if code.strip()]
        
        if showFixCodes:
            selectableCodes = Pep8FixableIssues
        else:
            selectableCodes = pep8.pep8_messages.keys()
        for code in sorted(selectableCodes, key=lambda a: a[1:]):
            if code in pep8.pep8_messages_sample_args:
                message = QCoreApplication.translate("pep8", 
                    pep8.pep8_messages[code]).format(
                        *pep8.pep8_messages_sample_args[code])
            else:
                message = QCoreApplication.translate("pep8", 
                    pep8.pep8_messages[code])
            itm = QTreeWidgetItem(self.codeTable, [code, message])
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
