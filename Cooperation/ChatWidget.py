# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the chat dialog.
"""

from PyQt4.QtCore import Qt, pyqtSlot, pyqtSignal, QDateTime, QPoint, QFileInfo
from PyQt4.QtGui import QWidget, QColor, QListWidgetItem, QMenu, QFileDialog, \
    QMessageBox, QApplication

from E5Gui.E5Application import e5App

from QScintilla.Editor import Editor

from .CooperationClient import CooperationClient

from .Ui_ChatWidget import Ui_ChatWidget

import Preferences
import Utilities
import UI.PixmapCache

class ChatWidget(QWidget, Ui_ChatWidget):
    """
    Class implementing the chat dialog.
    
    @signal connected(connected) emitted to signal a change of the connected
            state (boole)
    @signal editorCommand(hash, filename, message) emitted when an editor command
            has been received (string, string, string)
    @signal shareEditor(share) emitted to signal a share is requested (bool)
    @signal startEdit() emitted to start a shared edit session
    @signal sendEdit() emitted to send a shared edit session
    @signal cancelEdit() emitted to cancel a shared edit session
    """
    connected = pyqtSignal(bool)
    editorCommand = pyqtSignal(str, str, str)
    
    shareEditor = pyqtSignal(bool)
    startEdit = pyqtSignal()
    sendEdit = pyqtSignal()
    cancelEdit = pyqtSignal()
    
    def __init__(self, port = -1, parent = None):
        """
        Constructor
        
        @param port port to be used for the cooperation server (integer)
        @param parent reference to the parent widget (QWidget)
        """
        QWidget.__init__(self, parent)
        self.setupUi(self)
        
        self.shareButton.setIcon(
            UI.PixmapCache.getIcon("sharedEditDisconnected.png"))
        self.startEditButton.setIcon(
            UI.PixmapCache.getIcon("sharedEditStart.png"))
        self.sendEditButton.setIcon(
            UI.PixmapCache.getIcon("sharedEditSend.png"))
        self.cancelEditButton.setIcon(
            UI.PixmapCache.getIcon("sharedEditCancel.png"))
        
        self.__client = CooperationClient()
        self.__myNickName = self.__client.nickName()
        
        self.__chatMenu = QMenu(self)
        self.__clearChatAct = \
            self.__chatMenu.addAction(self.trUtf8("Clear"), self.__clearChat)
        self.__saveChatAct = \
            self.__chatMenu.addAction(self.trUtf8("Save"), self.__saveChat)
        self.__copyChatAct = \
            self.__chatMenu.addAction(self.trUtf8("Copy"), self.__copyChat)
        
        self.messageEdit.returnPressed.connect(self.__handleMessage)
        self.sendButton.clicked.connect(self.__handleMessage)
        self.__client.newMessage.connect(self.appendMessage)
        self.__client.newParticipant.connect(self.__newParticipant)
        self.__client.participantLeft.connect(self.__participantLeft)
        self.__client.connectionError.connect(self.__showErrorMessage)
        self.__client.cannotConnect.connect(self.__initialConnectionRefused)
        self.__client.editorCommand.connect(self.__editorCommandMessage)
        
        self.serverButton.setText(self.trUtf8("Start Server"))
        self.serverLed.setColor(QColor(Qt.red))
        if port == -1:
            port = Preferences.getCooperation("ServerPort")
        
        self.portSpin.setValue(port)
        self.serverPortSpin.setValue(port)
        
        self.__setConnected(False)
        
        if Preferences.getCooperation("AutoStartServer"):
            self.on_serverButton_clicked()
    
    def __handleMessage(self):
        """
        Private slot handling the Return key pressed in the message edit.
        """
        text = self.messageEdit.text()
        if text == "":
            return
        
        if text.startswith("/"):
            self.__showErrorMessage(
                self.trUtf8("! Unknown command: {0}\n").format(text.split()[0]))
        else:
            self.__client.sendMessage(text)
            self.appendMessage(self.__myNickName, text)
        
        self.messageEdit.clear()
    
    def __newParticipant(self, nick):
        """
        Private slot handling a new participant joining.
        
        @param nick nick name of the new participant (string)
        """
        if nick == "":
            return
        
        color = self.chatEdit.textColor()
        self.chatEdit.setTextColor(Qt.gray)
        self.chatEdit.append(
            QDateTime.currentDateTime().toString(Qt.SystemLocaleLongDate) + ":")
        self.chatEdit.append(self.trUtf8("* {0} has joined.\n").format(nick))
        self.chatEdit.setTextColor(color)
        
        QListWidgetItem(
            UI.PixmapCache.getIcon(
                "chatUser{0}.png".format(1 + self.usersList.count() % 6)), 
            nick, self.usersList)
        
        if not self.__connected:
            self.__setConnected(True)
    
    def __participantLeft(self, nick):
        """
        Private slot handling a participant leaving the session.
        
        @param nick nick name of the participant (string)
        """
        if nick == "":
            return
        
        items = self.usersList.findItems(nick, Qt.MatchExactly)
        for item in items:
            self.usersList.takeItem(self.usersList.row(item))
            del item
            
            color = self.chatEdit.textColor()
            self.chatEdit.setTextColor(Qt.gray)
            self.chatEdit.append(
                QDateTime.currentDateTime().toString(Qt.SystemLocaleLongDate) + ":")
            self.chatEdit.append(self.trUtf8("* {0} has left.\n").format(nick))
            self.chatEdit.setTextColor(color)
        
        if not self.__client.hasConnections():
            self.__setConnected(False)
    
    def appendMessage(self, from_, message):
        """
        Public slot to append a message to the display.
        
        @param from_ originator of the message (string)
        @param message message to be appended (string)
        """
        if from_ == "" or message == "":
            return
        
        self.chatEdit.append(
            QDateTime.currentDateTime().toString(Qt.SystemLocaleLongDate) + \
            " <" + from_ + ">:")
        self.chatEdit.append(message + "\n")
        bar = self.chatEdit.verticalScrollBar()
        bar.setValue(bar.maximum())
    
    @pyqtSlot(str)
    def on_hostEdit_textChanged(self, host):
        """
        Private slot handling the entry of a host to connect to.
        
        @param host host to connect to (string)
        """
        if not self.__connected:
            self.connectButton.setEnabled(host != "")
    
    @pyqtSlot()
    def on_connectButton_clicked(self):
        """
        Private slot initiating the connection.
        """
        if not self.__connected:
            if not self.__client.server().isListening():
                self.on_serverButton_clicked()
            if self.__client.server().isListening():
                self.__client.connectToHost(self.hostEdit.text(), self.portSpin.value())
                self.__setConnected(True)
        else:
            self.__client.disconnectConnections()
            self.__setConnected(False)
    
    @pyqtSlot()
    def on_serverButton_clicked(self):
        """
        Private slot to start the server.
        """
        if self.__client.server().isListening():
            self.__client.server().close()
            self.serverButton.setText(self.trUtf8("Start Server"))
            self.serverPortSpin.setEnabled(True)
            if self.serverPortSpin.value() != Preferences.getCooperation("ServerPort"):
                self.serverPortSpin.setValue(Preferences.getCooperation("ServerPort"))
            self.serverLed.setColor(QColor(Qt.red))
        else:
            res, port = self.__client.server().startListening(self.serverPortSpin.value())
            if res:
                self.serverButton.setText(self.trUtf8("Stop Server"))
                self.serverPortSpin.setValue(port)
                self.serverPortSpin.setEnabled(False)
                self.serverLed.setColor(QColor(Qt.green))
            else:
                self.__showErrorMessage(
                    self.trUtf8("! Server Error: {0}\n").format(
                    self.__client.server().errorString())
                )
    
    def __setConnected(self, connected):
        """
        Private slot to set the connected state.
        
        @param connected new connected state (boolean)
        """
        if connected:
            self.connectButton.setText(self.trUtf8("Disconnect"))
            self.connectButton.setEnabled(True)
            self.connectionLed.setColor(QColor(Qt.green))
        else:
            self.connectButton.setText(self.trUtf8("Connect"))
            self.connectButton.setEnabled(self.hostEdit.text() != "")
            self.connectionLed.setColor(QColor(Qt.red))
            self.cancelEditButton.click()
            self.shareButton.click()
        self.__connected = connected
        self.hostEdit.setEnabled(not connected)
        self.portSpin.setEnabled(not connected)
        self.serverButton.setEnabled(not connected)
        self.sharingGroup.setEnabled(connected)
        
        if connected:
            vm = e5App().getObject("ViewManager")
            aw = vm.activeWindow()
            if aw:
                self.checkEditorActions(aw)
    
    def __showErrorMessage(self, message):
        """
        Private slot to show an error message.
        
        @param message error message to show (string)
        """
        color = self.chatEdit.textColor()
        self.chatEdit.setTextColor(Qt.red)
        self.chatEdit.append(
            QDateTime.currentDateTime().toString(Qt.SystemLocaleLongDate) + ":")
        self.chatEdit.append(message)
        self.chatEdit.setTextColor(color)
    
    def __initialConnectionRefused(self):
        """
        Private slot to handle the refusal of the initial connection.
        """
        self.__setConnected(False)
    
    def preferencesChanged(self):
        """
        Public slot to handle a change of preferences.
        """
        if not self.__client.server().isListening():
            self.serverPortSpin.setValue(Preferences.getCooperation("ServerPort"))
            if Preferences.getCooperation("AutoStartServer"):
                self.on_serverButton_clicked()
    
    def getClient(self):
        """
        Public method to get a reference to the cooperation client.
        """
        return self.__client
    
    def __editorCommandMessage(self, hash, fileName, message):
        """
        Private slot to handle editor command messages from the client.
        
        @param hash hash of the project (string)
        @param fileName project relative file name of the editor (string)
        @param message command message (string)
        """
        self.editorCommand.emit(hash, fileName, message)
        
        if message.startswith(Editor.StartEditToken + Editor.Separator) or \
           message.startswith(Editor.EndEditToken + Editor.Separator):
            vm = e5App().getObject("ViewManager")
            aw = vm.activeWindow()
            if aw:
                self.checkEditorActions(aw)
    
    @pyqtSlot(bool)
    def on_shareButton_clicked(self, checked):
        """
        Private slot to share the current editor.
        
        @param checked flag indicating the button state (boolean)
        """
        if checked:
            self.shareButton.setIcon(
                UI.PixmapCache.getIcon("sharedEditConnected.png"))
        else:
            self.shareButton.setIcon(
                UI.PixmapCache.getIcon("sharedEditDisconnected.png"))
        self.startEditButton.setEnabled(checked)
        
        self.shareEditor.emit(checked)
    
    @pyqtSlot(bool)
    def on_startEditButton_clicked(self, checked):
        """
        Private slot to start a shared edit session.
        
        @param checked flag indicating the button state (boolean)
        """
        if checked:
            self.sendEditButton.setEnabled(True)
            self.cancelEditButton.setEnabled(True)
            self.shareButton.setEnabled(False)
            self.startEditButton.setEnabled(False)
            
            self.startEdit.emit()
    
    @pyqtSlot()
    def on_sendEditButton_clicked(self):
        """
        Private slot to end a shared edit session and send the changes.
        """
        self.sendEditButton.setEnabled(False)
        self.cancelEditButton.setEnabled(False)
        self.shareButton.setEnabled(True)
        self.startEditButton.setEnabled(True)
        self.startEditButton.setChecked(False)
        
        self.sendEdit.emit()
    
    @pyqtSlot()
    def on_cancelEditButton_clicked(self):
        """
        Private slot to cancel a shared edit session.
        """
        self.sendEditButton.setEnabled(False)
        self.cancelEditButton.setEnabled(False)
        self.shareButton.setEnabled(True)
        self.startEditButton.setEnabled(True)
        self.startEditButton.setChecked(False)
        
        self.cancelEdit.emit()
    
    def checkEditorActions(self, editor):
        """
        Public slot to set action according to an editor's state.
        
        @param editor reference to the editor (Editor)
        """
        shareable, sharing, editing, remoteEditing = editor.getSharingStatus()
        
        self.shareButton.setChecked(sharing)
        if sharing:
            self.shareButton.setIcon(
                UI.PixmapCache.getIcon("sharedEditConnected.png"))
        else:
            self.shareButton.setIcon(
                UI.PixmapCache.getIcon("sharedEditDisconnected.png"))
        self.startEditButton.setChecked(editing)
        
        self.shareButton.setEnabled(shareable and not editing)
        self.startEditButton.setEnabled(sharing and not editing and not remoteEditing)
        self.sendEditButton.setEnabled(editing)
        self.cancelEditButton.setEnabled(editing)
    
    @pyqtSlot(QPoint)
    def on_chatEdit_customContextMenuRequested(self, pos):
        """
        Private slot to show the context menu for the chat.
        
        @param pos the position of the mouse pointer (QPoint)
        """
        self.__saveChatAct.setEnabled(self.chatEdit.toPlainText() != "")
        self.__copyChatAct.setEnabled(self.chatEdit.toPlainText() != "")
        self.__chatMenu.popup(self.chatEdit.mapToGlobal(pos))
    
    def __clearChat(self):
        """
        Private slot to clear the contents of the chat display.
        """
        self.chatEdit.clear()
    
    def __saveChat(self):
        """
        Private slot to save the contents of the chat display.
        """
        txt = self.chatEdit.toPlainText()
        if txt:
            fname, selectedFilter = QFileDialog.getSaveFileNameAndFilter(\
                self,
                self.trUtf8("Save Chat"),
                "",
                self.trUtf8("Text Files (*.txt);;All Files (*)"),
                None,
                QFileDialog.Options(QFileDialog.DontConfirmOverwrite))
            if fname:
                ext = QFileInfo(fname).suffix()
                if not ext:
                    ex = selectedFilter.split("(*")[1].split(")")[0]
                    if ex:
                        fname += ex
                if QFileInfo(fname).exists():
                    res = QMessageBox.warning(self,
                        self.trUtf8("Save Chat"),
                        self.trUtf8("<p>The file <b>{0}</b> already exists.</p>")
                            .format(fname),
                        QMessageBox.StandardButtons(\
                            QMessageBox.Abort | \
                            QMessageBox.Save),
                        QMessageBox.Abort)
                    if res != QMessageBox.Save:
                        return
                    fname = Utilities.toNativeSeparators(fname)
                
                try:
                    f = open(fname, "w", encoding = "utf-8")
                    f.write(txt)
                    f.close()
                except IOError as err:
                    QMessageBox.critical(self,
                        self.trUtf8("Error saving Chat"),
                        self.trUtf8("""<p>The chat contents could not be written"""
                                    """ to <b>{0}</b></p><p>Reason: {1}</p>""")\
                            .format(fname, str(err)))
    
    def __copyChat(self):
        """
        Private slot to copy the contents of the chat display to the clipboard.
        """
        txt = self.chatEdit.toPlainText()
        if txt:
            cb = QApplication.clipboard()
            cb.setText(txt)
