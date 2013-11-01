# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to manage the list of hosts not to be cached.
"""

from __future__ import unicode_literals    # __IGNORE_WARNING__

from PyQt4.QtCore import pyqtSlot, Qt
from PyQt4.QtGui import QDialog, QStringListModel, QSortFilterProxyModel, \
    QInputDialog, QLineEdit

from .Ui_NoCacheHostsDialog import Ui_NoCacheHostsDialog

import Preferences


class NoCacheHostsDialog(QDialog, Ui_NoCacheHostsDialog):
    """
    Class implementing a dialog to manage the list of hosts not to be cached.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(NoCacheHostsDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.__model = QStringListModel(
            Preferences.getHelp("NoCacheHosts"), self)
        self.__model.sort(0)
        self.__proxyModel = QSortFilterProxyModel(self)
        self.__proxyModel.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.__proxyModel.setSourceModel(self.__model)
        self.noCacheList.setModel(self.__proxyModel)
        
        self.searchEdit.textChanged.connect(
            self.__proxyModel.setFilterFixedString)
        
        self.removeButton.clicked[()].connect(self.noCacheList.removeSelected)
        self.removeAllButton.clicked[()].connect(self.noCacheList.removeAll)
    
    @pyqtSlot()
    def on_addButton_clicked(self):
        """
        Private slot to add an entry to the list.
        """
        host, ok = QInputDialog.getText(
            self,
            self.trUtf8("Not Cached Hosts"),
            self.trUtf8("Enter host name to add to the list:"),
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
        Preferences.setHelp("NoCacheHosts", self.__model.stringList())
        
        super(NoCacheHostsDialog, self).accept()
