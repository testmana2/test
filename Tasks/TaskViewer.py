# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a task viewer and associated classes.

Tasks can be defined manually or automatically. Automatically
generated tasks are derived from a comment with a special
introductory text. This text is configurable.
"""

import os
import time
import fnmatch

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from E5Gui.E5Application import e5App
from E5Gui import E5MessageBox

from .TaskPropertiesDialog import TaskPropertiesDialog
from .TaskFilterConfigDialog import TaskFilterConfigDialog

import UI.PixmapCache

import Preferences
import Utilities


class Task(QTreeWidgetItem):
    """
    Class implementing the task data structure.
    """
    def __init__(self, description, priority=1, filename="", lineno=0,
                 completed=False, _time=0, isProjectTask=False,
                 isBugfixTask=False, project=None, longtext=""):
        """
        Constructor
        
        @param parent parent widget of the task (QWidget)
        @param description descriptive text of the task (string)
        @param priority priority of the task (0=high, 1=normal, 2=low)
        @param filename filename containing the task (string)
        @param lineno line number containing the task (integer)
        @param completed flag indicating completion status (boolean)
        @param _time creation time of the task (float, if 0 use current time)
        @param isProjectTask flag indicating a task related to the current project
            (boolean)
        @param isBugfixTask flag indicating a bugfix task (boolean)
        @param project reference to the project object (Project)
        @param longtext explanatory text of the task (string)
        """
        self.description = description
        self.longtext = longtext
        if priority in [0, 1, 2]:
            self.priority = priority
        else:
            self.priority = 1
        self.filename = filename
        self.lineno = lineno
        self.completed = completed
        self.created = _time and _time or time.time()
        self._isProjectTask = isProjectTask
        self.isBugfixTask = isBugfixTask
        self.project = project
        
        if isProjectTask:
            self.filename = self.project.getRelativePath(self.filename)
            
        QTreeWidgetItem.__init__(self, ["", "", self.description, self.filename,
            (self.lineno and "{0:6d}".format(self.lineno) or "")])
        
        if self.completed:
            self.setIcon(0, UI.PixmapCache.getIcon("taskCompleted.png"))
            strikeOut = True
        else:
            self.setIcon(0, UI.PixmapCache.getIcon("empty.png"))
            strikeOut = False
        for column in range(2, 5):
            f = self.font(column)
            f.setStrikeOut(strikeOut)
            self.setFont(column, f)
        
        if self.priority == 1:
            self.setIcon(1, UI.PixmapCache.getIcon("empty.png"))
        elif self.priority == 0:
            self.setIcon(1, UI.PixmapCache.getIcon("taskPrioHigh.png"))
        elif self.priority == 2:
            self.setIcon(1, UI.PixmapCache.getIcon("taskPrioLow.png"))
        else:
            self.setIcon(1, UI.PixmapCache.getIcon("empty.png"))
        
        self.colorizeTask()
        self.setTextAlignment(4, Qt.AlignRight)
    
    def colorizeTask(self):
        """
        Public slot to set the colors of the task item.
        """
        for col in range(5):
            if self.isBugfixTask:
                self.setTextColor(col, Preferences.getTasks("TasksBugfixColour"))
            else:
                self.setTextColor(col, Preferences.getTasks("TasksColour"))
            if self._isProjectTask:
                self.setBackgroundColor(col, Preferences.getTasks("TasksProjectBgColour"))
            else:
                self.setBackgroundColor(col, Preferences.getTasks("TasksBgColour"))
    
    def setDescription(self, description):
        """
        Public slot to update the description.
        
        @param longtext explanatory text of the task (string)
        """
        self.description = description
        self.setText(2, self.description)
    
    def setLongText(self, longtext):
        """
        Public slot to update the longtext field.
        
        @param longtext descriptive text of the task (string)
        """
        self.longtext = longtext
    
    def setPriority(self, priority):
        """
        Public slot to update the priority.
        
        @param priority priority of the task (0=high, 1=normal, 2=low)
        """
        if priority in [0, 1, 2]:
            self.priority = priority
        else:
            self.priority = 1
        
        if self.priority == 1:
            self.setIcon(1, UI.PixmapCache.getIcon("empty.png"))
        elif self.priority == 0:
            self.setIcon(1, UI.PixmapCache.getIcon("taskPrioHigh.png"))
        elif self.priority == 2:
            self.setIcon(1, UI.PixmapCache.getIcon("taskPrioLow.png"))
        else:
            self.setIcon(1, UI.PixmapCache.getIcon("empty.png"))
    
    def setCompleted(self, completed):
        """
        Public slot to update the completed flag.
        
        @param completed flag indicating completion status (boolean)
        """
        self.completed = completed
        if self.completed:
            self.setIcon(0, UI.PixmapCache.getIcon("taskCompleted.png"))
            strikeOut = True
        else:
            self.setIcon(0, UI.PixmapCache.getIcon("empty.png"))
            strikeOut = False
        for column in range(2, 5):
            f = self.font(column)
            f.setStrikeOut(strikeOut)
            self.setFont(column, f)
    
    def isCompleted(self):
        """
        Public slot to return the completion status.
        
        @return flag indicating the completion status (boolean)
        """
        return self.completed
    
    def getFilename(self):
        """
        Public method to retrieve the tasks filename.
        
        @return filename (string)
        """
        if self._isProjectTask and self.filename:
            return os.path.join(self.project.getProjectPath(), self.filename)
        else:
            return self.filename
    
    def getLineno(self):
        """
        Public method to retrieve the tasks linenumber.
        
        @return linenumber (integer)
        """
        return self.lineno
    
    def setProjectTask(self, pt):
        """
        Public method to set the project relation flag.
        
        @param pt flag indicating a project task (boolean)
        """
        self._isProjectTask = pt
        self.colorizeTask()
    
    def isProjectTask(self):
        """
        Public slot to return the project relation status.
        
        @return flag indicating the project relation status (boolean)
        """
        return self._isProjectTask


class TaskFilter(object):
    """
    Class implementing a filter for tasks.
    """
    def __init__(self):
        """
        Constructor
        """
        self.active = False
        
        self.descriptionFilter = None
        self.filenameFilter = None
        self.typeFilter = None        # standard (False) or bugfix (True)
        self.scopeFilter = None       # global (False) or project (True)
        self.statusFilter = None      # uncompleted (False) or completed (True)
        self.prioritiesFilter = None  # list of priorities [0 (high), 1 (normal), 2 (low)]
    
    def setActive(self, enabled):
        """
        Public method to activate the filter.
        
        @param enabled flag indicating the activation state (boolean)
        """
        self.active = enabled
    
    def setDescriptionFilter(self, filter):
        """
        Public method to set the description filter.
        
        @param filter a regular expression for the description filter
            to set (string) or None
        """
        if not filter:
            self.descriptionFilter = None
        else:
            self.descriptionFilter = QRegExp(filter)
    
    def setFileNameFilter(self, filter):
        """
        Public method to set the filename filter.
        
        @param filter a wildcard expression for the filename filter
            to set (string) or None
        """
        if not filter:
            self.filenameFilter = None
        else:
            self.filenameFilter = QRegExp(filter)
            self.filenameFilter.setPatternSyntax(QRegExp.Wildcard)
    
    def setTypeFilter(self, type_):
        """
        Public method to set the type filter.
        
        @param type_ flag indicating a bugfix task (boolean) or None
        """
        self.typeFilter = type_
        
    def setScopeFilter(self, scope):
        """
        Public method to set the scope filter.
        
        @param scope flag indicating a project task (boolean) or None
        """
        self.scopeFilter = scope
        
    def setStatusFilter(self, status):
        """
        Public method to set the status filter.
        
        @param status flag indicating a completed task (boolean) or None
        """
        self.statusFilter = status
        
    def setPrioritiesFilter(self, priorities):
        """
        Public method to set the priorities filter.
        
        @param priorities list of task priorities (list of integer) or None
        """
        self.prioritiesFilter = priorities
        
    def hasActiveFilter(self):
        """
        Public method to check for active filters.
        
        @return flag indicating an active filter was found (boolean)
        """
        return self.descriptionFilter is not None or \
               self.filenameFilter is not None or \
               self.typeFilter is not None or \
               self.scopeFilter is not None or \
               self.statusFilter is not None or \
               self.prioritiesFilter is not None
        
    def showTask(self, task):
        """
        Public method to check, if a task should be shown.
        
        @param task reference to the task object to check (Task)
        @return flag indicating whether the task should be shown (boolean)
        """
        if not self.active:
            return True
        
        if self.descriptionFilter and \
           self.descriptionFilter.indexIn(task.description) == -1:
            return False
        
        if self.filenameFilter and \
           not self.filenameFilter.exactMatch(task.filename):
            return False
        
        if self.typeFilter is not None and \
           self.typeFilter != task.isBugfixTask:
            return False
        
        if self.scopeFilter is not None and \
           self.scopeFilter != task._isProjectTask:
            return False
        
        if self.statusFilter is not None and \
           self.statusFilter != task.completed:
            return False
        
        if self.prioritiesFilter is not None and \
           not task.priority in self.prioritiesFilter:
            return False
        
        return True
    

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
        QTreeWidget.__init__(self, parent)
        
        self.setRootIsDecorated(False)
        self.setItemsExpandable(False)
        self.setSortingEnabled(True)
        
        self.__headerItem = QTreeWidgetItem(["", "", self.trUtf8("Summary"),
            self.trUtf8("Filename"), self.trUtf8("Line"), ""])
        self.__headerItem.setIcon(0, UI.PixmapCache.getIcon("taskCompleted.png"))
        self.__headerItem.setIcon(1, UI.PixmapCache.getIcon("taskPriority.png"))
        self.setHeaderItem(self.__headerItem)
        
        self.header().setSortIndicator(2, Qt.AscendingOrder)
        self.__resizeColumns()
        
        self.tasks = []
        self.copyTask = None
        self.projectOpen = False
        self.project = project
        self.projectTasksScanFilter = ""
        
        self.taskFilter = TaskFilter()
        self.taskFilter.setActive(False)
        
        self.__projectTasksMenu = QMenu(
            self.trUtf8("P&roject Tasks"), self)
        self.__projectTasksMenu.addAction(
            self.trUtf8("&Regenerate project tasks"),
            self.__regenerateProjectTasks)
        self.__projectTasksMenu.addSeparator()
        self.__projectTasksMenu.addAction(
            self.trUtf8("&Configure scan options"),
            self.__configureProjectTasksScanOptions)
        
        self.__menu = QMenu(self)
        self.__menu.addAction(self.trUtf8("&New Task..."), self.__newTask)
        self.__menu.addSeparator()
        self.projectTasksMenuItem = self.__menu.addMenu(self.__projectTasksMenu)
        self.__menu.addSeparator()
        self.gotoItem = self.__menu.addAction(self.trUtf8("&Go To"), self.__goToTask)
        self.__menu.addSeparator()
        self.copyItem = self.__menu.addAction(self.trUtf8("&Copy"), self.__copyTask)
        self.pasteItem = self.__menu.addAction(self.trUtf8("&Paste"), self.__pasteTask)
        self.deleteItem = self.__menu.addAction(self.trUtf8("&Delete"), self.__deleteTask)
        self.__menu.addSeparator()
        self.markCompletedItem = self.__menu.addAction(self.trUtf8("&Mark Completed"),
                                                       self.__markCompleted)
        self.__menu.addAction(self.trUtf8("Delete Completed &Tasks"),
                              self.__deleteCompleted)
        self.__menu.addSeparator()
        self.__menu.addAction(self.trUtf8("P&roperties..."), self.__editTaskProperties)
        self.__menu.addSeparator()
        self.__menuFilteredAct = self.__menu.addAction(self.trUtf8("&Filtered display"))
        self.__menuFilteredAct.setCheckable(True)
        self.__menuFilteredAct.setChecked(False)
        self.__menuFilteredAct.triggered[bool].connect(self.__activateFilter)
        self.__menu.addAction(self.trUtf8("Filter c&onfiguration..."),
                              self.__configureFilter)
        self.__menu.addSeparator()
        self.__menu.addAction(self.trUtf8("Resi&ze columns"), self.__resizeColumns)
        self.__menu.addSeparator()
        self.__menu.addAction(self.trUtf8("Configure..."), self.__configure)
        
        self.__backMenu = QMenu(self)
        self.__backMenu.addAction(self.trUtf8("&New Task..."), self.__newTask)
        self.__backMenu.addSeparator()
        self.backProjectTasksMenuItem = self.__backMenu.addMenu(self.__projectTasksMenu)
        self.__backMenu.addSeparator()
        self.backPasteItem = self.__backMenu.addAction(self.trUtf8("&Paste"),
                                                       self.__pasteTask)
        self.__backMenu.addSeparator()
        self.__backMenu.addAction(self.trUtf8("Delete Completed &Tasks"),
                                  self.__deleteCompleted)
        self.__backMenu.addSeparator()
        self.__backMenuFilteredAct = \
            self.__backMenu.addAction(self.trUtf8("&Filtered display"))
        self.__backMenuFilteredAct.setCheckable(True)
        self.__backMenuFilteredAct.setChecked(False)
        self.__backMenuFilteredAct.triggered[bool].connect(self.__activateFilter)
        self.__backMenu.addAction(self.trUtf8("Filter c&onfiguration..."),
                              self.__configureFilter)
        self.__backMenu.addSeparator()
        self.__backMenu.addAction(self.trUtf8("Resi&ze columns"), self.__resizeColumns)
        self.__backMenu.addSeparator()
        self.__backMenu.addAction(self.trUtf8("Configure..."), self.__configure)
        
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
            index = self.indexOfTopLevelItem(task)
            if self.taskFilter.showTask(task):
                # show the task
                if index == -1:
                    self.addTopLevelItem(task)
            else:
                # hide the task
                if index != -1:
                    self.takeTopLevelItem(index)
        self.__resort()
        self.__resizeColumns()
        
    def __taskItemActivated(self, itm, col):
        """
        Private slot to handle the activation of an item.
        
        @param itm reference to the activated item (QTreeWidgetItem)
        @param col column the item was activated in (integer)
        """
        fn = itm.getFilename()
        if fn:
            self.displayFile.emit(fn, itm.getLineno())
        else:
            self.__editTaskProperties()

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
    
    def addTask(self, description, priority=1, filename="", lineno=0,
                completed=False, _time=0, isProjectTask=False,
                isBugfixTask=False, longtext=""):
        """
        Public slot to add a task.
        
        @param description descriptive text of the task (string)
        @param priority priority of the task (0=high, 1=normal, 2=low)
        @param filename filename containing the task (string)
        @param lineno line number containing the task (integer)
        @param completed flag indicating completion status (boolean)
        @param _time creation time of the task (float, if 0 use current time)
        @param isProjectTask flag indicating a task related to the current
            project (boolean)
        @param isBugfixTask flag indicating a bugfix task (boolean)
        @param longtext explanatory text of the task (string)
        """
        task = Task(description, priority, filename, lineno, completed,
                   _time, isProjectTask, isBugfixTask,
                   self.project, longtext)
        self.tasks.append(task)
        if self.taskFilter.showTask(task):
            self.addTopLevelItem(task)
            self.__resort()
            self.__resizeColumns()
    
    def addFileTask(self, description, filename, lineno, isBugfixTask=False,
                    longtext=""):
        """
        Public slot to add a file related task.
        
        @param description descriptive text of the task (string)
        @param filename filename containing the task (string)
        @param lineno line number containing the task (integer)
        @param isBugfixTask flag indicating a bugfix task (boolean)
        @param longtext explanatory text of the task (string)
        """
        self.addTask(description, filename=filename, lineno=lineno,
                     isProjectTask=(
                        self.project and self.project.isProjectSource(filename)),
                     isBugfixTask=isBugfixTask, longtext=longtext)
        
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
        
    def clearProjectTasks(self):
        """
        Public slot to clear project related tasks.
        """
        for task in self.tasks[:]:
            if task.isProjectTask():
                if self.copyTask == task:
                    self.copyTask = None
                index = self.indexOfTopLevelItem(task)
                self.takeTopLevelItem(index)
                self.tasks.remove(task)
                del task
        
    def clearFileTasks(self, filename):
        """
        Public slot to clear all tasks related to a file.
        
        @param filename name of the file (string)
        """
        for task in self.tasks[:]:
            if task.getFilename() == filename:
                if self.copyTask == task:
                    self.copyTask = None
                index = self.indexOfTopLevelItem(task)
                self.takeTopLevelItem(index)
                self.tasks.remove(task)
                del task
        
    def __editTaskProperties(self):
        """
        Private slot to handle the "Properties" context menu entry
        """
        task = self.currentItem()
        dlg = TaskPropertiesDialog(task, self, self.projectOpen)
        ro = task.getFilename() != ""
        if ro:
            dlg.setReadOnly()
        if dlg.exec_() == QDialog.Accepted and not ro:
            data = dlg.getData()
            task.setDescription(data[0])
            task.setPriority(data[1])
            task.setCompleted(data[2])
            task.setProjectTask(data[3])
            task.setLongText(data[4])
    
    def __newTask(self):
        """
        Private slot to handle the "New Task" context menu entry.
        """
        dlg = TaskPropertiesDialog(None, self, self.projectOpen)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.getData()
            self.addTask(data[0], data[1], completed=data[2], isProjectTask=data[3],
                longtext=data[4])
    
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
            self.addTask(self.copyTask.description,
                         priority=self.copyTask.priority,
                         completed=self.copyTask.completed,
                         longtext=self.copyTask.longtext,
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
            res = E5MessageBox.yesNo(self,
                self.trUtf8("Activate task filter"),
                self.trUtf8("""The task filter doesn't have any active filters."""
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
            self.trUtf8("Scan Filter Patterns"),
            self.trUtf8("Enter filename patterns of files"
                        " to be excluded separated by a comma:"),
            QLineEdit.Normal,
            self.projectTasksScanFilter)
        if ok:
            self.projectTasksScanFilter = filter
    
    def __regenerateProjectTasks(self):
        """
        Private slot to handle the "Regenerated project tasks" context menu entry.
        """
        todoMarkers = Preferences.getTasks("TasksMarkers").split()
        bugfixMarkers = Preferences.getTasks("TasksMarkersBugfix").split()
        files = self.project.pdata["SOURCES"]
        
        # apply file filter
        filterList = [f.strip() for f in self.projectTasksScanFilter.split(",")
                      if f.strip()]
        if filterList:
            for filter in filterList:
                files = [f for f in files if not fnmatch.fnmatch(f, filter)]
        
        # remove all project tasks
        self.clearProjectTasks()
        
        # now process them
        progress = QProgressDialog(self.trUtf8("Extracting project tasks..."),
            self.trUtf8("Abort"), 0, len(files))
        progress.setMinimumDuration(0)
        count = 0
        
        for file in files:
            progress.setLabelText(
                self.trUtf8("Extracting project tasks...\n{0}").format(file))
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
                self.progress.setValue(count)
                continue
            
            # now search tasks and record them
            lineIndex = 0
            for line in lines:
                lineIndex += 1
                shouldContinue = False
                # normal tasks first
                for tasksMarker in todoMarkers:
                    index = line.find(tasksMarker)
                    if index > -1:
                        task = line[index:]
                        self.addFileTask(task, fn, lineIndex, False)
                        shouldContinue = True
                        break
                if shouldContinue:
                    continue
                
                # bugfix tasks second
                for tasksMarker in bugfixMarkers:
                    index = line.find(tasksMarker)
                    if index > -1:
                        task = line[index:]
                        self.addFileTask(task, fn, lineIndex, True)
                        shouldContinue = True
                        break
            
            count += 1
            
        progress.setValue(len(files))
    
    def __configure(self):
        """
        Private method to open the configuration dialog.
        """
        e5App().getObject("UserInterface").showPreferences("tasksPage")
