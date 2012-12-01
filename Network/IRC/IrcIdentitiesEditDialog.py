# -*- coding: utf-8 -*-

# Copyright (c) 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the identities management dialog.
"""

import copy

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QDialog, QInputDialog, QLineEdit, QItemSelectionModel

from E5Gui import E5MessageBox
from E5Gui.E5Application import e5App

from .Ui_IrcIdentitiesEditDialog import Ui_IrcIdentitiesEditDialog

from .IrcNetworkManager import IrcIdentity

import Utilities
import UI.PixmapCache


# TODO: implement "Away" page
# TODO: implement "Advanced" page
class IrcIdentitiesEditDialog(QDialog, Ui_IrcIdentitiesEditDialog):
    """
    Class implementing the identities management dialog.
    """
    def __init__(self, manager, identityName, parent=None):
        """
        Constructor
        
        @param manager reference to the IRC network manager object (IrcNetworkManager)
        @param identityName name of the identity to be selected (string)
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        self.addButton.setIcon(UI.PixmapCache.getIcon("plus.png"))
        self.copyButton.setIcon(UI.PixmapCache.getIcon("editCopy.png"))
        self.renameButton.setIcon(UI.PixmapCache.getIcon("editRename.png"))
        self.deleteButton.setIcon(UI.PixmapCache.getIcon("minus.png"))
        self.nicknameAddButton.setIcon(UI.PixmapCache.getIcon("plus.png"))
        self.nicknameDeleteButton.setIcon(UI.PixmapCache.getIcon("minus.png"))
        self.nicknameUpButton.setIcon(UI.PixmapCache.getIcon("1uparrow.png"))
        self.nicknameDownButton.setIcon(UI.PixmapCache.getIcon("1downarrow.png"))
        
        self.__manager = manager
        
        self.__identities = self.__manager.getIdentities()
        self.__currentIdentity = None
        
        identities = list(sorted(self.__manager.getIdentityNames()))
        identities[identities.index(IrcIdentity.DefaultIdentityName)] = \
            IrcIdentity.DefaultIdentityDisplay
        self.identitiesCombo.addItems(identities)
        if identityName == IrcIdentity.DefaultIdentityName:
            identityName = IrcIdentity.DefaultIdentityDisplay
        index = self.identitiesCombo.findText(identityName)
        if index == -1:
            index = 0
            identityName = self.identitiesCombo.itemText(0)
        self.identitiesCombo.setCurrentIndex(index)
        
        self.on_identitiesCombo_currentIndexChanged(identityName)

    def __updateIdentitiesButtons(self):
        """
        Private slot to update the status of the identity related buttons.
        """
        enable = self.identitiesCombo.currentText() != IrcIdentity.DefaultIdentityDisplay
        self.renameButton.setEnabled(enable)
        self.deleteButton.setEnabled(enable)
    
    @pyqtSlot(str)
    def on_identitiesCombo_currentIndexChanged(self, identity):
        """
        Private slot to handle the selection of an identity.
        """
        if identity == IrcIdentity.DefaultIdentityDisplay:
            identity = IrcIdentity.DefaultIdentityName
        self.__updateIdentitiesButtons()
        
        if self.__currentIdentity and not self.__checkCurrentIdentity():
            return
        
        self.__refreshCurrentIdentity()
        
        self.__currentIdentity = self.__identities[identity]
        
        # TODO: update of tab widget not implemented yet
        self.realnameEdit.setText(self.__currentIdentity.getRealName())
        self.nicknamesList.clear()
        self.nicknamesList.addItems(self.__currentIdentity.getNickNames())
        self.serviceEdit.setText(self.__currentIdentity.getServiceName())
        self.passwordEdit.setText(self.__currentIdentity.getPassword())
        
        self.__updateIdentitiesButtons()
        self.__updateNicknameUpDownButtons()
        self.__updateNicknameButtons()
##    void IdentityDialog::updateIdentity(int index)
##    {
##        m_insertRememberLineOnAwayChBox->setChecked(m_currentIdentity->getInsertRememberLineOnAway());
##        m_awayMessageEdit->setText(m_currentIdentity->getAwayMessage());
##        m_awayNickEdit->setText(m_currentIdentity->getAwayNickname());
##        awayCommandsGroup->setChecked(m_currentIdentity->getRunAwayCommands());
##        m_awayEdit->setText(m_currentIdentity->getAwayCommand());
##        m_unAwayEdit->setText(m_currentIdentity->getReturnCommand());
##        automaticAwayGroup->setChecked(m_currentIdentity->getAutomaticAway());
##        m_awayInactivitySpin->setValue(m_currentIdentity->getAwayInactivity());
##        m_automaticUnawayChBox->setChecked(m_currentIdentity->getAutomaticUnaway());
##
##        m_sCommandEdit->setText(m_currentIdentity->getShellCommand());
##        m_codecCBox->setCurrentIndex(Konversation::IRCCharsets::self()->shortNameToIndex(m_currentIdentity->getCodecName()));
##        m_loginEdit->setText(m_currentIdentity->getIdent());
##        m_quitEdit->setText(m_currentIdentity->getQuitReason());
##        m_partEdit->setText(m_currentIdentity->getPartReason());
##        m_kickEdit->setText(m_currentIdentity->getKickReason());
##    }
    
    def __refreshCurrentIdentity(self):
        """
        Private method to read back the data for the current identity.
        """
        if self.__currentIdentity is None:
            return
        
        self.__currentIdentity.setRealName(self.realnameEdit.text())
        self.__currentIdentity.setNickNames([self.nicknamesList.item(row).text()
            for row in range(self.nicknamesList.count())])
        self.__currentIdentity.setServiceName(self.serviceEdit.text())
        self.__currentIdentity.setPassword(self.passwordEdit.text())
##
##    void IdentityDialog::refreshCurrentIdentity()
##    {
##        m_currentIdentity->setInsertRememberLineOnAway(m_insertRememberLineOnAwayChBox->isChecked());
##        m_currentIdentity->setAwayMessage(m_awayMessageEdit->text());
##        m_currentIdentity->setAwayNickname(m_awayNickEdit->text());
##        m_currentIdentity->setRunAwayCommands(awayCommandsGroup->isChecked());
##        m_currentIdentity->setAwayCommand(m_awayEdit->text());
##        m_currentIdentity->setReturnCommand(m_unAwayEdit->text());
##        m_currentIdentity->setAutomaticAway(automaticAwayGroup->isChecked());
##        m_currentIdentity->setAwayInactivity(m_awayInactivitySpin->value());
##        m_currentIdentity->setAutomaticUnaway(m_automaticUnawayChBox->isChecked());
##
##        m_currentIdentity->setShellCommand(m_sCommandEdit->text());
##        if(m_codecCBox->currentIndex() >= 0 && m_codecCBox->currentIndex() < Konversation::IRCCharsets::self()->availableEncodingShortNames().count())
##            m_currentIdentity->setCodecName(Konversation::IRCCharsets::self()->availableEncodingShortNames()[m_codecCBox->currentIndex()]);
##        m_currentIdentity->setIdent(m_loginEdit->text());
##        m_currentIdentity->setQuitReason(m_quitEdit->text());
##        m_currentIdentity->setPartReason(m_partEdit->text());
##        m_currentIdentity->setKickReason(m_kickEdit->text());
##    }
##
    
    def __checkCurrentIdentity(self):
        """
        Private method to check the data for the current identity.
        
        @return flag indicating a successful check (boolean)
        """
        if self.nicknamesList.count() == 0:
            E5MessageBox.critical(self,
                self.trUtf8("Edit Identity"),
                self.trUtf8("""The identity must contain at least one nick name."""))
            block = self.identitiesCombo.blockSignals(True)
            identity = self.__currentIdentity.getName()
            if identity == IrcIdentity.DefaultIdentityName:
                identity = IrcIdentity.DefaultIdentityDisplay
            self.identitiesCombo.setCurrentIndex(self.identitiesCombo.findText(identity))
            self.identitiesCombo.blockSignals(block)
            self.identityTabWidget.setCurrentIndex(0)
            self.nicknameEdit.setFocus()
            return False
        
        if not self.realnameEdit.text():
            E5MessageBox.critical(self,
                self.trUtf8("Edit Identity"),
                self.trUtf8("""The identity must have a real name."""))
            block = self.identitiesCombo.blockSignals(True)
            identity = self.__currentIdentity.getName()
            if identity == IrcIdentity.DefaultIdentityName:
                identity = IrcIdentity.DefaultIdentityDisplay
            self.identitiesCombo.setCurrentIndex(self.identitiesCombo.findText(identity))
            self.identitiesCombo.blockSignals(block)
            self.identityTabWidget.setCurrentIndex(0)
            self.realnameEdit.setFocus()
            return False
        
        return True
    
    @pyqtSlot()
    def on_addButton_clicked(self):
        """
        Private slot to add a new idntity.
        """
        name, ok = QInputDialog.getText(
            self,
            self.trUtf8("Add Identity"),
            self.trUtf8("Identity Name:"),
            QLineEdit.Normal)
        
        if ok:
            if name:
                if name in self.__identities:
                    E5MessageBox.critical(self,
                        self.trUtf8("Add Identity"),
                        self.trUtf8("""An identity named <b>{0}</b> already exists."""
                                    """ You must provide a different name.""").format(
                            name))
                    self.on_addButton_clicked()
                else:
                    identity = IrcIdentity(name)
                    identity.setIdent(Utilities.getUserName())
                    identity.setRealName(Utilities.getRealName())
                    self.__identities[name] = identity
                    self.identitiesCombo.addItem(name)
                    self.identitiesCombo.setCurrentIndex(self.identitiesCombo.count() - 1)
            else:
                E5MessageBox.critical(self,
                    self.trUtf8("Add Identity"),
                    self.trUtf8("""The identity has to have a name."""))
                self.on_addButton_clicked()
    
    @pyqtSlot()
    def on_copyButton_clicked(self):
        """
        Private slot to copy the selected identity.
        """
        currentIdentity = self.identitiesCombo.currentText()
        name, ok = QInputDialog.getText(
            self,
            self.trUtf8("Copy Identity"),
            self.trUtf8("Identity Name:"),
            QLineEdit.Normal,
            currentIdentity)
        
        if ok:
            if name:
                if name in self.__identities:
                    E5MessageBox.critical(self,
                        self.trUtf8("Copy Identity"),
                        self.trUtf8("""An identity named <b>{0}</b> already exists."""
                                    """ You must provide a different name.""").format(
                            name))
                    self.on_copyButton_clicked()
                else:
                    identity = copy.deepcopy(self.__currentIdentity)
                    identity.setName(name)
                    self.__identities[name] = identity
                    self.identitiesCombo.addItem(name)
                    self.identitiesCombo.setCurrentIndex(self.identitiesCombo.count() - 1)
            else:
                E5MessageBox.critical(self,
                    self.trUtf8("Copy Identity"),
                    self.trUtf8("""The identity has to have a name."""))
                self.on_copyButton_clicked()
    
    @pyqtSlot()
    def on_renameButton_clicked(self):
        """
        Private slot to rename the selected identity.
        """
        currentIdentity = self.identitiesCombo.currentText()
        name, ok = QInputDialog.getText(
            self,
            self.trUtf8("Rename Identity"),
            self.trUtf8("Identity Name:"),
            QLineEdit.Normal,
            currentIdentity)
        
        if ok and name != currentIdentity:
            if name:
                if name in self.__identities:
                    E5MessageBox.critical(self,
                        self.trUtf8("Rename Identity"),
                        self.trUtf8("""An identity named <b>{0}</b> already exists."""
                                    """ You must provide a different name.""").format(
                            name))
                    self.on_renameButton_clicked()
                else:
                    del self.__identities[currentIdentity]
                    self.__currentIdentity.setName(name)
                    self.__identities[name] = self.__currentIdentity
                    self.identitiesCombo.setItemText(
                        self.identitiesCombo.currentIndex(), name)
            else:
                E5MessageBox.critical(self,
                    self.trUtf8("Copy Identity"),
                    self.trUtf8("""The identity has to have a name."""))
                self.on_renameButton_clicked()
    
    @pyqtSlot()
    def on_deleteButton_clicked(self):
        """
        Private slot to rename the selected identity.
        """
        currentIdentity = self.identitiesCombo.currentText()
        if currentIdentity == IrcIdentity.DefaultIdentityDisplay:
            return
        
        inUse = False
        for networkName in self.__manager.getNetworkNames():
            inUse = (
                self.__manager.getNetwork(networkName).getIdentityName() == 
                    currentIdentity)
            if inUse:
                break
        
        if inUse:
            msg = self.trUtf8("""This identity is in use. If you remove it, the network"""
                              """ settings using it will fall back to the default"""
                              """ identity. Should it be deleted anyway?""")
        else:
            msg = self.trUtf8("""Do you really want to delete all information for"""
                              """ this identity?""")
        res = E5MessageBox.yesNo(self,
            self.trUtf8("Delete Identity"),
            msg,
            icon = E5MessageBox.Warning)
        if res:
            del self.__identities[currentIdentity]
            self.identitiesCombo.removeItem(
                self.identitiesCombo.findText(currentIdentity))
    
    def __updateNicknameUpDownButtons(self):
        """
        Private method to set the enabled state of the nick name up and down buttons.
        """
        if len(self.nicknamesList.selectedItems()) == 0:
            self.nicknameUpButton.setEnabled(False)
            self.nicknameDownButton.setEnabled(False)
        else:
            if self.nicknamesList.currentRow() == 0:
                self.nicknameUpButton.setEnabled(False)
                self.nicknameDownButton.setEnabled(True)
            elif self.nicknamesList.currentRow() == self.nicknamesList.count() - 1:
                self.nicknameUpButton.setEnabled(True)
                self.nicknameDownButton.setEnabled(False)
            else:
                self.nicknameUpButton.setEnabled(True)
                self.nicknameDownButton.setEnabled(True)
    
    def __updateNicknameButtons(self):
        """
        Private slot to update the nick name buttons except the up and down buttons.
        """
        self.nicknameDeleteButton.setEnabled(
            len(self.nicknamesList.selectedItems()) != 0)
        
        self.nicknameAddButton.setEnabled(self.nicknameEdit.text() != "")
    
    @pyqtSlot(str)
    def on_nicknameEdit_textEdited(self, nick):
        """
        Private slot handling a change of the nick name.
        """
        itm = self.nicknamesList.currentItem()
        if itm:
            itm.setText(nick)
        
        self.__updateNicknameButtons()
    
    @pyqtSlot()
    def on_nicknamesList_itemSelectionChanged(self):
        """
        Private slot handling the selection of a nick name.
        """
        items = self.nicknamesList.selectedItems()
        if items:
            self.nicknameEdit.setText(items[0].text())
        
        self.__updateNicknameUpDownButtons()
        self.__updateNicknameButtons()
        
        self.nicknameEdit.setFocus()
    
    @pyqtSlot()
    def on_nicknameAddButton_clicked(self):
        """
        Private slot to add a new nickname.
        """
        nick = self.nicknameEdit.text()
        if nick not in [self.nicknamesList.item(row).text()
                        for row in range(self.nicknamesList.count())]:
            self.nicknamesList.insertItem(0, nick)
        self.nicknamesList.setCurrentRow(0, QItemSelectionModel.Clear)
        self.nicknameEdit.clear()
        self.__updateNicknameButtons()
    
    @pyqtSlot()
    def on_nicknameDeleteButton_clicked(self):
        """
        Private slot to delete a nick name.
        """
        itm = self.nicknamesList.takeItem(self.nicknamesList.currentRow())
        del itm
        self.__updateNicknameButtons()
    
    @pyqtSlot()
    def on_nicknameUpButton_clicked(self):
        """
        Private slot to move the selected entry up one row.
        """
        row = self.nicknamesList.currentRow()
        if row > 0:
            itm = self.nicknamesList.takeItem(row)
            row -= 1
            self.nicknamesList.insertItem(row, itm)
            self.nicknamesList.setCurrentItem(itm)
    
    @pyqtSlot()
    def on_nicknameDownButton_clicked(self):
        """
        Private slot to move the selected entry down one row.
        """
        row = self.nicknamesList.currentRow()
        if row < self.nicknamesList.count() - 1:
            itm = self.nicknamesList.takeItem(row)
            row += 1
            self.nicknamesList.insertItem(row, itm)
            self.nicknamesList.setCurrentItem(itm)
    
    def accept(self):
        """
        Public slot handling the acceptance of the dialog.
        """
        if not self.__checkCurrentIdentity():
            return
        
        self.__refreshCurrentIdentity()
        self.__manager.setIdentities(self.__identities)
        
        super().accept()
