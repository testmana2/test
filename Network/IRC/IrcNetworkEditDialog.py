# -*- coding: utf-8 -*-

# Copyright (c) 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog for editing IRC network definitions.
"""

import copy

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QDialog, QDialogButtonBox, QTreeWidgetItem

from E5Gui import E5MessageBox

from .Ui_IrcNetworkEditDialog import Ui_IrcNetworkEditDialog

from .IrcNetworkManager import IrcIdentity, IrcChannel
from .IrcChannelEditDialog import IrcChannelEditDialog
from .IrcServerEditDialog import IrcServerEditDialog

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
        self.editServerButton.setIcon(UI.PixmapCache.getIcon("ircConfigure.png"))
        self.editChannelButton.setIcon(UI.PixmapCache.getIcon("ircConfigure.png"))
        self.addChannelButton.setIcon(UI.PixmapCache.getIcon("plus.png"))
        self.deleteChannelButton.setIcon(UI.PixmapCache.getIcon("minus.png"))
        
        self.__okButton = self.buttonBox.button(QDialogButtonBox.Ok)
        
        # TODO: add the ADD mode
        self.__network = copy.deepcopy(self.__manager.getNetwork(networkName))
        
        # network name
        self.networkEdit.setText(networkName)
        
        # identities
        identities = list(sorted(self.__manager.getIdentityNames()))
        identities[identities.index(IrcIdentity.DefaultIdentityName)] = \
            IrcIdentity.DefaultIdentityDisplay
        self.identityCombo.addItems(identities)
        identity = self.__network.getIdentityName()
        if identity == IrcIdentity.DefaultIdentityName:
            identity = IrcIdentity.DefaultIdentityDisplay
        index = self.identityCombo.findText(identity)
        if index == -1:
            index = 0
        self.identityCombo.setCurrentIndex(index)
        
        # server
        self.serverEdit.setText(self.__network.getServerName())
        
        # channels
        for channelName in sorted(self.__network.getChannelNames()):
            channel = self.__network.getChannel(channelName)
            if channel.autoJoin():
                autoJoin = self.trUtf8("Yes")
            else:
                autoJoin = self.trUtf8("No")
            QTreeWidgetItem(self.channelList, [channelName, autoJoin])
        
        self.__updateOkButton()
        self.on_channelList_itemSelectionChanged()
    
    def __updateOkButton(self):
        """
        Private method to update the OK button state.
        """
        enable = True
        enable &= self.networkEdit.text() != ""
        enable &= self.serverEdit.text() != ""
        
        self.__okButton.setEnabled(enable)
    
    @pyqtSlot(str)
    def on_networkEdit_textChanged(self, txt):
        """
        Private slot to handle changes of the network name.
        
        @param txt text entered into the network name edit (string)
        """
        self.__updateOkButton()
    
    @pyqtSlot(str)
    def on_identityCombo_activated(self, identity):
        """
        Private slot to handle the selection of an identity.
        
        @param identity selected entity (string)
        """
        self.__network.setIdentityName(identity)
    
    @pyqtSlot()
    def on_editIdentitiesButton_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError
    
    @pyqtSlot()
    def on_editServerButton_clicked(self):
        """
        Private slot to edit the server configuration.
        """
        dlg = IrcServerEditDialog(self.__network.getServer())
        if dlg.exec_() == QDialog.Accepted:
            self.__network.setServer(dlg.getServer())
            self.serverEdit.setText(self.__network.getServerName())
    
    @pyqtSlot()
    def on_addChannelButton_clicked(self):
        """
        Private slot to add a channel.
        """
        self.__editChannel(None)
    
    @pyqtSlot()
    def on_editChannelButton_clicked(self):
        """
        Private slot to edit the selected channel.
        """
        itm = self.channelList.selectedItems()[0]
        if itm:
            self.__editChannel(itm)
    
    @pyqtSlot()
    def on_deleteChannelButton_clicked(self):
        """
        Private slot to delete the selected channel.
        """
        itm = self.channelList.selectedItems()[0]
        if itm:
            res = E5MessageBox.yesNo(self,
                self.trUtf8("Delete Channel"),
                self.trUtf8("""Do you really want to delete channel <b>{0}</b>?""")\
                    .format(itm.text(0)))
            if res:
                self.__network.deleteChannel(itm.text(0))
                
                index = self.channelList.indexOfTopLevelItem(itm)
                self.channelList.takeTopLevelItem(index)
                del itm
    
    @pyqtSlot(QTreeWidgetItem, int)
    def on_channelList_itemActivated(self, item, column):
        """
        Private slot to handle the activation of a channel entry.
        
        @param item reference to the activated item (QTreeWidgetItem)
        @param column column the activation occurred in (integer)
        """
        self.__editChannel(item)
    
    @pyqtSlot()
    def on_channelList_itemSelectionChanged(self):
        """
        Private slot to handle changes of the selection of channels.
        """
        selectedItems = self.channelList.selectedItems()
        if len(selectedItems) == 0:
            enable = False
        else:
            enable = True
        self.editChannelButton.setEnabled(enable)
        self.deleteChannelButton.setEnabled(enable)
    
    def __editChannel(self, itm):
        """
        Private method to edit a channel.
        
        @param itm reference to the item to be edited (QTreeWidgetItem)
        """
        if itm:
            channel = self.__network.getChannel(itm.text(0))
            name = channel.getName()
            key = channel.getKey()
            autoJoin = channel.autoJoin()
        else:
            # add a new channel
            name = ""
            key = ""
            autoJoin = False
        
        dlg = IrcChannelEditDialog(name, key, autoJoin, itm is not None, self)
        if dlg.exec_() == QDialog.Accepted:
            name, key, autoJoin = dlg.getData()
            channel = IrcChannel(name)
            channel.setKey(key)
            channel.setAutoJoin(autoJoin)
            if itm:
                if autoJoin:
                    itm.setText(1, self.trUtf8("Yes"))
                else:
                    itm.setText(1, self.trUtf8("No"))
                self.__network.setChannel(channel)
            else:
                if autoJoin:
                    autoJoinTxt = self.trUtf8("Yes")
                else:
                    autoJoinTxt = self.trUtf8("No")
                QTreeWidgetItem(self.channelList, [name, autoJoinTxt])
                self.__network.addChannel(channel)
    
    def getNetwork(self):
        """
        Public method to get the network object.
        
        @return edited network object (IrcNetwork)
        """
        self.__network.setName(self.networkEdit.text())
        return self.__network
