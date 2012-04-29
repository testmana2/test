# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the task filter configuration dialog.
"""

from PyQt4.QtGui import QDialog

from .Task import Task

from .Ui_TaskFilterConfigDialog import Ui_TaskFilterConfigDialog


class TaskFilterConfigDialog(QDialog, Ui_TaskFilterConfigDialog):
    """
    Class implementing the task filter configuration dialog.
    """
    def __init__(self, taskFilter, parent=None):
        """
        Constructor
        
        @param taskFilter the task filter object to be configured
        @param parent the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        self.typeCombo.addItem("", Task.TypeNone)
        self.typeCombo.addItem(self.trUtf8("Bugfix"), Task.TypeFixme)
        self.typeCombo.addItem(self.trUtf8("Warning"), Task.TypeWarning)
        self.typeCombo.addItem(self.trUtf8("ToDo"), Task.TypeTodo)
        self.typeCombo.addItem(self.trUtf8("Note"), Task.TypeNote)
        
        if taskFilter.descriptionFilter is None or \
           not taskFilter.descriptionFilter.pattern():
            self.descriptionGroup.setChecked(False)
            self.descriptionEdit.clear()
        else:
            self.descriptionGroup.setChecked(True)
            self.descriptionEdit.setText(taskFilter.descriptionFilter.pattern())
        
        if taskFilter.filenameFilter is None or \
           not taskFilter.filenameFilter.pattern():
            self.filenameGroup.setChecked(False)
            self.filenameEdit.clear()
        else:
            self.filenameGroup.setChecked(True)
            self.filenameEdit.setText(taskFilter.filenameFilter.pattern())
        
        if taskFilter.typeFilter == Task.TypeNone:
            self.typeGroup.setChecked(False)
            self.typeCombo.setCurrentIndex(0)
        else:
            self.typeGroup.setChecked(True)
            self.typeCombo.setCurrentIndex(self.typeCombo.findData(taskFilter.typeFilter))
        
        if taskFilter.scopeFilter is None:
            self.scopeGroup.setChecked(False)
            self.globalRadioButton.setChecked(True)
        else:
            self.scopeGroup.setChecked(True)
            if taskFilter.scopeFilter:
                self.projectRadioButton.setChecked(True)
            else:
                self.globalRadioButton.setChecked(True)
        
        if taskFilter.statusFilter is None:
            self.statusGroup.setChecked(False)
            self.uncompletedRadioButton.setChecked(True)
        else:
            self.statusGroup.setChecked(True)
            if taskFilter.statusFilter:
                self.completedRadioButton.setChecked(True)
            else:
                self.uncompletedRadioButton.setChecked(True)
        
        if taskFilter.prioritiesFilter is None:
            self.priorityGroup.setChecked(False)
            self.priorityHighCheckBox.setChecked(False)
            self.priorityNormalCheckBox.setChecked(False)
            self.priorityLowCheckBox.setChecked(False)
        else:
            self.priorityGroup.setChecked(True)
            self.priorityHighCheckBox.setChecked(0 in taskFilter.prioritiesFilter)
            self.priorityNormalCheckBox.setChecked(1 in taskFilter.prioritiesFilter)
            self.priorityLowCheckBox.setChecked(2 in taskFilter.prioritiesFilter)
    
    def configureTaskFilter(self, taskFilter):
        """
        Public method to set the parameters of the task filter object.
        
        @param taskFilter the task filter object to be configured
        """
        if self.descriptionGroup.isChecked():
            taskFilter.setDescriptionFilter(self.descriptionEdit.text())
        else:
            taskFilter.setDescriptionFilter(None)
        
        if self.filenameGroup.isChecked():
            taskFilter.setFileNameFilter(self.filenameEdit.text())
        else:
            taskFilter.setFileNameFilter(None)
        
        if self.typeGroup.isChecked():
            taskFilter.setTypeFilter(
                self.typeCombo.itemData(self.typeCombo.currentIndex()))
        else:
            taskFilter.setTypeFilter(Task.TypeNone)
        
        if self.scopeGroup.isChecked():
            if self.projectRadioButton.isChecked():
                taskFilter.setScopeFilter(True)
            else:
                taskFilter.setScopeFilter(False)
        else:
            taskFilter.setScopeFilter(None)
        
        if self.statusGroup.isChecked():
            if self.completedRadioButton.isChecked():
                taskFilter.setStatusFilter(True)
            else:
                taskFilter.setStatusFilter(False)
        else:
            taskFilter.setStatusFilter(None)
        
        if self.priorityGroup.isChecked():
            priorities = []
            self.priorityHighCheckBox.isChecked() and priorities.append(0)
            self.priorityNormalCheckBox.isChecked() and priorities.append(1)
            self.priorityLowCheckBox.isChecked() and priorities.append(2)
            taskFilter.setPrioritiesFilter(priorities)
        else:
            taskFilter.setPrioritiesFilter(None)
