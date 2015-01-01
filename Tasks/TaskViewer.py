# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a task viewer and associated classes.

Tasks can be defined manually or automatically. Automatically
generated tasks are derived from a comment with a special
introductory text. This text is configurable.
"""

from __future__ import unicode_literals

import os
import fnmatch

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QHeaderView, QLineEdit, QTreeWidget, QDialog, \
    QInputDialog, QApplication, QMenu, QAbstractItemView, QTreeWidgetItem

from E5Gui.E5Application import e5App
from E5Gui import E5MessageBox
from E5Gui.E5ProgressDialog import E5ProgressDialog

from .Task import Task

import UI.PixmapCache

import Preferences
import Utilities

from Utilities.AutoSaver import AutoSaver
    

class TaskViewer(QTreeWidget):
    """
    Class implementing the task viewer.
    
    @signal displayFile(str, int) emitted to go to a file task
    """
    displayFile = pyqtSignal(str, int)
    
    def __init__(self, parent, project):
        """
        Constructor
        
        @param parent the parent (QWidget)
        @param project reference to the project object
        """
        super(TaskViewer, self).__init__(parent)
        
        self.setRootIsDecorated(False)
        self.setItemsExpandable(False)
        self.setSortingEnabled(True)
        
        self.__headerItem = QTreeWidgetItem(
            ["", "", self.tr("Summary"), self.tr("Filename"),
             self.tr("Line"), ""])
        self.__headerItem.setIcon(
            0, UI.PixmapCache.getIcon("taskCompleted.png"))
        self.__headerItem.setIcon(
            1, UI.PixmapCache.getIcon("taskPriority.png"))
        self.setHeaderItem(self.__headerItem)
        
        self.header().setSortIndicator(2, Qt.AscendingOrder)
        self.__resizeColumns()
        
        self.tasks = []
        self.copyTask = None
        self.projectOpen = False
        self.project = project
        self.projectTasksScanFilter = ""
        
        from .TaskFilter import TaskFilter
        self.taskFilter = TaskFilter()
        self.taskFilter.setActive(False)
        
        self.__projectTasksSaveTimer = AutoSaver(self, self.saveProjectTasks)
        
        self.__projectTasksMenu = QMenu(
            self.tr("P&roject Tasks"), self)
        self.__projectTasksMenu.addAction(
            self.tr("&Regenerate project tasks"),
            self.__regenerateProjectTasks)
        self.__projectTasksMenu.addSeparator()
        self.__projectTasksMenu.addAction(
            self.tr("&Configure scan options"),
            self.__configureProjectTasksScanOptions)
        
        self.__menu = QMenu(self)
        self.__menu.addAction(self.tr("&New Task..."), self.__newTask)
        self.__menu.addSeparator()
        self.projectTasksMenuItem = self.__menu.addMenu(
            self.__projectTasksMenu)
        self.__menu.addSeparator()
        self.gotoItem = self.__menu.addAction(
            self.tr("&Go To"), self.__goToTask)
        self.__menu.addSeparator()
        self.copyItem = self.__menu.addAction(
            self.tr("&Copy"), self.__copyTask)
        self.pasteItem = self.__menu.addAction(
            self.tr("&Paste"), self.__pasteTask)
        self.deleteItem = self.__menu.addAction(
            self.tr("&Delete"), self.__deleteTask)
        self.__menu.addSeparator()
        self.markCompletedItem = self.__menu.addAction(
            self.tr("&Mark Completed"), self.__markCompleted)
        self.__menu.addAction(
            self.tr("Delete Completed &Tasks"), self.__deleteCompleted)
        self.__menu.addSeparator()
        self.__menu.addAction(
            self.tr("P&roperties..."), self.__editTaskProperties)
        self.__menu.addSeparator()
        self.__menuFilteredAct = self.__menu.addAction(
            self.tr("&Filtered display"))
        self.__menuFilteredAct.setCheckable(True)
        self.__menuFilteredAct.setChecked(False)
        self.__menuFilteredAct.triggered[bool].connect(self.__activateFilter)
        self.__menu.addAction(
            self.tr("Filter c&onfiguration..."), self.__configureFilter)
        self.__menu.addSeparator()
        self.__menu.addAction(
            self.tr("Resi&ze columns"), self.__resizeColumns)
        self.__menu.addSeparator()
        self.__menu.addAction(self.tr("Configure..."), self.__configure)
        
        self.__backMenu = QMenu(self)
        self.__backMenu.addAction(self.tr("&New Task..."), self.__newTask)
        self.__backMenu.addSeparator()
        self.backProjectTasksMenuItem = self.__backMenu.addMenu(
            self.__projectTasksMenu)
        self.__backMenu.addSeparator()
        self.backPasteItem = self.__backMenu.addAction(
            self.tr("&Paste"), self.__pasteTask)
        self.__backMenu.addSeparator()
        self.__backMenu.addAction(
            self.tr("Delete Completed &Tasks"), self.__deleteCompleted)
        self.__backMenu.addSeparator()
        self.__backMenuFilteredAct = self.__backMenu.addAction(
            self.tr("&Filtered display"))
        self.__backMenuFilteredAct.setCheckable(True)
        self.__backMenuFilteredAct.setChecked(False)
        self.__backMenuFilteredAct.triggered[bool].connect(
            self.__activateFilter)
        self.__backMenu.addAction(
            self.tr("Filter c&onfiguration..."), self.__configureFilter)
        self.__backMenu.addSeparator()
        self.__backMenu.addAction(
            self.tr("Resi&ze columns"), self.__resizeColumns)
        self.__backMenu.addSeparator()
        self.__backMenu.addAction(
            self.tr("Configure..."), self.__configure)
        
        self.__activating = False
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__showContextMenu)
        self.itemActivated.connect(self.__taskItemActivated)
        
        self.setWindowIcon(UI.PixmapCache.getIcon("eric.png"))
    
    def __resort(self):
        """
        Private method to resort the tree.
        """
        self.sortItems(self.sortColumn(), self.header().sortIndicatorOrder())
        
    def __resizeColumns(self):
        """
        Private method to resize the list columns.
        """
        self.header().resizeSections(QHeaderView.ResizeToContents)
        self.header().setStretchLastSection(True)
        
    def __refreshDisplay(self):
        """
        Private method to refresh the display.
        """
        for task in self.tasks:
            task.setHidden(not self.taskFilter.showTask(task))
        self.__resort()
        self.__resizeColumns()
        
    def __taskItemActivated(self, itm, col):
        """
        Private slot to handle the activation of an item.
        
        @param itm reference to the activated item (QTreeWidgetItem)
        @param col column the item was activated in (integer)
        """
        if not self.__activating:
            self.__activating = True
            fn = itm.getFilename()
            if fn:
                self.displayFile.emit(fn, itm.getLineno())
            else:
                self.__editTaskProperties()
            self.__activating = False

    def __showContextMenu(self, coord):
        """
        Private slot to show the context menu of the list.
        
        @param coord the position of the mouse pointer (QPoint)
        """
        itm = self.itemAt(coord)
        coord = self.mapToGlobal(coord)
        if itm is None:
            self.backProjectTasksMenuItem.setEnabled(self.projectOpen)
            if self.copyTask:
                self.backPasteItem.setEnabled(True)
            else:
                self.backPasteItem.setEnabled(False)
            self.__backMenu.popup(coord)
        else:
            self.projectTasksMenuItem.setEnabled(self.projectOpen)
            if itm.getFilename():
                self.gotoItem.setEnabled(True)
                self.deleteItem.setEnabled(True)
                self.markCompletedItem.setEnabled(False)
                self.copyItem.setEnabled(False)
            else:
                self.gotoItem.setEnabled(False)
                self.deleteItem.setEnabled(True)
                self.markCompletedItem.setEnabled(True)
                self.copyItem.setEnabled(True)
            if self.copyTask:
                self.pasteItem.setEnabled(True)
            else:
                self.pasteItem.setEnabled(False)
            
            self.__menu.popup(coord)
    
    def setProjectOpen(self, o=False):
        """
        Public slot to set the project status.
        
        @param o flag indicating the project status
        """
        self.projectOpen = o
    
    def addTask(self, summary, priority=1, filename="", lineno=0,
                completed=False, _time=0, isProjectTask=False,
                taskType=Task.TypeTodo, description=""):
        """
        Public slot to add a task.
        
        @param summary summary text of the task (string)
        @param priority priority of the task (0=high, 1=normal, 2=low)
        @param filename filename containing the task (string)
        @param lineno line number containing the task (integer)
        @param completed flag indicating completion status (boolean)
        @param _time creation time of the task (float, if 0 use current time)
        @param isProjectTask flag indicating a task related to the current
            project (boolean)
        @param taskType type of the task (one of Task.TypeFixme, Task.TypeTodo,
            Task.TypeWarning, Task.TypeNote)
        @param description explanatory text of the task (string)
        """
        task = Task(summary, priority, filename, lineno, completed,
                    _time, isProjectTask, taskType,
                    self.project, description)
        self.tasks.append(task)
        self.addTopLevelItem(task)
        task.setHidden(not self.taskFilter.showTask(task))
        self.__resort()
        self.__resizeColumns()
        
        if isProjectTask:
            self.__projectTasksSaveTimer.changeOccurred()
    
    def addFileTask(self, summary, filename, lineno, taskType=Task.TypeTodo,
                    description=""):
        """
        Public slot to add a file related task.
        
        @param summary summary text of the task (string)
        @param filename filename containing the task (string)
        @param lineno line number containing the task (integer)
        @param taskType type of the task (one of Task.TypeFixme, Task.TypeTodo,
            Task.TypeWarning, Task.TypeNote)
        @param description explanatory text of the task (string)
        """
        self.addTask(summary, filename=filename, lineno=lineno,
                     isProjectTask=(
                         self.project and
                         self.project.isProjectSource(filename)),
                     taskType=taskType, description=description)
        
    def getProjectTasks(self):
        """
        Public method to retrieve all project related tasks.
        
        @return copy of tasks (list of Task)
        """
        tasks = [task for task in self.tasks if task.isProjectTask()]
        return tasks[:]
        
    def getGlobalTasks(self):
        """
        Public method to retrieve all non project related tasks.
        
        @return copy of tasks (list of Task)
        """
        tasks = [task for task in self.tasks if not task.isProjectTask()]
        return tasks[:]
        
    def clearTasks(self):
        """
        Public slot to clear all tasks from display.
        """
        self.tasks = []
        self.clear()
        
    def clearProjectTasks(self, fileOnly=False):
        """
        Public slot to clear project related tasks.
        
        @keyparam fileOnly flag indicating to clear only file related
            project tasks (boolean)
        """
        for task in self.tasks[:]:
            if (fileOnly and task.isProjectFileTask()) or \
               (not fileOnly and task.isProjectTask()):
                if self.copyTask == task:
                    self.copyTask = None
                index = self.indexOfTopLevelItem(task)
                self.takeTopLevelItem(index)
                self.tasks.remove(task)
                del task
        
    def clearFileTasks(self, filename, conditionally=False):
        """
        Public slot to clear all tasks related to a file.
        
        @param filename name of the file (string)
        @param conditionally flag indicating to clear the tasks of the file
            checking some conditions (boolean)
        """
        if conditionally:
            if self.project and self.project.isProjectSource(filename):
                # project related tasks will not be cleared
                return
            if not Preferences.getTasks("ClearOnFileClose"):
                return
        for task in self.tasks[:]:
            if task.getFilename() == filename:
                if self.copyTask == task:
                    self.copyTask = None
                index = self.indexOfTopLevelItem(task)
                self.takeTopLevelItem(index)
                self.tasks.remove(task)
                if task.isProjectTask:
                    self.__projectTasksSaveTimer.changeOccurred()
                del task
        
    def __editTaskProperties(self):
        """
        Private slot to handle the "Properties" context menu entry.
        """
        from .TaskPropertiesDialog import TaskPropertiesDialog
        task = self.currentItem()
        dlg = TaskPropertiesDialog(task, self, self.projectOpen)
        ro = task.getFilename() != ""
        if ro:
            dlg.setReadOnly()
        if dlg.exec_() == QDialog.Accepted and not ro:
            data = dlg.getData()
            task.setSummary(data[0])
            task.setPriority(data[1])
            task.setCompleted(data[2])
            task.setProjectTask(data[3])
            task.setDescription(data[4])
            self.__projectTasksSaveTimer.changeOccurred()
    
    def __newTask(self):
        """
        Private slot to handle the "New Task" context menu entry.
        """
        from .TaskPropertiesDialog import TaskPropertiesDialog
        dlg = TaskPropertiesDialog(None, self, self.projectOpen)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.getData()
            self.addTask(data[0], data[1], completed=data[2],
                         isProjectTask=data[3], description=data[4])
    
    def __markCompleted(self):
        """
        Private slot to handle the "Mark Completed" context menu entry.
        """
        task = self.currentItem()
        task.setCompleted(True)
    
    def __deleteCompleted(self):
        """
        Private slot to handle the "Delete Completed Tasks" context menu entry.
        """
        for task in self.tasks[:]:
            if task.isCompleted():
                if self.copyTask == task:
                    self.copyTask = None
                index = self.indexOfTopLevelItem(task)
                self.takeTopLevelItem(index)
                self.tasks.remove(task)
                if task.isProjectTask:
                    self.__projectTasksSaveTimer.changeOccurred()
                del task
        ci = self.currentItem()
        if ci:
            ind = self.indexFromItem(ci, self.currentColumn())
            self.scrollTo(ind, QAbstractItemView.PositionAtCenter)
    
    def __copyTask(self):
        """
        Private slot to handle the "Copy" context menu entry.
        """
        task = self.currentItem()
        self.copyTask = task
    
    def __pasteTask(self):
        """
        Private slot to handle the "Paste" context menu entry.
        """
        if self.copyTask:
            self.addTask(self.copyTask.summary,
                         priority=self.copyTask.priority,
                         completed=self.copyTask.completed,
                         description=self.copyTask.description,
                         isProjectTask=self.copyTask._isProjectTask)
    
    def __deleteTask(self):
        """
        Private slot to handle the "Delete Task" context menu entry.
        """
        task = self.currentItem()
        if self.copyTask == task:
            self.copyTask = None
        index = self.indexOfTopLevelItem(task)
        self.takeTopLevelItem(index)
        self.tasks.remove(task)
        if task.isProjectTask:
            self.__projectTasksSaveTimer.changeOccurred()
        del task
        ci = self.currentItem()
        if ci:
            ind = self.indexFromItem(ci, self.currentColumn())
            self.scrollTo(ind, QAbstractItemView.PositionAtCenter)
    
    def __goToTask(self):
        """
        Private slot to handle the "Go To" context menu entry.
        """
        task = self.currentItem()
        self.displayFile.emit(task.getFilename(), task.getLineno())

    def handlePreferencesChanged(self):
        """
        Public slot to react to changes of the preferences.
        """
        for task in self.tasks:
            task.colorizeTask()

    def __activateFilter(self, on):
        """
        Private slot to handle the "Filtered display" context menu entry.
        
        @param on flag indicating the filter state (boolean)
        """
        if on and not self.taskFilter.hasActiveFilter():
            res = E5MessageBox.yesNo(
                self,
                self.tr("Activate task filter"),
                self.tr(
                    """The task filter doesn't have any active filters."""
                    """ Do you want to configure the filter settings?"""),
                yesDefault=True)
            if not res:
                on = False
            else:
                self.__configureFilter()
                on = self.taskFilter.hasActiveFilter()
        
        self.taskFilter.setActive(on)
        self.__menuFilteredAct.setChecked(on)
        self.__backMenuFilteredAct.setChecked(on)
        self.__refreshDisplay()
    
    def __configureFilter(self):
        """
        Private slot to handle the "Configure filter" context menu entry.
        """
        from .TaskFilterConfigDialog import TaskFilterConfigDialog
        dlg = TaskFilterConfigDialog(self.taskFilter)
        if dlg.exec_() == QDialog.Accepted:
            dlg.configureTaskFilter(self.taskFilter)
            self.__refreshDisplay()

    def __configureProjectTasksScanOptions(self):
        """
        Private slot to configure scan options for project tasks.
        """
        filter, ok = QInputDialog.getText(
            self,
            self.tr("Scan Filter Patterns"),
            self.tr("Enter filename patterns of files"
                    " to be excluded separated by a comma:"),
            QLineEdit.Normal,
            self.projectTasksScanFilter)
        if ok:
            self.projectTasksScanFilter = filter
    
    def __regenerateProjectTasks(self):
        """
        Private slot to handle the "Regenerated project tasks" context menu
        entry.
        """
        markers = {
            Task.TypeWarning:
            Preferences.getTasks("TasksWarningMarkers").split(),
            Task.TypeNote: Preferences.getTasks("TasksNoteMarkers").split(),
            Task.TypeTodo: Preferences.getTasks("TasksTodoMarkers").split(),
            Task.TypeFixme: Preferences.getTasks("TasksFixmeMarkers").split(),
        }
        files = self.project.pdata["SOURCES"]
        
        # apply file filter
        filterList = [f.strip() for f in self.projectTasksScanFilter.split(",")
                      if f.strip()]
        if filterList:
            for filter in filterList:
                files = [f for f in files if not fnmatch.fnmatch(f, filter)]
        
        # remove all project tasks
        self.clearProjectTasks(fileOnly=True)
        
        # now process them
        progress = E5ProgressDialog(
            self.tr("Extracting project tasks..."),
            self.tr("Abort"), 0, len(files), self.tr("%v/%m Files"))
        progress.setMinimumDuration(0)
        progress.setWindowTitle(self.tr("Tasks"))
        count = 0
        
        for file in files:
            progress.setLabelText(
                self.tr("Extracting project tasks...\n{0}").format(file))
            progress.setValue(count)
            QApplication.processEvents()
            if progress.wasCanceled():
                break
            
            fn = os.path.join(self.project.ppath, file)
            # read the file and split it into textlines
            try:
                text, encoding = Utilities.readEncodedFile(fn)
                lines = text.splitlines()
            except (UnicodeError, IOError):
                count += 1
                progress.setValue(count)
                continue
            
            # now search tasks and record them
            lineIndex = 0
            for line in lines:
                lineIndex += 1
                shouldBreak = False
                
                for taskType, taskMarkers in markers.items():
                    for taskMarker in taskMarkers:
                        index = line.find(taskMarker)
                        if index > -1:
                            task = line[index:]
                            self.addFileTask(task, fn, lineIndex, taskType)
                            shouldBreak = True
                            break
                    if shouldBreak:
                        break
            
            count += 1
            
        progress.setValue(len(files))
    
    def __configure(self):
        """
        Private method to open the configuration dialog.
        """
        e5App().getObject("UserInterface").showPreferences("tasksPage")
    
    def saveProjectTasks(self):
        """
        Public method to write the project tasks.
        """
        if self.projectOpen and Preferences.getTasks("TasksProjectAutoSave"):
            self.project.writeTasks()
