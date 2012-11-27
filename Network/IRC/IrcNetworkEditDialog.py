# -*- coding: utf-8 -*-

# Copyright (c) 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog for editing IRC network definitions.
"""

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QDialog, QDialogButtonBox, QTreeWidgetItem

from .Ui_IrcNetworkEditDialog import Ui_IrcNetworkEditDialog

from .IrcNetworkManager import IrcIdentity

import UI.PixmapCache


class IrcNetworkEditDialog(QDialog, Ui_IrcNetworkEditDialog):
    """
    Class implementing a dialog for editing IRC network definitions.
    """
    def __init__(self, manager, networkName, parent=None):
        """
        Constructor
        
        @param manager reference to the IRC network manager object (IrcNetworkManager)
        @param networkName name of the network to work on (string)
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        self.__manager = manager
        
        self.editIdentitiesButton.setIcon(UI.PixmapCache.getIcon("ircConfigure.png"))
        self.editServersButton.setIcon(UI.PixmapCache.getIcon("ircConfigure.png"))
        self.editChannelButton.setIcon(UI.PixmapCache.getIcon("ircConfigure.png"))
        self.addChannelButton.setIcon(UI.PixmapCache.getIcon("plus.png"))
        self.deleteChannelButton.setIcon(UI.PixmapCache.getIcon("minus.png"))
        
        self.__okButton = self.buttonBox.button(QDialogButtonBox.Ok)
        
        self.networkEdit.setText(networkName)
        identities = list(sorted(self.__manager.getIdentityNames()))
        identities[identities.index(IrcIdentity.DefaultIdentityName)] = \
            IrcIdentity.DefaultIdentityDisplay
        self.identityCombo.addItems(identities)
        
        self.__updateOkButton()
    
    def __updateOkButton(self):
        """
        Private method to update the OK button state.
        """
        enable = True
        enable &= self.networkEdit.text() != ""
        enable &= self.serverCombo.currentText() != ""
        
        self.__okButton.setEnabled(enable)
    
    @pyqtSlot(str)
    def on_networkEdit_textChanged(self, txt):
        """
        Private slot to handle changes of the network name.
        
        @param txt text entered into the network name edit (string)
        """
        self.__updateOkButton()
    
    @pyqtSlot()
    def on_editIdentitiesButton_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError
    
    @pyqtSlot(str)
    def on_serverCombo_activated(self, txt):
        """
        Private slot to handle the selection of a server.
        
        @param txt selected server (string)
        """
        self.__updateOkButton()
    
    @pyqtSlot()
    def on_editServersButton_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError
    
    @pyqtSlot()
    def on_addChannelButton_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError
    
    @pyqtSlot()
    def on_editChannelButton_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError
    
    @pyqtSlot()
    def on_deleteChannelButton_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError
    
    @pyqtSlot(QTreeWidgetItem, int)
    def on_channelList_itemActivated(self, item, column):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError
    
    @pyqtSlot()
    def on_channelList_itemSelectionChanged(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError
