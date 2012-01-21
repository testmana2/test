# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the project management functionality.
"""

import os
import time
import shutil
import glob
import fnmatch
import copy
import zipfile
import re

from PyQt4.QtCore import QFile, QFileInfo, pyqtSignal, QCryptographicHash, QIODevice, \
    QByteArray, QObject, Qt
from PyQt4.QtGui import QCursor, QLineEdit, QToolBar, QDialog, QInputDialog, \
    QApplication, QMenu

from E5Gui.E5Application import e5App
from E5Gui import E5FileDialog, E5MessageBox

from Globals import recentNameProject

from .ProjectBrowserModel import ProjectBrowserModel

from .AddLanguageDialog import AddLanguageDialog
from .AddFileDialog import AddFileDialog
from .AddDirectoryDialog import AddDirectoryDialog
from .PropertiesDialog import PropertiesDialog
from .AddFoundFilesDialog import AddFoundFilesDialog
from .DebuggerPropertiesDialog import DebuggerPropertiesDialog
from .FiletypeAssociationDialog import FiletypeAssociationDialog
from .LexerAssociationDialog import LexerAssociationDialog
from .UserPropertiesDialog import UserPropertiesDialog

from E5XML.ProjectReader import ProjectReader
from E5XML.ProjectWriter import ProjectWriter
from E5XML.UserProjectReader import UserProjectReader
from E5XML.UserProjectWriter import UserProjectWriter
from E5XML.SessionReader import SessionReader
from E5XML.SessionWriter import SessionWriter
from E5XML.TasksReader import TasksReader
from E5XML.TasksWriter import TasksWriter
from E5XML.DebuggerPropertiesReader import DebuggerPropertiesReader
from E5XML.DebuggerPropertiesWriter import DebuggerPropertiesWriter

import VCS
from VCS.CommandOptionsDialog import vcsCommandOptionsDialog
from VCS.ProjectHelper import VcsProjectHelper

from Graphics.ApplicationDiagram import ApplicationDiagram

from DataViews.CodeMetricsDialog import CodeMetricsDialog
from DataViews.PyCoverageDialog import PyCoverageDialog
from DataViews.PyProfileDialog import PyProfileDialog

import UI.PixmapCache

from E5Gui.E5Action import E5Action, createActionGroup

import Preferences
import Utilities


class Project(QObject):
    """
    Class implementing the project management functionality.
    
    @signal dirty(int) emitted when the dirty state changes
    @signal projectLanguageAdded(str) emitted after a new language was added
    @signal projectLanguageAddedByCode(str) emitted after a new language was added.
            The language code is sent by this signal.
    @signal projectLanguageRemoved(str) emitted after a language was removed
    @signal projectFormAdded(str) emitted after a new form was added
    @signal projectFormRemoved(str) emitted after a form was removed
    @signal projectSourceAdded(str) emitted after a new source file was added
    @signal projectSourceRemoved(str) emitted after a source was removed
    @signal projectInterfaceAdded(str) emitted after a new IDL file was added
    @signal projectInterfaceRemoved(str) emitted after a IDL file was removed
    @signal projectResourceAdded(str) emitted after a new resource file was added
    @signal projectResourceRemoved(str) emitted after a resource was removed
    @signal projectOthersAdded(str) emitted after a file or directory was added
            to the OTHERS project data area
    @signal projectOthersRemoved(str) emitted after a file was removed from the
            OTHERS project data area
    @signal projectAboutToBeCreated() emitted just before the project will be created
    @signal newProjectHooks() emitted after a new project was generated but before
            the newProject() signal is sent
    @signal newProject() emitted after a new project was generated
    @signal sourceFile(str) emitted after a project file was read to
            open the main script
    @signal projectOpenedHooks() emitted after a project file was read but before the
            projectOpened() signal is sent
    @signal projectOpened() emitted after a project file was read
    @signal projectClosedHooks() emitted after a project file was closed but before the
            projectClosed() signal is sent
    @signal projectClosed() emitted after a project was closed
    @signal projectFileRenamed(str, str) emitted after a file of the project
            has been renamed
    @signal projectPropertiesChanged() emitted after the project properties were changed
    @signal directoryRemoved(str) emitted after a directory has been removed from
            the project
    @signal prepareRepopulateItem(str) emitted before an item of the model is
            repopulated
    @signal completeRepopulateItem(str) emitted after an item of the model was
            repopulated
    @signal vcsStatusMonitorStatus(str, str) emitted to signal the status of the
            monitoring thread (ok, nok, op, off) and a status message
    @signal reinitVCS() emitted after the VCS has been reinitialized
    @signal showMenu(str, QMenu) emitted when a menu is about to be shown. The name
            of the menu and a reference to the menu are given.
    @signal lexerAssociationsChanged() emitted after the lexer associations have been
            changed
    """
    dirty = pyqtSignal(int)
    projectLanguageAdded = pyqtSignal(str)
    projectLanguageAddedByCode = pyqtSignal(str)
    projectLanguageRemoved = pyqtSignal(str)
    projectFormAdded = pyqtSignal(str)
    projectFormRemoved = pyqtSignal(str)
    projectSourceAdded = pyqtSignal(str)
    projectSourceRemoved = pyqtSignal(str)
    projectInterfaceAdded = pyqtSignal(str)
    projectInterfaceRemoved = pyqtSignal(str)
    projectResourceAdded = pyqtSignal(str)
    projectResourceRemoved = pyqtSignal(str)
    projectOthersAdded = pyqtSignal(str)
    projectOthersRemoved = pyqtSignal(str)
    projectAboutToBeCreated = pyqtSignal()
    newProjectHooks = pyqtSignal()
    newProject = pyqtSignal()
    sourceFile = pyqtSignal(str)
    projectOpenedHooks = pyqtSignal()
    projectOpened = pyqtSignal()
    projectClosedHooks = pyqtSignal()
    projectClosed = pyqtSignal()
    projectFileRenamed = pyqtSignal(str, str)
    projectPropertiesChanged = pyqtSignal()
    directoryRemoved = pyqtSignal(str)
    prepareRepopulateItem = pyqtSignal(str)
    completeRepopulateItem = pyqtSignal(str)
    vcsStatusMonitorStatus = pyqtSignal(str, str)
    reinitVCS = pyqtSignal()
    showMenu = pyqtSignal(str, QMenu)
    lexerAssociationsChanged = pyqtSignal()
    
    keynames = [
        "PROGLANGUAGE", "MIXEDLANGUAGE", "PROJECTTYPE",
        "SPELLLANGUAGE", "SPELLWORDS", "SPELLEXCLUDES",
        "DESCRIPTION", "VERSION", "HASH",
        "AUTHOR", "EMAIL",
        "SOURCES", "FORMS", "RESOURCES",
        "TRANSLATIONS", "TRANSLATIONPATTERN", "TRANSLATIONSBINPATH",
        "TRANSLATIONEXCEPTIONS",
        "MAINSCRIPT", "EOL",
        "VCS", "VCSOPTIONS", "VCSOTHERDATA",
        "OTHERS", "INTERFACES",
        "FILETYPES", "LEXERASSOCS",
        "PROJECTTYPESPECIFICDATA",
        "DOCUMENTATIONPARMS",
        "PACKAGERSPARMS",
        "CHECKERSPARMS",
        "OTHERTOOLSPARMS",
    ]
    
    dbgKeynames = [
        "INTERPRETER", "DEBUGCLIENT",
        "ENVIRONMENTOVERRIDE", "ENVIRONMENTSTRING",
        "REMOTEDEBUGGER", "REMOTEHOST", "REMOTECOMMAND",
        "PATHTRANSLATION", "REMOTEPATH", "LOCALPATH",
        "CONSOLEDEBUGGER", "CONSOLECOMMAND",
        "REDIRECT", "NOENCODING",
    ]
    
    userKeynames = [
        "VCSOVERRIDE", "VCSSTATUSMONITORINTERVAL",
    ]
    
    eols = [os.linesep, "\n", "\r", "\r\n"]
    
    def __init__(self, parent=None, filename=None):
        """
        Constructor
        
        @param parent parent widget (usually the ui object) (QWidget)
        @param filename optional filename of a project file to open (string)
        """
        super().__init__(parent)
        
        self.ui = parent
        
        self.sourceExtensions = {
            "Python2": Preferences.getPython("PythonExtensions"),
            "Python3": Preferences.getPython("Python3Extensions"),
            "Ruby": ['.rb'],
            "Mixed": Preferences.getPython("Python3Extensions") + ['.rb'],
        }
        
        self.dbgFilters = {
            "Python2": self.trUtf8(
                         "Python2 Files (*.py2);;"
                         "Python2 GUI Files (*.pyw2);;"),
            "Python3": self.trUtf8(
                         "Python3 Files (*.py *.py3);;"
                         "Python3 GUI Files (*.pyw *.pyw3);;"),
            "Ruby": self.trUtf8("Ruby Files (*.rb);;"),
        }
        
        self.vcsMenu = None
        
        self.__initProjectTypes()
        
        self.__initData()
        
        self.recent = []
        self.__loadRecent()
        
        if filename is not None:
            self.openProject(filename)
        else:
            self.vcs = self.initVCS()
        
        self.__model = ProjectBrowserModel(self)
        
        self.codemetrics = None
        self.codecoverage = None
        self.profiledata = None
        self.applicationDiagram = None
        
    def __initProjectTypes(self):
        """
        Private method to initialize the list of supported project types.
        """
        self.__projectTypes = {}
        self.__fileTypeCallbacks = {}
        self.__lexerAssociationCallbacks = {}
        self.__binaryTranslationsCallbacks = {}
        self.__projectTypes["Qt4"] = self.trUtf8("Qt4 GUI")
        self.__projectTypes["Qt4C"] = self.trUtf8("Qt4 Console")
        self.__projectTypes["E4Plugin"] = self.trUtf8("Eric Plugin")
        self.__projectTypes["Console"] = self.trUtf8("Console")
        self.__projectTypes["Other"] = self.trUtf8("Other")
        if Utilities.checkPyside():
            self.__projectTypes["PySide"] = self.trUtf8("PySide GUI")
            self.__projectTypes["PySideC"] = self.trUtf8("PySide Console")
        else:
            pass
        
    def getProjectTypes(self):
        """
        Public method to get the list of supported project types.
        
        @return reference to the dictionary of project types.
        """
        return self.__projectTypes
        
    def hasProjectType(self, type_):
        """
        Public method to check, if a project type is already registered.
        
        @param type_ internal type designator to be unregistered (string)
        """
        return type_ in self.__projectTypes
        
    def registerProjectType(self, type_, description, fileTypeCallback=None,
        binaryTranslationsCallback=None, lexerAssociationCallback=None):
        """
        Public method to register a project type.
        
        @param type_ internal type designator to be registered (string)
        @param description more verbose type name (display string) (string)
        @keyparam fileTypeCallback reference to a method returning a dictionary
            of filetype associations.
        @keyparam binaryTranslationsCallback reference to a method returning the
            name of the binary translation file given the name of the raw
            translation file
        @keyparam lexerAssociationCallback reference to a method returning the
            lexer type to be used for syntax highlighting given the name of
            a file
        """
        if type_ in self.__projectTypes:
            E5MessageBox.critical(self.ui,
                self.trUtf8("Registering Project Type"),
                self.trUtf8("""<p>The Project type <b>{0}</b> already exists.</p>""")\
                    .format(type_)
            )
        else:
            self.__projectTypes[type_] = description
            self.__fileTypeCallbacks[type_] = fileTypeCallback
            self.__lexerAssociationCallbacks[type_] = lexerAssociationCallback
            self.__binaryTranslationsCallbacks[type_] = binaryTranslationsCallback
        
    def unregisterProjectType(self, type_):
        """
        Public method to unregister a project type.
        
        @param type_ internal type designator to be unregistered (string)
        """
        if type_ in self.__projectTypes:
            del self.__projectTypes[type_]
        if type_ in self.__fileTypeCallbacks:
            del self.__fileTypeCallbacks[type_]
        if type_ in self.__lexerAssociationCallbacks:
            del self.__lexerAssociationCallbacks[type_]
        if type_ in self.__binaryTranslationsCallbacks:
            del self.__binaryTranslationsCallbacks[type_]
        
    def __initData(self):
        """
        Private method to initialize the project data part.
        """
        self.loaded = False     # flag for the loaded status
        self.__dirty = False      # dirty flag
        self.pfile = ""         # name of the project file
        self.ppath = ""         # name of the project directory
        self.ppathRe = None
        self.translationsRoot = ""  # the translations prefix
        self.name = ""
        self.opened = False
        self.subdirs = [""]  # record the project dir as a relative path (i.e. empty path)
        self.otherssubdirs = []
        self.vcs = None
        self.dbgCmdline = ''
        self.dbgWd = ''
        self.dbgEnv = ''
        self.dbgReportExceptions = True
        self.dbgExcList = []
        self.dbgExcIgnoreList = []
        self.dbgAutoClearShell = True
        self.dbgTracePython = False
        self.dbgAutoContinue = True
        
        self.pdata = {}
        for key in self.__class__.keynames:
            self.pdata[key] = []
        self.pdata["AUTHOR"] = ['']
        self.pdata["EMAIL"] = ['']
        self.pdata["HASH"] = ['']
        self.pdata["PROGLANGUAGE"] = ["Python3"]
        self.pdata["MIXEDLANGUAGE"] = [False]
        self.pdata["PROJECTTYPE"] = ["Qt4"]
        self.pdata["SPELLLANGUAGE"] = \
            [Preferences.getEditor("SpellCheckingDefaultLanguage")]
        self.pdata["SPELLWORDS"] = ['']
        self.pdata["SPELLEXCLUDES"] = ['']
        self.pdata["FILETYPES"] = {}
        self.pdata["LEXERASSOCS"] = {}
        self.pdata["PROJECTTYPESPECIFICDATA"] = {}
        self.pdata["CHECKERSPARMS"] = {}
        self.pdata["PACKAGERSPARMS"] = {}
        self.pdata["DOCUMENTATIONPARMS"] = {}
        self.pdata["OTHERTOOLSPARMS"] = {}
        self.pdata["EOL"] = [0]
        
        self.__initDebugProperties()
        
        self.pudata = {}
        for key in self.__class__.userKeynames:
            self.pudata[key] = []
        
        self.vcs = self.initVCS()
        
    def getData(self, category, key):
        """
        Public method to get data out of the project data store.
        
        @param category category of the data to get (string, one of
            PROJECTTYPESPECIFICDATA, CHECKERSPARMS, PACKAGERSPARMS, DOCUMENTATIONPARMS
            or OTHERTOOLSPARMS)
        @param key key of the data entry to get (string).
        @return a copy of the requested data or None
        """
        if category in ["PROJECTTYPESPECIFICDATA", "CHECKERSPARMS", "PACKAGERSPARMS",
                        "DOCUMENTATIONPARMS", "OTHERTOOLSPARMS"] and \
           key in self.pdata[category]:
            return copy.deepcopy(self.pdata[category][key])
        else:
            return None
        
    def setData(self, category, key, data):
        """
        Public method to store data in the project data store.
        
        @param category category of the data to get (string, one of
            PROJECTTYPESPECIFICDATA, CHECKERSPARMS, PACKAGERSPARMS, DOCUMENTATIONPARMS
            or OTHERTOOLSPARMS)
        @param key key of the data entry to get (string).
        @param data data to be stored
        @return flag indicating success (boolean)
        """
        if category not in ["PROJECTTYPESPECIFICDATA", "CHECKERSPARMS", "PACKAGERSPARMS",
                            "DOCUMENTATIONPARMS", "OTHERTOOLSPARMS"]:
            return False
        
        # test for changes of data and save them in the project
        # 1. there were none, now there are
        if key not in self.pdata[category] and len(data) > 0:
            self.pdata[category][key] = copy.deepcopy(data)
            self.setDirty(True)
        # 2. there were some, now there aren't
        elif key in self.pdata[category] and len(data) == 0:
            del self.pdata[category][key]
            self.setDirty(True)
        # 3. there were some and still are
        elif key in self.pdata[category] and len(data) > 0:
            if data != self.pdata[category][key]:
                self.pdata[category][key] = copy.deepcopy(data)
                self.setDirty(True)
        # 4. there were none and none are given
        else:
            return False
        return True
        
    def initFileTypes(self):
        """
        Public method to initialize the filetype associations with default values.
        """
        self.pdata["FILETYPES"] = {}
        if self.pdata["MIXEDLANGUAGE"][0]:
            sourceKey = "Mixed"
        else:
            sourceKey = self.pdata["PROGLANGUAGE"][0]
        for ext in self.sourceExtensions[sourceKey]:
            self.pdata["FILETYPES"]["*{0}".format(ext)] = "SOURCES"
        self.pdata["FILETYPES"]["*.idl"] = "INTERFACES"
        if self.pdata["PROJECTTYPE"][0] in ["Qt4", "E4Plugin", "PySide"]:
            self.pdata["FILETYPES"]["*.ui"] = "FORMS"
            self.pdata["FILETYPES"]["*.ui.h"] = "FORMS"
        if self.pdata["PROJECTTYPE"][0] in ["Qt4", "Qt4C", "E4Plugin",
                                            "PySide", "PySideC"]:
            self.pdata["FILETYPES"]["*.qrc"] = "RESOURCES"
        if self.pdata["PROJECTTYPE"][0] in ["Qt4", "Qt4C", "E4Plugin",
                                            "PySide", "PySideC"]:
            self.pdata["FILETYPES"]["*.ts"] = "TRANSLATIONS"
            self.pdata["FILETYPES"]["*.qm"] = "TRANSLATIONS"
        try:
            if self.__fileTypeCallbacks[self.pdata["PROJECTTYPE"][0]] is not None:
                ftypes = self.__fileTypeCallbacks[self.pdata["PROJECTTYPE"][0]]()
                self.pdata["FILETYPES"].update(ftypes)
        except KeyError:
            pass
        self.setDirty(True)
        
    def updateFileTypes(self):
        """
        Public method to update the filetype associations with new default values.
        """
        if self.pdata["PROJECTTYPE"][0] in ["Qt4", "Qt4C", "E4Plugin",
                                            "PySide", "PySideC"]:
            if "*.ts" not in self.pdata["FILETYPES"]:
                self.pdata["FILETYPES"]["*.ts"] = "TRANSLATIONS"
            if "*.qm" not in self.pdata["FILETYPES"]:
                self.pdata["FILETYPES"]["*.qm"] = "TRANSLATIONS"
        try:
            if self.__fileTypeCallbacks[self.pdata["PROJECTTYPE"][0]] is not None:
                ftypes = self.__fileTypeCallbacks[self.pdata["PROJECTTYPE"][0]]()
                for pattern, ftype in list(ftypes.items()):
                    if pattern not in self.pdata["FILETYPES"]:
                        self.pdata["FILETYPES"][pattern] = ftype
                        self.setDirty(True)
        except KeyError:
            pass
        
    def __loadRecent(self):
        """
        Private method to load the recently opened project filenames.
        """
        self.recent = []
        Preferences.Prefs.rsettings.sync()
        rp = Preferences.Prefs.rsettings.value(recentNameProject)
        if rp is not None:
            for f in rp:
                if QFileInfo(f).exists():
                    self.recent.append(f)
    
    def __saveRecent(self):
        """
        Private method to save the list of recently opened filenames.
        """
        Preferences.Prefs.rsettings.setValue(recentNameProject, self.recent)
        Preferences.Prefs.rsettings.sync()
        
    def getMostRecent(self):
        """
        Public method to get the most recently opened project.
        
        @return path of the most recently opened project (string)
        """
        if len(self.recent):
            return self.recent[0]
        else:
            return None
        
    def getModel(self):
        """
        Public method to get a reference to the project browser model.
        
        @return reference to the project browser model (ProjectBrowserModel)
        """
        return self.__model
        
    def getVcs(self):
        """
        Public method to get a reference to the VCS object.
        
        @return reference to the VCS object
        """
        return self.vcs
        
    def handlePreferencesChanged(self):
        """
        Public slot used to handle the preferencesChanged signal.
        """
        if self.pudata["VCSSTATUSMONITORINTERVAL"]:
            self.setStatusMonitorInterval(
                self.pudata["VCSSTATUSMONITORINTERVAL"][0])
        else:
            self.setStatusMonitorInterval(
                Preferences.getVCS("StatusMonitorInterval"))
        
        self.__model.preferencesChanged()
        
    def setDirty(self, b):
        """
        Public method to set the dirty state.
        
        It emits the signal dirty(int).
        
        @param b dirty state (boolean)
        """
        self.__dirty = b
        self.saveAct.setEnabled(b)
        self.dirty.emit(bool(b))
        
    def isDirty(self):
        """
        Public method to return the dirty state.
        
        @return dirty state (boolean)
        """
        return self.__dirty
        
    def isOpen(self):
        """
        Public method to return the opened state.
        
        @return open state (boolean)
        """
        return self.opened
        
    def __checkFilesExist(self, index):
        """
        Private method to check, if the files in a list exist.
        
        The files in the indicated list are checked for existance in the
        filesystem. Non existant files are removed from the list and the
        dirty state of the project is changed accordingly.
        
        @param index key of the list to be checked (string)
        """
        removed = False
        removelist = []
        for file in self.pdata[index]:
            if not os.path.exists(os.path.join(self.ppath, file)):
                removelist.append(file)
                removed = True
                
        if removed:
            for file in removelist:
                self.pdata[index].remove(file)
            self.setDirty(True)
        
    def __makePpathRe(self):
        """
        Private method to generate a regular expression for the project path.
        """
        ppathRe = (self.ppath + os.sep)\
            .replace("\\", "@@")\
            .replace("/", "@@")\
            .replace("@@", r"[\\/]")
        if Utilities.isWindowsPlatform():
            self.ppathRe = re.compile(ppathRe, re.IGNORECASE)
        else:
            self.ppathRe = re.compile(ppathRe)
        
    def __readProject(self, fn):
        """
        Private method to read in a project (.e4p) file.
        
        @param fn filename of the project file to be read (string)
        @return flag indicating success
        """
        f = QFile(fn)
        if f.open(QIODevice.ReadOnly):
            reader = ProjectReader(f, self)
            reader.readXML()
            res = not reader.hasError()
            f.close()
        else:
            QApplication.restoreOverrideCursor()
            E5MessageBox.critical(self.ui,
                self.trUtf8("Read project file"),
                self.trUtf8("<p>The project file <b>{0}</b> could not be read.</p>")\
                    .format(fn))
            return False
        
        self.pfile = os.path.abspath(fn)
        self.ppath = os.path.abspath(os.path.dirname(fn))
        self.__makePpathRe()
        
        # insert filename into list of recently opened projects
        self.__syncRecent()
        
        if res:
            if len(self.pdata["TRANSLATIONPATTERN"]) == 1:
                self.translationsRoot = \
                    self.pdata["TRANSLATIONPATTERN"][0].split("%language%")[0]
            elif len(self.pdata["MAINSCRIPT"]) == 1:
                self.translationsRoot = os.path.splitext(self.pdata["MAINSCRIPT"][0])[0]
            if os.path.isdir(os.path.join(self.ppath, self.translationsRoot)):
                dn = self.translationsRoot
            else:
                dn = os.path.dirname(self.translationsRoot)
            if dn not in self.subdirs:
                self.subdirs.append(dn)
                
            self.name = os.path.splitext(os.path.basename(fn))[0]
            
            # check, if the files of the project still exist in the project directory
            self.__checkFilesExist("SOURCES")
            self.__checkFilesExist("FORMS")
            self.__checkFilesExist("INTERFACES")
            self.__checkFilesExist("TRANSLATIONS")
            self.__checkFilesExist("RESOURCES")
            self.__checkFilesExist("OTHERS")
            
            # get the names of subdirectories the files are stored in
            for fn in self.pdata["SOURCES"] + \
                      self.pdata["FORMS"] + \
                      self.pdata["INTERFACES"] + \
                      self.pdata["RESOURCES"] + \
                      self.pdata["TRANSLATIONS"]:
                dn = os.path.dirname(fn)
                if dn not in self.subdirs:
                    self.subdirs.append(dn)
            
            # get the names of other subdirectories
            for fn in self.pdata["OTHERS"]:
                dn = os.path.dirname(fn)
                if dn not in self.otherssubdirs:
                    self.otherssubdirs.append(dn)
            
            # create hash value, if it doesn't have one
            if not self.pdata["HASH"][0]:
                hash = str(QCryptographicHash.hash(
                    QByteArray(self.ppath), QCryptographicHash.Sha1).toHex(),
                    encoding="utf-8")
                self.pdata["HASH"] = [hash]
                self.setDirty(True)
            
        return res

    def __writeProject(self, fn=None):
        """
        Private method to save the project infos to a project file.
        
        @param fn optional filename of the project file to be written (string).
                If fn is None, the filename stored in the project object
                is used. This is the 'save' action. If fn is given, this filename
                is used instead of the one in the project object. This is the
                'save as' action.
        @return flag indicating success
        """
        if self.vcs is not None:
            self.pdata["VCSOPTIONS"] = [copy.deepcopy(self.vcs.vcsGetOptions())]
            self.pdata["VCSOTHERDATA"] = [copy.deepcopy(self.vcs.vcsGetOtherData())]
        
        if fn is None:
            fn = self.pfile
        
        f = QFile(fn)
        if f.open(QIODevice.WriteOnly):
            ProjectWriter(f, os.path.splitext(os.path.basename(fn))[0]).writeXML()
            res = True
        else:
            E5MessageBox.critical(self.ui,
                self.trUtf8("Save project file"),
                self.trUtf8("<p>The project file <b>{0}</b> could not be written.</p>")\
                    .format(fn))
            res = False
        
        if res:
            self.pfile = os.path.abspath(fn)
            self.ppath = os.path.abspath(os.path.dirname(fn))
            self.__makePpathRe()
            self.name = os.path.splitext(os.path.basename(fn))[0]
            self.setDirty(False)
            
            # insert filename into list of recently opened projects
            self.__syncRecent()
        
        return res
        
    def __readUserProperties(self):
        """
        Private method to read in the user specific project file (.e4q)
        """
        if self.pfile is None:
            return
        
        fn, ext = os.path.splitext(os.path.basename(self.pfile))
        fn = os.path.join(self.getProjectManagementDir(), '{0}.e4q'.format(fn))
        if os.path.exists(fn):
            f = QFile(fn)
            if f.open(QIODevice.ReadOnly):
                reader = UserProjectReader(f, self)
                reader.readXML()
                f.close()
            else:
                E5MessageBox.critical(self.ui,
                    self.trUtf8("Read user project properties"),
                    self.trUtf8("<p>The user specific project properties file <b>{0}</b>"
                        " could not be read.</p>").format(fn))
        
    def __writeUserProperties(self):
        """
        Private method to write the project data to an XML file.
        """
        if self.pfile is None:
            return
        
        fn, ext = os.path.splitext(os.path.basename(self.pfile))
        fn = os.path.join(self.getProjectManagementDir(), '{0}.e4q'.format(fn))
        
        f = QFile(fn)
        if f.open(QIODevice.WriteOnly):
            UserProjectWriter(f, os.path.splitext(os.path.basename(fn))[0]).writeXML()
            f.close()
        else:
            E5MessageBox.critical(self.ui,
                self.trUtf8("Save user project properties"),
                self.trUtf8("<p>The user specific project properties file <b>{0}</b>"
                    " could not be written.</p>").format(fn))
        
    def __readSession(self, quiet=False, indicator=""):
        """
        Private method to read in the project session file (.e4s)
        
        @param quiet flag indicating quiet operations.
                If this flag is true, no errors are reported.
        @keyparam indicator indicator string (string)
        """
        if self.pfile is None:
            if not quiet:
                E5MessageBox.critical(self.ui,
                    self.trUtf8("Read project session"),
                    self.trUtf8("Please save the project first."))
            return
            
        fn, ext = os.path.splitext(os.path.basename(self.pfile))
        fn = os.path.join(self.getProjectManagementDir(),
                          '{0}{1}.e4s'.format(fn, indicator))
        
        f = QFile(fn)
        if f.open(QIODevice.ReadOnly):
            reader = SessionReader(f, False)
            reader.readXML(quiet=quiet)
            f.close()
        else:
            if not quiet:
                E5MessageBox.critical(self.ui,
                    self.trUtf8("Read project session"),
                    self.trUtf8("<p>The project session file <b>{0}</b> could not be"
                        " read.</p>").format(fn))
        
    def __writeSession(self, quiet=False, indicator=""):
        """
        Private method to write the session data to an XML file (.e4s).
        
        @param quiet flag indicating quiet operations.
                If this flag is true, no errors are reported.
        @keyparam indicator indicator string (string)
        """
        if self.pfile is None:
            if not quiet:
                E5MessageBox.critical(self.ui,
                    self.trUtf8("Save project session"),
                    self.trUtf8("Please save the project first."))
            return
        
        fn, ext = os.path.splitext(os.path.basename(self.pfile))
        fn = os.path.join(self.getProjectManagementDir(),
                          '{0}{1}.e4s'.format(fn, indicator))
        
        f = QFile(fn)
        if f.open(QIODevice.WriteOnly):
            SessionWriter(f, os.path.splitext(os.path.basename(fn))[0]).writeXML()
            f.close()
        else:
            if not quiet:
                E5MessageBox.critical(self.ui,
                    self.trUtf8("Save project session"),
                    self.trUtf8("<p>The project session file <b>{0}</b> could not be"
                        " written.</p>").format(fn))
        
    def __deleteSession(self):
        """
        Private method to delete the session file.
        """
        if self.pfile is None:
            E5MessageBox.critical(self.ui,
                self.trUtf8("Delete project session"),
                self.trUtf8("Please save the project first."))
            return
            
        fname, ext = os.path.splitext(os.path.basename(self.pfile))
        
        for fn in [os.path.join(self.getProjectManagementDir(), "{0}.e4s".format(fname))]:
            if os.path.exists(fn):
                try:
                    os.remove(fn)
                except OSError:
                    E5MessageBox.critical(self.ui,
                        self.trUtf8("Delete project session"),
                        self.trUtf8("<p>The project session file <b>{0}</b> could not be"
                            " deleted.</p>").format(fn))
        
    def __readTasks(self):
        """
        Private method to read in the project tasks file (.e4t)
        """
        if self.pfile is None:
            E5MessageBox.critical(self.ui,
                self.trUtf8("Read tasks"),
                self.trUtf8("Please save the project first."))
            return
            
        fn, ext = os.path.splitext(os.path.basename(self.pfile))
        fn = os.path.join(self.getProjectManagementDir(), '{0}.e4t'.format(fn))
        if not os.path.exists(fn):
            return
        f = QFile(fn)
        if f.open(QIODevice.ReadOnly):
            reader = TasksReader(f, True)
            reader.readXML()
            f.close()
        else:
            E5MessageBox.critical(self.ui,
                self.trUtf8("Read tasks"),
                self.trUtf8("<p>The tasks file <b>{0}</b> could not be read.</p>")\
                    .format(fn))
        
    def __writeTasks(self):
        """
        Private method to write the tasks data to an XML file (.e4t).
        """
        if self.pfile is None:
            return
            
        fn, ext = os.path.splitext(os.path.basename(self.pfile))
        
        fn = os.path.join(self.getProjectManagementDir(), '{0}.e4t'.format(fn))
        f = QFile(fn)
        ok = f.open(QIODevice.WriteOnly)
        if not ok:
            E5MessageBox.critical(self.ui,
                self.trUtf8("Save tasks"),
                self.trUtf8("<p>The tasks file <b>{0}</b> could not be written.</p>")
                    .format(fn))
            return
        
        TasksWriter(f, True, os.path.splitext(os.path.basename(fn))[0]).writeXML()
        f.close()
        
    def __readDebugProperties(self, quiet=False):
        """
        Private method to read in the project debugger properties file (.e4d)
        
        @param quiet flag indicating quiet operations.
                If this flag is true, no errors are reported.
        """
        if self.pfile is None:
            if not quiet:
                E5MessageBox.critical(self.ui,
                    self.trUtf8("Read debugger properties"),
                    self.trUtf8("Please save the project first."))
            return
            
        fn, ext = os.path.splitext(os.path.basename(self.pfile))
        fn = os.path.join(self.getProjectManagementDir(), '{0}.e4d'.format(fn))
        
        f = QFile(fn)
        if f.open(QIODevice.ReadOnly):
            reader = DebuggerPropertiesReader(f, self)
            reader.readXML(quiet=quiet)
            f.close()
        else:
            if not quiet:
                E5MessageBox.critical(self.ui,
                    self.trUtf8("Read debugger properties"),
                    self.trUtf8("<p>The project debugger properties file <b>{0}</b> could"
                                " not be read.</p>").format(fn))
        
    def __writeDebugProperties(self, quiet=False):
        """
        Private method to write the project debugger properties file (.e4d)
        
        @param quiet flag indicating quiet operations.
                If this flag is true, no errors are reported.
        """
        if self.pfile is None:
            if not quiet:
                E5MessageBox.critical(self.ui,
                    self.trUtf8("Save debugger properties"),
                    self.trUtf8("Please save the project first."))
            return
            
        fn, ext = os.path.splitext(os.path.basename(self.pfile))
        fn = os.path.join(self.getProjectManagementDir(), '{0}.e4d'.format(fn))
        
        f = QFile(fn)
        if f.open(QIODevice.WriteOnly):
            DebuggerPropertiesWriter(f, os.path.splitext(os.path.basename(fn))[0])\
                .writeXML()
            f.close()
        else:
            if not quiet:
                E5MessageBox.critical(self.ui,
                    self.trUtf8("Save debugger properties"),
                    self.trUtf8("<p>The project debugger properties file <b>{0}</b> could"
                                " not be written.</p>")
                        .format(fn))
        
    def __deleteDebugProperties(self):
        """
        Private method to delete the project debugger properties file (.e4d)
        """
        if self.pfile is None:
            E5MessageBox.critical(self.ui,
                self.trUtf8("Delete debugger properties"),
                self.trUtf8("Please save the project first."))
            return
            
        fname, ext = os.path.splitext(os.path.basename(self.pfile))
        
        for fn in [os.path.join(self.getProjectManagementDir(), "{0}.e4d".format(fname))]:
            if os.path.exists(fn):
                try:
                    os.remove(fn)
                except OSError:
                    E5MessageBox.critical(self.ui,
                        self.trUtf8("Delete debugger properties"),
                        self.trUtf8("<p>The project debugger properties file <b>{0}</b>"
                                    " could not be deleted.</p>")
                            .format(fn))
        
    def __initDebugProperties(self):
        """
        Private method to initialize the debug properties.
        """
        self.debugPropertiesLoaded = False
        self.debugProperties = {}
        for key in self.__class__.dbgKeynames:
            self.debugProperties[key] = ""
        self.debugProperties["ENVIRONMENTOVERRIDE"] = False
        self.debugProperties["REMOTEDEBUGGER"] = False
        self.debugProperties["PATHTRANSLATION"] = False
        self.debugProperties["CONSOLEDEBUGGER"] = False
        self.debugProperties["REDIRECT"] = True
        self.debugProperties["NOENCODING"] = False
    
    def isDebugPropertiesLoaded(self):
        """
        Public method to return the status of the debug properties.
        
        @return load status of debug properties (boolean)
        """
        return self.debugPropertiesLoaded
        
    def __showDebugProperties(self):
        """
        Private slot to display the debugger properties dialog.
        """
        dlg = DebuggerPropertiesDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            dlg.storeData()
        
    def getDebugProperty(self, key):
        """
        Public method to retrieve a debugger property.
        
        @param key key of the property (string)
        @return value of the property
        """
        return self.debugProperties[key]
        
    def setDbgInfo(self, argv, wd, env, excReporting, excList, excIgnoreList,
                   autoClearShell, tracePython=None, autoContinue=None):
        """
        Public method to set the debugging information.
        
        @param argv command line arguments to be used (string)
        @param wd working directory (string)
        @param env environment setting (string)
        @param excReporting flag indicating the highlighting of exceptions
        @param excList list of exceptions to be highlighted (list of strings)
        @param excIgnoreList list of exceptions to be ignored (list of strings)
        @param autoClearShell flag indicating, that the interpreter window
            should be cleared (boolean)
        @keyparam tracePython flag to indicate if the Python library should be
            traced as well (boolean)
        @keyparam autoContinue flag indicating, that the debugger should not stop
            at the first executable line (boolean)
        """
        self.dbgCmdline = argv
        self.dbgWd = wd
        self.dbgEnv = env
        self.dbgReportExceptions = excReporting
        self.dbgExcList = excList[:]                # keep a copy of the list
        self.dbgExcIgnoreList = excIgnoreList[:]    # keep a copy of the list
        self.dbgAutoClearShell = autoClearShell
        if tracePython is not None:
            self.dbgTracePython = tracePython
        if autoContinue is not None:
            self.dbgAutoContinue = autoContinue
    
    def getTranslationPattern(self):
        """
        Public method to get the translation pattern.
        
        @return translation pattern (string)
        """
        if self.pdata["TRANSLATIONPATTERN"]:
            return self.pdata["TRANSLATIONPATTERN"][0]
        else:
            return ""
    
    def addLanguage(self):
        """
        Public slot used to add a language to the project.
        """
        if len(self.pdata["TRANSLATIONPATTERN"]) == 0 or \
           self.pdata["TRANSLATIONPATTERN"][0] == '':
            E5MessageBox.critical(self.ui,
                self.trUtf8("Add Language"),
                self.trUtf8("You have to specify a translation pattern first."))
            return
        
        dlg = AddLanguageDialog(self.parent())
        if dlg.exec_() == QDialog.Accepted:
            lang = dlg.getSelectedLanguage()
            if self.pdata["PROJECTTYPE"][0] in \
                    ["Qt4", "Qt4C", "E4Plugin", "PySide", "PySideC"]:
                langFile = self.pdata["TRANSLATIONPATTERN"][0].replace("%language%", lang)
                self.appendFile(langFile)
            self.projectLanguageAddedByCode.emit(lang)
        
    def __binaryTranslationFile(self, langFile):
        """
        Private method to calculate the filename of the binary translations file
        given the name of the raw translations file.
        
        @param langFile name of the raw translations file (string)
        @return name of the binary translations file (string)
        """
        qmFile = ""
        try:
            if self.__binaryTranslationsCallbacks[self.pdata["PROJECTTYPE"][0]] \
               is not None:
                qmFile = self.__binaryTranslationsCallbacks[
                    self.pdata["PROJECTTYPE"][0]](langFile)
        except KeyError:
                qmFile = langFile.replace('.ts', '.qm')
        if qmFile == langFile:
            qmFile = ""
        return qmFile
        
    def checkLanguageFiles(self):
        """
        Public slot to check the language files after a release process.
        """
        tbPath = self.pdata["TRANSLATIONSBINPATH"] and \
                 self.pdata["TRANSLATIONSBINPATH"][0] or ""
        for langFile in self.pdata["TRANSLATIONS"][:]:
            qmFile = self.__binaryTranslationFile(langFile)
            if qmFile:
                if qmFile not in self.pdata["TRANSLATIONS"] and \
                   os.path.exists(os.path.join(self.ppath, qmFile)):
                    self.appendFile(qmFile)
                if tbPath:
                    qmFile = os.path.join(tbPath, os.path.basename(qmFile))
                    if qmFile not in self.pdata["TRANSLATIONS"] and \
                       os.path.exists(os.path.join(self.ppath, qmFile)):
                        self.appendFile(qmFile)
        
    def removeLanguageFile(self, langFile):
        """
        Public slot to remove a translation from the project.
        
        The translation file is not deleted from the project directory.
        
        @param langFile the translation file to be removed (string)
        """
        langFile = self.getRelativePath(langFile)
        qmFile = self.__binaryTranslationFile(langFile)
        self.pdata["TRANSLATIONS"].remove(langFile)
        self.__model.removeItem(langFile)
        if qmFile:
            try:
                if self.pdata["TRANSLATIONSBINPATH"]:
                    qmFile = self.getRelativePath(
                        os.path.join(self.pdata["TRANSLATIONSBINPATH"][0],
                        os.path.basename(qmFile)))
                self.pdata["TRANSLATIONS"].remove(qmFile)
                self.__model.removeItem(qmFile)
            except ValueError:
                pass
        self.setDirty(True)
        
    def deleteLanguageFile(self, langFile):
        """
        Public slot to delete a translation from the project directory.
        
        @param langFile the translation file to be removed (string)
        """
        langFile = self.getRelativePath(langFile)
        qmFile = self.__binaryTranslationFile(langFile)
        
        try:
            fn = os.path.join(self.ppath, langFile)
            if os.path.exists(fn):
                os.remove(fn)
        except IOError:
            E5MessageBox.critical(self.ui,
                self.trUtf8("Delete translation"),
                self.trUtf8("<p>The selected translation file <b>{0}</b> could not be"
                    " deleted.</p>").format(langFile))
            return
        
        self.removeLanguageFile(langFile)
        
        # now get rid of the .qm file
        if qmFile:
            try:
                if self.pdata["TRANSLATIONSBINPATH"]:
                    qmFile = self.getRelativePath(
                        os.path.join(self.pdata["TRANSLATIONSBINPATH"][0],
                        os.path.basename(qmFile)))
                fn = os.path.join(self.ppath, qmFile)
                if os.path.exists(fn):
                    os.remove(fn)
            except IOError:
                E5MessageBox.critical(self.ui,
                    self.trUtf8("Delete translation"),
                    self.trUtf8("<p>The selected translation file <b>{0}</b> could not be"
                        " deleted.</p>").format(qmFile))
                return
        
    def appendFile(self, fn, isSourceFile=False, updateModel=True):
        """
        Public method to append a file to the project.
        
        @param fn filename to be added to the project (string)
        @param isSourceFile flag indicating that this is a source file
                even if it doesn't have the source extension (boolean)
        @param updateModel flag indicating an update of the model is requested (boolean)
        """
        dirty = False
        
        if os.path.isabs(fn):
            # make it relative to the project root, if it starts with that path
            newfn = self.getRelativePath(fn)
        else:
            # assume relative paths are relative to the project root
            newfn = fn
        newdir = os.path.dirname(newfn)
        
        if isSourceFile:
            filetype = "SOURCES"
        else:
            filetype = "OTHERS"
            bfn = os.path.basename(newfn)
            if fnmatch.fnmatch(bfn, '*.ts') or fnmatch.fnmatch(bfn, '*.qm'):
                filetype = "TRANSLATIONS"
            else:
                for pattern in reversed(sorted(self.pdata["FILETYPES"].keys())):
                    if fnmatch.fnmatch(bfn, pattern):
                        filetype = self.pdata["FILETYPES"][pattern]
                        break
        
        if filetype == "__IGNORE__":
            return
        
        if filetype in ["SOURCES", "FORMS", "INTERFACES", "RESOURCES"]:
            if filetype == "SOURCES":
                if newfn not in self.pdata["SOURCES"]:
                    self.pdata["SOURCES"].append(newfn)
                    self.projectSourceAdded.emit(newfn)
                    updateModel and self.__model.addNewItem("SOURCES", newfn)
                    dirty = True
                else:
                    updateModel and self.repopulateItem(newfn)
            elif filetype == "FORMS":
                if newfn not in self.pdata["FORMS"]:
                    self.pdata["FORMS"].append(newfn)
                    self.projectFormAdded.emit(newfn)
                    updateModel and self.__model.addNewItem("FORMS", newfn)
                    dirty = True
                else:
                    updateModel and self.repopulateItem(newfn)
            elif filetype == "INTERFACES":
                if newfn not in self.pdata["INTERFACES"]:
                    self.pdata["INTERFACES"].append(newfn)
                    self.projectInterfaceAdded.emit(newfn)
                    updateModel and self.__model.addNewItem("INTERFACES", newfn)
                    dirty = True
                else:
                    updateModel and self.repopulateItem(newfn)
            elif filetype == "RESOURCES":
                if newfn not in self.pdata["RESOURCES"]:
                    self.pdata["RESOURCES"].append(newfn)
                    self.projectResourceAdded.emit(newfn)
                    updateModel and self.__model.addNewItem("RESOURCES", newfn)
                    dirty = True
                else:
                    updateModel and self.repopulateItem(newfn)
            if newdir not in self.subdirs:
                self.subdirs.append(newdir)
        elif filetype == "TRANSLATIONS":
            if newfn not in self.pdata["TRANSLATIONS"]:
                self.pdata["TRANSLATIONS"].append(newfn)
                updateModel and self.__model.addNewItem("TRANSLATIONS", newfn)
                self.projectLanguageAdded.emit(newfn)
                dirty = True
            else:
                updateModel and self.repopulateItem(newfn)
        else:   # filetype == "OTHERS"
            if newfn not in self.pdata["OTHERS"]:
                self.pdata['OTHERS'].append(newfn)
                self.othersAdded(newfn, updateModel)
                dirty = True
            else:
                updateModel and self.repopulateItem(newfn)
            if newdir not in self.otherssubdirs:
                self.otherssubdirs.append(newdir)
        
        if dirty:
            self.setDirty(True)
        
    def addFiles(self, filter=None, startdir=None):
        """
        Public slot used to add files to the project.
        
        @param filter filter to be used by the add file dialog
            (string out of source, form, resource, interface, others)
        @param startdir start directory for the selection dialog
        """
        if startdir is None:
            startdir = self.ppath
        dlg = AddFileDialog(self, self.parent(), filter, startdir=startdir)
        if dlg.exec_() == QDialog.Accepted:
            fnames, target, isSource = dlg.getData()
            if target != '':
                for fn in fnames:
                    targetfile = os.path.join(target, os.path.basename(fn))
                    if not Utilities.samepath(os.path.dirname(fn), target):
                        try:
                            if not os.path.isdir(target):
                                os.makedirs(target)
                                
                            if os.path.exists(targetfile):
                                res = E5MessageBox.yesNo(self.ui,
                                    self.trUtf8("Add file"),
                                    self.trUtf8("<p>The file <b>{0}</b> already"
                                        " exists.</p><p>Overwrite it?</p>")
                                        .format(targetfile),
                                    icon=E5MessageBox.Warning)
                                if not res:
                                    return  # don't overwrite
                                    
                            shutil.copy(fn, target)
                        except IOError as why:
                            E5MessageBox.critical(self.ui,
                                self.trUtf8("Add file"),
                                self.trUtf8("<p>The selected file <b>{0}</b> could not be"
                                    " added to <b>{1}</b>.</p><p>Reason: {2}</p>")
                                    .format(fn, target, str(why)))
                            return
                            
                    self.appendFile(targetfile, isSource or filter == 'source')
            else:
                E5MessageBox.critical(self.ui,
                    self.trUtf8("Add file"),
                    self.trUtf8("The target directory must not be empty."))
        
    def __addSingleDirectory(self, filetype, source, target, quiet=False):
        """
        Private method used to add all files of a single directory to the project.
        
        @param filetype type of files to add (string)
        @param source source directory (string)
        @param target target directory (string)
        @param quiet flag indicating quiet operations (boolean)
        """
        # get all relevant filename patterns
        patterns = []
        ignorePatterns = []
        for pattern, patterntype in list(self.pdata["FILETYPES"].items()):
            if patterntype == filetype:
                patterns.append(pattern)
            elif patterntype == "__IGNORE__":
                ignorePatterns.append(pattern)
        
        files = []
        for pattern in patterns:
            sstring = "{0}{1}{2}".format(source, os.sep, pattern)
            files.extend(glob.glob(sstring))
        
        if len(files) == 0:
            if not quiet:
                E5MessageBox.information(self.ui,
                    self.trUtf8("Add directory"),
                    self.trUtf8("<p>The source directory doesn't contain"
                        " any files belonging to the selected category.</p>"))
            return
        
        if not Utilities.samepath(target, source) and not os.path.isdir(target):
            try:
                os.makedirs(target)
            except IOError as why:
                E5MessageBox.critical(self.ui,
                    self.trUtf8("Add directory"),
                    self.trUtf8("<p>The target directory <b>{0}</b> could not be"
                        " created.</p><p>Reason: {1}</p>")
                        .format(target, str(why)))
                return
        
        for file in files:
            for pattern in ignorePatterns:
                if fnmatch.fnmatch(file, pattern):
                    continue
            
            targetfile = os.path.join(target, os.path.basename(file))
            if not Utilities.samepath(target, source):
                try:
                    if os.path.exists(targetfile):
                        res = E5MessageBox.yesNo(self.ui,
                            self.trUtf8("Add directory"),
                            self.trUtf8("<p>The file <b>{0}</b> already exists.</p>"
                                        "<p>Overwrite it?</p>")
                                .format(targetfile),
                            icon=E5MessageBox.Warning)
                        if not res:
                            continue  # don't overwrite, carry on with next file
                            
                    shutil.copy(file, target)
                except EnvironmentError:
                    continue
            self.appendFile(targetfile)
        
    def __addRecursiveDirectory(self, filetype, source, target):
        """
        Private method used to add all files of a directory tree.
        
        The tree is rooted at source to another one rooted at target. This
        method decents down to the lowest subdirectory.
        
        @param filetype type of files to add (string)
        @param source source directory (string)
        @param target target directory (string)
        """
        # first perform the addition of source
        self.__addSingleDirectory(filetype, source, target, True)
        
        # now recurse into subdirectories
        for name in os.listdir(source):
            ns = os.path.join(source, name)
            if os.path.isdir(ns):
                nt = os.path.join(target, name)
                self.__addRecursiveDirectory(filetype, ns, nt)
        
    def addDirectory(self, filter=None, startdir=None):
        """
        Public method used to add all files of a directory to the project.
        
        @param filter filter to be used by the add directory dialog
            (string out of source, form, resource, interface, others)
        @param startdir start directory for the selection dialog (string)
        """
        if startdir is None:
            startdir = self.ppath
        dlg = AddDirectoryDialog(self, filter, self.parent(), startdir=startdir)
        if dlg.exec_() == QDialog.Accepted:
            filetype, source, target, recursive = dlg.getData()
            if target == '':
                E5MessageBox.critical(self.ui,
                    self.trUtf8("Add directory"),
                    self.trUtf8("The target directory must not be empty."))
                return
            
            if filetype == 'OTHERS':
                self.addToOthers(source)
                return
            
            if source == '':
                E5MessageBox.critical(self.ui,
                    self.trUtf8("Add directory"),
                    self.trUtf8("The source directory must not be empty."))
                return
            
            if recursive:
                self.__addRecursiveDirectory(filetype, source, target)
            else:
                self.__addSingleDirectory(filetype, source, target)
        
    def addToOthers(self, fn):
        """
        Public method to add a file/directory to the OTHERS project data.
        
        @param fn file name or directory name to add (string)
        """
        if fn:
            # if it is below the project directory, make it relative to that
            fn = self.getRelativePath(fn)
            
            # if it ends with the directory separator character, remove it
            if fn.endswith(os.sep):
                fn = fn[:-1]
            
            if fn not in self.pdata["OTHERS"]:
                self.pdata['OTHERS'].append(fn)
                self.othersAdded(fn)
                self.setDirty(True)
            
            if os.path.isdir(fn) and fn not in self.otherssubdirs:
                self.otherssubdirs.append(fn)
        
    def addSourceFiles(self):
        """
        Public slot to add source files to the current project.
        """
        self.addFiles('source')
        
    def addUiFiles(self):
        """
        Public slot to add forms to the current project.
        """
        self.addFiles('form')
        
    def addIdlFiles(self):
        """
        Public slot to add IDL interfaces to the current project.
        """
        self.addFiles('interface')
        
    def addResourceFiles(self):
        """
        Public slot to add Qt resources to the current project.
        """
        self.addFiles('resource')
        
    def addOthersFiles(self):
        """
        Public slot to add files to the OTHERS project data.
        """
        self.addFiles('others')
        
    def addSourceDir(self):
        """
        Public slot to add all source files of a directory to the current project.
        """
        self.addDirectory('source')
        
    def addUiDir(self):
        """
        Public slot to add all forms of a directory to the current project.
        """
        self.addDirectory('form')
        
    def addIdlDir(self):
        """
        Public slot to add all IDL interfaces of a directory to the current project.
        """
        self.addDirectory('interface')
        
    def addResourceDir(self):
        """
        Public slot to add all Qt resource files of a directory to the current project.
        """
        self.addDirectory('resource')
        
    def addOthersDir(self):
        """
        Public slot to add a directory to the OTHERS project data.
        """
        self.addDirectory('others')
        
    def renameMainScript(self, oldfn, newfn):
        """
        Public method to rename the main script.
        
        @param oldfn old filename (string)
        @param newfn new filename of the main script (string)
        """
        if self.pdata["MAINSCRIPT"]:
            ofn = self.getRelativePath(oldfn)
            if ofn != self.pdata["MAINSCRIPT"][0]:
                return
            
            fn = self.getRelativePath(newfn)
            self.pdata["MAINSCRIPT"] = [fn]
            self.setDirty(True)
        
    def renameFile(self, oldfn, newfn=None):
        """
        Public slot to rename a file of the project.
        
        @param oldfn old filename of the file (string)
        @param newfn new filename of the file (string)
        @return flag indicating success
        """
        fn = self.getRelativePath(oldfn)
        isSourceFile = fn in self.pdata["SOURCES"]
        
        if newfn is None:
            newfn = E5FileDialog.getSaveFileName(
                None,
                self.trUtf8("Rename file"),
                os.path.dirname(oldfn),
                "",
                E5FileDialog.Options(E5FileDialog.DontConfirmOverwrite))
            if not newfn:
                return False
            newfn = Utilities.toNativeSeparators(newfn)
        
        if os.path.exists(newfn):
            res = E5MessageBox.yesNo(self.ui,
                self.trUtf8("Rename File"),
                self.trUtf8("""<p>The file <b>{0}</b> already exists."""
                            """ Overwrite it?</p>""")
                    .format(newfn),
                icon=E5MessageBox.Warning)
            if not res:
                return False
        
        try:
            os.rename(oldfn, newfn)
        except OSError as msg:
            E5MessageBox.critical(self.ui,
                self.trUtf8("Rename File"),
                self.trUtf8("""<p>The file <b>{0}</b> could not be renamed.<br />"""
                    """Reason: {1}</p>""").format(oldfn, str(msg)))
            return False

        if fn in self.pdata["SOURCES"] or \
           fn in self.pdata["FORMS"] or \
           fn in self.pdata["TRANSLATIONS"] or \
           fn in self.pdata["INTERFACES"] or \
           fn in self.pdata["RESOURCES"] or \
           fn in self.pdata["OTHERS"]:
            self.renameFileInPdata(oldfn, newfn, isSourceFile)
        
        return True
        
    def renameFileInPdata(self, oldname, newname, isSourceFile=False):
        """
        Public method to rename a file in the pdata structure.
        
        @param oldname old filename (string)
        @param newname new filename (string)
        @param isSourceFile flag indicating that this is a source file
                even if it doesn't have the source extension (boolean)
        """
        fn = self.getRelativePath(oldname)
        if os.path.dirname(oldname) == os.path.dirname(newname):
            self.removeFile(oldname, False)
            self.appendFile(newname, isSourceFile, False)
            self.__model.renameItem(fn, newname)
        else:
            self.removeFile(oldname)
            self.appendFile(newname, isSourceFile)
        self.projectFileRenamed.emit(oldname, newname)
        
        self.renameMainScript(fn, newname)
        
    def getFiles(self, start):
        """
        Public method to get all files starting with a common prefix.
        
        @param start prefix (string)
        """
        filelist = []
        start = self.getRelativePath(start)
        for key in ["SOURCES", "FORMS", "INTERFACES", "RESOURCES", "OTHERS"]:
            for entry in self.pdata[key][:]:
                if entry.startswith(start):
                    filelist.append(os.path.join(self.ppath, entry))
        return filelist
        
    def copyDirectory(self, olddn, newdn):
        """
        Public slot to copy a directory.
        
        @param olddn original directory name (string)
        @param newdn new directory name (string)
        """
        olddn = self.getRelativePath(olddn)
        newdn = self.getRelativePath(newdn)
        for key in ["SOURCES", "FORMS", "INTERFACES", "RESOURCES", "OTHERS"]:
            for entry in self.pdata[key][:]:
                if entry.startswith(olddn):
                    entry = entry.replace(olddn, newdn)
                    self.appendFile(os.path.join(self.ppath, entry), key == "SOURCES")
        self.setDirty(True)
        
    def moveDirectory(self, olddn, newdn):
        """
        Public slot to move a directory.
        
        @param olddn old directory name (string)
        @param newdn new directory name (string)
        """
        olddn = self.getRelativePath(olddn)
        newdn = self.getRelativePath(newdn)
        typeStrings = []
        for key in ["SOURCES", "FORMS", "INTERFACES", "RESOURCES", "OTHERS"]:
            for entry in self.pdata[key][:]:
                if entry.startswith(olddn):
                    if key not in typeStrings:
                        typeStrings.append(key)
                    self.pdata[key].remove(entry)
                    entry = entry.replace(olddn, newdn)
                    self.pdata[key].append(entry)
            if key == "OTHERS":
                if newdn not in self.otherssubdirs:
                    self.otherssubdirs.append(newdn)
            else:
                if newdn not in self.subdirs:
                    self.subdirs.append(newdn)
        self.setDirty(True)
        typeString = typeStrings[0]
        del typeStrings[0]
        self.__model.removeItem(olddn)
        self.__model.addNewItem(typeString, newdn, typeStrings)
        self.directoryRemoved.emit(olddn)
        
    def removeFile(self, fn, updateModel=True):
        """
        Public slot to remove a file from the project.
        
        The file is not deleted from the project directory.
        
        @param fn filename to be removed from the project
        @param updateModel flag indicating an update of the model is requested (boolean)
        """
        fn = self.getRelativePath(fn)
        dirty = True
        if fn in self.pdata["SOURCES"]:
            self.pdata["SOURCES"].remove(fn)
            self.projectSourceRemoved.emit(fn)
        elif fn in self.pdata["FORMS"]:
            self.pdata["FORMS"].remove(fn)
            self.projectFormRemoved.emit(fn)
        elif fn in self.pdata["INTERFACES"]:
            self.pdata["INTERFACES"].remove(fn)
            self.projectInterfaceRemoved.emit(fn)
        elif fn in self.pdata["RESOURCES"]:
            self.pdata["RESOURCES"].remove(fn)
            self.projectResourceRemoved.emit(fn)
        elif fn in self.pdata["OTHERS"]:
            self.pdata["OTHERS"].remove(fn)
            self.projectOthersRemoved.emit(fn)
        elif fn in self.pdata["TRANSLATIONS"]:
            self.pdata["TRANSLATIONS"].remove(fn)
            self.projectLanguageRemoved.emit(fn)
        else:
            dirty = False
        updateModel and self.__model.removeItem(fn)
        if dirty:
            self.setDirty(True)
        
    def removeDirectory(self, dn):
        """
        Public slot to remove a directory from the project.
        
        The directory is not deleted from the project directory.
        
        @param dn directory name to be removed from the project
        """
        dirty = False
        dn = self.getRelativePath(dn)
        for entry in self.pdata["OTHERS"][:]:
            if entry.startswith(dn):
                self.pdata["OTHERS"].remove(entry)
                dirty = True
        if not dn.endswith(os.sep):
            dn2 = dn + os.sep
        else:
            dn2 = dn
        for key in ["SOURCES", "FORMS", "INTERFACES", "RESOURCES", ]:
            for entry in self.pdata[key][:]:
                if entry.startswith(dn2):
                    self.pdata[key].remove(entry)
                    dirty = True
        self.__model.removeItem(dn)
        if dirty:
            self.setDirty(True)
        self.directoryRemoved.emit(dn)
        
    def deleteFile(self, fn):
        """
        Public slot to delete a file from the project directory.
        
        @param fn filename to be deleted from the project
        @return flag indicating success (boolean)
        """
        try:
            os.remove(os.path.join(self.ppath, fn))
            path, ext = os.path.splitext(fn)
            if ext == '.ui':
                fn2 = os.path.join(self.ppath, '{0}.h'.format(fn))
                if os.path.isfile(fn2):
                    os.remove(fn2)
            head, tail = os.path.split(path)
            for ext in ['.pyc', '.pyo']:
                fn2 = os.path.join(self.ppath, path + ext)
                if os.path.isfile(fn2):
                    os.remove(fn2)
                pat = os.path.join(
                    self.ppath, head, "__pycache__", "{0}.*{1}".format(tail, ext))
                for f in glob.glob(pat):
                    os.remove(f)
        except EnvironmentError:
            E5MessageBox.critical(self.ui,
                self.trUtf8("Delete file"),
                self.trUtf8("<p>The selected file <b>{0}</b> could not be deleted.</p>")
                    .format(fn))
            return False
        
        self.removeFile(fn)
        if ext == '.ui':
            self.removeFile(fn + '.h')
        return True
        
    def deleteDirectory(self, dn):
        """
        Public slot to delete a directory from the project directory.
        
        @param dn directory name to be removed from the project
        @return flag indicating success (boolean)
        """
        if not os.path.isabs(dn):
            dn = os.path.join(self.ppath, dn)
        try:
            shutil.rmtree(dn, True)
        except EnvironmentError:
            E5MessageBox.critical(self.ui,
                self.trUtf8("Delete directory"),
                self.trUtf8("<p>The selected directory <b>{0}</b> could not be"
                    " deleted.</p>").format(dn))
            return False
        
        self.removeDirectory(dn)
        return True
    
    def hasEntry(self, fn):
        """
        Public method to check the project for a file.
        
        @param fn filename to be checked (string)
        @return flag indicating, if the project contains the file (boolean)
        """
        fn = self.getRelativePath(fn)
        if fn in self.pdata["SOURCES"] or \
           fn in self.pdata["FORMS"] or \
           fn in self.pdata["INTERFACES"] or \
           fn in self.pdata["RESOURCES"] or \
           fn in self.pdata["OTHERS"]:
            return True
        else:
            return False
        
    def createNewProject(self):
        """
        Public slot to built a new project.
        
        This method displays the new project dialog and initializes
        the project object with the data entered.
        """
        if not self.checkDirty():
            return
            
        dlg = PropertiesDialog(self, True)
        if dlg.exec_() == QDialog.Accepted:
            self.closeProject()
            dlg.storeData()
            self.__makePpathRe()
            self.pdata["VCS"] = ['None']
            self.opened = True
            if not self.pdata["FILETYPES"]:
                self.initFileTypes()
            self.setDirty(True)
            self.closeAct.setEnabled(True)
            self.saveasAct.setEnabled(True)
            self.actGrp2.setEnabled(True)
            self.propsAct.setEnabled(True)
            self.userPropsAct.setEnabled(True)
            self.filetypesAct.setEnabled(True)
            self.lexersAct.setEnabled(True)
            self.sessActGrp.setEnabled(False)
            self.dbgActGrp.setEnabled(True)
            self.menuDebuggerAct.setEnabled(True)
            self.menuSessionAct.setEnabled(False)
            self.menuCheckAct.setEnabled(True)
            self.menuShowAct.setEnabled(True)
            self.menuDiagramAct.setEnabled(True)
            self.menuApidocAct.setEnabled(True)
            self.menuPackagersAct.setEnabled(True)
            self.pluginGrp.setEnabled(self.pdata["PROJECTTYPE"][0] == "E4Plugin")
            self.addLanguageAct.setEnabled(
                len(self.pdata["TRANSLATIONPATTERN"]) > 0 and \
                self.pdata["TRANSLATIONPATTERN"][0] != '')
            
            self.projectAboutToBeCreated.emit()
            
            hash = str(QCryptographicHash.hash(
                QByteArray(self.ppath), QCryptographicHash.Sha1).toHex(),
                encoding="utf-8")
            self.pdata["HASH"] = [hash]
            
            # create the project directory if it doesn't exist already
            if not os.path.isdir(self.ppath):
                try:
                    os.makedirs(self.ppath)
                except EnvironmentError:
                    E5MessageBox.critical(self.ui,
                        self.trUtf8("Create project directory"),
                        self.trUtf8("<p>The project directory <b>{0}</b> could not"
                            " be created.</p>")
                            .format(self.ppath))
                    self.vcs = self.initVCS()
                    return
                # create an empty __init__.py file to make it a Python package
                # (only for Python and Python3)
                if self.pdata["PROGLANGUAGE"][0] in ["Python", "Python2", "Python3"]:
                    fn = os.path.join(self.ppath, "__init__.py")
                    f = open(fn, "w", encoding="utf-8")
                    f.close()
                    self.appendFile(fn, True)
                # create an empty main script file, if a name was given
                if len(self.pdata["MAINSCRIPT"]) and self.pdata["MAINSCRIPT"][0]:
                    if not os.path.isabs(self.pdata["MAINSCRIPT"][0]):
                        ms = os.path.join(self.ppath, self.pdata["MAINSCRIPT"][0])
                    else:
                        ms = self.pdata["MAINSCRIPT"][0]
                    f = open(ms, "w")
                    f.close()
                    self.appendFile(ms, True)
                tpd = os.path.join(self.ppath, self.translationsRoot)
                if not self.translationsRoot.endswith(os.sep):
                    tpd = os.path.dirname(tpd)
                if not os.path.isdir(tpd):
                    os.makedirs(tpd)
                if self.pdata["TRANSLATIONSBINPATH"]:
                    tpd = os.path.join(self.ppath, self.pdata["TRANSLATIONSBINPATH"][0])
                    if not os.path.isdir(tpd):
                        os.makedirs(tpd)
                
                # create management directory if not present
                mgmtDir = self.getProjectManagementDir()
                if not os.path.exists(mgmtDir):
                    os.makedirs(mgmtDir)
                
                self.saveProject()
            else:
                # create management directory if not present
                mgmtDir = self.getProjectManagementDir()
                if not os.path.exists(mgmtDir):
                    os.makedirs(mgmtDir)
                
                try:
                    ms = os.path.join(self.ppath, self.pdata["MAINSCRIPT"][0])
                    if not os.path.exists(ms):
                        f = open(ms, "w")
                        f.close()
                    self.appendFile(ms)
                except IndexError:
                    ms = ""
                
                # add existing files to the project
                res = E5MessageBox.yesNo(self.ui,
                    self.trUtf8("New Project"),
                    self.trUtf8("""Add existing files to the project?"""),
                    yesDefault=True)
                if res:
                    self.newProjectAddFiles(ms)
                # create an empty __init__.py file to make it a Python package
                # if none exists (only for Python and Python3)
                if self.pdata["PROGLANGUAGE"][0] in ["Python", "Python2", "Python3"]:
                    fn = os.path.join(self.ppath, "__init__.py")
                    if not os.path.exists(fn):
                        f = open(fn, "w", encoding="utf-8")
                        f.close()
                        self.appendFile(fn, True)
                self.saveProject()
                
                # check, if the existing project directory is already under
                # VCS control
                pluginManager = e5App().getObject("PluginManager")
                for indicator, vcsData in list(
                        pluginManager.getVcsSystemIndicators().items()):
                    if os.path.exists(os.path.join(self.ppath, indicator)):
                        if len(vcsData) > 1:
                            vcsList = []
                            for vcsSystemStr, vcsSystemDisplay in vcsData:
                                vcsList.append(vcsSystemDisplay)
                            res, vcs_ok = QInputDialog.getItem(
                                None,
                                self.trUtf8("New Project"),
                                self.trUtf8("Select Version Control System"),
                                vcsList,
                                0, False)
                            if vcs_ok:
                                for vcsSystemStr, vcsSystemDisplay in vcsData:
                                    if res == vcsSystemDisplay:
                                        vcsSystem = vcsSystemStr
                                        break
                                else:
                                    vcsSystem = "None"
                            else:
                                vcsSystem = "None"
                        else:
                            vcsSystem = vcsData[0][1]
                        self.pdata["VCS"] = [vcsSystem]
                        self.vcs = self.initVCS()
                        self.setDirty(True)
                        if self.vcs is not None:
                            # edit VCS command options
                            vcores = E5MessageBox.yesNo(self.ui,
                                self.trUtf8("New Project"),
                                self.trUtf8("""Would you like to edit the VCS"""
                                    """ command options?"""))
                            if vcores:
                                codlg = vcsCommandOptionsDialog(self.vcs)
                                if codlg.exec_() == QDialog.Accepted:
                                    self.vcs.vcsSetOptions(codlg.getOptions())
                            # add project file to repository
                            if res == 0:
                                apres = E5MessageBox.yesNo(self.ui,
                                    self.trUtf8("New project"),
                                    self.trUtf8("Shall the project file be added"
                                        " to the repository?"),
                                    yesDefault=True)
                                if apres:
                                    self.saveProject()
                                    self.vcs.vcsAdd(self.pfile)
                        else:
                            self.pdata["VCS"] = ['None']
                        self.saveProject()
                        break
            
            # put the project under VCS control
            if self.vcs is None:
                vcsSystemsDict = e5App().getObject("PluginManager")\
                    .getPluginDisplayStrings("version_control")
                vcsSystemsDisplay = [self.trUtf8("None")]
                keys = sorted(vcsSystemsDict.keys())
                for key in keys:
                    vcsSystemsDisplay.append(vcsSystemsDict[key])
                vcsSelected, ok = QInputDialog.getItem(
                    None,
                    self.trUtf8("New Project"),
                    self.trUtf8("Select version control system for the project"),
                    vcsSystemsDisplay,
                    0, False)
                if ok and vcsSelected != self.trUtf8("None"):
                    for vcsSystem, vcsSystemDisplay in list(vcsSystemsDict.items()):
                        if vcsSystemDisplay == vcsSelected:
                            break
                    else:
                        vcsSystem = "None"
                    self.pdata["VCS"] = [vcsSystem]
                else:
                    self.pdata["VCS"] = ['None']
                self.vcs = self.initVCS()
                if self.vcs is not None:
                    vcsdlg = self.vcs.vcsOptionsDialog(self, self.name)
                    if vcsdlg.exec_() == QDialog.Accepted:
                        vcsDataDict = vcsdlg.getData()
                    else:
                        self.pdata["VCS"] = ['None']
                        self.vcs = self.initVCS()
                self.setDirty(True)
                if self.vcs is not None:
                    # edit VCS command options
                    vcores = E5MessageBox.yesNo(self.ui,
                        self.trUtf8("New Project"),
                        self.trUtf8("""Would you like to edit the VCS command"""
                                    """ options?"""))
                    if vcores:
                        codlg = vcsCommandOptionsDialog(self.vcs)
                        if codlg.exec_() == QDialog.Accepted:
                            self.vcs.vcsSetOptions(codlg.getOptions())
                    
                    # create the project in the VCS
                    self.vcs.vcsSetDataFromDict(vcsDataDict)
                    self.saveProject()
                    self.vcs.vcsConvertProject(vcsDataDict, self)
                else:
                    self.newProjectHooks.emit()
                    self.newProject.emit()
            
            else:
                self.newProjectHooks.emit()
                self.newProject.emit()
            

    def newProjectAddFiles(self, mainscript):
        """
        Public method to add files to a new project.
        
        @param mainscript name of the mainscript (string)
        """
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QApplication.processEvents()
        
        # search the project directory for files with known extensions
        filespecs = list(self.pdata["FILETYPES"].keys())
        for filespec in filespecs:
            files = Utilities.direntries(self.ppath, True, filespec)
            for file in files:
                self.appendFile(file)
        
        # special handling for translation files
        if self.translationsRoot:
            tpd = os.path.join(self.ppath, self.translationsRoot)
            if not self.translationsRoot.endswith(os.sep):
                tpd = os.path.dirname(tpd)
        else:
            tpd = self.ppath
        tslist = []
        if self.pdata["TRANSLATIONPATTERN"]:
            pattern = os.path.basename(self.pdata["TRANSLATIONPATTERN"][0])
            if "%language%" in pattern:
                pattern = pattern.replace("%language%", "*")
            else:
                tpd = self.pdata["TRANSLATIONPATTERN"][0].split("%language%")[0]
        else:
            pattern = "*.ts"
        tslist.extend(Utilities.direntries(tpd, True, pattern))
        pattern = self.__binaryTranslationFile(pattern)
        if pattern:
            tslist.extend(Utilities.direntries(tpd, True, pattern))
        if tslist:
            if '_' in os.path.basename(tslist[0]):
                # the first entry determines the mainscript name
                mainscriptname = os.path.splitext(mainscript)[0] or \
                                 os.path.basename(tslist[0]).split('_')[0]
                self.pdata["TRANSLATIONPATTERN"] = \
                    [os.path.join(os.path.dirname(tslist[0]),
                     "{0}_%language%{1}".format(os.path.basename(tslist[0]).split('_')[0],
                        os.path.splitext(tslist[0])[1]))]
            else:
                pattern, ok = QInputDialog.getText(
                    None,
                    self.trUtf8("Translation Pattern"),
                    self.trUtf8("Enter the path pattern for translation files "
                                "(use '%language%' in place of the language code):"),
                    QLineEdit.Normal,
                    tslist[0])
                if pattern:
                    self.pdata["TRANSLATIONPATTERN"] = [pattern]
            if self.pdata["TRANSLATIONPATTERN"]:
                self.pdata["TRANSLATIONPATTERN"][0] = \
                    self.getRelativePath(self.pdata["TRANSLATIONPATTERN"][0])
                pattern = self.pdata["TRANSLATIONPATTERN"][0].replace("%language%", "*")
                for ts in tslist:
                    if fnmatch.fnmatch(ts, pattern):
                        self.pdata["TRANSLATIONS"].append(ts)
                        self.projectLanguageAdded.emit(ts)
            if self.pdata["TRANSLATIONSBINPATH"]:
                tpd = os.path.join(self.ppath,
                                   self.pdata["TRANSLATIONSBINPATH"][0])
                pattern = os.path.splitext(
                    os.path.basename(self.pdata["TRANSLATIONPATTERN"][0]))
                pattern = self.__binaryTranslationFile(pattern)
                qmlist = Utilities.direntries(tpd, True, pattern)
                for qm in qmlist:
                    self.pdata["TRANSLATIONS"].append(qm)
                    self.projectLanguageAdded.emit(qm)
            if len(self.pdata["MAINSCRIPT"]) == 0 or \
               len(self.pdata["MAINSCRIPT"][0]) == 0:
                if self.pdata["PROGLANGUAGE"][0] in ["Python", "Python2", "Python3"]:
                    self.pdata["MAINSCRIPT"] = ['{0}.py'.format(mainscriptname)]
                elif self.pdata["PROGLANGUAGE"][0] == "Ruby":
                    self.pdata["MAINSCRIPT"] = ['{0}.rb'.format(mainscriptname)]
        self.setDirty(True)
        QApplication.restoreOverrideCursor()
    
    def __showProperties(self):
        """
        Private slot to display the properties dialog.
        """
        dlg = PropertiesDialog(self, False)
        if dlg.exec_() == QDialog.Accepted:
            projectType = self.pdata["PROJECTTYPE"][0]
            dlg.storeData()
            self.setDirty(True)
            try:
                ms = os.path.join(self.ppath, self.pdata["MAINSCRIPT"][0])
                if os.path.exists(ms):
                    self.appendFile(ms)
            except IndexError:
                pass
            
            if self.pdata["PROJECTTYPE"][0] != projectType:
                # reinitialize filetype associations
                self.initFileTypes()
            
            if self.translationsRoot:
                tp = os.path.join(self.ppath, self.translationsRoot)
                if not self.translationsRoot.endswith(os.sep):
                    tp = os.path.dirname(tp)
            else:
                tp = self.ppath
            if not os.path.isdir(tp):
                os.makedirs(tp)
            if tp != self.ppath and tp not in self.subdirs:
                self.subdirs.append(tp)
            
            if self.pdata["TRANSLATIONSBINPATH"]:
                tp = os.path.join(self.ppath, self.pdata["TRANSLATIONSBINPATH"][0])
                if not os.path.isdir(tp):
                    os.makedirs(tp)
                if tp != self.ppath and tp not in self.subdirs:
                    self.subdirs.append(tp)
            
            self.pluginGrp.setEnabled(self.pdata["PROJECTTYPE"][0] == "E4Plugin")
            
            self.__model.projectPropertiesChanged()
            self.projectPropertiesChanged.emit()
        
    def __showUserProperties(self):
        """
        Private slot to display the user specific properties dialog.
        """
        vcsSystem = self.pdata["VCS"] and self.pdata["VCS"][0] or None
        vcsSystemOverride = \
            self.pudata["VCSOVERRIDE"] and self.pudata["VCSOVERRIDE"][0] or None
        
        dlg = UserPropertiesDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            dlg.storeData()
            
            if (self.pdata["VCS"] and \
                self.pdata["VCS"][0] != vcsSystem) or \
               (self.pudata["VCSOVERRIDE"] and \
                self.pudata["VCSOVERRIDE"][0] != vcsSystemOverride) or \
               (vcsSystemOverride is not None and \
                len(self.pudata["VCSOVERRIDE"]) == 0):
                # stop the VCS monitor thread and shutdown VCS
                if self.vcs is not None:
                    self.vcs.stopStatusMonitor()
                    self.vcs.vcsStatusMonitorData.disconnect(self.__model.changeVCSStates)
                    self.vcs.vcsStatusMonitorStatus.disconnect(self.__statusMonitorStatus)
                    self.vcs.vcsShutdown()
                    self.vcs = None
                    e5App().getObject("PluginManager").deactivateVcsPlugins()
                # reinit VCS
                self.vcs = self.initVCS()
                # start the VCS monitor thread
                if self.vcs is not None:
                    self.vcs.startStatusMonitor(self)
                    self.vcs.vcsStatusMonitorData.connect(self.__model.changeVCSStates)
                    self.vcs.vcsStatusMonitorStatus.connect(self.__statusMonitorStatus)
                self.reinitVCS.emit()
            
            if self.pudata["VCSSTATUSMONITORINTERVAL"]:
                self.setStatusMonitorInterval(
                    self.pudata["VCSSTATUSMONITORINTERVAL"][0])
            else:
                self.setStatusMonitorInterval(
                    Preferences.getVCS("StatusMonitorInterval"))
        
    def __showFiletypeAssociations(self):
        """
        Public slot to display the filetype association dialog.
        """
        dlg = FiletypeAssociationDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            dlg.transferData()
            self.setDirty(True)
        
    def __showLexerAssociations(self):
        """
        Public slot to display the lexer association dialog.
        """
        dlg = LexerAssociationDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            dlg.transferData()
            self.setDirty(True)
            self.lexerAssociationsChanged.emit()
        
    def getEditorLexerAssoc(self, filename):
        """
        Public method to retrieve a lexer association.
        
        @param filename filename used to determine the associated lexer language (string)
        @return the requested lexer language (string)
        """
        # try user settings first
        for pattern, language in list(self.pdata["LEXERASSOCS"].items()):
            if fnmatch.fnmatch(filename, pattern):
                return language
        
        # try project type specific defaults next
        projectType = self.pdata["PROJECTTYPE"][0]
        try:
            if self.__lexerAssociationCallbacks[projectType] is not None:
                return self.__lexerAssociationCallbacks[projectType](filename)
        except KeyError:
            pass
        
        # return empty string to signal to use the global setting
        return ""
        
    def openProject(self, fn=None, restoreSession=True, reopen=False):
        """
        Public slot to open a project.
        
        @param fn optional filename of the project file to be read
        @param restoreSession flag indicating to restore the project
            session (boolean)
        @keyparam reopen flag indicating a reopening of the project (boolean)
        """
        if not self.checkDirty():
            return
        
        if fn is None:
            fn = E5FileDialog.getOpenFileName(
                self.parent(),
                self.trUtf8("Open project"),
                "",
                self.trUtf8("Project Files (*.e4p)"))
        
        QApplication.processEvents()
        
        if fn:
            if self.closeProject():
                QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
                QApplication.processEvents()
                if self.__readProject(fn):
                    self.opened = True
                    if not self.pdata["FILETYPES"]:
                        self.initFileTypes()
                    else:
                        self.updateFileTypes()
                    
                    QApplication.restoreOverrideCursor()
                    QApplication.processEvents()
                    
                    # create the management directory if not present
                    mgmtDir = self.getProjectManagementDir()
                    if not os.path.exists(mgmtDir):
                        os.mkdir(mgmtDir)
                    
                    # read a user specific project file
                    self.__readUserProperties()
                    
                    QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
                    QApplication.processEvents()
                    
                    self.vcs = self.initVCS()
                    if self.vcs is None:
                        # check, if project is version controlled
                        pluginManager = e5App().getObject("PluginManager")
                        for indicator, vcsData in \
                                list(pluginManager.getVcsSystemIndicators().items()):
                            if os.path.exists(os.path.join(self.ppath, indicator)):
                                if len(vcsData) > 1:
                                    vcsList = []
                                    for vcsSystemStr, vcsSystemDisplay in vcsData:
                                        vcsList.append(vcsSystemDisplay)
                                    QApplication.restoreOverrideCursor()
                                    res, vcs_ok = QInputDialog.getItem(
                                        None,
                                        self.trUtf8("New Project"),
                                        self.trUtf8("Select Version Control System"),
                                        vcsList,
                                        0, False)
                                    QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
                                    QApplication.processEvents()
                                    if vcs_ok:
                                        for vcsSystemStr, vcsSystemDisplay in vcsData:
                                            if res == vcsSystemDisplay:
                                                vcsSystem = vcsSystemStr
                                                break
                                        else:
                                            vcsSystem = "None"
                                    else:
                                        vcsSystem = "None"
                                else:
                                    vcsSystem = vcsData[0][0]
                                self.pdata["VCS"] = [vcsSystem]
                                self.vcs = self.initVCS()
                                self.setDirty(True)
                    if self.vcs is not None and \
                       self.vcs.vcsRegisteredState(self.ppath) != self.vcs.canBeCommitted:
                        self.pdata["VCS"] = ['None']
                        self.vcs = self.initVCS()
                    self.closeAct.setEnabled(True)
                    self.saveasAct.setEnabled(True)
                    self.actGrp2.setEnabled(True)
                    self.propsAct.setEnabled(True)
                    self.userPropsAct.setEnabled(True)
                    self.filetypesAct.setEnabled(True)
                    self.lexersAct.setEnabled(True)
                    self.sessActGrp.setEnabled(True)
                    self.dbgActGrp.setEnabled(True)
                    self.menuDebuggerAct.setEnabled(True)
                    self.menuSessionAct.setEnabled(True)
                    self.menuCheckAct.setEnabled(True)
                    self.menuShowAct.setEnabled(True)
                    self.menuDiagramAct.setEnabled(True)
                    self.menuApidocAct.setEnabled(True)
                    self.menuPackagersAct.setEnabled(True)
                    self.pluginGrp.setEnabled(self.pdata["PROJECTTYPE"][0] == "E4Plugin")
                    self.addLanguageAct.setEnabled(
                        len(self.pdata["TRANSLATIONPATTERN"]) > 0 and \
                        self.pdata["TRANSLATIONPATTERN"][0] != '')
                    
                    self.__model.projectOpened()
                    self.projectOpenedHooks.emit()
                    self.projectOpened.emit()
                    
                    QApplication.restoreOverrideCursor()
                    
                    if Preferences.getProject("SearchNewFiles"):
                        self.__doSearchNewFiles()
                    
                    # read a project tasks file
                    self.__readTasks()
                    self.ui.taskViewer.setProjectOpen(True)
                    
                    if restoreSession:
                        # open the main script
                        if len(self.pdata["MAINSCRIPT"]) == 1:
                            self.sourceFile.emit(
                                os.path.join(self.ppath, self.pdata["MAINSCRIPT"][0]))
                        
                        # open a project session file being quiet about errors
                        if reopen:
                            self.__readSession(quiet=True, indicator="_tmp")
                        elif Preferences.getProject("AutoLoadSession"):
                            self.__readSession(quiet=True)
                    
                    # open a project debugger properties file being quiet about errors
                    if Preferences.getProject("AutoLoadDbgProperties"):
                        self.__readDebugProperties(True)
                    
                    # start the VCS monitor thread
                    if self.vcs is not None:
                        self.vcs.startStatusMonitor(self)
                        self.vcs.vcsStatusMonitorData.connect(
                            self.__model.changeVCSStates)
                        self.vcs.vcsStatusMonitorStatus.connect(
                            self.__statusMonitorStatus)
                else:
                    QApplication.restoreOverrideCursor()
        
    def reopenProject(self):
        """
        Public slot to reopen the current project.
        """
        projectFile = self.pfile
        res = self.closeProject(reopen=True)
        if res:
            self.openProject(projectFile, reopen=True)
        
    def saveProject(self):
        """
        Public slot to save the current project.
        
        @return flag indicating success
        """
        if self.isDirty():
            if len(self.pfile) > 0:
                ok = self.__writeProject()
            else:
                ok = self.saveProjectAs()
        else:
            ok = True
        self.sessActGrp.setEnabled(ok)
        self.menuSessionAct.setEnabled(ok)
        return ok
        
    def saveProjectAs(self):
        """
        Public slot to save the current project to a different file.
        
        @return flag indicating success (boolean)
        """
        defaultFilter = self.trUtf8("Project Files (*.e4p)")
        fn, selectedFilter = E5FileDialog.getSaveFileNameAndFilter(
            self.parent(),
            self.trUtf8("Save project as"),
            self.ppath,
            self.trUtf8("Project Files (*.e4p)"),
            defaultFilter,
            E5FileDialog.Options(E5FileDialog.DontConfirmOverwrite))
        
        if fn:
            ext = QFileInfo(fn).suffix()
            if not ext:
                ex = selectedFilter.split("(*")[1].split(")")[0]
                if ex:
                    fn += ex
            if QFileInfo(fn).exists():
                res = E5MessageBox.yesNo(self.ui,
                    self.trUtf8("Save File"),
                    self.trUtf8("""<p>The file <b>{0}</b> already exists."""
                                """ Overwrite it?</p>""").format(fn),
                    icon=E5MessageBox.Warning)
                if not res:
                    return False
                
            self.name = QFileInfo(fn).baseName()
            ok = self.__writeProject(fn)
            
            if ok:
                # create management directory if not present
                mgmtDir = self.getProjectManagementDir()
                if not os.path.exists(mgmtDir):
                    os.makedirs(mgmtDir)
                
                # now save the tasks
                self.__writeTasks()
            
            self.sessActGrp.setEnabled(ok)
            self.menuSessionAct.setEnabled(ok)
            self.projectClosedHooks.emit()
            self.projectClosed.emit()
            self.projectOpenedHooks.emit()
            self.projectOpened.emit()
            return True
        else:
            return False
    
    def checkDirty(self):
        """
        Public method to check dirty status and open a message window.
        
        @return flag indicating whether this operation was successful (boolean)
        """
        if self.isDirty():
            res = E5MessageBox.okToClearData(self.parent(),
                self.trUtf8("Close Project"),
                self.trUtf8("The current project has unsaved changes."),
                self.saveProject)
            if res:
                self.setDirty(False)
            return res
            
        return True
        
    def __closeAllWindows(self):
        """
        Private method to close all project related windows.
        """
        self.codemetrics        and self.codemetrics.close()
        self.codecoverage       and self.codecoverage.close()
        self.profiledata        and self.profiledata.close()
        self.applicationDiagram and self.applicationDiagram.close()
        
    def closeProject(self, reopen=False, noSave=False):
        """
        Public slot to close the current project.
        
        @keyparam reopen flag indicating a reopening of the project (boolean)
        @keyparam noSave flag indicating to not perform save actions (boolean)
        @return flag indicating success (boolean)
        """
        # save the list of recently opened projects
        self.__saveRecent()
        
        if not self.isOpen():
            return True
        
        if not self.checkDirty():
            return False
        
        # save the user project properties
        if not noSave:
            self.__writeUserProperties()
        
        # save the project session file being quiet about error
        if reopen:
            self.__writeSession(quiet=True, indicator="_tmp")
        elif Preferences.getProject("AutoSaveSession") and not noSave:
            self.__writeSession(quiet=True)
        
        # save the project debugger properties file being quiet about error
        if Preferences.getProject("AutoSaveDbgProperties") and \
           self.isDebugPropertiesLoaded() and \
           not noSave:
            self.__writeDebugProperties(True)
        
        # now save all open modified files of the project
        vm = e5App().getObject("ViewManager")
        success = True
        for fn in vm.getOpenFilenames():
            if self.isProjectFile(fn):
                success &= vm.closeWindow(fn)
        
        if not success:
            return False
        
        # stop the VCS monitor thread
        if self.vcs is not None:
            self.vcs.stopStatusMonitor()
            try:
                self.vcs.vcsStatusMonitorData.disconnect(
                    self.__model.changeVCSStates)
            except TypeError:
                pass
            try:
                self.vcs.vcsStatusMonitorStatus.disconnect(
                    self.__statusMonitorStatus)
            except TypeError:
                pass
        
        # now save the tasks
        if not noSave:
            self.__writeTasks()
        self.ui.taskViewer.clearProjectTasks()
        self.ui.taskViewer.setProjectOpen(False)
        
        # now shutdown the vcs interface
        if self.vcs:
            self.vcs.vcsShutdown()
            self.vcs = None
            e5App().getObject("PluginManager").deactivateVcsPlugins()
        
        # now close all project related windows
        self.__closeAllWindows()
        
        self.__initData()
        self.closeAct.setEnabled(False)
        self.saveasAct.setEnabled(False)
        self.saveAct.setEnabled(False)
        self.actGrp2.setEnabled(False)
        self.propsAct.setEnabled(False)
        self.userPropsAct.setEnabled(False)
        self.filetypesAct.setEnabled(False)
        self.lexersAct.setEnabled(False)
        self.sessActGrp.setEnabled(False)
        self.dbgActGrp.setEnabled(False)
        self.menuDebuggerAct.setEnabled(False)
        self.menuSessionAct.setEnabled(False)
        self.menuCheckAct.setEnabled(False)
        self.menuShowAct.setEnabled(False)
        self.menuDiagramAct.setEnabled(False)
        self.menuApidocAct.setEnabled(False)
        self.menuPackagersAct.setEnabled(False)
        self.pluginGrp.setEnabled(False)
        
        self.__model.projectClosed()
        self.projectClosedHooks.emit()
        self.projectClosed.emit()
        
        return True

    def saveAllScripts(self, reportSyntaxErrors=False):
        """
        Public method to save all scripts belonging to the project.
        
        @keyparam reportSyntaxErrors flag indicating special reporting
            for syntax errors (boolean)
        @return flag indicating success (boolean)
        """
        vm = e5App().getObject("ViewManager")
        success = True
        filesWithSyntaxErrors = 0
        for fn in vm.getOpenFilenames():
            rfn = self.getRelativePath(fn)
            if rfn in self.pdata["SOURCES"] or rfn in self.pdata["OTHERS"]:
                editor = vm.getOpenEditor(fn)
                success &= vm.saveEditorEd(editor)
                if reportSyntaxErrors and editor.hasSyntaxErrors():
                    filesWithSyntaxErrors += 1
        
        if reportSyntaxErrors and filesWithSyntaxErrors > 0:
            E5MessageBox.critical(self.ui,
                self.trUtf8("Syntax errors detected"),
                self.trUtf8("""The project contains %n file(s) with syntax errors.""",
                    "", filesWithSyntaxErrors)
            )
            return False
        else:
            return success
        
    def getMainScript(self, normalized=False):
        """
        Public method to return the main script filename.
        
        @param normalized flag indicating a normalized filename is wanted (boolean)
        @return filename of the projects main script (string)
        """
        if len(self.pdata["MAINSCRIPT"]):
            if normalized:
                return os.path.join(self.ppath, self.pdata["MAINSCRIPT"][0])
            else:
                return self.pdata["MAINSCRIPT"]
        else:
            return None
        
    def getSources(self, normalized=False):
        """
        Public method to return the source script files.
        
        @param normalized flag indicating a normalized filename is wanted (boolean)
        @return list of the projects scripts (list of string)
        """
        if normalized:
            return [os.path.join(self.ppath, fn) for fn in self.pdata["SOURCES"]]
        else:
            return self.pdata["SOURCES"]
        
    def getProjectType(self):
        """
        Public method to get the type of the project.
        
        @return UI type of the project (string)
        """
        return self.pdata["PROJECTTYPE"][0]
        
    def getProjectLanguage(self):
        """
        Public method to get the project's programming language.
        
        @return programming language (string)
        """
        return self.pdata["PROGLANGUAGE"][0]
        
    def isPy3Project(self):
        """
        Public method to check, if this project is a Python3 project.
        
        @return flag indicating a Python3 project (boolean)
        """
        return self.pdata["PROGLANGUAGE"][0] == "Python3"
        
    def isPy2Project(self):
        """
        Public method to check, if this project is a Python2 project.
        
        @return flag indicating a Python2 project (boolean)
        """
        return self.pdata["PROGLANGUAGE"][0] in ["Python", "Python2"]
        
    def isRubyProject(self):
        """
        Public method to check, if this project is a Ruby project.
        
        @return flag indicating a Ruby project (boolean)
        """
        return self.pdata["PROGLANGUAGE"][0] == "Ruby"
        
    def getProjectSpellLanguage(self):
        """
        Public method to get the project's programming language.
        
        @return programming language (string)
        """
        return self.pdata["SPELLLANGUAGE"][0]
        
    def getProjectDictionaries(self):
        """
        Public method to get the names of the project specific dictionaries.
        
        @return tuple of two strings giving the absolute path names of the
            project specific word and exclude list
        """
        pwl = ""
        if len(self.pdata["SPELLWORDS"][0]) > 0:
            pwl = os.path.join(self.ppath, self.pdata["SPELLWORDS"][0])
        
        pel = ""
        if len(self.pdata["SPELLEXCLUDES"][0]) > 0:
            pel = os.path.join(self.ppath, self.pdata["SPELLEXCLUDES"][0])
        
        return (pwl, pel)
        
    def getDefaultSourceExtension(self):
        """
        Public method to get the default extension for the project's
        programming language.
        
        @return default extension (including the dot) (string)
        """
        if self.pdata["PROGLANGUAGE"]:
            lang = self.pdata["PROGLANGUAGE"][0]
            if lang == "":
                lang = "Python3"
            elif lang == "Python":
                lang = "Python2"
            return self.sourceExtensions[lang][0]
        else:
            return ""
        
    def getProjectPath(self):
        """
        Public method to get the project path.
        
        @return project path (string)
        """
        return self.ppath
        
    def startswithProjectPath(self, path):
        """
        Public method to check, if a path starts with the project path.
        
        @param path path to be checked (string)
        """
        if self.ppath and path == self.ppath:
            return True
        elif self.ppathRe:
            return self.ppathRe.match(path) is not None
        else:
            return False
        
    def getProjectFile(self):
        """
        Public method to get the path of the project file.
        
        @return path of the project file (string)
        """
        return self.pfile
        
    def getProjectManagementDir(self):
        """
        Public method to get the path of the management directory.
        
        @return path of the management directory (string)
        """
        if Utilities.isWindowsPlatform():
            return os.path.join(self.ppath, "_eric5project")
        else:
            return os.path.join(self.ppath, ".eric5project")
        
    def getHash(self):
        """
        Public method to get the project hash.
        
        @return project hash as a hex string (string)
        """
        return self.pdata["HASH"][0]
        
    def getRelativePath(self, path):
        """
        Public method to convert a file path to a project relative
        file path.
        
        @param path file or directory name to convert (string)
        @return project relative path or unchanged path, if path doesn't
            belong to the project (string)
        """
        if self.startswithProjectPath(path):
            if self.ppath and path == self.ppath:
                return ""
            else:
                return self.ppathRe.sub("", path, 1)
        else:
            return path
        
    def getRelativeUniversalPath(self, path):
        """
        Public method to convert a file path to a project relative
        file path with universal separators.
        
        @param path file or directory name to convert (string)
        @return project relative path or unchanged path, if path doesn't
            belong to the project (string)
        """
        return Utilities.fromNativeSeparators(self.getRelativePath(path))
        
    def getAbsoluteUniversalPath(self, fn):
        """
        Public method to convert a project relative file path with universal
        separators to an absolute file path.
        
        @param fn file or directory name to convert (string)
        @return absolute path (string)
        """
        if not os.path.isabs(fn):
            fn = os.path.join(self.ppath, Utilities.toNativeSeparators(fn))
        return fn
        
    def getEolString(self):
        """
        Public method to get the EOL-string to be used by the project.
        
        @return eol string (string)
        """
        return self.eols[self.pdata["EOL"][0]]
        
    def useSystemEol(self):
        """
        Public method to check, if the project uses the system eol setting.
        
        @return flag indicating the usage of system eol (boolean)
        """
        return self.pdata["EOL"][0] == 0
        
    def isProjectFile(self, fn):
        """
        Public method used to check, if the passed in filename belongs to the project.
        
        @param fn filename to be checked (string)
        @return flag indicating membership (boolean)
        """
        newfn = os.path.abspath(fn)
        newfn = self.getRelativePath(newfn)
        if newfn in self.pdata["SOURCES"] or \
           newfn in self.pdata["FORMS"] or \
           newfn in self.pdata["INTERFACES"] or \
           newfn in self.pdata["RESOURCES"] or \
           newfn in self.pdata["TRANSLATIONS"] or \
           newfn in self.pdata["OTHERS"]:
            return True
        else:
            for entry in self.pdata["OTHERS"]:
                if newfn.startswith(entry):
                    return True
        
        if Utilities.isWindowsPlatform():
            # try the above case-insensitive
            newfn = newfn.lower()
            for group in ["SOURCES", "FORMS", "INTERFACES",
                          "RESOURCES", "TRANSLATIONS", "OTHERS"]:
                for entry in self.pdata[group]:
                    if entry.lower() == newfn:
                        return True
            for entry in self.pdata["OTHERS"]:
                if newfn.startswith(entry.lower()):
                    return True
        
        return False
        
    def isProjectSource(self, fn):
        """
        Public method used to check, if the passed in filename belongs to the project
        sources.
        
        @param fn filename to be checked (string)
        @return flag indicating membership (boolean)
        """
        newfn = os.path.abspath(fn)
        newfn = self.getRelativePath(newfn)
        return newfn in self.pdata["SOURCES"]
        
    def isProjectForm(self, fn):
        """
        Public method used to check, if the passed in filename belongs to the project
        forms.
        
        @param fn filename to be checked (string)
        @return flag indicating membership (boolean)
        """
        newfn = os.path.abspath(fn)
        newfn = self.getRelativePath(newfn)
        return newfn in self.pdata["FORMS"]
        
    def isProjectInterface(self, fn):
        """
        Public method used to check, if the passed in filename belongs to the project
        interfaces.
        
        @param fn filename to be checked (string)
        @return flag indicating membership (boolean)
        """
        newfn = os.path.abspath(fn)
        newfn = self.getRelativePath(newfn)
        return newfn in self.pdata["INTERFACES"]
        
    def isProjectResource(self, fn):
        """
        Public method used to check, if the passed in filename belongs to the project
        resources.
        
        @param fn filename to be checked (string)
        @return flag indicating membership (boolean)
        """
        newfn = os.path.abspath(fn)
        newfn = self.getRelativePath(newfn)
        return newfn in self.pdata["RESOURCES"]
        
    def initActions(self):
        """
        Public slot to initialize the project related actions.
        """
        self.actions = []
        
        self.actGrp1 = createActionGroup(self)
        
        act = E5Action(self.trUtf8('New project'),
                UI.PixmapCache.getIcon("projectNew.png"),
                self.trUtf8('&New...'), 0, 0,
                self.actGrp1, 'project_new')
        act.setStatusTip(self.trUtf8('Generate a new project'))
        act.setWhatsThis(self.trUtf8(
            """<b>New...</b>"""
            """<p>This opens a dialog for entering the info for a"""
            """ new project.</p>"""
        ))
        act.triggered[()].connect(self.createNewProject)
        self.actions.append(act)

        act = E5Action(self.trUtf8('Open project'),
                UI.PixmapCache.getIcon("projectOpen.png"),
                self.trUtf8('&Open...'), 0, 0,
                self.actGrp1, 'project_open')
        act.setStatusTip(self.trUtf8('Open an existing project'))
        act.setWhatsThis(self.trUtf8(
            """<b>Open...</b>"""
            """<p>This opens an existing project.</p>"""
        ))
        act.triggered[()].connect(self.openProject)
        self.actions.append(act)

        self.closeAct = E5Action(self.trUtf8('Close project'),
                UI.PixmapCache.getIcon("projectClose.png"),
                self.trUtf8('&Close'), 0, 0, self, 'project_close')
        self.closeAct.setStatusTip(self.trUtf8('Close the current project'))
        self.closeAct.setWhatsThis(self.trUtf8(
            """<b>Close</b>"""
            """<p>This closes the current project.</p>"""
        ))
        self.closeAct.triggered[()].connect(self.closeProject)
        self.actions.append(self.closeAct)

        self.saveAct = E5Action(self.trUtf8('Save project'),
                UI.PixmapCache.getIcon("projectSave.png"),
                self.trUtf8('&Save'), 0, 0, self, 'project_save')
        self.saveAct.setStatusTip(self.trUtf8('Save the current project'))
        self.saveAct.setWhatsThis(self.trUtf8(
            """<b>Save</b>"""
            """<p>This saves the current project.</p>"""
        ))
        self.saveAct.triggered[()].connect(self.saveProject)
        self.actions.append(self.saveAct)

        self.saveasAct = E5Action(self.trUtf8('Save project as'),
                UI.PixmapCache.getIcon("projectSaveAs.png"),
                self.trUtf8('Save &as...'), 0, 0, self, 'project_save_as')
        self.saveasAct.setStatusTip(self.trUtf8('Save the current project to a new file'))
        self.saveasAct.setWhatsThis(self.trUtf8(
            """<b>Save as</b>"""
            """<p>This saves the current project to a new file.</p>"""
        ))
        self.saveasAct.triggered[()].connect(self.saveProjectAs)
        self.actions.append(self.saveasAct)

        self.actGrp2 = createActionGroup(self)
        
        self.addFilesAct = E5Action(self.trUtf8('Add files to project'),
                UI.PixmapCache.getIcon("fileMisc.png"),
                self.trUtf8('Add &files...'), 0, 0,
                self.actGrp2, 'project_add_file')
        self.addFilesAct.setStatusTip(self.trUtf8('Add files to the current project'))
        self.addFilesAct.setWhatsThis(self.trUtf8(
            """<b>Add files...</b>"""
            """<p>This opens a dialog for adding files"""
            """ to the current project. The place to add is"""
            """ determined by the file extension.</p>"""
        ))
        self.addFilesAct.triggered[()].connect(self.addFiles)
        self.actions.append(self.addFilesAct)

        self.addDirectoryAct = E5Action(self.trUtf8('Add directory to project'),
                UI.PixmapCache.getIcon("dirOpen.png"),
                self.trUtf8('Add directory...'), 0, 0,
                self.actGrp2, 'project_add_directory')
        self.addDirectoryAct.setStatusTip(
            self.trUtf8('Add a directory to the current project'))
        self.addDirectoryAct.setWhatsThis(self.trUtf8(
            """<b>Add directory...</b>"""
            """<p>This opens a dialog for adding a directory"""
            """ to the current project.</p>"""
        ))
        self.addDirectoryAct.triggered[()].connect(self.addDirectory)
        self.actions.append(self.addDirectoryAct)

        self.addLanguageAct = E5Action(self.trUtf8('Add translation to project'),
                UI.PixmapCache.getIcon("linguist4.png"),
                self.trUtf8('Add &translation...'), 0, 0,
                self.actGrp2, 'project_add_translation')
        self.addLanguageAct.setStatusTip(
            self.trUtf8('Add a translation to the current project'))
        self.addLanguageAct.setWhatsThis(self.trUtf8(
            """<b>Add translation...</b>"""
            """<p>This opens a dialog for add a translation"""
            """ to the current project.</p>"""
        ))
        self.addLanguageAct.triggered[()].connect(self.addLanguage)
        self.actions.append(self.addLanguageAct)

        act = E5Action(self.trUtf8('Search new files'),
                self.trUtf8('Searc&h new files...'), 0, 0,
                self.actGrp2, 'project_search_new_files')
        act.setStatusTip(self.trUtf8('Search new files in the project directory.'))
        act.setWhatsThis(self.trUtf8(
            """<b>Search new files...</b>"""
            """<p>This searches for new files (sources, *.ui, *.idl) in the project"""
            """ directory and registered subdirectories.</p>"""
        ))
        act.triggered[()].connect(self.__searchNewFiles)
        self.actions.append(act)

        self.propsAct = E5Action(self.trUtf8('Project properties'),
                UI.PixmapCache.getIcon("projectProps.png"),
                self.trUtf8('&Properties...'), 0, 0, self, 'project_properties')
        self.propsAct.setStatusTip(self.trUtf8('Show the project properties'))
        self.propsAct.setWhatsThis(self.trUtf8(
            """<b>Properties...</b>"""
            """<p>This shows a dialog to edit the project properties.</p>"""
        ))
        self.propsAct.triggered[()].connect(self.__showProperties)
        self.actions.append(self.propsAct)

        self.userPropsAct = E5Action(self.trUtf8('User project properties'),
                UI.PixmapCache.getIcon("projectUserProps.png"),
                self.trUtf8('&User Properties...'), 0, 0, self, 'project_user_properties')
        self.userPropsAct.setStatusTip(self.trUtf8(
            'Show the user specific project properties'))
        self.userPropsAct.setWhatsThis(self.trUtf8(
            """<b>User Properties...</b>"""
            """<p>This shows a dialog to edit the user specific project properties.</p>"""
        ))
        self.userPropsAct.triggered[()].connect(self.__showUserProperties)
        self.actions.append(self.userPropsAct)

        self.filetypesAct = E5Action(self.trUtf8('Filetype Associations'),
                self.trUtf8('Filetype Associations...'), 0, 0,
                self, 'project_filetype_associatios')
        self.filetypesAct.setStatusTip(
            self.trUtf8('Show the project filetype associations'))
        self.filetypesAct.setWhatsThis(self.trUtf8(
            """<b>Filetype Associations...</b>"""
            """<p>This shows a dialog to edit the filetype associations of the project."""
            """ These associations determine the type (source, form, interface"""
            """ or others) with a filename pattern. They are used when adding a file"""
            """ to the project and when performing a search for new files.</p>"""
        ))
        self.filetypesAct.triggered[()].connect(self.__showFiletypeAssociations)
        self.actions.append(self.filetypesAct)

        self.lexersAct = E5Action(self.trUtf8('Lexer Associations'),
                self.trUtf8('Lexer Associations...'), 0, 0,
                self, 'project_lexer_associatios')
        self.lexersAct.setStatusTip(
            self.trUtf8('Show the project lexer associations (overriding defaults)'))
        self.lexersAct.setWhatsThis(self.trUtf8(
            """<b>Lexer Associations...</b>"""
            """<p>This shows a dialog to edit the lexer associations of the project."""
            """ These associations override the global lexer associations. Lexers"""
            """ are used to highlight the editor text.</p>"""
        ))
        self.lexersAct.triggered[()].connect(self.__showLexerAssociations)
        self.actions.append(self.lexersAct)

        self.dbgActGrp = createActionGroup(self)
        
        act = E5Action(self.trUtf8('Debugger Properties'),
                self.trUtf8('Debugger &Properties...'), 0, 0,
                self.dbgActGrp, 'project_debugger_properties')
        act.setStatusTip(self.trUtf8('Show the debugger properties'))
        act.setWhatsThis(self.trUtf8(
            """<b>Debugger Properties...</b>"""
            """<p>This shows a dialog to edit project specific debugger settings.</p>"""
        ))
        act.triggered[()].connect(self.__showDebugProperties)
        self.actions.append(act)
        
        act = E5Action(self.trUtf8('Load'),
                self.trUtf8('&Load'), 0, 0,
                self.dbgActGrp, 'project_debugger_properties_load')
        act.setStatusTip(self.trUtf8('Load the debugger properties'))
        act.setWhatsThis(self.trUtf8(
            """<b>Load Debugger Properties</b>"""
            """<p>This loads the project specific debugger settings.</p>"""
        ))
        act.triggered[()].connect(self.__readDebugProperties)
        self.actions.append(act)
        
        act = E5Action(self.trUtf8('Save'),
                self.trUtf8('&Save'), 0, 0,
                self.dbgActGrp, 'project_debugger_properties_save')
        act.setStatusTip(self.trUtf8('Save the debugger properties'))
        act.setWhatsThis(self.trUtf8(
            """<b>Save Debugger Properties</b>"""
            """<p>This saves the project specific debugger settings.</p>"""
        ))
        act.triggered[()].connect(self.__writeDebugProperties)
        self.actions.append(act)
        
        act = E5Action(self.trUtf8('Delete'),
                self.trUtf8('&Delete'), 0, 0,
                self.dbgActGrp, 'project_debugger_properties_delete')
        act.setStatusTip(self.trUtf8('Delete the debugger properties'))
        act.setWhatsThis(self.trUtf8(
            """<b>Delete Debugger Properties</b>"""
            """<p>This deletes the file containing the project specific"""
            """ debugger settings.</p>"""
        ))
        act.triggered[()].connect(self.__deleteDebugProperties)
        self.actions.append(act)
        
        act = E5Action(self.trUtf8('Reset'),
                self.trUtf8('&Reset'), 0, 0,
                self.dbgActGrp, 'project_debugger_properties_resets')
        act.setStatusTip(self.trUtf8('Reset the debugger properties'))
        act.setWhatsThis(self.trUtf8(
            """<b>Reset Debugger Properties</b>"""
            """<p>This resets the project specific debugger settings.</p>"""
        ))
        act.triggered[()].connect(self.__initDebugProperties)
        self.actions.append(act)
        
        self.sessActGrp = createActionGroup(self)

        act = E5Action(self.trUtf8('Load session'),
                self.trUtf8('Load session'), 0, 0,
                self.sessActGrp, 'project_load_session')
        act.setStatusTip(self.trUtf8('Load the projects session file.'))
        act.setWhatsThis(self.trUtf8(
            """<b>Load session</b>"""
            """<p>This loads the projects session file. The session consists"""
            """ of the following data.<br>"""
            """- all open source files<br>"""
            """- all breakpoint<br>"""
            """- the commandline arguments<br>"""
            """- the working directory<br>"""
            """- the exception reporting flag</p>"""
        ))
        act.triggered[()].connect(self.__readSession)
        self.actions.append(act)

        act = E5Action(self.trUtf8('Save session'),
                self.trUtf8('Save session'), 0, 0,
                self.sessActGrp, 'project_save_session')
        act.setStatusTip(self.trUtf8('Save the projects session file.'))
        act.setWhatsThis(self.trUtf8(
            """<b>Save session</b>"""
            """<p>This saves the projects session file. The session consists"""
            """ of the following data.<br>"""
            """- all open source files<br>"""
            """- all breakpoint<br>"""
            """- the commandline arguments<br>"""
            """- the working directory<br>"""
            """- the exception reporting flag</p>"""
        ))
        act.triggered[()].connect(self.__writeSession)
        self.actions.append(act)
        
        act = E5Action(self.trUtf8('Delete session'),
                self.trUtf8('Delete session'), 0, 0,
                self.sessActGrp, 'project_delete_session')
        act.setStatusTip(self.trUtf8('Delete the projects session file.'))
        act.setWhatsThis(self.trUtf8(
            """<b>Delete session</b>"""
            """<p>This deletes the projects session file</p>"""
        ))
        act.triggered[()].connect(self.__deleteSession)
        self.actions.append(act)
        
        self.chkGrp = createActionGroup(self)

        self.codeMetricsAct = E5Action(self.trUtf8('Code Metrics'),
                self.trUtf8('&Code Metrics...'), 0, 0,
                self.chkGrp, 'project_code_metrics')
        self.codeMetricsAct.setStatusTip(
            self.trUtf8('Show some code metrics for the project.'))
        self.codeMetricsAct.setWhatsThis(self.trUtf8(
            """<b>Code Metrics...</b>"""
            """<p>This shows some code metrics for all Python files in the project.</p>"""
        ))
        self.codeMetricsAct.triggered[()].connect(self.__showCodeMetrics)
        self.actions.append(self.codeMetricsAct)

        self.codeCoverageAct = E5Action(self.trUtf8('Python Code Coverage'),
                self.trUtf8('Code Co&verage...'), 0, 0,
                self.chkGrp, 'project_code_coverage')
        self.codeCoverageAct.setStatusTip(
            self.trUtf8('Show code coverage information for the project.'))
        self.codeCoverageAct.setWhatsThis(self.trUtf8(
            """<b>Code Coverage...</b>"""
            """<p>This shows the code coverage information for all Python files"""
            """ in the project.</p>"""
        ))
        self.codeCoverageAct.triggered[()].connect(self.__showCodeCoverage)
        self.actions.append(self.codeCoverageAct)

        self.codeProfileAct = E5Action(self.trUtf8('Profile Data'),
                self.trUtf8('&Profile Data...'), 0, 0,
                self.chkGrp, 'project_profile_data')
        self.codeProfileAct.setStatusTip(
            self.trUtf8('Show profiling data for the project.'))
        self.codeProfileAct.setWhatsThis(self.trUtf8(
            """<b>Profile Data...</b>"""
            """<p>This shows the profiling data for the project.</p>"""
        ))
        self.codeProfileAct.triggered[()].connect(self.__showProfileData)
        self.actions.append(self.codeProfileAct)

        self.applicationDiagramAct = E5Action(self.trUtf8('Application Diagram'),
                self.trUtf8('&Application Diagram...'), 0, 0,
                self.chkGrp, 'project_application_diagram')
        self.applicationDiagramAct.setStatusTip(
            self.trUtf8('Show a diagram of the project.'))
        self.applicationDiagramAct.setWhatsThis(self.trUtf8(
            """<b>Application Diagram...</b>"""
            """<p>This shows a diagram of the project.</p>"""
        ))
        self.applicationDiagramAct.triggered[()].connect(self.handleApplicationDiagram)
        self.actions.append(self.applicationDiagramAct)

        self.pluginGrp = createActionGroup(self)

        self.pluginPkgListAct = E5Action(self.trUtf8('Create Package List'),
                UI.PixmapCache.getIcon("pluginArchiveList.png"),
                self.trUtf8('Create &Package List'), 0, 0,
                self.pluginGrp, 'project_plugin_pkglist')
        self.pluginPkgListAct.setStatusTip(
            self.trUtf8('Create an initial PKGLIST file for an eric5 plugin.'))
        self.pluginPkgListAct.setWhatsThis(self.trUtf8(
            """<b>Create Package List</b>"""
            """<p>This creates an initial list of files to include in an eric5 """
            """plugin archive. The list is created from the project file.</p>"""
        ))
        self.pluginPkgListAct.triggered[()].connect(self.__pluginCreatePkgList)
        self.actions.append(self.pluginPkgListAct)

        self.pluginArchiveAct = E5Action(self.trUtf8('Create Plugin Archive'),
                UI.PixmapCache.getIcon("pluginArchive.png"),
                self.trUtf8('Create Plugin &Archive'), 0, 0,
                self.pluginGrp, 'project_plugin_archive')
        self.pluginArchiveAct.setStatusTip(
            self.trUtf8('Create an eric5 plugin archive file.'))
        self.pluginArchiveAct.setWhatsThis(self.trUtf8(
            """<b>Create Plugin Archive</b>"""
            """<p>This creates an eric5 plugin archive file using the list of files """
            """given in the PKGLIST file. The archive name is built from the main """
            """script name.</p>"""
        ))
        self.pluginArchiveAct.triggered[()].connect(self.__pluginCreateArchive)
        self.actions.append(self.pluginArchiveAct)
    
        self.pluginSArchiveAct = E5Action(self.trUtf8('Create Plugin Archive (Snapshot)'),
                UI.PixmapCache.getIcon("pluginArchiveSnapshot.png"),
                self.trUtf8('Create Plugin Archive (&Snapshot)'), 0, 0,
                self.pluginGrp, 'project_plugin_sarchive')
        self.pluginSArchiveAct.setStatusTip(
            self.trUtf8('Create an eric5 plugin archive file (snapshot release).'))
        self.pluginSArchiveAct.setWhatsThis(self.trUtf8(
            """<b>Create Plugin Archive (Snapshot)</b>"""
            """<p>This creates an eric5 plugin archive file using the list of files """
            """given in the PKGLIST file. The archive name is built from the main """
            """script name. The version entry of the main script is modified to """
            """reflect a snapshot release.</p>"""
        ))
        self.pluginSArchiveAct.triggered[()].connect(self.__pluginCreateSnapshotArchive)
        self.actions.append(self.pluginSArchiveAct)

        self.closeAct.setEnabled(False)
        self.saveAct.setEnabled(False)
        self.saveasAct.setEnabled(False)
        self.actGrp2.setEnabled(False)
        self.propsAct.setEnabled(False)
        self.userPropsAct.setEnabled(False)
        self.filetypesAct.setEnabled(False)
        self.lexersAct.setEnabled(False)
        self.sessActGrp.setEnabled(False)
        self.dbgActGrp.setEnabled(False)
        self.pluginGrp.setEnabled(False)
        
    def initMenu(self):
        """
        Public slot to initialize the project menu.
        
        @return the menu generated (QMenu)
        """
        menu = QMenu(self.trUtf8('&Project'), self.parent())
        self.recentMenu = QMenu(self.trUtf8('Open &Recent Projects'), menu)
        self.vcsMenu = QMenu(self.trUtf8('&Version Control'), menu)
        self.vcsMenu.setTearOffEnabled(True)
        self.vcsProjectHelper.initMenu(self.vcsMenu)
        self.checksMenu = QMenu(self.trUtf8('Chec&k'), menu)
        self.checksMenu.setTearOffEnabled(True)
        self.menuShow = QMenu(self.trUtf8('Sho&w'), menu)
        self.graphicsMenu = QMenu(self.trUtf8('&Diagrams'), menu)
        self.sessionMenu = QMenu(self.trUtf8('Session'), menu)
        self.apidocMenu = QMenu(self.trUtf8('Source &Documentation'), menu)
        self.apidocMenu.setTearOffEnabled(True)
        self.debuggerMenu = QMenu(self.trUtf8('Debugger'), menu)
        self.packagersMenu = QMenu(self.trUtf8('Pac&kagers'), menu)
        self.packagersMenu.setTearOffEnabled(True)
        
        self.__menus = {
            "Main": menu,
            "Recent": self.recentMenu,
            "VCS": self.vcsMenu,
            "Checks": self.checksMenu,
            "Show": self.menuShow,
            "Graphics": self.graphicsMenu,
            "Session": self.sessionMenu,
            "Apidoc": self.apidocMenu,
            "Debugger": self.debuggerMenu,
            "Packagers": self.packagersMenu,
        }
        
        # connect the aboutToShow signals
        self.recentMenu.aboutToShow.connect(self.__showContextMenuRecent)
        self.recentMenu.triggered.connect(self.__openRecent)
        self.vcsMenu.aboutToShow.connect(self.__showContextMenuVCS)
        self.checksMenu.aboutToShow.connect(self.__showContextMenuChecks)
        self.menuShow.aboutToShow.connect(self.__showContextMenuShow)
        self.graphicsMenu.aboutToShow.connect(self.__showContextMenuGraphics)
        self.apidocMenu.aboutToShow.connect(self.__showContextMenuApiDoc)
        self.packagersMenu.aboutToShow.connect(self.__showContextMenuPackagers)
        menu.aboutToShow.connect(self.__showMenu)
        
        # build the show menu
        self.menuShow.setTearOffEnabled(True)
        self.menuShow.addAction(self.codeMetricsAct)
        self.menuShow.addAction(self.codeCoverageAct)
        self.menuShow.addAction(self.codeProfileAct)
        
        # build the diagrams menu
        self.graphicsMenu.setTearOffEnabled(True)
        self.graphicsMenu.addAction(self.applicationDiagramAct)
        
        # build the session menu
        self.sessionMenu.setTearOffEnabled(True)
        self.sessionMenu.addActions(self.sessActGrp.actions())
        
        # build the debugger menu
        self.debuggerMenu.setTearOffEnabled(True)
        self.debuggerMenu.addActions(self.dbgActGrp.actions())
        
        # build the packagers menu
        self.packagersMenu.addActions(self.pluginGrp.actions())
        self.packagersMenu.addSeparator()
        
        # build the main menu
        menu.setTearOffEnabled(True)
        menu.addActions(self.actGrp1.actions())
        self.menuRecentAct = menu.addMenu(self.recentMenu)
        menu.addSeparator()
        menu.addAction(self.closeAct)
        menu.addSeparator()
        menu.addAction(self.saveAct)
        menu.addAction(self.saveasAct)
        menu.addSeparator()
        self.menuDebuggerAct = menu.addMenu(self.debuggerMenu)
        self.menuSessionAct = menu.addMenu(self.sessionMenu)
        menu.addSeparator()
        menu.addActions(self.actGrp2.actions())
        menu.addSeparator()
        self.menuDiagramAct = menu.addMenu(self.graphicsMenu)
        menu.addSeparator()
        self.menuCheckAct = menu.addMenu(self.checksMenu)
        menu.addSeparator()
        menu.addMenu(self.vcsMenu)
        menu.addSeparator()
        self.menuShowAct = menu.addMenu(self.menuShow)
        menu.addSeparator()
        self.menuApidocAct = menu.addMenu(self.apidocMenu)
        menu.addSeparator()
        self.menuPackagersAct = menu.addMenu(self.packagersMenu)
        menu.addSeparator()
        menu.addAction(self.propsAct)
        menu.addAction(self.userPropsAct)
        menu.addAction(self.filetypesAct)
        menu.addAction(self.lexersAct)
        
        self.menuCheckAct.setEnabled(False)
        self.menuShowAct.setEnabled(False)
        self.menuDiagramAct.setEnabled(False)
        self.menuSessionAct.setEnabled(False)
        self.menuDebuggerAct.setEnabled(False)
        self.menuApidocAct.setEnabled(False)
        self.menuPackagersAct.setEnabled(False)
        
        self.menu = menu
        return menu
        
    def initToolbar(self, toolbarManager):
        """
        Public slot to initialize the project toolbar.
        
        @param toolbarManager reference to a toolbar manager object (E5ToolBarManager)
        @return the toolbar generated (QToolBar)
        """
        tb = QToolBar(self.trUtf8("Project"), self.ui)
        tb.setIconSize(UI.Config.ToolBarIconSize)
        tb.setObjectName("ProjectToolbar")
        tb.setToolTip(self.trUtf8('Project'))
        
        tb.addActions(self.actGrp1.actions())
        tb.addAction(self.closeAct)
        tb.addSeparator()
        tb.addAction(self.saveAct)
        tb.addAction(self.saveasAct)
        
        toolbarManager.addToolBar(tb, tb.windowTitle())
        toolbarManager.addAction(self.addFilesAct, tb.windowTitle())
        toolbarManager.addAction(self.addDirectoryAct, tb.windowTitle())
        toolbarManager.addAction(self.addLanguageAct, tb.windowTitle())
        toolbarManager.addAction(self.propsAct, tb.windowTitle())
        toolbarManager.addAction(self.userPropsAct, tb.windowTitle())
        
        return tb
        
    def __showMenu(self):
        """
        Private method to set up the project menu.
        """
        self.menuRecentAct.setEnabled(len(self.recent) > 0)
        
        self.showMenu.emit("Main", self.__menus["Main"])
        
    def __syncRecent(self):
        """
        Private method to synchronize the list of recently opened projects
        with the central store.
        """
        for recent in self.recent[:]:
            if Utilities.samepath(self.pfile, recent):
                self.recent.remove(recent)
        self.recent.insert(0, self.pfile)
        maxRecent = Preferences.getProject("RecentNumber")
        if len(self.recent) > maxRecent:
            self.recent = self.recent[:maxRecent]
        self.__saveRecent()
        
    def __showContextMenuRecent(self):
        """
        Private method to set up the recent projects menu.
        """
        self.__loadRecent()
        
        self.recentMenu.clear()
        
        idx = 1
        for rp in self.recent:
            if idx < 10:
                formatStr = '&{0:d}. {1}'
            else:
                formatStr = '{0:d}. {1}'
            act = self.recentMenu.addAction(
                formatStr.format(idx,
                    Utilities.compactPath(rp, self.ui.maxMenuFilePathLen)))
            act.setData(rp)
            act.setEnabled(QFileInfo(rp).exists())
            idx += 1
        
        self.recentMenu.addSeparator()
        self.recentMenu.addAction(self.trUtf8('&Clear'), self.__clearRecent)
        
    def __openRecent(self, act):
        """
        Private method to open a project from the list of rencently opened projects.
        
        @param act reference to the action that triggered (QAction)
        """
        file = act.data()
        if file:
            self.openProject(file)
        
    def __clearRecent(self):
        """
        Private method to clear the recent projects menu.
        """
        self.recent = []
        
    def __searchNewFiles(self):
        """
        Private slot used to handle the search new files action.
        """
        self.__doSearchNewFiles(False, True)
        
    def __doSearchNewFiles(self, AI=True, onUserDemand=False):
        """
        Private method to search for new files in the project directory.
        
        If new files were found, it shows a dialog listing these files and
        gives the user the opportunity to select the ones he wants to
        include. If 'Automatic Inclusion' is enabled, the new files are
        automatically added to the project.
        
        @param AI flag indicating whether the automatic inclusion should
                be honoured (boolean)
        @param onUserDemand flag indicating whether this method was
                requested by the user via a menu action (boolean)
        """
        autoInclude = Preferences.getProject("AutoIncludeNewFiles")
        recursiveSearch = Preferences.getProject("SearchNewFilesRecursively")
        newFiles = []
        
        dirs = self.subdirs[:]
        for dir in dirs:
            curpath = os.path.join(self.ppath, dir)
            try:
                newSources = os.listdir(curpath)
            except OSError:
                newSources = []
            if self.pdata["TRANSLATIONPATTERN"]:
                pattern = self.pdata["TRANSLATIONPATTERN"][0].replace("%language%", "*")
            else:
                pattern = "*.ts"
            binpattern = self.__binaryTranslationFile(pattern)
            for ns in newSources:
                # ignore hidden files and directories
                if ns.startswith('.'):
                    continue
                if Utilities.isWindowsPlatform() and \
                   os.path.isdir(os.path.join(curpath, ns)) and \
                   ns.startswith('_'):
                    # dot net hack
                    continue
                
                # set fn to project relative name
                # then reset ns to fully qualified name for insertion, possibly.
                if dir == "":
                    fn = ns
                else:
                    fn = os.path.join(dir, ns)
                ns = os.path.abspath(os.path.join(curpath, ns))
                
                # do not bother with dirs here...
                if os.path.isdir(ns):
                    if recursiveSearch:
                        d = self.getRelativePath(ns)
                        if d not in dirs:
                            dirs.append(d)
                    continue
                
                filetype = ""
                bfn = os.path.basename(fn)
                for pattern in reversed(sorted(self.pdata["FILETYPES"].keys())):
                    if fnmatch.fnmatch(bfn, pattern):
                        filetype = self.pdata["FILETYPES"][pattern]
                        break
                
                if (filetype == "SOURCES" and fn not in self.pdata["SOURCES"]) or \
                   (filetype == "FORMS" and fn not in self.pdata["FORMS"]) or \
                   (filetype == "INTERFACES" and fn not in self.pdata["INTERFACES"]) or \
                   (filetype == "RESOURCES" and fn not in self.pdata["RESOURCES"]) or \
                   (filetype == "OTHERS" and fn not in self.pdata["OTHERS"]):
                    if autoInclude and AI:
                        self.appendFile(ns)
                    else:
                        newFiles.append(ns)
                elif filetype == "TRANSLATIONS" and fn not in self.pdata["TRANSLATIONS"]:
                    if fnmatch.fnmatch(ns, pattern) or fnmatch.fnmatch(ns, binpattern):
                        if autoInclude and AI:
                            self.appendFile(ns)
                        else:
                            newFiles.append(ns)
        
        # if autoInclude is set there is no more work left
        if (autoInclude and AI):
            return
        
        # if newfiles is empty, put up message box informing user nothing found
        if not newFiles:
            if onUserDemand:
                E5MessageBox.information(self.ui,
                    self.trUtf8("Search New Files"),
                    self.trUtf8("There were no new files found to be added."))
            return
            
        # autoInclude is not set, show a dialog
        dlg = AddFoundFilesDialog(newFiles, self.parent(), None)
        res = dlg.exec_()
        
        # the 'Add All' button was pressed
        if res == 1:
            for file in newFiles:
                self.appendFile(file)
            
        # the 'Add Selected' button was pressed
        elif res == 2:
            files = dlg.getSelection()
            for file in files:
                self.appendFile(file)
        
    def othersAdded(self, fn, updateModel=True):
        """
        Public slot to be called, if something was added to the OTHERS project data area.
        
        @param fn filename or directory name added (string)
        @param updateModel flag indicating an update of the model is requested (boolean)
        """
        self.projectOthersAdded.emit(fn)
        updateModel and self.__model.addNewItem("OTHERS", fn)
        
    def getActions(self):
        """
        Public method to get a list of all actions.
        
        @return list of all actions (list of E5Action)
        """
        return self.actions[:]
        
    def addE5Actions(self, actions):
        """
        Public method to add actions to the list of actions.
        
        @param actions list of actions (list of E5Action)
        """
        self.actions.extend(actions)
        
    def removeE5Actions(self, actions):
        """
        Public method to remove actions from the list of actions.
        
        @param actions list of actions (list of E5Action)
        """
        for act in actions:
            try:
                self.actions.remove(act)
            except ValueError:
                pass
        
    def getMenu(self, menuName):
        """
        Public method to get a reference to the main menu or a submenu.
        
        @param menuName name of the menu (string)
        @return reference to the requested menu (QMenu) or None
        """
        try:
            return self.__menus[menuName]
        except KeyError:
            return None
        
    def repopulateItem(self, fullname):
        """
        Public slot to repopulate a named item.
        
        @param fullname full name of the item to repopulate (string)
        """
        if not self.isOpen():
            return
        
        name = self.getRelativePath(fullname)
        self.prepareRepopulateItem.emit(name)
        self.__model.repopulateItem(name)
        self.completeRepopulateItem.emit(name)
    
    ##############################################################
    ## Below is the VCS interface
    ##############################################################
    
    def initVCS(self, vcsSystem=None, nooverride=False):
        """
        Public method used to instantiate a vcs system.
        
        @param vcsSystem type of VCS to be used (string)
        @param nooverride flag indicating to ignore an override request (boolean)
        @return a reference to the vcs object
        """
        vcs = None
        forProject = True
        override = False
        
        if vcsSystem is None:
            if len(self.pdata["VCS"]):
                if self.pdata["VCS"][0] != 'None':
                    vcsSystem = self.pdata["VCS"][0]
        else:
            forProject = False
        
        if self.pdata["VCS"] and self.pdata["VCS"][0] != 'None':
            if self.pudata["VCSOVERRIDE"] and \
               self.pudata["VCSOVERRIDE"][0] is not None and \
               not nooverride:
                vcsSystem = self.pudata["VCSOVERRIDE"][0]
                override = True
        
        if vcsSystem is not None:
            try:
                vcs = VCS.factory(vcsSystem)
            except ImportError:
                if override:
                    # override failed, revert to original
                    self.pudata["VCSOVERRIDE"] = []
                    return self.initVCS(nooverride=True)
        
        if vcs:
            vcsExists, msg = vcs.vcsExists()
            if not vcsExists:
                if override:
                    # override failed, revert to original
                    QApplication.restoreOverrideCursor()
                    E5MessageBox.critical(self.ui,
                        self.trUtf8("Version Control System"),
                        self.trUtf8("<p>The selected VCS <b>{0}</b> could not be found."
                                    "<br/>Reverting override.</p><p>{1}</p>")\
                            .format(vcsSystem, msg))
                    self.pudata["VCSOVERRIDE"] = []
                    return self.initVCS(nooverride=True)
                
                QApplication.restoreOverrideCursor()
                E5MessageBox.critical(self.ui,
                    self.trUtf8("Version Control System"),
                    self.trUtf8("<p>The selected VCS <b>{0}</b> could not be found.<br/>"
                                "Disabling version control.</p><p>{1}</p>")\
                        .format(vcsSystem, msg))
                vcs = None
                if forProject:
                    self.pdata["VCS"][0] = 'None'
                    self.setDirty(True)
        
        if vcs and forProject:
            # set the vcs options
            try:
                vcsopt = copy.deepcopy(self.pdata["VCSOPTIONS"][0])
                vcs.vcsSetOptions(vcsopt)
            except LookupError:
                pass
            # set vcs specific data
            try:
                vcsother = copy.deepcopy(self.pdata["VCSOTHERDATA"][0])
                vcs.vcsSetOtherData(vcsother)
            except LookupError:
                pass
        
        if vcs is None:
            self.vcsProjectHelper = VcsProjectHelper(None, self)
            self.vcsBasicHelper = True
        else:
            self.vcsProjectHelper = vcs.vcsGetProjectHelper(self)
            self.vcsBasicHelper = False
        if self.vcsMenu is not None:
            self.vcsProjectHelper.initMenu(self.vcsMenu)
        return vcs
        
    def __showContextMenuVCS(self):
        """
        Private slot called before the vcs menu is shown.
        """
        self.vcsProjectHelper.showMenu()
        if self.vcsBasicHelper:
            self.showMenu.emit("VCS", self.vcsMenu)
    
    #########################################################################
    ## Below is the interface to the checker tools
    #########################################################################
    
    def __showContextMenuChecks(self):
        """
        Private slot called before the checks menu is shown.
        """
        self.showMenu.emit("Checks", self.checksMenu)
    
    #########################################################################
    ## Below is the interface to the packagers tools
    #########################################################################
    
    def __showContextMenuPackagers(self):
        """
        Private slot called before the packagers menu is shown.
        """
        self.showMenu.emit("Packagers", self.packagersMenu)
    
    #########################################################################
    ## Below is the interface to the apidoc tools
    #########################################################################
    
    def __showContextMenuApiDoc(self):
        """
        Private slot called before the apidoc menu is shown.
        """
        self.showMenu.emit("Apidoc", self.apidocMenu)
    
    #########################################################################
    ## Below is the interface to the show tools
    #########################################################################
    
    def __showCodeMetrics(self):
        """
        Private slot used to calculate some code metrics for the project files.
        """
        files = [os.path.join(self.ppath, file) \
            for file in self.pdata["SOURCES"] if file.endswith(".py")]
        self.codemetrics = CodeMetricsDialog()
        self.codemetrics.show()
        self.codemetrics.prepare(files, self)

    def __showCodeCoverage(self):
        """
        Private slot used to show the code coverage information for the project files.
        """
        fn = self.getMainScript(True)
        if fn is None:
            E5MessageBox.critical(self.ui,
                self.trUtf8("Coverage Data"),
                self.trUtf8("There is no main script defined for the"
                    " current project. Aborting"))
            return
        
        tfn = Utilities.getTestFileName(fn)
        basename = os.path.splitext(fn)[0]
        tbasename = os.path.splitext(tfn)[0]
        
        # determine name of coverage file to be used
        files = []
        f = "{0}.coverage".format(basename)
        tf = "{0}.coverage".format(tbasename)
        if os.path.isfile(f):
            files.append(f)
        if os.path.isfile(tf):
            files.append(tf)
        
        if files:
            if len(files) > 1:
                fn, ok = QInputDialog.getItem(
                    None,
                    self.trUtf8("Code Coverage"),
                    self.trUtf8("Please select a coverage file"),
                    files,
                    0, False)
                if not ok:
                    return
            else:
                fn = files[0]
        else:
            return
        
        files = [os.path.join(self.ppath, file) \
            for file in self.pdata["SOURCES"] if file.endswith(".py")]
        self.codecoverage = PyCoverageDialog()
        self.codecoverage.show()
        self.codecoverage.start(fn, files)

    def __showProfileData(self):
        """
        Private slot used to show the profiling information for the project.
        """
        fn = self.getMainScript(True)
        if fn is None:
            E5MessageBox.critical(self.ui,
                self.trUtf8("Profile Data"),
                self.trUtf8("There is no main script defined for the"
                    " current project. Aborting"))
            return
        
        tfn = Utilities.getTestFileName(fn)
        basename = os.path.splitext(fn)[0]
        tbasename = os.path.splitext(tfn)[0]
        
        # determine name of profile file to be used
        files = []
        f = "{0}.profile".format(basename)
        tf = "{0}.profile".format(tbasename)
        if os.path.isfile(f):
            files.append(f)
        if os.path.isfile(tf):
            files.append(tf)
        
        if files:
            if len(files) > 1:
                fn, ok = QInputDialog.getItem(
                    None,
                    self.trUtf8("Profile Data"),
                    self.trUtf8("Please select a profile file"),
                    files,
                    0, False)
                if not ok:
                    return
            else:
                fn = files[0]
        else:
            return
        
        self.profiledata = PyProfileDialog()
        self.profiledata.show()
        self.profiledata.start(fn)
        
    def __showContextMenuShow(self):
        """
        Private slot called before the show menu is shown.
        """
        fn = self.getMainScript(True)
        if fn is not None:
            tfn = Utilities.getTestFileName(fn)
            basename = os.path.splitext(fn)[0]
            tbasename = os.path.splitext(tfn)[0]
            self.codeProfileAct.setEnabled(
                os.path.isfile("{0}.profile".format(basename)) or \
                os.path.isfile("{0}.profile".format(tbasename)))
            self.codeCoverageAct.setEnabled(
                self.isPy3Project() and \
                (os.path.isfile("{0}.coverage".format(basename)) or \
                 os.path.isfile("{0}.coverage".format(tbasename))))
        else:
            self.codeProfileAct.setEnabled(False)
            self.codeCoverageAct.setEnabled(False)
        
        self.showMenu.emit("Show", self.menuShow)
    
    #########################################################################
    ## Below is the interface to the diagrams
    #########################################################################
    
    def __showContextMenuGraphics(self):
        """
        Private slot called before the graphics menu is shown.
        """
        self.showMenu.emit("Graphics", self.graphicsMenu)
    
    def handleApplicationDiagram(self):
        """
        Private method to handle the application diagram context menu action.
        """
        res = E5MessageBox.yesNo(self.ui,
            self.trUtf8("Application Diagram"),
            self.trUtf8("""Include module names?"""),
            yesDefault=True)
        
        self.applicationDiagram = ApplicationDiagram(self, self.parent(),
            noModules=not res)
        self.applicationDiagram.show()
    
    #########################################################################
    ## Below is the interface to the VCS monitor thread
    #########################################################################
    
    def __statusMonitorStatus(self, status, statusMsg):
        """
        Private method to receive the status monitor status.
        
        It simply reemits the received status.
        
        @param status status of the monitoring thread (string, ok, nok or off)
        @param statusMsg explanotory text for the signaled status (string)
        """
        self.vcsStatusMonitorStatus.emit(status, statusMsg)
        
    def setStatusMonitorInterval(self, interval):
        """
        Public method to se the interval of the VCS status monitor thread.
        
        @param interval status monitor interval in seconds (integer)
        """
        if self.vcs is not None:
            self.vcs.setStatusMonitorInterval(interval, self)
        
    def getStatusMonitorInterval(self):
        """
        Public method to get the monitor interval.
        
        @return interval in seconds (integer)
        """
        if self.vcs is not None:
            return self.vcs.getStatusMonitorInterval()
        else:
            return 0
        
    def setStatusMonitorAutoUpdate(self, auto):
        """
        Public method to enable the auto update function.
        
        @param auto status of the auto update function (boolean)
        """
        if self.vcs is not None:
            self.vcs.setStatusMonitorAutoUpdate(auto)
        
    def getStatusMonitorAutoUpdate(self):
        """
        Public method to retrieve the status of the auto update function.
        
        @return status of the auto update function (boolean)
        """
        if self.vcs is not None:
            return self.vcs.getStatusMonitorAutoUpdate()
        else:
            return False
        
    def checkVCSStatus(self):
        """
        Public method to wake up the VCS status monitor thread.
        """
        if self.vcs is not None:
            self.vcs.checkVCSStatus()
        
    def clearStatusMonitorCachedState(self, name):
        """
        Public method to clear the cached VCS state of a file/directory.
        
        @param name name of the entry to be cleared (string)
        """
        if self.vcs is not None:
            self.vcs.clearStatusMonitorCachedState(name)
        
    def startStatusMonitor(self):
        """
        Public method to start the VCS status monitor thread.
        """
        if self.vcs is not None:
            self.vcs.startStatusMonitor(self)
        
    def stopStatusMonitor(self):
        """
        Public method to stop the VCS status monitor thread.
        """
        if self.vcs is not None:
            self.vcs.stopStatusMonitor()
    
    #########################################################################
    ## Below are the plugin development related methods
    #########################################################################
    
    def __pluginCreatePkgList(self):
        """
        Private slot to create a PKGLIST file needed for archive file creation.
        """
        pkglist = os.path.join(self.ppath, "PKGLIST")
        if os.path.exists(pkglist):
            res = E5MessageBox.yesNo(self.ui,
                self.trUtf8("Create Package List"),
                self.trUtf8("<p>The file <b>PKGLIST</b> already"
                    " exists.</p><p>Overwrite it?</p>"),
                icon=E5MessageBox.Warning)
            if not res:
                return  # don't overwrite
        
        # build the list of entries
        lst = []
        for key in \
            ["SOURCES", "FORMS", "RESOURCES", "TRANSLATIONS", "INTERFACES", "OTHERS"]:
            lst.extend(self.pdata[key])
        lst.sort()
        if "PKGLIST" in lst:
            lst.remove("PKGLIST")
        
        # write the file
        try:
            if self.pdata["EOL"][0] == 0:
                newline = None
            else:
                newline = self.getEolString()
            pkglistFile = open(pkglist, "w", encoding="utf-8", newline=newline)
            pkglistFile.write("\n".join(lst))
            pkglistFile.close()
        except IOError as why:
            E5MessageBox.critical(self.ui,
                self.trUtf8("Create Package List"),
                self.trUtf8("""<p>The file <b>PKGLIST</b> could not be created.</p>"""
                            """<p>Reason: {0}</p>""").format(str(why)))
            return
        
        if not "PKGLIST" in self.pdata["OTHERS"]:
            self.appendFile("PKGLIST")
        
    def __pluginCreateArchive(self, snapshot=False):
        """
        Private slot to create an eric5 plugin archive.
        
        @param snapshot flag indicating a snapshot archive (boolean)
        """
        pkglist = os.path.join(self.ppath, "PKGLIST")
        if not os.path.exists(pkglist):
            E5MessageBox.critical(self.ui,
                self.trUtf8("Create Plugin Archive"),
                self.trUtf8("""<p>The file <b>PKGLIST</b> does not exist. """
                            """Aborting...</p>"""))
            return
        
        if len(self.pdata["MAINSCRIPT"]) == 0 or \
           len(self.pdata["MAINSCRIPT"][0]) == 0:
            E5MessageBox.critical(self.ui,
                self.trUtf8("Create Plugin Archive"),
                self.trUtf8("""The project does not have a main script defined. """
                            """Aborting..."""))
            return
        
        try:
            pkglistFile = open(pkglist, "r", encoding="utf-8")
            names = pkglistFile.read()
            pkglistFile.close()
            names = sorted(names.splitlines())
        except IOError as why:
            E5MessageBox.critical(self.ui,
                self.trUtf8("Create Plugin Archive"),
                self.trUtf8("""<p>The file <b>PKGLIST</b> could not be read.</p>"""
                            """<p>Reason: {0}</p>""").format(str(why)))
            return
        
        archive = \
            os.path.join(self.ppath, self.pdata["MAINSCRIPT"][0].replace(".py", ".zip"))
        try:
            archiveFile = zipfile.ZipFile(archive, "w")
        except IOError as why:
            E5MessageBox.critical(self.ui,
                self.trUtf8("Create Plugin Archive"),
                self.trUtf8("""<p>The eric5 plugin archive file <b>{0}</b> could """
                            """not be created.</p>"""
                            """<p>Reason: {1}</p>""").format(archive, str(why)))
            return
        
        for name in names:
            try:
                self.__createZipDirEntries(os.path.split(name)[0], archiveFile)
                if snapshot and name == self.pdata["MAINSCRIPT"][0]:
                    snapshotSource, version = self.__createSnapshotSource(
                        os.path.join(self.ppath, self.pdata["MAINSCRIPT"][0]))
                    archiveFile.writestr(name, snapshotSource)
                else:
                    archiveFile.write(os.path.join(self.ppath, name), name)
                    if name == self.pdata["MAINSCRIPT"][0]:
                        version = self.__pluginExtractVersion(
                            os.path.join(self.ppath, self.pdata["MAINSCRIPT"][0]))
            except OSError as why:
                E5MessageBox.critical(self.ui,
                    self.trUtf8("Create Plugin Archive"),
                    self.trUtf8("""<p>The file <b>{0}</b> could not be stored """
                                """in the archive. Ignoring it.</p>"""
                                """<p>Reason: {1}</p>""")\
                                .format(os.path.join(self.ppath, name), str(why)))
        archiveFile.writestr("VERSION", version.encode("utf-8"))
        archiveFile.close()
        
        if not archive in self.pdata["OTHERS"]:
            self.appendFile(archive)
        
        E5MessageBox.information(self.ui,
            self.trUtf8("Create Plugin Archive"),
            self.trUtf8("""<p>The eric5 plugin archive file <b>{0}</b> was """
                        """created successfully.</p>""").format(archive))
    
    def __pluginCreateSnapshotArchive(self):
        """
        Private slot to create an eric5 plugin archive snapshot release.
        """
        self.__pluginCreateArchive(True)
    
    def __createZipDirEntries(self, path, zipFile):
        """
        Private method to create dir entries in the zip file.
        
        @param path name of the directory entry to create (string)
        @param zipFile open ZipFile object (zipfile.ZipFile)
        """
        if path == "" or path == "/" or path == "\\":
            return
        
        if not path.endswith("/") and not path.endswith("\\"):
            path = "{0}/".format(path)
        
        if not path in zipFile.namelist():
            self.__createZipDirEntries(os.path.split(path[:-1])[0], zipFile)
            zipFile.writestr(path, b"")
    
    def __createSnapshotSource(self, filename):
        """
        Private method to create a snapshot plugin version.
        
        The version entry in the plugin module is modified to signify
        a snapshot version. This method appends the string "-snapshot-"
        and date indicator to the version string.
        
        @param filename name of the plugin file to modify (string)
        @return modified source (bytes), snapshot version string (string)
        """
        try:
            sourcelines, encoding = Utilities.readEncodedFile(filename)
            sourcelines = sourcelines.splitlines(True)
        except (IOError, UnicodeError) as why:
            E5MessageBox.critical(self.ui,
                self.trUtf8("Create Plugin Archive"),
                self.trUtf8("""<p>The plugin file <b>{0}</b> could """
                            """not be read.</p>"""
                            """<p>Reason: {1}</p>""").format(filename, str(why)))
            return b"", ""
        
        lineno = 0
        while lineno < len(sourcelines):
            if sourcelines[lineno].startswith("version = "):
                # found the line to modify
                datestr = time.strftime("%Y%m%d")
                lineend = sourcelines[lineno].replace(sourcelines[lineno].rstrip(), "")
                sversion = "{0}-snapshot-{1}".format(
                    sourcelines[lineno].replace("version = ", "").strip()[1:-1],
                    datestr)
                sourcelines[lineno] = '{0} + "-snapshot-{1}"{2}'.format(
                    sourcelines[lineno].rstrip(), datestr, lineend)
                break
            
            lineno += 1
        
        source = Utilities.encode("".join(sourcelines), encoding)[0]
        return source, sversion
    
    def __pluginExtractVersion(self, filename):
        """
        Private method to extract the version number entry.
        
        @param filename name of the plugin file (string)
        @return version string (string)
        """
        version = "0.0.0"
        try:
            sourcelines = Utilities.readEncodedFile(filename)[0]
            sourcelines = sourcelines.splitlines(True)
        except (IOError, UnicodeError) as why:
            E5MessageBox.critical(self.ui,
                self.trUtf8("Create Plugin Archive"),
                self.trUtf8("""<p>The plugin file <b>{0}</b> could """
                            """not be read.</p>"""
                            """<p>Reason: {1}</p>""").format(filename, str(why)))
            return ""
        
        for sourceline in sourcelines:
            if sourceline.startswith("version = "):
                version = sourceline.replace("version = ", "").strip()\
                            .replace('"', "").replace("'", "")
                break
        
        return version
