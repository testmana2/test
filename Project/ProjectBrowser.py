# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the project browser part of the eric5 UI.
"""

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QColor, QApplication

from UI.Browser import Browser

from E5Gui.E5TabWidget import E5TabWidget
from E5Gui.E5Led import E5Led

import UI.PixmapCache
import Preferences

from .ProjectBrowserFlags import SourcesBrowserFlag, FormsBrowserFlag, \
    ResourcesBrowserFlag, TranslationsBrowserFlag, InterfacesBrowserFlag, \
    OthersBrowserFlag, AllBrowsersFlag


class ProjectBrowser(E5TabWidget):
    """
    Class implementing the project browser part of the eric5 UI.
    
    It generates a widget with up to seven tabs. The individual tabs contain
    the project sources browser, the project forms browser,
    the project resources browser, the project translations browser,
    the project interfaces (IDL) browser and a browser for stuff,
    that doesn't fit these categories. Optionally it contains an additional
    tab with the file system browser.
    """
    def __init__(self, project, parent=None, embeddedBrowser=True):
        """
        Constructor
        
        @param project reference to the project object
        @param parent parent widget (QWidget)
        @param embeddedBrowser flag indicating whether the file browser should
            be included. This flag is set to False by those layouts, that
            have the file browser in a separate window or embedded
            in the debeug browser instead
        """
        E5TabWidget.__init__(self, parent)
        self.project = project
        
        self.setWindowIcon(UI.PixmapCache.getIcon("eric.png"))
        
        self.setUsesScrollButtons(True)
        
        self.vcsStatusIndicator = E5Led(self)
        self.setCornerWidget(self.vcsStatusIndicator, Qt.TopLeftCorner)
        self.vcsStatusColorNames = {
            "A": "VcsAdded",
            "M": "VcsModified",
            "O": "VcsRemoved",
            "R": "VcsReplaced",
            "U": "VcsUpdate",
            "Z": "VcsConflict",
        }
        self.vcsStatusText = {
            " ": self.trUtf8("up to date"),
            "A": self.trUtf8("files added"),
            "M": self.trUtf8("local modifications"),
            "O": self.trUtf8("files removed"),
            "R": self.trUtf8("files replaced"),
            "U": self.trUtf8("update required"),
            "Z": self.trUtf8("conflict"),
        }
        self.__vcsStateChanged(" ")
        
        # step 1: create all the individual browsers
        from .ProjectSourcesBrowser import ProjectSourcesBrowser
        from .ProjectFormsBrowser import ProjectFormsBrowser
        from .ProjectTranslationsBrowser import ProjectTranslationsBrowser
        from .ProjectResourcesBrowser import ProjectResourcesBrowser
        from .ProjectInterfacesBrowser import ProjectInterfacesBrowser
        from .ProjectOthersBrowser import ProjectOthersBrowser
        # sources browser
        self.psBrowser = ProjectSourcesBrowser(self.project)
        # forms browser
        self.pfBrowser = ProjectFormsBrowser(self.project)
        # resources browser
        self.prBrowser = ProjectResourcesBrowser(self.project)
        # translations browser
        self.ptBrowser = ProjectTranslationsBrowser(self.project)
        # interfaces (IDL) browser
        self.piBrowser = ProjectInterfacesBrowser(self.project)
        # others browser
        self.poBrowser = ProjectOthersBrowser(self.project)
        
        # add the file browser, if it should be embedded here
        self.embeddedBrowser = embeddedBrowser
        if embeddedBrowser:
            self.fileBrowser = Browser()
        
        # step 2: connect all the browsers
        # connect the sources browser
        self.project.projectClosed.connect(self.psBrowser._projectClosed)
        self.project.projectOpened.connect(self.psBrowser._projectOpened)
        self.project.newProject.connect(self.psBrowser._newProject)
        self.project.reinitVCS.connect(self.psBrowser._initMenusAndVcs)
        
        # connect the forms browser
        self.project.projectClosed.connect(self.pfBrowser._projectClosed)
        self.project.projectOpened.connect(self.pfBrowser._projectOpened)
        self.project.newProject.connect(self.pfBrowser._newProject)
        self.project.reinitVCS.connect(self.pfBrowser._initMenusAndVcs)
        
        # connect the resources browser
        self.project.projectClosed.connect(self.prBrowser._projectClosed)
        self.project.projectOpened.connect(self.prBrowser._projectOpened)
        self.project.newProject.connect(self.prBrowser._newProject)
        self.project.reinitVCS.connect(self.prBrowser._initMenusAndVcs)
        
        # connect the translations browser
        self.project.projectClosed.connect(self.ptBrowser._projectClosed)
        self.project.projectOpened.connect(self.ptBrowser._projectOpened)
        self.project.newProject.connect(self.ptBrowser._newProject)
        self.project.reinitVCS.connect(self.ptBrowser._initMenusAndVcs)
        
        # connect the interfaces (IDL)  browser
        self.project.projectClosed.connect(self.piBrowser._projectClosed)
        self.project.projectOpened.connect(self.piBrowser._projectOpened)
        self.project.newProject.connect(self.piBrowser._newProject)
        self.project.reinitVCS.connect(self.piBrowser._initMenusAndVcs)
        
        # connect the others browser
        self.project.projectClosed.connect(self.poBrowser._projectClosed)
        self.project.projectOpened.connect(self.poBrowser._projectOpened)
        self.project.newProject.connect(self.poBrowser._newProject)
        self.project.reinitVCS.connect(self.poBrowser._initMenusAndVcs)
        
        # add signal connection to ourself
        self.project.projectOpened.connect(self.__projectOpened)
        self.project.projectClosed.connect(self.__projectClosed)
        self.project.newProject.connect(self.__newProject)
        self.project.projectPropertiesChanged.connect(
            self.__projectPropertiesChanged)
        self.currentChanged.connect(self.__currentChanged)
        self.project.getModel().vcsStateChanged.connect(self.__vcsStateChanged)
        
        self.__currentBrowsersFlags = 0
        self.__projectPropertiesChanged()
        if self.embeddedBrowser:
            self.setCurrentWidget(self.fileBrowser)
        else:
            self.setCurrentIndex(0)
        
    def __setBrowsersAvailable(self, browserFlags):
        """
        Private method to add selected browsers to the project browser.
        
        @param browserFlags flags indicating the browsers to add (integer)
        """
        # step 1: remove all tabs
        while self.count() > 0:
            self.removeTab(0)
        
        # step 2: add browsers
        if browserFlags & SourcesBrowserFlag:
            index = self.addTab(self.psBrowser,
                UI.PixmapCache.getIcon("projectSources.png"), '')
            self.setTabToolTip(index, self.psBrowser.windowTitle())
        
        if browserFlags & FormsBrowserFlag:
            index = self.addTab(self.pfBrowser,
                UI.PixmapCache.getIcon("projectForms.png"), '')
            self.setTabToolTip(index, self.pfBrowser.windowTitle())
        
        if browserFlags & ResourcesBrowserFlag:
            index = self.addTab(self.prBrowser,
                UI.PixmapCache.getIcon("projectResources.png"), '')
            self.setTabToolTip(index, self.prBrowser.windowTitle())
        
        if browserFlags & TranslationsBrowserFlag:
            index = self.addTab(self.ptBrowser,
                UI.PixmapCache.getIcon("projectTranslations.png"), '')
            self.setTabToolTip(index, self.ptBrowser.windowTitle())
        
        if browserFlags & InterfacesBrowserFlag:
            index = self.addTab(self.piBrowser,
                UI.PixmapCache.getIcon("projectInterfaces.png"), '')
            self.setTabToolTip(index, self.piBrowser.windowTitle())
        
        if browserFlags & OthersBrowserFlag:
            index = self.addTab(self.poBrowser,
                UI.PixmapCache.getIcon("projectOthers.png"), '')
            self.setTabToolTip(index, self.poBrowser.windowTitle())
        
        if self.embeddedBrowser:
            index = self.addTab(self.fileBrowser,
                UI.PixmapCache.getIcon("browser.png"), '')
            self.setTabToolTip(index, self.fileBrowser.windowTitle())
        
        QApplication.processEvents()
        
    def showEvent(self, evt):
        """
        Protected method handleing the show event.
        
        @param evt show event to handle (QShowEvent)
        """
        E5TabWidget.showEvent(self, evt)
        if self.embeddedBrowser:
            self.fileBrowser.layoutDisplay()
        
    def __currentChanged(self, index):
        """
        Private slot to handle the currentChanged(int) signal.
        
        @param index index of the tab (integer)
        """
        if index > -1:
            browser = self.widget(index)
            if browser is not None:
                browser.layoutDisplay()
        
    def __projectOpened(self):
        """
        Private slot to handle the projectOpened signal.
        """
        self.__projectPropertiesChanged()
        self.setCurrentIndex(0)
        self.__vcsStateChanged(" ")
        
    def __projectClosed(self):
        """
        Private slot to handle the projectClosed signal.
        """
        self.__projectPropertiesChanged()
        if self.embeddedBrowser:
            self.setCurrentWidget(self.fileBrowser)
        else:
            self.setCurrentIndex(0)
        self.__setSourcesIcon()
        self.__vcsStateChanged(" ")
        
    def __newProject(self):
        """
        Private slot to handle the newProject signal.
        """
        self.setCurrentIndex(0)
        self.__projectPropertiesChanged()
        
    def __projectPropertiesChanged(self):
        """
        Private slot to handle the projectPropertiesChanged signal.
        """
        if self.project.isOpen():
            flags = Preferences.getProjectBrowserFlags(
                self.project.getProjectType())
        else:
            flags = AllBrowsersFlag
        
        if flags != self.__currentBrowsersFlags:
            self.__currentBrowsersFlags = flags
            self.__setBrowsersAvailable(flags)
        
        if self.embeddedBrowser:
            endIndex = self.count() - 1
        else:
            endIndex = self.count()
        for index in range(endIndex):
            self.setTabEnabled(index, self.project.isOpen())
        
        self.__setSourcesIcon()
        
    def __setSourcesIcon(self):
        """
        Private method to set the right icon for the sources browser tab.
        """
        if not self.project.isOpen():
            icon = UI.PixmapCache.getIcon("projectSources.png")
        else:
            if self.project.pdata["PROGLANGUAGE"][0] in \
                    ["Python", "Python2", "Python3"]:
                if self.project.pdata["MIXEDLANGUAGE"][0]:
                    icon = UI.PixmapCache.getIcon("projectSourcesPyMixed.png")
                else:
                    icon = UI.PixmapCache.getIcon("projectSourcesPy.png")
            elif self.project.pdata["PROGLANGUAGE"][0] == "Ruby":
                if self.project.pdata["MIXEDLANGUAGE"][0]:
                    icon = UI.PixmapCache.getIcon("projectSourcesRbMixed.png")
                else:
                    icon = UI.PixmapCache.getIcon("projectSourcesRb.png")
            else:
                icon = UI.PixmapCache.getIcon("projectSources.png")
        self.setTabIcon(self.indexOf(self.psBrowser), icon)
        
    def handleEditorChanged(self, fn):
        """
        Public slot to handle the editorChanged signal.
        
        @param fn filename of the changed file (string)
        """
        if Preferences.getProject("FollowEditor"):
            if self.project.isProjectSource(fn):
                self.psBrowser.selectFile(fn)
            elif self.project.isProjectForm(fn):
                self.pfBrowser.selectFile(fn)
            elif self.project.isProjectInterface(fn):
                self.piBrowser.selectFile(fn)
    
    def handleEditorLineChanged(self, fn, lineno):
        """
        Public slot to handle the editorLineChanged signal.
        
        @param fn filename of the changed file (string)
        @param lineno one based line number of the item (integer)
        """
        if Preferences.getProject("FollowEditor") and \
           Preferences.getProject("FollowCursorLine"):
            if self.project.isProjectSource(fn):
                self.psBrowser.selectFileLine(fn, lineno)
    
    def getProjectBrowsers(self):
        """
        Public method to get references to the individual project browsers.
        
        @return list of references to project browsers
        """
        return [self.psBrowser, self.pfBrowser, self.prBrowser,
                self.ptBrowser, self.piBrowser, self.poBrowser]
    
    def getProjectBrowser(self, name):
        """
        Public method to get a reference to the named project browser.
        
        @param name name of the requested project browser (string).
            Valid names are "sources, forms, resources, translations,
            interfaces, others".
        @return reference to the requested browser or None
        """
        if name == "sources":
            return self.psBrowser
        elif name == "forms":
            return self.pfBrowser
        elif name == "resources":
            return self.prBrowser
        elif name == "translations":
            return self.ptBrowser
        elif name == "interfaces":
            return self.piBrowser
        elif name == "others":
            return self.poBrowser
        else:
            return None
    
    def handlePreferencesChanged(self):
        """
        Public slot used to handle the preferencesChanged signal.
        """
        self.__projectPropertiesChanged()
        self.__vcsStateChanged(self.currentVcsStatus)
    
    def __vcsStateChanged(self, state):
        """
        Private slot to handle a change in the vcs state.
        
        @param state new vcs state (string)
        """
        self.currentVcsStatus = state
        if state == " " or state not in self.vcsStatusColorNames:
            self.vcsStatusIndicator.setColor(QColor(Qt.lightGray))
        else:
            self.vcsStatusIndicator.setColor(
                Preferences.getProjectBrowserColour(
                    self.vcsStatusColorNames[state]))
        if state not in self.vcsStatusText:
            self.vcsStatusIndicator.setToolTip(self.trUtf8("unknown status"))
        else:
            self.vcsStatusIndicator.setToolTip(self.vcsStatusText[state])
