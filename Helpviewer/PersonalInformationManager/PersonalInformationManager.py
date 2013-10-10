# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a personal information manager used to complete form
fields.
"""

from PyQt4.QtCore import Qt, QObject
from PyQt4.QtGui import QDialog, QMenu

import Preferences
import UI.PixmapCache


class PersonalInformationManager(QObject):
    """
    Class implementing the personal information manager used to complete form
    fields.
    """
    FullName = 0
    LastName = 1
    FirstName = 2
    Email = 3
    Mobile = 4
    Phone = 5
    Address = 6
    City = 7
    Zip = 8
    State = 9
    Country = 10
    HomePage = 11
    Special1 = 12
    Special2 = 13
    Special3 = 14
    Special4 = 15
    Max = 16
    Invalid = 256
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        super().__init__(parent)
        
        self.__loaded = False
        self.__allInfo = {}
        self.__infoMatches = {}
        self.__translations = {}
        
        self.__view = None
        self.__element = None
    
    def __loadSettings(self):
        """
        Private method to load the settings.
        """
        self.__allInfo[self.FullName] = Preferences.getHelp("PimFullName")
        self.__allInfo[self.LastName] = Preferences.getHelp("PimLastName")
        self.__allInfo[self.FirstName] = Preferences.getHelp("PimFirstName")
        self.__allInfo[self.Email] = Preferences.getHelp("PimEmail")
        self.__allInfo[self.Mobile] = Preferences.getHelp("PimMobile")
        self.__allInfo[self.Phone] = Preferences.getHelp("PimPhone")
        self.__allInfo[self.Address] = Preferences.getHelp("PimAddress")
        self.__allInfo[self.City] = Preferences.getHelp("PimCity")
        self.__allInfo[self.Zip] = Preferences.getHelp("PimZip")
        self.__allInfo[self.State] = Preferences.getHelp("PimState")
        self.__allInfo[self.Country] = Preferences.getHelp("PimCountry")
        self.__allInfo[self.HomePage] = Preferences.getHelp("PimHomePage")
        self.__allInfo[self.Special1] = Preferences.getHelp("PimSpecial1")
        self.__allInfo[self.Special2] = Preferences.getHelp("PimSpecial2")
        self.__allInfo[self.Special3] = Preferences.getHelp("PimSpecial3")
        self.__allInfo[self.Special4] = Preferences.getHelp("PimSpecial4")
        
        self.__translations[self.FullName] = self.trUtf8("Full Name")
        self.__translations[self.LastName] = self.trUtf8("Last Name")
        self.__translations[self.FirstName] = self.trUtf8("First Name")
        self.__translations[self.Email] = self.trUtf8("E-mail")
        self.__translations[self.Mobile] = self.trUtf8("Mobile")
        self.__translations[self.Phone] = self.trUtf8("Phone")
        self.__translations[self.Address] = self.trUtf8("Address")
        self.__translations[self.City] = self.trUtf8("City")
        self.__translations[self.Zip] = self.trUtf8("ZIP Code")
        self.__translations[self.State] = self.trUtf8("State/Region")
        self.__translations[self.Country] = self.trUtf8("Country")
        self.__translations[self.HomePage] = self.trUtf8("Home Page")
        self.__translations[self.Special1] = self.trUtf8("Custom 1")
        self.__translations[self.Special2] = self.trUtf8("Custom 2")
        self.__translations[self.Special3] = self.trUtf8("Custom 3")
        self.__translations[self.Special4] = self.trUtf8("Custom 4")
        
        self.__infoMatches[self.FullName] = ["fullname", "realname"]
        self.__infoMatches[self.LastName] = ["lastname", "surname"]
        self.__infoMatches[self.FirstName] = ["firstname", "name"]
        self.__infoMatches[self.Email] = ["email", "e-mail", "mail"]
        self.__infoMatches[self.Mobile] = ["mobile", "mobilephone"]
        self.__infoMatches[self.Phone] = ["phone", "telephone"]
        self.__infoMatches[self.Address] = ["address"]
        self.__infoMatches[self.City] = ["city"]
        self.__infoMatches[self.Zip] = ["zip"]
        self.__infoMatches[self.State] = ["state", "region"]
        self.__infoMatches[self.Country] = ["country"]
        self.__infoMatches[self.HomePage] = ["homepage", "www"]
        
        self.__loaded = True
    
    def showConfigurationDialog(self):
        """
        Public method to show the configuration dialog.
        """
        from .PersonalDataDialog import PersonalDataDialog
        dlg = PersonalDataDialog()
        if dlg.exec_() == QDialog.Accepted:
            dlg.storeData()
            self.__loadSettings()
    
    def createSubMenu(self, menu, view, hitTestResult):
        """
        Public method to create the personal information sub-menu.
        
        @param menu reference to the main menu (QMenu)
        @param view reference to the view (HelpBrowser)
        @param hitTestResult reference to the hit test result
            (QWebHitTestResult)
        """
        self.__view = view
        self.__element = hitTestResult.element()
        
        if not hitTestResult.isContentEditable():
            return
        
        if not self.__loaded:
            self.__loadSettings()
        
        submenu = QMenu(self.trUtf8("Insert Personal Information"), menu)
        submenu.setIcon(UI.PixmapCache.getIcon("pim.png"))
        
        for key, info in sorted(self.__allInfo.items()):
            if info:
                act = submenu.addAction(
                    self.__translations[key], self.__insertData)
                act.setData(info)
        
        submenu.addSeparator()
        submenu.addAction(self.trUtf8("Edit Personal Information"),
                          self.showConfigurationDialog)
        
        menu.addMenu(submenu)
        menu.addSeparator()
    
    def __insertData(self):
        """
        Private slot to insert the selected personal information.
        """
        act = self.sender()
        if not self.__element or self.__element.isNull() or act is None:
            return
        
        info = act.data()
        info = info.replace('"', '\\"')
        self.__element.evaluateJavaScript(
            'var newVal = this.value.substring(0, this.selectionStart) +'
            ' "{0}" + this.value.substring(this.selectionEnd); this.value ='
            ' newVal;'.format(info))
    
    def viewKeyPressEvent(self, view, evt):
        """
        Public method to handle key press events we are interested in.
        
        @param view reference to the view (HelpBrowser)
        @param evt reference to the key event (QKeyEvent)
        @return flag indicating handling of the event (boolean)
        """
        if view is None:
            return False
        
        isEnter = evt.key() in [Qt.Key_Return, Qt.Key_Enter]
        if not isEnter or evt.modifiers() != Qt.ControlModifier:
            return False
        
        if not self.__loaded:
            self.__loadSettings()
        
        document = view.page().mainFrame().documentElement()
        elements = document.findAll('input[type="text"]')
        
        for element in elements:
            name = element.attribute("name")
            if name == "":
                continue
            
            match = self.__nameMatch(name)
            if match != self.Invalid:
                element.evaluateJavaScript(
                    'this.value = "{0}"'.format(self.__allInfo[match]))
        
        return True
    
    def __nameMatch(self, name):
        """
        Private method to find the information entry for the given field.
        
        @param name name of the form field (string)
        @return value of the information entry (integer)
        """
        for index in range(self.Max):
            if self.__allInfo[index]:
                for n in self.__infoMatches[index]:
                    if name == n or n in name:
                        return index
        
        return self.Invalid
    
    def connectPage(self, page):
        """
        Public method to allow the personal information manager to connect to
        the page.
        
        @param page reference to the web page (HelpWebPage)
        """
        page.loadFinished.connect(self.__pageLoadFinished)
    
    def __pageLoadFinished(self, ok):
        """
        Private slot to handle the completion of a page load.
        
        @param ok flag indicating a successful load (boolean)
        """
        page = self.sender()
        if page is None or not ok:
            return
        
        if not self.__loaded:
            self.__loadSettings()
        
        document = page.mainFrame().documentElement()
        elements = document.findAll('input[type="text"]')
        
        for element in elements:
            name = element.attribute("name")
            if name == "":
                continue
            
            match = self.__nameMatch(name)
            if match != self.Invalid:
                element.setStyleProperty(
                    "-webkit-appearance", "none")
                element.setStyleProperty(
                    "-webkit-box-shadow", "inset 0 0 2px 1px #0000EE")
