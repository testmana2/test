# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show all saved logins.
"""

from PyQt4.QtCore import pyqtSlot, QFont, QFontMetrics, QSortFilterProxyModel
from PyQt4.QtGui import QDialog

from E5Gui import E5MessageBox

import Helpviewer.HelpWindow

from .PasswordModel import PasswordModel

from .Ui_PasswordsDialog import Ui_PasswordsDialog

import UI.PixmapCache


class PasswordsDialog(QDialog, Ui_PasswordsDialog):
    """
    Class implementing a dialog to show all saved logins.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        
        self.clearButton.setIcon(UI.PixmapCache.getIcon("clearLeft.png"))
        
        self.__showPasswordsText = self.trUtf8("Show Passwords")
        self.__hidePasswordsText = self.trUtf8("Hide Passwords")
        self.passwordsButton.setText(self.__showPasswordsText)
        
        self.removeButton.clicked[()].connect(self.passwordsTable.removeSelected)
        self.removeAllButton.clicked[()].connect(self.passwordsTable.removeAll)
        
        self.passwordsTable.verticalHeader().hide()
        self.__passwordModel = \
            PasswordModel(Helpviewer.HelpWindow.HelpWindow.passwordManager(), self)
        self.__proxyModel = QSortFilterProxyModel(self)
        self.__proxyModel.setSourceModel(self.__passwordModel)
        self.searchEdit.textChanged.connect(self.__proxyModel.setFilterFixedString)
        self.passwordsTable.setModel(self.__proxyModel)
        
        fm = QFontMetrics(QFont())
        height = fm.height() + fm.height() // 3
        self.passwordsTable.verticalHeader().setDefaultSectionSize(height)
        self.passwordsTable.verticalHeader().setMinimumSectionSize(-1)
        
        self.__calculateHeaderSizes()
    
    def __calculateHeaderSizes(self):
        """
        Private method to calculate the section sizes of the horizontal header.
        """
        fm = QFontMetrics(QFont())
        for section in range(self.__passwordModel.columnCount()):
            header = self.passwordsTable.horizontalHeader().sectionSizeHint(section)
            if section == 0:
                header = fm.width("averagebiglongsitename")
            elif section == 1:
                header = fm.width("averagelongusername")
            elif section == 2:
                header = fm.width("averagelongpassword")
            buffer = fm.width("mm")
            header += buffer
            self.passwordsTable.horizontalHeader().resizeSection(section, header)
        self.passwordsTable.horizontalHeader().setStretchLastSection(True)
    
    @pyqtSlot()
    def on_passwordsButton_clicked(self):
        """
        Private slot to switch the password display mode.
        """
        if self.__passwordModel.showPasswords():
            self.__passwordModel.setShowPasswords(False)
            self.passwordsButton.setText(self.__showPasswordsText)
        else:
            res = E5MessageBox.yesNo(self,
                self.trUtf8("Saved Passwords"),
                self.trUtf8("""Do you really want to show passwords?"""))
            if res:
                self.__passwordModel.setShowPasswords(True)
                self.passwordsButton.setText(self.__hidePasswordsText)
        self.__calculateHeaderSizes()
