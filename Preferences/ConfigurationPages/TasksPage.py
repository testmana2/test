# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Tasks configuration page.
"""

from PyQt4.QtCore import pyqtSlot

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_TasksPage import Ui_TasksPage

import Preferences


class TasksPage(ConfigurationPageBase, Ui_TasksPage):
    """
    Class implementing the Tasks configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super().__init__()
        self.setupUi(self)
        self.setObjectName("TasksPage")
        
        self.tasksColours = {}
        
        # set initial values
        self.tasksMarkerFixmeEdit.setText(
            Preferences.getTasks("TasksFixmeMarkers"))
        self.tasksMarkerWarningEdit.setText(
            Preferences.getTasks("TasksWarningMarkers"))
        self.tasksMarkerTodoEdit.setText(
            Preferences.getTasks("TasksTodoMarkers"))
        self.tasksMarkerNoteEdit.setText(
            Preferences.getTasks("TasksNoteMarkers"))
        
        self.tasksColours["TasksFixmeColor"] = \
            self.initColour("TasksFixmeColor", self.tasksFixmeColourButton,
                Preferences.getTasks)
        self.tasksColours["TasksWarningColor"] = \
            self.initColour("TasksWarningColor", self.tasksWarningColourButton,
                Preferences.getTasks)
        self.tasksColours["TasksTodoColor"] = \
            self.initColour("TasksTodoColor", self.tasksTodoColourButton,
                Preferences.getTasks)
        self.tasksColours["TasksNoteColor"] = \
            self.initColour("TasksNoteColor", self.tasksNoteColourButton,
                Preferences.getTasks)
        
        self.clearCheckBox.setChecked(Preferences.getTasks("ClearOnFileClose"))
        
    def save(self):
        """
        Public slot to save the Tasks configuration.
        """
        Preferences.setTasks("TasksFixmeMarkers",
            self.tasksMarkerFixmeEdit.text())
        Preferences.setTasks("TasksWarningMarkers",
            self.tasksMarkerWarningEdit.text())
        Preferences.setTasks("TasksTodoMarkers",
            self.tasksMarkerTodoEdit.text())
        Preferences.setTasks("TasksNoteMarkers",
            self.tasksMarkerNoteEdit.text())
        for key in list(self.tasksColours.keys()):
            Preferences.setTasks(key, self.tasksColours[key])
        Preferences.setTasks("ClearOnFileClose", self.clearCheckBox.isChecked())
        
    @pyqtSlot()
    def on_tasksFixmeColourButton_clicked(self):
        """
        Private slot to set the colour for standard tasks.
        """
        self.tasksColours["TasksColour"] = \
            self.selectColour(self.tasksColourButton, self.tasksColours["TasksColour"])
        
    @pyqtSlot()
    def on_tasksWarningColourButton_clicked(self):
        """
        Private slot to set the colour for bugfix tasks.
        """
        self.tasksColours["TasksBugfixColour"] = \
            self.selectColour(self.tasksBugfixColourButton,
                self.tasksColours["TasksBugfixColour"])
        
    @pyqtSlot()
    def on_tasksTodoColourButton_clicked(self):
        """
        Private slot to set the background colour for global tasks.
        """
        self.tasksColours["TasksBgColour"] = \
            self.selectColour(self.tasksBgColourButton,
                self.tasksColours["TasksBgColour"])
        
    @pyqtSlot()
    def on_tasksNoteColourButton_clicked(self):
        """
        Private slot to set the backgroundcolour for project tasks.
        """
        self.tasksColours["TasksProjectBgColour"] = \
            self.selectColour(self.tasksProjectBgColourButton,
                self.tasksColours["TasksProjectBgColour"])
    

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    """
    page = TasksPage()
    return page
