# -*- coding: utf-8 -*-

# Copyright (c) 2008 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the multi project browser.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QListWidget, QListWidgetItem, QDialog, QMenu

from E5Gui.E5Application import e5App

import UI.PixmapCache


class MultiProjectBrowser(QListWidget):
    """
    Class implementing the multi project browser.
    """
    def __init__(self, multiProject, parent=None):
        """
        Constructor
        
        @param multiProject reference to the multi project object
        @param parent parent widget (QWidget)
        """
        super(MultiProjectBrowser, self).__init__(parent)
        self.multiProject = multiProject
        
        self.setWindowIcon(UI.PixmapCache.getIcon("eric.png"))
        self.setAlternatingRowColors(True)
        
        self.__openingProject = False
        
        self.multiProject.newMultiProject.connect(
            self.__newMultiProject)
        self.multiProject.multiProjectOpened.connect(
            self.__multiProjectOpened)
        self.multiProject.multiProjectClosed.connect(
            self.__multiProjectClosed)
        self.multiProject.projectDataChanged.connect(
            self.__projectDataChanged)
        self.multiProject.projectAdded.connect(
            self.__projectAdded)
        self.multiProject.projectRemoved.connect(
            self.__projectRemoved)
        self.multiProject.projectOpened.connect(
            self.__projectOpened)
        
        self.__createPopupMenu()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__contextMenuRequested)
        self.itemActivated.connect(self.__openItem)
    
    ###########################################################################
    ## Slot handling methods below
    ###########################################################################
    
    def __newMultiProject(self):
        """
        Private slot to handle the creation of a new multi project.
        """
        self.clear()
    
    def __multiProjectOpened(self):
        """
        Private slot to handle the opening of a multi project.
        """
        for project in self.multiProject.getProjects():
            self.__addProject(project)
        
        self.sortItems()
    
    def __multiProjectClosed(self):
        """
        Private slot to handle the closing of a multi project.
        """
        self.clear()
    
    def __projectAdded(self, project):
        """
        Private slot to handle the addition of a project to the multi project.
        
        @param project reference to the project data dictionary
        """
        self.__addProject(project)
        self.sortItems()
    
    def __projectRemoved(self, project):
        """
        Private slot to handle the removal of a project from the multi project.
        
        @param project reference to the project data dictionary
        """
        row = self.__findProjectItem(project)
        if row > -1:
            itm = self.takeItem(row)
            del itm
    
    def __projectDataChanged(self, project):
        """
        Private slot to handle the change of a project of the multi project.
        
        @param project reference to the project data dictionary
        """
        row = self.__findProjectItem(project)
        if row > -1:
            self.__setItemData(self.item(row), project)
            
            self.sortItems()
    
    def __projectOpened(self, projectfile):
        """
        Private slot to handle the opening of a project.
        
        @param projectfile file name of the opened project file (string)
        """
        project = {
            'name': "",
            'file': projectfile,
            'master': False,
            'description': "",
        }
        row = self.__findProjectItem(project)
        if row > -1:
            self.item(row).setSelected(True)
    
    def __contextMenuRequested(self, coord):
        """
        Private slot to show the context menu.
        
        @param coord the position of the mouse pointer (QPoint)
        """
        itm = self.itemAt(coord)
        if itm is None:
            self.__backMenu.popup(self.mapToGlobal(coord))
        else:
            self.__menu.popup(self.mapToGlobal(coord))
    
    def __openItem(self, itm=None):
        """
        Private slot to open a project.
        
        @param itm reference to the project item to be opened (QListWidgetItem)
        """
        if itm is None:
            itm = self.currentItem()
            if itm is None:
                return
        
        if not self.__openingProject:
            filename = itm.data(Qt.UserRole)
            if filename:
                self.__openingProject = True
                self.multiProject.openProject(filename)
                self.__openingProject = False
    
    ###########################################################################
    ## Private methods below
    ###########################################################################
    
    def __addProject(self, project):
        """
        Private method to add a project to the list.
        
        @param project reference to the project data dictionary
        """
        itm = QListWidgetItem(self)
        self.__setItemData(itm, project)
    
    def __setItemData(self, itm, project):
        """
        Private method to set the data of a project item.
        
        @param itm reference to the item to be set (QListWidgetItem)
        @param project reference to the project data dictionary
        """
        itm.setText(project['name'])
        if project['master']:
            itm.setIcon(UI.PixmapCache.getIcon("masterProject.png"))
        else:
            itm.setIcon(UI.PixmapCache.getIcon("empty.png"))
        itm.setToolTip(project['file'])
        itm.setData(Qt.UserRole, project['file'])
    
    def __findProjectItem(self, project):
        """
        Private method to search a specific project item.
        
        @param project reference to the project data dictionary
        @return row number of the project, -1 if not found (integer)
        """
        row = 0
        while row < self.count():
            itm = self.item(row)
            data = itm.data(Qt.UserRole)
            if data == project['file']:
                return row
            row += 1
        
        return -1
    
    def __removeProject(self):
        """
        Private method to handle the Remove context menu entry.
        """
        itm = self.currentItem()
        if itm is not None:
            filename = itm.data(Qt.UserRole)
            if filename:
                self.multiProject.removeProject(filename)
    
    def __showProjectProperties(self):
        """
        Private method to show the data of a project entry.
        """
        itm = self.currentItem()
        if itm is not None:
            filename = itm.data(Qt.UserRole)
            if filename:
                project = self.multiProject.getProject(filename)
                if project is not None:
                    from .AddProjectDialog import AddProjectDialog
                    dlg = AddProjectDialog(self, project=project)
                    if dlg.exec_() == QDialog.Accepted:
                        name, filename, isMaster, description = dlg.getData()
                        project = {
                            'name': name,
                            'file': filename,
                            'master': isMaster,
                            'description': description,
                        }
                        self.multiProject.changeProjectProperties(project)
    
    def __addNewProject(self):
        """
        Private method to add a new project entry.
        """
        self.multiProject.addProject()
    
    def __createPopupMenu(self):
        """
        Private method to create the popup menu.
        """
        self.__menu = QMenu(self)
        self.__menu.addAction(self.trUtf8("Open"), self.__openItem)
        self.__menu.addAction(self.trUtf8("Remove"), self.__removeProject)
        self.__menu.addAction(self.trUtf8("Properties"),
                              self.__showProjectProperties)
        self.__menu.addSeparator()
        self.__menu.addAction(self.trUtf8("Add Project..."),
                              self.__addNewProject)
        self.__menu.addSeparator()
        self.__menu.addAction(self.trUtf8("Configure..."), self.__configure)
        
        self.__backMenu = QMenu(self)
        self.__backMenu.addAction(self.trUtf8("Add Project..."),
                                  self.__addNewProject)
        self.__backMenu.addSeparator()
        self.__backMenu.addAction(self.trUtf8("Configure..."),
                                  self.__configure)
    
    def __configure(self):
        """
        Private method to open the configuration dialog.
        """
        e5App().getObject("UserInterface").showPreferences("multiProjectPage")
