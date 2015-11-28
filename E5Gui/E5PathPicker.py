# -*- coding: utf-8 -*-

# Copyright (c) 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a path picker widget.
"""

from __future__ import unicode_literals

import os

try:
    from enum import Enum
except ImportError:
    from ThirdParty.enum import Enum

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QToolButton

from . import E5FileDialog
from .E5LineEdit import E5ClearableLineEdit
from .E5Completers import E5FileCompleter, E5DirCompleter
from .E5ComboBox import E5ClearableComboBox

import UI.PixmapCache
import Utilities


class E5PathPickerModes(Enum):
    """
    Class implementing the path picker modes.
    """
    OpenFileMode = 0
    OpenFilesMode = 1
    SaveFileMode = 2
    DirectoryMode = 3


class E5PathPicker(QWidget):
    """
    Class implementing a path picker widget consisting of a line edit and a
    tool button to open a file dialog.
    
    @signal textChanged(path) emitted when the entered path has changed
    @signal pathSelected(path) emitted after a path has been selected via the
        file dialog
    @signal aboutToShowPathPickerDialog emitted before the file dialog is shown
    """
    DefaultMode = E5PathPickerModes.OpenFileMode
    
    textChanged = pyqtSignal(str)
    pathSelected = pyqtSignal(str)
    aboutToShowPathPickerDialog = pyqtSignal()
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget
        @type QWidget
        """
        super(E5PathPicker, self).__init__(parent)
        
        self.__mode = E5PathPicker.DefaultMode
        self.__editorEnabled = True
        
        self.__completer = None
        self.__filters = ""
        self.__defaultDirectory = ""
        self.__windowTitle = ""
        
        self.__layout = QHBoxLayout()
        self.__layout.setSpacing(0)
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.__layout)
        
        self.__editor = E5ClearableLineEdit(self, self.tr("Enter Path Name"))
        
        self.__button = QToolButton(self)
        self.__button.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.__button.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.__layout.addWidget(self.__editor)
        self.__layout.addWidget(self.__button)
        
        self.__button.clicked.connect(self.__showPathPickerDialog)
        self.__editor.textChanged.connect(self.textChanged)
    
    def setMode(self, mode):
        """
        Public method to set the path picker mode.
        
        @param mode picker mode
        @type E5PathPickerModes
        """
        assert mode in E5PathPickerModes
        
        oldMode = self.__mode
        self.__mode = mode
        
        if mode != oldMode:
            # Remove current completer
            self.__editor.setCompleter(None)
            self.__completer = None
            
            # Set a new completer
            if mode == E5PathPickerModes.DirectoryMode:
                self.__completer = E5DirCompleter(self.__editor)
            else:
                self.__completer = E5FileCompleter(self.__editor)
            
            # set inactive text
            if mode == E5PathPickerModes.OpenFilesMode:
                self.__editor.setInactiveText(
                    self.tr("Enter Path Names separated by ';'"))
            else:
                self.__editor.setInactiveText(
                    self.tr("Enter Path Name"))
    
    def mode(self):
        """
        Public method to get the path picker mode.
        
        @return path picker mode
        @rtype E5PathPickerModes
        """
        return self.__mode
    
    def clear(self):
        """
        Public method to clear the current path.
        """
        self.__editor.clear()
    
    def setText(self, path):
        """
        Public method to set the current path.
        
        @param path path to be set
        @type str
        """
        if self.__mode == E5PathPickerModes.OpenFilesMode:
            self.__editor.setText(path)
        else:
            self.__editor.setText(Utilities.toNativeSeparators(path))
    
    def text(self):
        """
        Public method to get the current path.
        
        @return current path
        @rtype str
        """
        if self.__mode == E5PathPickerModes.OpenFilesMode:
            return ";".join(
                [Utilities.toNativeSeparators(path)
                 for path in self.__editor.text().split(";")])
        else:
            return os.path.expanduser(
                Utilities.toNativeSeparators(self.__editor.text()))
    
    def setPath(self, path):
        """
        Public method to set the current path.
        
        @param path path to be set
        @type str
        """
        self.setText(path)
    
    def path(self):
        """
        Public method to get the current path.
        
        @return current path
        @rtype str
        """
        return self.text()
    
    def paths(self):
        """
        Public method to get the list of entered paths.
        
        @return entered paths
        @rtype list of str
        """
        if self.__mode == E5PathPickerModes.OpenFilesMode:
            return self.path().split(";")
        else:
            return [self.path()]
    
    def firstPath(self):
        """
        Public method to get the first path of a list of entered paths.
        
        @return first path
        @rtype str
        """
        if self.__mode == E5PathPickerModes.OpenFilesMode:
            return self.path().split(";")[0]
        else:
            return self.path()
    
    def lastPath(self):
        """
        Public method to get the last path of a list of entered paths.
        
        @return first path
        @rtype str
        """
        if self.__mode == E5PathPickerModes.OpenFilesMode:
            return self.path().split(";")[-1]
        else:
            return self.path()
    
    def setEditorEnabled(self, enable):
        """
        Public method to set the path editor's enabled state.
        
        @param enable flag indicating the enable state
        @type bool
        """
        if enable != self.__editorEnabled:
            self.__editorEnabled = enable
            self.__editor.setEnabled(enable)
    
    def editorEnabled(self):
        """
        Public method to get the path editor's enabled state.
        
        @return flag indicating the enabled state
        @rtype bool
        """
        return self.__editorEnabled
    
    def setDefaultDirectory(self, directory):
        """
        Public method to set the default directory.
        
        @param directory default directory
        @type str
        """
        self.__defaultDirectory = directory
    
    def defaultDirectory(self):
        """
        Public method to get the default directory.
        
        @return default directory
        @rtype str
        """
        return self.__defaultDirectory
    
    def setWindowTitle(self, title):
        """
        Public method to set the path picker dialog window title.
        
        @param title window title
        @type str
        """
        self.__windowTitle = title
    
    def windowTitle(self):
        """
        Public method to get the path picker dialog's window title.
        
        @return window title
        @rtype str
        """
        return self.__windowTitle
    
    def setFilters(self, filters):
        """
        Public method to set the filters for the path picker dialog.
        
        Note: Multiple filters must be separated by ';;'.
        
        @param filters string containing the file filters
        @type str
        """
        self.__filters = filters
    
    def filters(self):
        """
        Public methods to get the filter string.
        
        @return filter string
        @rtype str
        """
        return self.__filters
    
    def setButtonToolTip(self, tooltip):
        """
        Public method to set the tool button tool tip.
        
        @param tooltip text to be set as a tool tip
        @type str
        """
        self.__button.setToolTip(tooltip)
    
    def buttonToolTip(self):
        """
        Public method to get the tool button tool tip.
        
        @return tool tip text
        @rtype str
        """
        return self.__button.toolTip()
    
    def setEditorToolTip(self, tooltip):
        """
        Public method to set the editor tool tip.
        
        @param tooltip text to be set as a tool tip
        @type str
        """
        self.__editor.setToolTip(tooltip)
    
    def editorToolTip(self):
        """
        Public method to get the editor tool tip.
        
        @return tool tip text
        @rtype str
        """
        return self.__editor.toolTip()
    
    def __showPathPickerDialog(self):
        """
        Private slot to show the path picker dialog.
        """
        self.aboutToShowPathPickerDialog.emit()
        
        windowTitle = self.__windowTitle
        if not windowTitle:
            if self.__mode == E5PathPickerModes.OpenFileMode:
                windowTitle = self.tr("Choose a file to open")
            elif self.__mode == E5PathPickerModes.OpenFilesMode:
                windowTitle = self.tr("Choose files to open")
            elif self.__mode == E5PathPickerModes.SaveFileMode:
                windowTitle = self.tr("Choose a file to save")
            elif self.__mode == E5PathPickerModes.DirectoryMode:
                windowTitle = self.tr("Choose a directory")
        
        directory = self.__editor.text()
        if not directory and self.__defaultDirectory:
            directory = self.__defaultDirectory
        if self.__mode == E5PathPickerModes.OpenFilesMode:
            directory = os.path.expanduser(directory.split(";")[0])
        else:
            directory = os.path.expanduser(directory)
        if not os.path.isabs(directory) and self.__defaultDirectory:
            directory = os.path.join(self.__defaultDirectory, directory)
        directory = Utilities.fromNativeSeparators(directory)
        
        if self.__mode == E5PathPickerModes.OpenFileMode:
            path = E5FileDialog.getOpenFileName(
                self,
                windowTitle,
                directory,
                self.__filters)
            path = Utilities.toNativeSeparators(path)
        elif self.__mode == E5PathPickerModes.OpenFilesMode:
            paths = E5FileDialog.getOpenFileNames(
                self,
                windowTitle,
                directory,
                self.__filters)
            path = ";".join([Utilities.toNativeSeparators(path)
                             for path in paths])
        elif self.__mode == E5PathPickerModes.SaveFileMode:
            path = E5FileDialog.getSaveFileName(
                self,
                windowTitle,
                directory,
                self.__filters,
                E5FileDialog.Options(E5FileDialog.DontConfirmOverwrite))
            path = Utilities.toNativeSeparators(path)
        elif self.__mode == E5PathPickerModes.DirectoryMode:
            path = E5FileDialog.getExistingDirectory(
                self,
                windowTitle,
                directory,
                E5FileDialog.Options(E5FileDialog.ShowDirsOnly))
            path = Utilities.toNativeSeparators(path)
            while path.endswith(os.sep):
                path = path[:-1]
        
        if path:
            self.__editor.setText(path)
            self.pathSelected.emit(path)


class E5ComboPathPicker(QWidget):
    """
    Class implementing a path picker widget consisting of a combobox and a
    tool button to open a file dialog.
    
    @signal editTextChanged(path) emitted when the entered path has changed
    @signal pathSelected(path) emitted after a path has been selected via the
        file dialog
    @signal aboutToShowPathPickerDialog emitted before the file dialog is shown
    """
    DefaultMode = E5PathPickerModes.OpenFileMode
    
    editTextChanged = pyqtSignal(str)
    pathSelected = pyqtSignal(str)
    aboutToShowPathPickerDialog = pyqtSignal()
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget
        @type QWidget
        """
        super(E5ComboPathPicker, self).__init__(parent)
        
        self.__mode = E5PathPicker.DefaultMode
        self.__editorEnabled = True
        
        self.__completer = None
        self.__filters = ""
        self.__defaultDirectory = ""
        self.__windowTitle = ""
        
        self.__layout = QHBoxLayout()
        self.__layout.setSpacing(0)
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.__layout)
        
        self.__editor = E5ClearableComboBox(self, self.tr("Enter Path Name"))
        
        self.__button = QToolButton(self)
        self.__button.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.__button.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.__layout.addWidget(self.__editor)
        self.__layout.addWidget(self.__button)
        
        self.__button.clicked.connect(self.__showPathPickerDialog)
        self.__editor.editTextChanged.connect(self.editTextChanged)
    
    def setMode(self, mode):
        """
        Public method to set the path picker mode.
        
        @param mode picker mode
        @type E5PathPickerModes
        """
        assert mode in E5PathPickerModes
        
        oldMode = self.__mode
        self.__mode = mode
        
        if mode != oldMode:
            # Remove current completer
            self.__editor.setCompleter(None)
            self.__completer = None
            
            # Set a new completer
            if mode == E5PathPickerModes.DirectoryMode:
                self.__completer = E5DirCompleter(self.__editor)
            else:
                self.__completer = E5FileCompleter(self.__editor)
            
            # set inactive text
            if mode == E5PathPickerModes.OpenFilesMode:
                self.__editor.setInactiveText(
                    self.tr("Enter Path Names separated by ';'"))
            else:
                self.__editor.setInactiveText(
                    self.tr("Enter Path Name"))
    
    def mode(self):
        """
        Public method to get the path picker mode.
        
        @return path picker mode
        @rtype E5PathPickerModes
        """
        return self.__mode
    
    def clear(self):
        """
        Public method to clear the list of paths.
        """
        self.__editor.clear()
    
    def clearEditText(self):
        """
        Public method to clear the current path.
        """
        self.__editor.clearEditText()
    
    def setEditText(self, path):
        """
        Public method to set the current path.
        
        @param path path to be set
        @type str
        """
        if self.__mode == E5PathPickerModes.OpenFilesMode:
            self.__editor.setEditText(path)
        else:
            self.__editor.setEditText(Utilities.toNativeSeparators(path))
    
    def currentText(self):
        """
        Public method to get the current path.
        
        @return current path
        @rtype str
        """
        if self.__mode == E5PathPickerModes.OpenFilesMode:
            return ";".join(
                [Utilities.toNativeSeparators(path)
                 for path in self.__editor.currentText().split(";")])
        else:
            return os.path.expanduser(
                Utilities.toNativeSeparators(self.__editor.currentText()))
    
    def setPath(self, path):
        """
        Public method to set the current path.
        
        @param path path to be set
        @type str
        """
        self.setEditText(path)
    
    def path(self):
        """
        Public method to get the current path.
        
        @return current path
        @rtype str
        """
        return self.currentText()
    
    def paths(self):
        """
        Public method to get the list of entered paths.
        
        @return entered paths
        @rtype list of str
        """
        if self.__mode == E5PathPickerModes.OpenFilesMode:
            return self.path().split(";")
        else:
            return [self.path()]
    
    def firstPath(self):
        """
        Public method to get the first path of a list of entered paths.
        
        @return first path
        @rtype str
        """
        if self.__mode == E5PathPickerModes.OpenFilesMode:
            return self.path().split(";")[0]
        else:
            return self.path()
    
    def lastPath(self):
        """
        Public method to get the last path of a list of entered paths.
        
        @return first path
        @rtype str
        """
        if self.__mode == E5PathPickerModes.OpenFilesMode:
            return self.path().split(";")[-1]
        else:
            return self.path()
    
    def addItems(self, pathsList):
        """
        Public method to add paths to the current list.
        
        @param pathsList list of paths to add
        @type list of str
        """
        self.__editor.addItems(pathsList)
    
    def addItem(self, path):
        """
        Public method to add a paths to the current list.
        
        @param path path to add
        @type str
        """
        self.__editor.addItem(path)
    
    def setPathsList(self, pathsList):
        """
        Public method to set the paths list.
        
        @param pathsList list of paths
        @type list of str
        """
        self.clear()
        self.addItems(pathsList)
    
    def setCurrentIndex(self, index):
        """
        Public slot to set the current index.
        
        @param index index of the item to set current
        @type int
        """
        self.__editor.setCurrentIndex(index)
    
    def setEditorEnabled(self, enable):
        """
        Public method to set the path editor's enabled state.
        
        @param enable flag indicating the enable state
        @type bool
        """
        if enable != self.__editorEnabled:
            self.__editorEnabled = enable
            self.__editor.setEnabled(enable)
    
    def editorEnabled(self):
        """
        Public method to get the path editor's enabled state.
        
        @return flag indicating the enabled state
        @rtype bool
        """
        return self.__editorEnabled
    
    def setDefaultDirectory(self, directory):
        """
        Public method to set the default directory.
        
        @param directory default directory
        @type str
        """
        self.__defaultDirectory = directory
    
    def defaultDirectory(self):
        """
        Public method to get the default directory.
        
        @return default directory
        @rtype str
        """
        return self.__defaultDirectory
    
    def setWindowTitle(self, title):
        """
        Public method to set the path picker dialog window title.
        
        @param title window title
        @type str
        """
        self.__windowTitle = title
    
    def windowTitle(self):
        """
        Public method to get the path picker dialog's window title.
        
        @return window title
        @rtype str
        """
        return self.__windowTitle
    
    def setFilters(self, filters):
        """
        Public method to set the filters for the path picker dialog.
        
        Note: Multiple filters must be separated by ';;'.
        
        @param filters string containing the file filters
        @type str
        """
        self.__filters = filters
    
    def filters(self):
        """
        Public methods to get the filter string.
        
        @return filter string
        @rtype str
        """
        return self.__filters
    
    def setButtonToolTip(self, tooltip):
        """
        Public method to set the tool button tool tip.
        
        @param tooltip text to be set as a tool tip
        @type str
        """
        self.__button.setToolTip(tooltip)
    
    def buttonToolTip(self):
        """
        Public method to get the tool button tool tip.
        
        @return tool tip text
        @rtype str
        """
        return self.__button.toolTip()
    
    def setEditorToolTip(self, tooltip):
        """
        Public method to set the editor tool tip.
        
        @param tooltip text to be set as a tool tip
        @type str
        """
        self.__editor.setToolTip(tooltip)
    
    def editorToolTip(self):
        """
        Public method to get the editor tool tip.
        
        @return tool tip text
        @rtype str
        """
        return self.__editor.toolTip()
    
    def __showPathPickerDialog(self):
        """
        Private slot to show the path picker dialog.
        """
        self.aboutToShowPathPickerDialog.emit()
        
        windowTitle = self.__windowTitle
        if not windowTitle:
            if self.__mode == E5PathPickerModes.OpenFileMode:
                windowTitle = self.tr("Choose a file to open")
            elif self.__mode == E5PathPickerModes.OpenFilesMode:
                windowTitle = self.tr("Choose files to open")
            elif self.__mode == E5PathPickerModes.SaveFileMode:
                windowTitle = self.tr("Choose a file to save")
            elif self.__mode == E5PathPickerModes.DirectoryMode:
                windowTitle = self.tr("Choose a directory")
        
        directory = self.__editor.currentText()
        if not directory and self.__defaultDirectory:
            directory = self.__defaultDirectory
        if self.__mode == E5PathPickerModes.OpenFilesMode:
            directory = os.path.expanduser(directory.split(";")[0])
        else:
            directory = os.path.expanduser(directory)
        if not os.path.isabs(directory) and self.__defaultDirectory:
            directory = os.path.join(self.__defaultDirectory, directory)
        directory = Utilities.fromNativeSeparators(directory)
        
        if self.__mode == E5PathPickerModes.OpenFileMode:
            path = E5FileDialog.getOpenFileName(
                self,
                windowTitle,
                directory,
                self.__filters)
            path = Utilities.toNativeSeparators(path)
        elif self.__mode == E5PathPickerModes.OpenFilesMode:
            paths = E5FileDialog.getOpenFileNames(
                self,
                windowTitle,
                directory,
                self.__filters)
            path = ";".join([Utilities.toNativeSeparators(path)
                             for path in paths])
        elif self.__mode == E5PathPickerModes.SaveFileMode:
            path = E5FileDialog.getSaveFileName(
                self,
                windowTitle,
                directory,
                self.__filters,
                E5FileDialog.Options(E5FileDialog.DontConfirmOverwrite))
            path = Utilities.toNativeSeparators(path)
        elif self.__mode == E5PathPickerModes.DirectoryMode:
            path = E5FileDialog.getExistingDirectory(
                self,
                windowTitle,
                directory,
                E5FileDialog.Options(E5FileDialog.ShowDirsOnly))
            path = Utilities.toNativeSeparators(path)
            while path.endswith(os.sep):
                path = path[:-1]
        
        if path:
            self.__editor.setEditText(path)
            self.pathSelected.emit(path)
