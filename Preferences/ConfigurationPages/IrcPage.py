# -*- coding: utf-8 -*-

# Copyright (c) 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the IRC configuration page.
"""

from PyQt4.QtCore import pyqtSlot

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_IrcPage import Ui_IrcPage

import Preferences


class IrcPage(ConfigurationPageBase, Ui_IrcPage):
    """
    Class implementing the IRC configuration page.
    """
    TimeFormats = ["hh:mm", "hh:mm:ss", "h:mm ap", "h:mm:ss ap"]
    DateFormats = ["yyyy-MM-dd", "dd.MM.yyyy", "MM/dd/yyyy",
                   "yyyy MMM. dd", "dd MMM. yyyy", "MMM. dd, yyyy"]
    
    def __init__(self):
        """
        Constructor
        """
        super().__init__()
        self.setupUi(self)
        self.setObjectName("IrcPage")
        
        self.timeFormatCombo.addItems(IrcPage.TimeFormats)
        self.dateFormatCombo.addItems(IrcPage.DateFormats)
        
        self.ircColours = {}
        
        # set initial values
        # timestamps
        self.timestampGroup.setChecked(Preferences.getIrc("ShowTimestamps"))
        self.showDateCheckBox.setChecked(Preferences.getIrc("TimestampIncludeDate"))
        self.timeFormatCombo.setCurrentIndex(
            self.timeFormatCombo.findText(Preferences.getIrc("TimeFormat")))
        self.dateFormatCombo.setCurrentIndex(
            self.dateFormatCombo.findText(Preferences.getIrc("DateFormat")))
        
        # colours
        # TODO: convert this to the code style below
        self.ircColours["NetworkMessageColour"] = \
            self.initColour("NetworkMessageColour", self.networkButton,
                Preferences.getIrc)
        self.ircColours["ServerMessageColour"] = \
            self.initColour("ServerMessageColour", self.serverButton,
                Preferences.getIrc)
        self.ircColours["ErrorMessageColour"] = \
            self.initColour("ErrorMessageColour", self.errorButton,
                Preferences.getIrc)
        self.ircColours["TimestampColour"] = \
            self.initColour("TimestampColour", self.timestampButton,
                Preferences.getIrc)
        self.ircColours["HyperlinkColour"] = \
            self.initColour("HyperlinkColour", self.hyperlinkButton,
                Preferences.getIrc)
        self.ircColours["ChannelMessageColour"] = \
            self.initColour("ChannelMessageColour", self.channelButton,
                Preferences.getIrc)
        self.ircColours["OwnNickColour"] = \
            self.initColour("OwnNickColour", self.ownNickButton,
                Preferences.getIrc)
        self.ircColours["NickColour"] = \
            self.initColour("NickColour", self.nickButton,
                Preferences.getIrc)
        self.ircColours["JoinChannelColour"] = \
            self.initColour("JoinChannelColour", self.joinButton,
                Preferences.getIrc)
        self.ircColours["LeaveChannelColour"] = \
            self.initColour("LeaveChannelColour", self.leaveButton,
                Preferences.getIrc)
        self.ircColours["ChannelInfoColour"] = \
            self.initColour("ChannelInfoColour", self.infoButton,
                Preferences.getIrc)
        
        # notifications
        self.notificationsGroup.setChecked(Preferences.getIrc("ShowNotifications"))
        self.joinLeaveCheckBox.setChecked(Preferences.getIrc("NotifyJoinPart"))
        self.messageCheckBox.setChecked(Preferences.getIrc("NotifyMessage"))
        self.ownNickCheckBox.setChecked(Preferences.getIrc("NotifyNick"))
        
        # IRC text colors
        # TODO: optimize further: put colour dict and select slot in base class
        self.initColour2(self.ircColours, "IrcColor0", self.ircColor0Button,
            Preferences.getIrc, self.__selectColour)
        self.initColour2(self.ircColours, "IrcColor1", self.ircColor1Button,
            Preferences.getIrc, self.__selectColour)
        self.initColour2(self.ircColours, "IrcColor2", self.ircColor2Button,
            Preferences.getIrc, self.__selectColour)
        self.initColour2(self.ircColours, "IrcColor3", self.ircColor3Button,
            Preferences.getIrc, self.__selectColour)
        self.initColour2(self.ircColours, "IrcColor4", self.ircColor4Button,
            Preferences.getIrc, self.__selectColour)
        self.initColour2(self.ircColours, "IrcColor5", self.ircColor5Button,
            Preferences.getIrc, self.__selectColour)
        self.initColour2(self.ircColours, "IrcColor6", self.ircColor6Button,
            Preferences.getIrc, self.__selectColour)
        self.initColour2(self.ircColours, "IrcColor7", self.ircColor7Button,
            Preferences.getIrc, self.__selectColour)
        self.initColour2(self.ircColours, "IrcColor8", self.ircColor8Button,
            Preferences.getIrc, self.__selectColour)
        self.initColour2(self.ircColours, "IrcColor9", self.ircColor9Button,
            Preferences.getIrc, self.__selectColour)
        self.initColour2(self.ircColours, "IrcColor10", self.ircColor10Button,
            Preferences.getIrc, self.__selectColour)
        self.initColour2(self.ircColours, "IrcColor11", self.ircColor11Button,
            Preferences.getIrc, self.__selectColour)
        self.initColour2(self.ircColours, "IrcColor12", self.ircColor12Button,
            Preferences.getIrc, self.__selectColour)
        self.initColour2(self.ircColours, "IrcColor13", self.ircColor13Button,
            Preferences.getIrc, self.__selectColour)
        self.initColour2(self.ircColours, "IrcColor14", self.ircColor14Button,
            Preferences.getIrc, self.__selectColour)
        self.initColour2(self.ircColours, "IrcColor15", self.ircColor15Button,
            Preferences.getIrc, self.__selectColour)
    
    def save(self):
        """
        Public slot to save the IRC configuration.
        """
        # timestamps
        Preferences.setIrc("ShowTimestamps", self.timestampGroup.isChecked())
        Preferences.setIrc("TimestampIncludeDate", self.showDateCheckBox.isChecked())
        Preferences.setIrc("TimeFormat", self.timeFormatCombo.currentText())
        Preferences.setIrc("DateFormat", self.dateFormatCombo.currentText())
        
        # notifications
        Preferences.setIrc("ShowNotifications", self.notificationsGroup.isChecked())
        Preferences.setIrc("NotifyJoinPart", self.joinLeaveCheckBox.isChecked())
        Preferences.setIrc("NotifyMessage", self.messageCheckBox.isChecked())
        Preferences.setIrc("NotifyNick", self.ownNickCheckBox.isChecked())
        
        # colours
        for key in self.ircColours:
            Preferences.setIrc(key, self.ircColours[key].name())
    
    @pyqtSlot()
    def on_networkButton_clicked(self):
        """
        Private slot to set the color for network messages.
        """
        self.ircColours["NetworkMessageColour"] = \
            self.selectColour(self.networkButton,
                self.ircColours["NetworkMessageColour"])
    
    @pyqtSlot()
    def on_nickButton_clicked(self):
        """
        Private slot to set the color for nick names.
        """
        self.ircColours["NickColour"] = \
            self.selectColour(self.nickButton,
                self.ircColours["NickColour"])
    
    @pyqtSlot()
    def on_serverButton_clicked(self):
        """
        Private slot to set the color for server messages.
        """
        self.ircColours["ServerMessageColour"] = \
            self.selectColour(self.serverButton,
                self.ircColours["ServerMessageColour"])
    
    @pyqtSlot()
    def on_ownNickButton_clicked(self):
        """
        Private slot to set the color for own nick name.
        """
        self.ircColours["OwnNickColour"] = \
            self.selectColour(self.ownNickButton,
                self.ircColours["OwnNickColour"])
    
    @pyqtSlot()
    def on_channelButton_clicked(self):
        """
        Private slot to set the color for channel messages.
        """
        self.ircColours["ChannelMessageColour"] = \
            self.selectColour(self.channelButton,
                self.ircColours["ChannelMessageColour"])
    
    @pyqtSlot()
    def on_joinButton_clicked(self):
        """
        Private slot to set the color for join events.
        """
        self.ircColours["JoinChannelColour"] = \
            self.selectColour(self.joinButton,
                self.ircColours["JoinChannelColour"])
    
    @pyqtSlot()
    def on_errorButton_clicked(self):
        """
        Private slot to set the color for error messages.
        """
        self.ircColours["ErrorMessageColour"] = \
            self.selectColour(self.errorButton,
                self.ircColours["ErrorMessageColour"])
    
    @pyqtSlot()
    def on_leaveButton_clicked(self):
        """
        Private slot to set the color for leave events.
        """
        self.ircColours["LeaveChannelColour"] = \
            self.selectColour(self.leaveButton,
                self.ircColours["LeaveChannelColour"])
    
    @pyqtSlot()
    def on_timestampButton_clicked(self):
        """
        Private slot to set the color for timestamps.
        """
        self.ircColours["TimestampColour"] = \
            self.selectColour(self.timestampButton,
                self.ircColours["TimestampColour"])
    
    @pyqtSlot()
    def on_infoButton_clicked(self):
        """
        Private slot to set the color for info messages.
        """
        self.ircColours["ChannelInfoColour"] = \
            self.selectColour(self.infoButton,
                self.ircColours["ChannelInfoColour"])
    
    @pyqtSlot()
    def on_hyperlinkButton_clicked(self):
        """
        Private slot to set the color for hyperlinks.
        """
        self.ircColours["HyperlinkColour"] = \
            self.selectColour(self.hyperlinkButton,
                self.ircColours["HyperlinkColour"])
    
    @pyqtSlot()
    def __selectColour(self):
        """
        Private slot to select a color.
        """
        button = self.sender()
        colorKey = button.property("colorName")
        self.ircColours[colorKey] = self.selectColour(
            button, self.ircColours[colorKey])


def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    """
    page = IrcPage()
    return page
