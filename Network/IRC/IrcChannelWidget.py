# -*- coding: utf-8 -*-

# Copyright (c) 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the IRC channel widget.
"""

import re

from PyQt4.QtCore import pyqtSlot, pyqtSignal, QDateTime, QPoint
from PyQt4.QtGui import QWidget, QListWidgetItem, QIcon, QPainter, QMenu

from E5Gui import E5MessageBox
from E5Gui.E5Application import e5App

from .Ui_IrcChannelWidget import Ui_IrcChannelWidget

from .IrcUtilities import ircFilter, ircTimestamp, getChannelModesDict

import Utilities
import UI.PixmapCache
import Preferences


class IrcUserItem(QListWidgetItem):
    """
    Class implementing a list widget item containing an IRC channel user.
    """
    Normal = 0x00       # no privileges
    Operator = 0x01     # channel operator
    Voice = 0x02        # voice operator
    Admin = 0x04        # administrator
    Halfop = 0x08       # half operator
    Owner = 0x10        # channel owner
    Away = 0x80         # user away
    
    PrivilegeMapping = {
        "a": Away,
        "o": Operator,
        "O": Owner,
        "v": Voice,
        
    }
    
    def __init__(self, name, parent=None):
        """
        Constructor
        
        @param name string with user name and privilege prefix (string)
        @param parent reference to the parent widget (QListWidget or QListWidgetItem)
        """
        super().__init__(name, parent)
        
        self.__privilege = IrcUserItem.Normal
        self.__name = name
        
        self.__setIcon()
    
    def name(self):
        """
        Public method to get the user name.
        
        @return user name (string)
        """
        return self.__name
    
    def setName(self, name):
        """
        Public method to set a new nick name.
        
        @param name new nick name for the user (string)
        """
        self.__name = name
        self.setText(name)
    
    def changePrivilege(self, privilege):
        """
        Public method to set or unset a user privilege.
        
        @param privilege privilege to set or unset (string)
        """
        oper = privilege[0]
        priv = privilege[1]
        if oper == "+":
            if priv in IrcUserItem.PrivilegeMapping:
                self.__privilege |= IrcUserItem.PrivilegeMapping[priv]
        elif oper == "-":
            if priv in IrcUserItem.PrivilegeMapping:
                self.__privilege &= ~IrcUserItem.PrivilegeMapping[priv]
        self.__setIcon()
    
    def clearPrivileges(self):
        """
        Public method to clear the user privileges.
        """
        self.__privilege = IrcUserItem.Normal
        self.__setIcon()
    
    def __setIcon(self):
        """
        Private method to set the icon dependent on user privileges.
        """
        # step 1: determine the icon
        if self.__privilege & IrcUserItem.Voice:
            icon = UI.PixmapCache.getIcon("ircVoice.png")
        elif self.__privilege & IrcUserItem.Owner:
            icon = UI.PixmapCache.getIcon("ircOwner.png")
        elif self.__privilege & IrcUserItem.Operator:
            icon = UI.PixmapCache.getIcon("ircOp.png")
        elif self.__privilege & IrcUserItem.Halfop:
            icon = UI.PixmapCache.getIcon("ircHalfop.png")
        elif self.__privilege & IrcUserItem.Admin:
            icon = UI.PixmapCache.getIcon("ircAdmin.png")
        else:
            icon = UI.PixmapCache.getIcon("ircNormal.png")
        if self.__privilege & IrcUserItem.Away:
            icon = self.__awayIcon(icon)
        
        # step 2: set the icon
        self.setIcon(icon)
    
    def __awayIcon(self, icon):
        """
        Private method to convert an icon to an away icon.
        
        @param icon icon to be converted (QIcon)
        @param away icon (QIcon)
        """
        pix1 = icon.pixmap(16, 16)
        pix2 = UI.PixmapCache.getPixmap("ircAway.png")
        painter = QPainter(pix1)
        painter.drawPixmap(0, 0, pix2)
        painter.end()
        return QIcon(pix1)


class IrcChannelWidget(QWidget, Ui_IrcChannelWidget):
    """
    Class implementing the IRC channel widget.
    
    @signal sendData(str) emitted to send a message to the channel
    @signal channelClosed(str) emitted after the user has left the channel
    """
    sendData = pyqtSignal(str)
    channelClosed = pyqtSignal(str)
    
    UrlRe = re.compile(r"""((?:http|ftp|https):\/\/[\w\-_]+(?:\.[\w\-_]+)+"""
        r"""(?:[\w\-\.,@?^=%&amp;:/~\+#]*[\w\-\@?^=%&amp;/~\+#])?)""")
    
    JoinIndicator = "--&gt;"
    LeaveIndicator = "&lt;--"
    MessageIndicator = "***"
    
    # TODO: add context menu to users list with these entries:
    #       Whois
    #       Private Message
    # TODO: add "Auto WHO" functionality (WHO <channel> %nf)
    #       The possible combinations for this field are listed below:
    #       H The user is not away.
    #       G The user is set away.
    #       * The user is an IRC operator.
    #       @ The user is a channel op in the channel listed in the first field.
    #       + The user is voiced in the channel listed.
    # TODO: add context menu to messages pane with these entries:
    #       Copy
    #       Copy Link Location
    #       Copy All
    #       Clear
    #       Save
    #       Remember Position
    # TODO: Remember current position with <hr/> when widget is invisible
    # TODO: Remember current position with <hr/> when away and configured accordingly
    # TODO: Check away indication in the user list
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        self.__ui = e5App().getObject("UserInterface")
        
        self.__initMessagesMenu()
        
        self.__name = ""
        self.__userName = ""
        self.__partMessage = ""
        self.__prefixToPrivilege = {}
        
        self.__markerLine = ""
        
        self.__patterns = [
            # :foo_!n=foo@foohost.bar.net PRIVMSG #eric-ide :some long message
            (re.compile(r":([^!]+).*\sPRIVMSG\s([^ ]+)\s:(.*)"), self.__message),
            # :foo_!n=foo@foohost.bar.net JOIN :#eric-ide
            # :detlev_!~detlev@mnch-5d876cfa.pool.mediaWays.net JOIN #eric-ide
            (re.compile(r":([^!]+)!([^ ]+)\sJOIN\s:?([^ ]+)"), self.__userJoin),
            # :foo_!n=foo@foohost.bar.net PART #eric-ide :part message
            (re.compile(r":([^!]+).*\sPART\s([^ ]+)\s:(.*)"), self.__userPart),
            # :foo_!n=foo@foohost.bar.net PART #eric-ide
            (re.compile(r":([^!]+).*\sPART\s([^ ]+)\s*"), self.__userPart),
            # :foo_!n=foo@foohost.bar.net QUIT :quit message
            (re.compile(r":([^!]+).*\sQUIT\s:(.*)"), self.__userQuit),
            # :foo_!n=foo@foohost.bar.net QUIT
            (re.compile(r":([^!]+).*\sQUIT\s*"), self.__userQuit),
            # :foo_!n=foo@foohost.bar.net NICK :newnick
            (re.compile(r":([^!]+).*\sNICK\s:(.*)"), self.__userNickChange),
            # :barty!n=foo@foohost.bar.net MODE #eric-ide +o foo_
            (re.compile(r":([^!]+).*\sMODE\s([^ ]+)\s([^ ]+)\s([^ ]+).*"),
                self.__setUserPrivilege),
            # :zelazny.freenode.net 324 foo_ #eric-ide +cnt
            (re.compile(r":.*\s324\s.*\s([^ ]+)\s(.+)"), self.__channelModes),
            # :zelazny.freenode.net 328 foo_ #eric-ide :http://www.buggeroff.com/
            (re.compile(r":.*\s328\s.*\s([^ ]+)\s:(.+)"), self.__channelUrl),
            # :zelazny.freenode.net 329 foo_ #eric-ide 1353001005
            (re.compile(r":.*\s329\s.*\s([^ ]+)\s(.+)"), self.__channelCreated),
            # :zelazny.freenode.net 332 foo_ #eric-ide :eric support channel
            (re.compile(r":.*\s332\s.*\s([^ ]+)\s:(.*)"), self.__setTopic),
            # :zelazny.freenode.net foo_ 333 #eric-ide foo 1353089020
            (re.compile(r":.*\s333\s.*\s([^ ]+)\s([^ ]+)\s(\d+)"), self.__topicCreated), 
            # :zelazny.freenode.net 353 foo_ @ #eric-ide :@user1 +user2 user3
            (re.compile(r":.*\s353\s.*\s.\s([^ ]+)\s:(.*)"), self.__userList),
            # :zelazny.freenode.net 366 foo_ #eric-ide :End of /NAMES list.
            (re.compile(r":.*\s366\s.*\s([^ ]+)\s:(.*)"), self.__ignore),
        ]
    
    @pyqtSlot()
    def on_messageEdit_returnPressed(self):
        """
        Private slot to send a message to the channel.
        """
        msg = self.messageEdit.text()
        if msg:
            self.messages.append(
                '<font color="{0}">{2} <b>&lt;</b><font color="{1}">{3}</font>'
                '<b>&gt;</b> {4}</font>'.format(
                Preferences.getIrc("ChannelMessageColour"),
                Preferences.getIrc("OwnNickColour"),
                ircTimestamp(), self.__userName, Utilities.html_encode(msg)))
            self.sendData.emit("PRIVMSG " + self.__name + " :" + msg)
            self.messageEdit.clear()
    
    def requestLeave(self):
        """
        Public method to leave the channel.
        """
        ok = E5MessageBox.yesNo(self,
            self.trUtf8("Leave IRC channel"),
            self.trUtf8("""Do you really want to leave the IRC channel <b>{0}</b>?""")\
                .format(self.__name))
        if ok:
            self.sendData.emit("PART " + self.__name + " :" + self.__partMessage)
            self.channelClosed.emit(self.__name)
    
    def name(self):
        """
        Public method to get the name of the channel.
        
        @return name of the channel (string)
        """
        return self.__name
    
    def setName(self, name):
        """
        Public method to set the name of the channel.
        
        @param name of the channel (string)
        """
        self.__name = name
    
    def getUsersCount(self):
        """
        Public method to get the users count of the channel.
        
        @return users count of the channel (integer)
        """
        return self.usersList.count()
    
    def userName(self):
        """
        Public method to get the nick name of the user.
        
        @return nick name of the user (string)
        """
        return self.__userName
    
    def setUserName(self, name):
        """
        Public method to set the user name for the channel.
        
        @param name user name for the channel (string)
        """
        self.__userName = name.lower()
    
    def partMessage(self):
        """
        Public method to get the part message.
        
        @return part message (string)
        """
        return self.__partMessage
    
    def setPartMessage(self, message):
        """
        Public method to set the part message.
        
        @param message message to be used for PART messages (string)
        """
        self.__partMessage = message
    
    def handleMessage(self, line):
        """
        Public method to handle the message sent by the server.
        
        @param line server message (string)
        @return flag indicating, if the message was handled (boolean)
        """
        for patternRe, patternFunc in self.__patterns:
            match = patternRe.match(line)
            if match is not None:
                if patternFunc(match):
                    return True
        
        return False
    
    def __message(self, match):
        """
        Private method to handle messages to the channel.
        
        @param match match object that matched the pattern
        @return flag indicating whether the message was handled (boolean)
        """
        if match.group(2).lower() == self.__name:
            msg = ircFilter(match.group(3))
            self.messages.append(
                '<font color="{0}">{2} <b>&lt;</b><font color="{1}">{3}</font>'
                '<b>&gt;</b> {4}</font>'.format(
                Preferences.getIrc("ChannelMessageColour"),
                Preferences.getIrc("NickColour"),
                ircTimestamp(), match.group(1),
                msg))
            if Preferences.getIrc("ShowNotifications"):
                if Preferences.getIrc("NotifyMessage"):
                    self.__ui.showNotification(UI.PixmapCache.getPixmap("irc48.png"),
                        self.trUtf8("Channel Message"), msg)
                elif Preferences.getIrc("NotifyNick") and self.__userName in msg:
                    self.__ui.showNotification(UI.PixmapCache.getPixmap("irc48.png"),
                        self.trUtf8("Nick mentioned"), msg)
            return True
        
        return False
    
    def __userJoin(self, match):
        """
        Private method to handle a user joining the channel.
        
        @param match match object that matched the pattern
        @return flag indicating whether the message was handled (boolean)
        """
        if match.group(3).lower() == self.__name:
            if self.__userName != match.group(1):
                IrcUserItem(match.group(1), self.usersList)
                msg = self.trUtf8("{0} has joined the channel {1} ({2}).").format(
                    match.group(1), self.__name, match.group(2))
                self.__addManagementMessage(IrcChannelWidget.JoinIndicator, msg)
            else:
                msg = self.trUtf8("You have joined the channel {0} ({1}).").format(
                    self.__name, match.group(2))
                self.__addManagementMessage(IrcChannelWidget.JoinIndicator, msg)
            if Preferences.getIrc("ShowNotifications") and \
               Preferences.getIrc("NotifyJoinPart"):
                self.__ui.showNotification(UI.PixmapCache.getPixmap("irc48.png"),
                    self.trUtf8("Join Channel"), msg)
            return True
        
        return False
    
    def __userPart(self, match):
        """
        Private method to handle a user leaving the channel.
        
        @param match match object that matched the pattern
        @return flag indicating whether the message was handled (boolean)
        """
        if match.group(2).lower() == self.__name:
            itm = self.__findUser(match.group(1))
            self.usersList.takeItem(self.usersList.row(itm))
            del itm
            if match.lastindex == 2:
                msg = self.trUtf8("{0} has left {1}.").format(
                    match.group(1), self.__name)
                nmsg = msg
                self.__addManagementMessage(IrcChannelWidget.LeaveIndicator, msg)
            else:
                msg = self.trUtf8("{0} has left {1}: {2}.").format(
                    match.group(1), self.__name, ircFilter(match.group(3)))
                nmsg = self.trUtf8("{0} has left {1}: {2}.").format(
                    match.group(1), self.__name, match.group(3))
                self.__addManagementMessage(IrcChannelWidget.LeaveIndicator, msg)
            if Preferences.getIrc("ShowNotifications") and \
               Preferences.getIrc("NotifyJoinPart"):
                self.__ui.showNotification(UI.PixmapCache.getPixmap("irc48.png"),
                    self.trUtf8("Leave Channel"), nmsg)
            return True
        
        return False
    
    def __userQuit(self, match):
        """
        Private method to handle a user logging off the server.
        
        @param match match object that matched the pattern
        @return flag indicating whether the message was handled (boolean)
        """
        itm = self.__findUser(match.group(1))
        if itm:
            self.usersList.takeItem(self.usersList.row(itm))
            del itm
            if match.lastindex == 1:
                msg = self.trUtf8("{0} has quit {1}.").format(
                    match.group(1), self.__name)
                self.__addManagementMessage(IrcChannelWidget.MessageIndicator, msg)
            else:
                msg = self.trUtf8("{0} has quit {1}: {2}.").format(
                    match.group(1), self.__name, ircFilter(match.group(2)))
                self.__addManagementMessage(IrcChannelWidget.MessageIndicator, msg)
            if Preferences.getIrc("ShowNotifications") and \
               Preferences.getIrc("NotifyJoinPart"):
                self.__ui.showNotification(UI.PixmapCache.getPixmap("irc48.png"),
                    self.trUtf8("Quit"), msg)
        
        # always return False for other channels and server to process
        return False
    
    def __userNickChange(self, match):
        """
        Private method to handle a nickname change of a user.
        
        @param match match object that matched the pattern
        @return flag indicating whether the message was handled (boolean)
        """
        itm = self.__findUser(match.group(1))
        if itm:
            itm.setName(match.group(2))
            if match.group(1) == self.__userName:
                self.__addManagementMessage(IrcChannelWidget.MessageIndicator,
                    self.trUtf8("You are now known as {0}.").format(
                        match.group(2)))
                self.__userName = match.group(2)
            else:
                self.__addManagementMessage(IrcChannelWidget.MessageIndicator,
                    self.trUtf8("User {0} is now known as {1}.").format(
                        match.group(1), match.group(2)))
        
        # always return False for other channels and server to process
        return False
    
    def __userList(self, match):
        """
        Private method to handle the receipt of a list of users of the channel.
        
        @param match match object that matched the pattern
        @return flag indicating whether the message was handled (boolean)
        """
        if match.group(1).lower() == self.__name:
            users = match.group(2).split()
            for user in users:
                userPrivileges, userName = self.__extractPrivilege(user)
                itm = self.__findUser(userName)
                if itm is None:
                    itm = IrcUserItem(userName, self.usersList)
                for privilege in userPrivileges:
                    itm.changePrivilege(privilege)
            return True
        
        return False
    
    def __setTopic(self, match):
        """
        Private method to handle a topic change of the channel.
        
        @param match match object that matched the pattern
        @return flag indicating whether the message was handled (boolean)
        """
        if match.group(1).lower() == self.__name:
            self.topicLabel.setText(match.group(2))
            self.__addManagementMessage(IrcChannelWidget.MessageIndicator,
                ircFilter(self.trUtf8('The channel topic is: "{0}".').format(
                    match.group(2))))
            return True
        
        return False
    
    def __topicCreated(self, match):
        """
        Private method to handle a topic created message.
        
        @param match match object that matched the pattern
        @return flag indicating whether the message was handled (boolean)
        """
        if match.group(1).lower() == self.__name:
            self.__addManagementMessage(IrcChannelWidget.MessageIndicator,
                self.trUtf8("The topic was set by {0} on {1}.").format(
                    match.group(2), QDateTime.fromTime_t(int(match.group(3)))\
                                    .toString("yyyy-MM-dd hh:mm")))
            return True
        
        return False
    
    def __channelUrl(self, match):
        """
        Private method to handle a channel URL message.
        
        @param match match object that matched the pattern
        @return flag indicating whether the message was handled (boolean)
        """
        if match.group(1).lower() == self.__name:
            self.__addManagementMessage(IrcChannelWidget.MessageIndicator,
                ircFilter(self.trUtf8("Channel URL: {0}").format(match.group(2))))
            return True
        
        return False
    
    def __channelModes(self, match):
        """
        Private method to handle a message reporting the channel modes.
        
        @param match match object that matched the pattern
        @return flag indicating whether the message was handled (boolean)
        """
        if match.group(1).lower() == self.__name:
            modesDict = getChannelModesDict()
            modesParameters = match.group(2).split()
            modeString = modesParameters.pop(0)
            modes = []
            for modeChar in modeString:
                if modeChar == "+":
                    continue
                elif modeChar == "k":
                    parameter = modesParameters.pop(0)
                    modes.append(
                        self.trUtf8("password protected ({0})").format(parameter))
                elif modeChar == "l":
                    parameter = modesParameters.pop(0)
                    modes.append(
                        self.trUtf8("limited to %n user(s)", "", int(parameter)))
                elif modeChar in modesDict:
                    modes.append(modesDict[modeChar])
                else:
                    modes.append(modeChar)
            
            self.__addManagementMessage(IrcChannelWidget.MessageIndicator,
                self.trUtf8("Channel modes: {0}.").format(", ".join(modes)))
            
            return True
        
        return False
    
    def __channelCreated(self, match):
        """
        Private method to handle a channel created message.
        
        @param match match object that matched the pattern
        @return flag indicating whether the message was handled (boolean)
        """
        if match.group(1).lower() == self.__name:
            self.__addManagementMessage(IrcChannelWidget.MessageIndicator,
                self.trUtf8("This channel was created on {0}.").format(
                    QDateTime.fromTime_t(int(match.group(2)))\
                        .toString("yyyy-MM-dd hh:mm")))
            return True
        
        return False
    
    def __setUserPrivilege(self, match):
        """
        Private method to handle a change of user privileges for the channel.
        
        @param match match object that matched the pattern
        @return flag indicating whether the message was handled (boolean)
        """
        if match.group(2).lower() == self.__name:
            itm = self.__findUser(match.group(4))
            if itm:
                itm.changePrivilege(match.group(3))
                self.__addManagementMessage(IrcChannelWidget.MessageIndicator,
                    self.trUtf8("{0} sets mode for {1}: {2}.").format(
                        match.group(1), match.group(4), match.group(3)))
            return True
        
        return False
    
    def __ignore(self, match):
        """
        Private method to handle a channel message we are not interested in.
        
        @param match match object that matched the pattern
        @return flag indicating whether the message was handled (boolean)
        """
        if match.group(1).lower() == self.__name:
            return True
        
        return False
    
    def setUserPrivilegePrefix(self, prefixes):
        """
        Public method to set the user privilege to prefix mapping.
        
        @param prefixes dictionary with privilege as key and prefix as value
        """
        self.__prefixToPrivilege = {}
        for privilege, prefix in prefixes.items():
            if prefix:
                self.__prefixToPrivilege[prefix] = privilege
    
    def __findUser(self, name):
        """
        Private method to find the user in the list of users.
        
        @param name user name to search for (string)
        @return reference to the list entry (QListWidgetItem)
        """
        for row in range(self.usersList.count()):
            itm = self.usersList.item(row)
            if itm.name() == name:
                return itm
        
        return None
    
    def __extractPrivilege(self, name):
        """
        Private method to extract the user privileges out of the name.
        
        @param name user name and prefixes (string)
        return list of privileges and user name (list of string, string)
        """
        privileges = []
        while name[0] in self.__prefixToPrivilege:
            prefix = name[0]
            privileges.append(self.__prefixToPrivilege[prefix])
            name = name[1:]
            if name[0] == ",":
                name = name[1:]
        
        return privileges, name
    
    def __addManagementMessage(self, indicator, message):
        """
        Private method to add a channel management message to the list.
        
        @param indicator indicator to be shown (string)
        @param message message to be shown (string)
        @keyparam isLocal flag indicating a message related to the local user (boolean)
        """
        if indicator == self.JoinIndicator:
            color = Preferences.getIrc("JoinChannelColour")
        elif indicator == self.LeaveIndicator:
            color = Preferences.getIrc("LeaveChannelColour")
        else:
            color = Preferences.getIrc("ChannelInfoColour")
        self.messages.append(
            '<font color="{0}">{1} <b>[</b>{2}<b>]</b> {3}</font>'.format(
            color, ircTimestamp(), indicator, message))
    
    def setMarkerLine(self):
        """
        Public method to draw a line to mark the current position.
        """
        self.unsetMarkerLine()
        # TODO: make colors configurable
        self.__markerLine = \
            '<span style=" color:#000000; background-color:#ffff00;">{0}</span>'.format(
            self.trUtf8('--- New From Here ---'))
        self.messages.append(self.__markerLine)
    
    def unsetMarkerLine(self):
        """
        Public method to remove the marker line.
        """
        if self.__markerLine:
            txt = self.messages.toHtml()
            if txt.endswith(self.__markerLine + "</p></body></html>"):
                # remove empty last paragraph
                pos = txt.rfind("<p")
                txt = txt[:pos] + "</body></html>"
            else:
                txt = txt.replace(self.__markerLine, "")
            self.messages.setHtml(txt)
            self.__markerLine = ""
    
    def __initMessagesMenu(self):
        """
        Private slot to initialize the context menu of the messages pane.
        """
        self.__messagesMenu = QMenu(self)
##        self.__cutMessagesAct = \
##            self.__messagesMenu.addAction(
##                UI.PixmapCache.getIcon("editCut.png"),
##                self.trUtf8("Cut"), self.__cutMessages)
##        self.__copyMessagesAct = \
##            self.__messagesMenu.addAction(
##                UI.PixmapCache.getIcon("editCopy.png"),
##                self.trUtf8("Copy"), self.__copyMessages)
##        self.__messagesMenu.addSeparator()
##        self.__cutAllMessagesAct = \
##            self.__messagesMenu.addAction(
##                UI.PixmapCache.getIcon("editCut.png"),
##                self.trUtf8("Cut all"), self.__cutAllMessages)
##        self.__copyAllMessagesAct = \
##            self.__messagesMenu.addAction(
##                UI.PixmapCache.getIcon("editCopy.png"),
##                self.trUtf8("Copy all"), self.__copyAllMessages)
##        self.__messagesMenu.addSeparator()
##        self.__clearMessagesAct = \
##            self.__messagesMenu.addAction(
##                UI.PixmapCache.getIcon("editDelete.png"),
##                self.trUtf8("Clear"), self.__clearMessages)
##        self.__messagesMenu.addSeparator()
##        self.__saveMessagesAct = \
##            self.__messagesMenu.addAction(
##                UI.PixmapCache.getIcon("fileSave.png"),
##                self.trUtf8("Save"), self.__saveMessages)
        self.__setMarkerMessagesAct = \
            self.__messagesMenu.addAction(self.trUtf8("Mark Current Position"),
                self.setMarkerLine)
        self.__unsetMarkerMessagesAct = \
            self.__messagesMenu.addAction(self.trUtf8("Remove Position Marker"),
                self.unsetMarkerLine)
    
    @pyqtSlot(QPoint)
    def on_messages_customContextMenuRequested(self, pos):
        """
        Private slot to show the context menu of the messages pane.
        """
        self.__setMarkerMessagesAct.setEnabled(self.__markerLine == "")
        self.__unsetMarkerMessagesAct.setEnabled(self.__markerLine != "")
        self.__messagesMenu.popup(self.messages.mapToGlobal(pos))
    
    @pyqtSlot(QPoint)
    def on_usersList_customContextMenuRequested(self, pos):
        """
        Private slot to show the context menu of the users list.
        """
        # TODO: not implemented yet
        return
