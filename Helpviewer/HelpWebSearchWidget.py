# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a web search widget for the web browser.
"""

import os
import imp

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import QWebSettings

import UI.PixmapCache

import Preferences

from E4Gui.E4LineEdit import E4LineEdit

from .OpenSearch.OpenSearchManager import OpenSearchManager
from .OpenSearch.OpenSearchEngineAction import OpenSearchEngineAction

class HelpWebSearchWidget(QWidget):
    """
    Class implementing a web search widget for the web browser.
    
    @signal search(url) emitted when the search should be done
    """
    _openSearchManager = None
    
    def __init__(self, parent = None):
        """
        Constructor
        
        @param inactiveText text to be shown on inactivity (string)
        @param parent reference to the parent widget (QWidget)
        """
        QWidget.__init__(self, parent)
        
        self.mw = parent
        
        self.connect(HelpWebSearchWidget.openSearchManager(), 
                     SIGNAL("currentEngineChanged()"), 
                     self.__currentEngineChanged)
        self.__currentEngine = ""
        
        self.__layout = QHBoxLayout(self)
        self.__layout.setMargin(0)
        self.__layout.setSpacing(0)
        self.setLayout(self.__layout)
        
        self.__enginesMenu = QMenu(self)
        
        self.__engineButton = QToolButton(self)
        self.__engineButton.setPopupMode(QToolButton.InstantPopup)
        self.__engineButton.setMenu(self.__enginesMenu)
        self.__layout.addWidget(self.__engineButton)
        
        self.__searchButton = QToolButton(self)
        self.__searchButton.setIcon(UI.PixmapCache.getIcon("webSearch.png"))
        self.__layout.addWidget(self.__searchButton)
        
        self.__searchEdit = E4LineEdit(parent = self)
        self.__layout.addWidget(self.__searchEdit)
        
        self.__clearButton = QToolButton(self)
        self.__clearButton.setIcon(UI.PixmapCache.getIcon("clearLeft.png"))
        self.__layout.addWidget(self.__clearButton)
        
        self.__model = QStandardItemModel(self)
        self.__completer = QCompleter()
        self.__completer.setModel(self.__model)
        self.__completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.__completer.setWidget(self.__searchEdit)
        
        self.connect(self.__searchButton, SIGNAL("clicked()"), self.__searchButtonClicked)
        self.connect(self.__searchEdit, SIGNAL("textEdited(const QString&)"), 
                     self.__textEdited)
        self.connect(self.__clearButton, SIGNAL("clicked()"), self.__searchEdit.clear)
        self.connect(self.__searchEdit, SIGNAL("returnPressed()"), self.__searchNow)
        self.connect(self.__completer, SIGNAL("activated(const QModelIndex &)"), 
                     self.__completerActivated)
        self.connect(self.__completer, SIGNAL("highlighted(const QModelIndex &)"), 
                     self.__completerHighlighted)
        self.connect(self.__enginesMenu, SIGNAL("aboutToShow()"), self.__showEnginesMenu)
        
        self.__suggestionsItem = None
        self.__suggestions = []
        self.__suggestTimer = None
        self.__suggestionsEnabled = Preferences.getHelp("WebSearchSuggestions")
        
        self.__recentSearchesItem = None
        self.__recentSearches = []
        self.__maxSavedSearches = 10
        
        self.__engine = None
        self.__loadSearches()
        self.__setupCompleterMenu()
        self.__currentEngineChanged()
    
    def __searchNow(self):
        """
        Private slot to perform the web search.
        """
        searchText = self.__searchEdit.text()
        if not searchText:
            return
        
        globalSettings = QWebSettings.globalSettings()
        if not globalSettings.testAttribute(QWebSettings.PrivateBrowsingEnabled):
            if searchText in self.__recentSearches:
                self.__recentSearches.remove(searchText)
            self.__recentSearches.insert(0, searchText)
            if len(self.__recentSearches) > self.__maxSavedSearches:
                self.__recentSearches = self.__recentSearches[:self.__maxSavedSearches]
            self.__setupCompleterMenu()
        
        url = HelpWebSearchWidget.openSearchManager()\
                                 .currentEngine()\
                                 .searchUrl(searchText)
        self.emit(SIGNAL("search"), url)
    
    def __setupCompleterMenu(self):
        """
        Private method to create the completer menu.
        """
        if not self.__suggestions or \
           (self.__model.rowCount() > 0 and \
            self.__model.item(0) != self.__suggestionsItem):
            self.__model.clear()
            self.__suggestionsItem = None
        else:
            self.__model.removeRows(1, self.__model.rowCount() - 1)
        
        boldFont = QFont()
        boldFont.setBold(True)
        
        if self.__suggestions:
            if self.__model.rowCount() == 0:
                if not self.__suggestionsItem:
                    self.__suggestionsItem = QStandardItem(self.trUtf8("Suggestions"))
                    self.__suggestionsItem.setFont(boldFont)
                self.__model.appendRow(self.__suggestionsItem)
            
            for suggestion in self.__suggestions:
                self.__model.appendRow(QStandardItem(suggestion))
        
        if not self.__recentSearches:
            self.__recentSearchesItem = QStandardItem(self.trUtf8("No Recent Searches"))
            self.__recentSearchesItem.setFont(boldFont)
            self.__model.appendRow(self.__recentSearchesItem)
        else:
            self.__recentSearchesItem = QStandardItem(self.trUtf8("Recent Searches"))
            self.__recentSearchesItem.setFont(boldFont)
            self.__model.appendRow(self.__recentSearchesItem)
            for recentSearch in self.__recentSearches:
                self.__model.appendRow(QStandardItem(recentSearch))
        
        view = self.__completer.popup()
        view.setFixedHeight(
            view.sizeHintForRow(0) * self.__model.rowCount() + view.frameWidth() * 2)
        
        self.__searchButton.setEnabled(
            bool(self.__recentSearches or self.__suggestions))
    
    def __completerActivated(self, index):
        """
        Private slot handling the selection of an entry from the completer.
        
        @param index index of the item (QModelIndex)
        """
        if self.__suggestionsItem and \
           self.__suggestionsItem.index().row() == index.row():
            return
        
        if self.__recentSearchesItem and \
           self.__recentSearchesItem.index().row() == index.row():
            return
        
        self.__searchNow()
    
    def __completerHighlighted(self, index):
        """
        Private slot handling the highlighting of an entry of the completer.
        
        @param index index of the item (QModelIndex)
        """
        if self.__suggestionsItem and \
           self.__suggestionsItem.index().row() == index.row():
            return False
        
        if self.__recentSearchesItem and \
           self.__recentSearchesItem.index().row() == index.row():
            return False
        
        self.__searchEdit.setText(index.data())
        return True
    
    def __textEdited(self, txt):
        """
        Private slot to handle changes of the search text.
        
        @param txt search text (string)
        """
        if self.__suggestionsEnabled:
            if self.__suggestTimer is None:
                self.__suggestTimer = QTimer(self)
                self.__suggestTimer.setSingleShot(True)
                self.__suggestTimer.setInterval(200)
                self.connect(self.__suggestTimer, SIGNAL("timeout()"), 
                             self.__getSuggestions)
            self.__suggestTimer.start()
        else:
            self.__completer.setCompletionPrefix(txt)
            self.__completer.complete()
    
    def __getSuggestions(self):
        """
        Private slot to get search suggestions from the configured search engine.
        """
        searchText = self.__searchEdit.text()
        if searchText:
            HelpWebSearchWidget.openSearchManager()\
                               .currentEngine()\
                               .requestSuggestions(searchText)
    
    def __newSuggestions(self, suggestions):
        """
        Private slot to receive a new list of suggestions.
        
        @param suggestions list of suggestions (list of strings)
        """
        self.__suggestions = suggestions
        self.__setupCompleterMenu()
        self.__completer.complete()
    
    def __showEnginesMenu(self):
        """
        Private slot to handle the display of the engines menu.
        """
        self.__enginesMenu.clear()
        
        osm = HelpWebSearchWidget.openSearchManager()
        engineNames = osm.allEnginesNames()
        for engineName in engineNames:
            engine = osm.engine(engineName)
            action = OpenSearchEngineAction(engine, self.__enginesMenu)
            action.setData(engineName)
            self.connect(action, SIGNAL("triggered()"), self.__changeCurrentEngine)
            self.__enginesMenu.addAction(action)
            
            if osm.currentEngineName() == engineName:
                action.setCheckable(True)
                action.setChecked(True)
        
        ct = self.mw.currentBrowser()
        linkedResources = ct.linkedResources("search")
        
        if len(linkedResources) > 0:
            self.__enginesMenu.addSeparator()
        
        for linkedResource in linkedResources:
            url = QUrl(linkedResource.href)
            title = linkedResource.title
            mimetype = linkedResource.type_
            
            if mimetype != "application/opensearchdescription+xml":
                continue
            if url.isEmpty():
                continue
            
            if url.isRelative():
                url = ct.url().resolved(url)
            
            if not title:
                if not ct.title():
                    title = url.host()
                else:
                    title = ct.title()
            
            action = self.__enginesMenu.addAction(self.trUtf8("Add '{0}'").format(title), 
                                                  self.__addEngineFromUrl)
            action.setData(url)
            action.setIcon(ct.icon())
        
        self.__enginesMenu.addSeparator()
        self.__enginesMenu.addAction(self.mw.searchEnginesAction())
        
        if self.__recentSearches:
            self.__enginesMenu.addAction(self.trUtf8("Clear Recent Searches"), 
                                         self.clear)
    
    def __changeCurrentEngine(self):
        """
        Private slot to handle the selection of a search engine.
        """
        action = self.sender()
        if action is not None:
            name = action.data()
            HelpWebSearchWidget.openSearchManager().setCurrentEngineName(name)
    
    def __addEngineFromUrl(self):
        """
        Private slot to add a search engine given it's URL.
        """
        action = self.sender()
        if action is not None:
            url = action.data()
            if not isinstance(url, QUrl):
                return 
            
            HelpWebSearchWidget.openSearchManager().addEngine(url)
    
    def __searchButtonClicked(self):
        """
        Private slot to show the search menu via the search button.
        """
        self.__setupCompleterMenu()
        self.__completer.complete()
    
    def clear(self):
        """
        Public method to clear all private data.
        """
        self.__recentSearches = []
        self.__setupCompleterMenu()
        self.__searchEdit.clear()
        self.clearFocus()
    
    def preferencesChanged(self):
        """
        Public method to handle the change of preferences.
        """
        self.__suggestionsEnabled = Preferences.getHelp("WebSearchSuggestions")
        if not self.__suggestionsEnabled:
            self.__suggestions = []
            self.__setupCompleterMenu()
    
    def saveSearches(self):
        """
        Public method to save the recently performed web searches.
        """
        Preferences.Prefs.settings.setValue('Help/WebSearches',
            self.__recentSearches)
    
    def __loadSearches(self):
        """
        Public method to load the recently performed web searches.
        """
        searches = Preferences.Prefs.settings.value('Help/WebSearches')
        if searches is not None:
            self.__recentSearches = searches
    
    @classmethod
    def openSearchManager(cls):
        """
        Class method to get a reference to the opensearch manager object.
        
        @return reference to the opensearch manager object (OpenSearchManager)
        """
        if cls._openSearchManager is None:
            cls._openSearchManager = OpenSearchManager()
        return cls._openSearchManager
    
    def __currentEngineChanged(self):
        """
        Private slot to track a change of the current search engine.
        """
        osm = HelpWebSearchWidget.openSearchManager()
        if osm.engineExists(self.__currentEngine):
            oldEngine = osm.engine(self.__currentEngine)
            self.disconnect(oldEngine, SIGNAL("imageChanged()"), 
                            self.__engineImageChanged)
            if self.__suggestionsEnabled:
                self.disconnect(oldEngine, SIGNAL("suggestions(const QStringList&)"), 
                                self.__newSuggestions)
        
        newEngine = osm.currentEngine()
        if newEngine.networkAccessManager() is None:
            newEngine.setNetworkAccessManager(self.mw.networkAccessManager())
        self.connect(newEngine, SIGNAL("imageChanged()"), 
                     self.__engineImageChanged)
        if self.__suggestionsEnabled:
            self.connect(newEngine, SIGNAL("suggestions(const QStringList&)"), 
                         self.__newSuggestions)
        
        self.__searchEdit.setInactiveText(osm.currentEngineName())
        self.__currentEngine = osm.currentEngineName()
        self.__engineButton.setIcon(
            QIcon(QPixmap.fromImage(osm.currentEngine().image())))
        self.__suggestions = []
        self.__setupCompleterMenu()
    
    def __engineImageChanged(self):
        """
        Private slot to handle a change of the current search engine icon.
        """
        osm = HelpWebSearchWidget.openSearchManager()
        self.__engineButton.setIcon(
            QIcon(QPixmap.fromImage(osm.currentEngine().image())))
