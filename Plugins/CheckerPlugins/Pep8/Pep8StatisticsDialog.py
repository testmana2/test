# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog showing statistical data for the last PEP 8 run.
"""

from PyQt4.QtCore import Qt, QCoreApplication
from PyQt4.QtGui import QDialog, QTreeWidgetItem

from . import pep8

from .Ui_Pep8StatisticsDialog import Ui_Pep8StatisticsDialog

import UI.PixmapCache


class Pep8StatisticsDialog(QDialog, Ui_Pep8StatisticsDialog):
    """
    Class implementing a dialog showing statistical data for the last
    PEP 8 run.
    """
    def __init__(self, statistics, parent=None):
        """
        Constructor
        
        @param dictionary with the statistical data
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        stats = statistics.copy()
        filesCount = stats["_FilesCount"]
        filesIssues = stats["_FilesIssues"]
        fixesCount = stats["_IssuesFixed"]
        del stats["_FilesCount"]
        del stats["_FilesIssues"]
        del stats["_IssuesFixed"]
        
        totalIssues = 0
        
        for code in sorted(stats.keys(), key=lambda a: a[1:]):
            if code in pep8.pep8_messages_sample_args:
                message = QCoreApplication.translate("pep8",
                    pep8.pep8_messages[code]).format(
                        *pep8.pep8_messages_sample_args[code])
            else:
                message = QCoreApplication.translate("pep8",
                    pep8.pep8_messages[code])
            self.__createItem(stats[code], code, message)
            totalIssues += stats[code]
        
        self.totalIssues.setText(
            self.trUtf8("%n issue(s) found", "", totalIssues))
        self.fixedIssues.setText(
            self.trUtf8("%n issue(s) fixed", "", fixesCount))
        self.filesChecked.setText(
            self.trUtf8("%n file(s) checked", "", filesCount))
        self.filesIssues.setText(
            self.trUtf8("%n file(s) with issues found", "", filesIssues))
        
        self.statisticsList.resizeColumnToContents(0)
        self.statisticsList.resizeColumnToContents(1)
    
    def __createItem(self, count, code, message):
        """
        Private method to create an entry in the result list.
        
        @param count occurrences of the issue (integer)
        @param code of a PEP 8 message (string)
        @param message PEP 8 message to be shown (string)
        """
        itm = QTreeWidgetItem(self.statisticsList)
        itm.setData(0, Qt.DisplayRole, count)
        itm.setData(1, Qt.DisplayRole, code)
        itm.setData(2, Qt.DisplayRole, message)
        if code.startswith("W"):
            itm.setIcon(1, UI.PixmapCache.getIcon("warning.png"))
        elif code.startswith("E"):
            itm.setIcon(1, UI.PixmapCache.getIcon("syntaxError.png"))
        
        itm.setTextAlignment(0, Qt.AlignRight)
        itm.setTextAlignment(1, Qt.AlignHCenter)
