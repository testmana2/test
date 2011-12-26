# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the VCS configuration page.
"""

from PyQt4.QtCore import pyqtSlot

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_VcsPage import Ui_VcsPage

import Preferences


class VcsPage(ConfigurationPageBase, Ui_VcsPage):
    """
    Class implementing the VCS configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super().__init__()
        self.setupUi(self)
        self.setObjectName("VcsPage")
        
        self.projectBrowserColours = {}
        
        # set initial values
        self.vcsAutoCloseCheckBox.setChecked(Preferences.getVCS("AutoClose"))
        self.vcsAutoSaveCheckBox.setChecked(Preferences.getVCS("AutoSaveFiles"))
        self.vcsAutoSaveProjectCheckBox.setChecked(
            Preferences.getVCS("AutoSaveProject"))
        self.vcsStatusMonitorIntervalSpinBox.setValue(
            Preferences.getVCS("StatusMonitorInterval"))
        self.vcsMonitorLocalStatusCheckBox.setChecked(
            Preferences.getVCS("MonitorLocalStatus"))
        self.autoUpdateCheckBox.setChecked(
            Preferences.getVCS("AutoUpdate"))
        
        self.projectBrowserColours["VcsAdded"] = \
            self.initColour("VcsAdded", self.pbVcsAddedButton,
                Preferences.getProjectBrowserColour)
        self.projectBrowserColours["VcsConflict"] = \
            self.initColour("VcsConflict", self.pbVcsConflictButton,
                Preferences.getProjectBrowserColour)
        self.projectBrowserColours["VcsModified"] = \
            self.initColour("VcsModified", self.pbVcsModifiedButton,
                Preferences.getProjectBrowserColour)
        self.projectBrowserColours["VcsReplaced"] = \
            self.initColour("VcsReplaced", self.pbVcsReplacedButton,
                Preferences.getProjectBrowserColour)
        self.projectBrowserColours["VcsUpdate"] = \
            self.initColour("VcsUpdate", self.pbVcsUpdateButton,
                Preferences.getProjectBrowserColour)
        self.projectBrowserColours["VcsConflict"] = \
            self.initColour("VcsConflict", self.pbVcsConflictButton,
                Preferences.getProjectBrowserColour)
        self.projectBrowserColours["VcsRemoved"] = \
            self.initColour("VcsRemoved", self.pbVcsRemovedButton,
                Preferences.getProjectBrowserColour)
    
    def save(self):
        """
        Public slot to save the VCS configuration.
        """
        Preferences.setVCS("AutoClose",
            self.vcsAutoCloseCheckBox.isChecked())
        Preferences.setVCS("AutoSaveFiles",
            self.vcsAutoSaveCheckBox.isChecked())
        Preferences.setVCS("AutoSaveProject",
            self.vcsAutoSaveProjectCheckBox.isChecked())
        Preferences.setVCS("StatusMonitorInterval",
            self.vcsStatusMonitorIntervalSpinBox.value())
        Preferences.setVCS("MonitorLocalStatus",
            self.vcsMonitorLocalStatusCheckBox.isChecked())
        Preferences.setVCS("AutoUpdate",
            self.autoUpdateCheckBox.isChecked())
    
        for key in list(self.projectBrowserColours.keys()):
            Preferences.setProjectBrowserColour(key, self.projectBrowserColours[key])
    
    @pyqtSlot()
    def on_pbVcsAddedButton_clicked(self):
        """
        Private slot to set the background colour for entries with VCS
        status "added".
        """
        self.projectBrowserColours["VcsAdded"] = \
            self.selectColour(self.pbVcsAddedButton,
                self.projectBrowserColours["VcsAdded"])
    
    @pyqtSlot()
    def on_pbVcsConflictButton_clicked(self):
        """
        Private slot to set the background colour for entries with VCS
        status "conflict".
        """
        self.projectBrowserColours["VcsConflict"] = \
            self.selectColour(self.pbVcsConflictButton,
                self.projectBrowserColours["VcsConflict"])
    
    @pyqtSlot()
    def on_pbVcsModifiedButton_clicked(self):
        """
        Private slot to set the background colour for entries with VCS
        status "modified".
        """
        self.projectBrowserColours["VcsModified"] = \
            self.selectColour(self.pbVcsModifiedButton,
                self.projectBrowserColours["VcsModified"])
    
    @pyqtSlot()
    def on_pbVcsReplacedButton_clicked(self):
        """
        Private slot to set the background colour for entries with VCS
        status "replaced".
        """
        self.projectBrowserColours["VcsReplaced"] = \
            self.selectColour(self.pbVcsReplacedButton,
                self.projectBrowserColours["VcsReplaced"])
    
    @pyqtSlot()
    def on_pbVcsRemovedButton_clicked(self):
        """
        Private slot to set the background colour for entries with VCS
        status "removed".
        """
        self.projectBrowserColours["VcsRemoved"] = \
            self.selectColour(self.pbVcsRemovedButton,
                self.projectBrowserColours["VcsRemoved"])
    
    @pyqtSlot()
    def on_pbVcsUpdateButton_clicked(self):
        """
        Private slot to set the background colour for entries with VCS
        status "needs update".
        """
        self.projectBrowserColours["VcsUpdate"] = \
            self.selectColour(self.pbVcsUpdateButton,
                self.projectBrowserColours["VcsUpdate"])


def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    """
    page = VcsPage()
    return page
