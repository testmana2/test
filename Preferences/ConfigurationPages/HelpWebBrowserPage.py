# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Help web browser configuration page.
"""

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtWebKit import QWebSettings
from PyQt4.QtNetwork import QNetworkRequest

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_HelpWebBrowserPage import Ui_HelpWebBrowserPage

import Preferences

class HelpWebBrowserPage(ConfigurationPageBase, Ui_HelpWebBrowserPage):
    """
    Class implementing the Help web browser configuration page.
    """
    def __init__(self, configDialog):
        """
        Constructor
        
        @param configDialog reference to the configuration dialog (ConfigurationDialog)
        """
        ConfigurationPageBase.__init__(self)
        self.setupUi(self)
        self.setObjectName("HelpWebBrowserPage")
        
        mw = configDialog.parent().parent()
        if hasattr(mw, "helpWindow") and mw.helpWindow is not None:
            self.__helpWindow = mw.helpWindow
        elif hasattr(mw, "currentBrowser"):
            self.__helpWindow = mw
        else:
            self.__helpWindow = None
        self.setCurrentPageButton.setEnabled(self.__helpWindow is not None)
        
        defaultSchemes = ["file://", "http://", "https://", "qthelp://"]
        self.defaultSchemeCombo.addItems(defaultSchemes)
        
        # set initial values
        self.singleHelpWindowCheckBox.setChecked(
            Preferences.getHelp("SingleHelpWindow"))
        self.saveGeometryCheckBox.setChecked(
            Preferences.getHelp("SaveGeometry"))
        self.webSuggestionsCheckBox.setChecked(
            Preferences.getHelp("WebSearchSuggestions"))
        self.showTabPreviews.setChecked(
            Preferences.getHelp("ShowPreview"))
        
        self.javaCheckBox.setChecked(
            Preferences.getHelp("JavaEnabled"))
        self.javaScriptCheckBox.setChecked(
            Preferences.getHelp("JavaScriptEnabled"))
        self.jsOpenWindowsCheckBox.setChecked(
            Preferences.getHelp("JavaScriptCanOpenWindows"))
        self.jsClipboardCheckBox.setChecked(
            Preferences.getHelp("JavaScriptCanAccessClipboard"))
        self.pluginsCheckBox.setChecked(
            Preferences.getHelp("PluginsEnabled"))
        
        self.savePasswordsCheckBox.setChecked(
            Preferences.getHelp("SavePasswords"))
        if hasattr(QWebSettings, "DnsPrefetchEnabled"):
            self.dnsPrefetchCheckBox.setChecked(
            Preferences.getHelp("DnsPrefetchEnabled"))
        else:
            self.dnsPrefetchCheckBox.setEnabled(False)
        
        self.diskCacheCheckBox.setChecked(
            Preferences.getHelp("DiskCacheEnabled"))
        self.cacheSizeSpinBox.setValue(
            Preferences.getHelp("DiskCacheSize"))
        cachePolicy = Preferences.getHelp("CachePolicy")
        if cachePolicy == QNetworkRequest.PreferNetwork:
            self.cacheKeepButton.setChecked(True)
        elif cachePolicy == QNetworkRequest.PreferCache:
            self.cachePreferButton.setChecked(True)
        elif cachePolicy == QNetworkRequest.AlwaysCache:
            self.cacheOfflineButton.setChecked(True)
        
        self.printBackgroundsCheckBox.setChecked(
            Preferences.getHelp("PrintBackgrounds"))
        
        self.startupCombo.setCurrentIndex(
            Preferences.getHelp("StartupBehavior"))
        self.homePageEdit.setText(
            Preferences.getHelp("HomePage"))
        
        self.defaultSchemeCombo.setEditText(
            Preferences.getHelp("DefaultScheme"))
        
        historyLimit = Preferences.getHelp("HistoryLimit")
        idx = 0
        if historyLimit == 1:
           idx = 0
        elif historyLimit == 7:
           idx = 1 
        elif historyLimit == 14:
            idx = 2
        elif historyLimit == 30:
            idx = 3
        elif historyLimit == 365:
            idx = 4
        elif historyLimit == -1:
            idx = 5
        elif historyLimit == -2:
            idx = 6
        else:
            idx = 5
        self.expireHistory.setCurrentIndex(idx)
        
    def save(self):
        """
        Public slot to save the Help Viewers configuration.
        """
        Preferences.setHelp("SingleHelpWindow",
            self.singleHelpWindowCheckBox.isChecked())
        Preferences.setHelp("SaveGeometry",
            self.saveGeometryCheckBox.isChecked())
        Preferences.setHelp("WebSearchSuggestions",
            self.webSuggestionsCheckBox.isChecked())
        Preferences.setHelp("ShowPreview", 
            self.showTabPreviews.isChecked())
        
        Preferences.setHelp("JavaEnabled",
            self.javaCheckBox.isChecked())
        Preferences.setHelp("JavaScriptEnabled",
            self.javaScriptCheckBox.isChecked())
        Preferences.setHelp("JavaScriptCanOpenWindows",
            self.jsOpenWindowsCheckBox.isChecked())
        Preferences.setHelp("JavaScriptCanAccessClipboard",
            self.jsClipboardCheckBox.isChecked())
        Preferences.setHelp("PluginsEnabled", 
            self.pluginsCheckBox.isChecked())
        
        Preferences.setHelp("SavePasswords", 
            self.savePasswordsCheckBox.isChecked())
        if self.dnsPrefetchCheckBox.isEnabled():
            Preferences.setHelp("DnsPrefetchEnabled", 
                self.dnsPrefetchCheckBox.isChecked())
        
        Preferences.setHelp("DiskCacheEnabled",
            self.diskCacheCheckBox.isChecked())
        Preferences.setHelp("DiskCacheSize",
            self.cacheSizeSpinBox.value())
        if self.cacheKeepButton.isChecked():
            Preferences.setHelp("CachePolicy", 
                QNetworkRequest.PreferNetwork)
        elif self.cachePreferButton.isChecked():
            Preferences.setHelp("CachePolicy", 
                QNetworkRequest.PreferCache)
        elif self.cacheOfflineButton.isChecked():
            Preferences.setHelp("CachePolicy", 
                QNetworkRequest.AlwaysCache)
        
        Preferences.setHelp("PrintBackgrounds",
            self.printBackgroundsCheckBox.isChecked())
        
        Preferences.setHelp("StartupBehavior", 
            self.startupCombo.currentIndex())
        Preferences.setHelp("HomePage", 
            self.homePageEdit.text())
        
        Preferences.setHelp("DefaultScheme", 
            self.defaultSchemeCombo.currentText())
        
        idx = self.expireHistory.currentIndex()
        if idx == 0:
            historyLimit = 1
        elif idx == 1:
            historyLimit = 7
        elif idx == 2:
            historyLimit = 14
        elif idx == 3:
            historyLimit = 30
        elif idx == 4:
            historyLimit = 365
        elif idx == 5:
            historyLimit = -1
        elif idx == 6:
            historyLimit = -2
        Preferences.setHelp("HistoryLimit", historyLimit)
    
    @pyqtSlot()
    def on_setCurrentPageButton_clicked(self):
        """
        Private slot to set the current page as the home page.
        """
        url = self.__helpWindow.currentBrowser().url()
        self.homePageEdit.setText(bytes(url.toEncoded()).decode())
    
    @pyqtSlot()
    def on_defaultHomeButton_clicked(self):
        """
        Private slot to set the default home page.
        """
        self.homePageEdit.setText(Preferences.Prefs.helpDefaults["HomePage"])
    
def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    """
    page = HelpWebBrowserPage(dlg)
    return page
