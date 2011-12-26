# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a menu to select the user agent string.
"""

from PyQt4.QtCore import QByteArray, QXmlStreamReader
from PyQt4.QtGui import QMenu, QAction, QActionGroup, QInputDialog, QLineEdit

from E5Gui import E5MessageBox

from .UserAgentDefaults import UserAgentDefaults

from Helpviewer.HelpBrowserWV import HelpWebPage

class UserAgentMenu(QMenu):
    """
    Class implementing a menu to select the user agent string.
    """
    def __init__(self, title, parent = None):
        """
        Constructor
        
        @param title title of the menu (string)
        @param parent reference to the parent widget (QWidget)
        """
        QMenu.__init__(self, title, parent)
        
        self.aboutToShow.connect(self.__populateMenu)
    
    def __populateMenu(self):
        """
        Private slot to populate the menu.
        """
        self.aboutToShow.disconnect(self.__populateMenu)
        
        # add default action
        self.__defaultUserAgent = QAction(self)
        self.__defaultUserAgent.setText(self.trUtf8("Default"))
        self.__defaultUserAgent.setCheckable(True)
        self.__defaultUserAgent.triggered[()].connect(self.__switchToDefaultUserAgent)
        self.__defaultUserAgent.setChecked(HelpWebPage().userAgent() == "")
        self.addAction(self.__defaultUserAgent)
        
        # add default extra user agents
        self.__addDefaultActions()
        
        # add other action
        self.addSeparator()
        self.__otherUserAgent = QAction(self)
        self.__otherUserAgent.setText(self.trUtf8("Other..."))
        self.__otherUserAgent.setCheckable(True)
        self.__otherUserAgent.triggered[()].connect(self.__switchToOtherUserAgent)
        self.addAction(self.__otherUserAgent)
        
        usingCustomUserAgent = True
        actionGroup = QActionGroup(self)
        for act in self.actions():
            actionGroup.addAction(act)
            if act.isChecked():
                usingCustomUserAgent = False
        self.__otherUserAgent.setChecked(usingCustomUserAgent)
    
    def __switchToDefaultUserAgent(self):
        """
        Private slot to set the default user agent.
        """
        HelpWebPage().setUserAgent("")
    
    def __switchToOtherUserAgent(self):
        """
        Private slot to set a custom user agent string.
        """
        userAgent, ok = QInputDialog.getText(
            self,
            self.trUtf8("Custom user agent"),
            self.trUtf8("User agent:"),
            QLineEdit.Normal,
            HelpWebPage().userAgent(resolveEmpty = True))
        if ok:
            HelpWebPage().setUserAgent(userAgent)
    
    def __changeUserAgent(self):
        """
        Private slot to change the user agent.
        """
        act = self.sender()
        HelpWebPage().setUserAgent(act.data())
    
    def __addDefaultActions(self):
        """
        Private slot to add the default user agent entries.
        """
        defaultUserAgents = QByteArray(UserAgentDefaults)
        
        currentUserAgentString = HelpWebPage().userAgent()
        xml = QXmlStreamReader(defaultUserAgents)
        while not xml.atEnd():
            xml.readNext()
            if xml.isStartElement() and xml.name() == "separator":
                self.addSeparator()
                continue
            
            if xml.isStartElement() and xml.name() == "useragent":
                attributes = xml.attributes()
                title = attributes.value("description")
                userAgent = attributes.value("useragent")
                
                act = QAction(self)
                act.setText(title)
                act.setData(userAgent)
                act.setToolTip(userAgent)
                act.setCheckable(True)
                act.setChecked(userAgent == currentUserAgentString)
                act.triggered[()].connect(self.__changeUserAgent)
                self.addAction(act)
        
        if xml.hasError():
            E5MessageBox.critical(self,
                self.trUtf8("Parsing default user agents"),
                self.trUtf8("""<p>Error parsing default user agents.</p><p>{0}</p>""")\
                    .format(xml.errorString()))
