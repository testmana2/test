# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to manage the list of messages to be ignored.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot, Qt, QSortFilterProxyModel, QStringListModel
from PyQt5.QtWidgets import QDialog, QInputDialog, QLineEdit

from .Ui_E5ErrorMessageFilterDialog import Ui_E5ErrorMessageFilterDialog


class E5ErrorMessageFilterDialog(QDialog, Ui_E5ErrorMessageFilterDialog):
    """
    Class implementing a dialog to manage the list of messages to be ignored.
    """
    def __init__(self, messageFilters, parent=None):
        """
        Constructor
        
        @param messageFilters list of message filters to be edited
            (list of strings)
        @param parent reference to the parent widget (QWidget)
        """
        super(E5ErrorMessageFilterDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.__model = QStringListModel(messageFilters, self)
        self.__model.sort(0)
        self.__proxyModel = QSortFilterProxyModel(self)
        self.__proxyModel.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.__proxyModel.setSourceModel(self.__model)
        self.filterList.setModel(self.__proxyModel)
        
        self.searchEdit.textChanged.connect(
            self.__proxyModel.setFilterFixedString)
        
        self.removeButton.clicked.connect(self.filterList.removeSelected)
        self.removeAllButton.clicked.connect(self.filterList.removeAll)
    
    @pyqtSlot()
    def on_addButton_clicked(self):
        """
        Private slot to add an entry to the list.
        """
        filter, ok = QInputDialog.getText(
            self,
            self.tr("Error Messages Filter"),
            self.tr("Enter message filter to add to the list:"),
            QLineEdit.Normal)
        if ok and filter != "" and filter not in self.__model.stringList():
            self.__model.insertRow(self.__model.rowCount())
            self.__model.setData(
                self.__model.index(self.__model.rowCount() - 1), filter)
            self.__model.sort(0)
    
    def getFilters(self):
        """
        Public method to get the list of message filters.
        
        @return error message filters (list of strings)
        """
        return self.__model.stringList()[:]
