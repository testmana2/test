# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to manage the Send Referer whitelist.
"""

from PyQt4.QtCore import pyqtSlot, Qt
from PyQt4.QtGui import QDialog, QStringListModel, QSortFilterProxyModel, \
    QInputDialog, QLineEdit

from .Ui_SendRefererWhitelistDialog import Ui_SendRefererWhitelistDialog

import Preferences


class SendRefererWhitelistDialog(QDialog, Ui_SendRefererWhitelistDialog):
    """
    Class implementing a dialog to manage the Send Referer whitelist.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        self.__model = QStringListModel(Preferences.getHelp("SendRefererWhitelist"), self)
        self.__model.sort(0)
        self.__proxyModel = QSortFilterProxyModel(self)
        self.__proxyModel.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.__proxyModel.setSourceModel(self.__model)
        self.whitelist.setModel(self.__proxyModel)
        
        self.searchEdit.textChanged.connect(self.__proxyModel.setFilterFixedString)
        
        self.removeButton.clicked[()].connect(self.whitelist.removeSelected)
        self.removeAllButton.clicked[()].connect(self.whitelist.removeAll)
    
    @pyqtSlot()
    def on_addButton_clicked(self):
        """
        Private slot to add an entry to the whitelist.
        """
        host, ok = QInputDialog.getText(
            self,
            self.trUtf8("Send Referer Whitelist"),
            self.trUtf8("Enter host name to add to the whitelist:"),
            QLineEdit.Normal)
        if ok and host != "" and host not in self.__model.stringList():
            self.__model.insertRow(self.__model.rowCount())
            self.__model.setData(
                self.__model.index(self.__model.rowCount() - 1), host)
            self.__model.sort(0)
    
    def accept(self):
        """
        Public method to accept the dialog data.
        """
        Preferences.setHelp("SendRefererWhitelist", self.__model.stringList())
        
        super().accept()