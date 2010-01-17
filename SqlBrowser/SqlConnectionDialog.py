# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter the connection parameters.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtSql import QSqlDatabase

from E5Gui.E5Completers import E5FileCompleter

from .Ui_SqlConnectionDialog import Ui_SqlConnectionDialog

import Utilities

class SqlConnectionDialog(QDialog, Ui_SqlConnectionDialog):
    """
    Class implementing a dialog to enter the connection parameters.
    """
    def __init__(self, parent = None):
        """
        Constructor
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        
        self.databaseFileCompleter = E5FileCompleter()
        
        self.okButton = self.buttonBox.button(QDialogButtonBox.Ok)
        
        drivers = QSqlDatabase.drivers()
        
        # remove compatibility names
        if "QMYSQL3" in drivers:
            drivers.remove("QMYSQL3")
        if "QOCI8" in drivers:
            drivers.remove("QOCI8")
        if "QODBC3" in drivers:
            drivers.remove("QODBC3")
        if "QPSQL7" in drivers:
            drivers.remove("QPSQL7")
        if "QTDS7" in drivers:
            drivers.remove("QTDS7")
        
        self.driverCombo.addItems(drivers)
        
        self.__updateDialog()
    
    def __updateDialog(self):
        """
        Private slot to update the dialog depending on it's contents.
        """
        driver = self.driverCombo.currentText()
        if driver.startswith("QSQLITE"):
            self.databaseEdit.setCompleter(self.databaseFileCompleter)
            self.databaseFileButton.setEnabled(True)
        else:
            self.databaseEdit.setCompleter(None)
            self.databaseFileButton.setEnabled(False)
        
        if self.databaseEdit.text() == "" or driver == "":
            self.okButton.setEnabled(False)
        else:
            self.okButton.setEnabled(True)
    
    @pyqtSlot(str)
    def on_driverCombo_activated(self, txt):
        """
        Private slot handling the selection of a database driver.
        """
        self.__updateDialog()
    
    @pyqtSlot(str)
    def on_databaseEdit_textChanged(self, p0):
        """
        Private slot handling the change of the database name.
        """
        self.__updateDialog()
    
    @pyqtSlot()
    def on_databaseFileButton_clicked(self):
        """
        Private slot to open a database file via a file selection dialog.
        """
        startdir = self.databaseEdit.text()
        dbFile = QFileDialog.getOpenFileName(
            self,
            self.trUtf8("Select Database File"),
            startdir,
            self.trUtf8("All Files (*)"))
        
        if dbFile:
            self.databaseEdit.setText(Utilities.toNativeSeparators(dbFile))
    
    def getData(self):
        """
        Public method to retrieve the connection data.
        
        @return tuple giving the driver name (QString), the database name (QString),
            the user name (QString), the password (QString), the host name (QString)
            and the port (integer)
        """
        return (
            self.driverCombo.currentText(), 
            self.databaseEdit.text(), 
            self.usernameEdit.text(), 
            self.passwordEdit.text(), 
            self.hostnameEdit.text(), 
            self.portSpinBox.value(), 
        )
