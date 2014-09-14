# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a scheme access handler for Python resources.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QFile, QByteArray

from .SchemeAccessHandler import SchemeAccessHandler


class EricAccessHandler(SchemeAccessHandler):
    """
    Class implementing a scheme access handler for Python resources.
    """
    _homePage = None
    _speedDialPage = None
    
    def createRequest(self, op, request, outgoingData=None):
        """
        Public method to create a request.
        
        @param op the operation to be performed
            (QNetworkAccessManager.Operation)
        @param request reference to the request object (QNetworkRequest)
        @param outgoingData reference to an IODevice containing data to be sent
            (QIODevice)
        @return reference to the created reply object (QNetworkReply)
        """
        from .NetworkReply import NetworkReply
        from .NetworkProtocolUnknownErrorReply import \
            NetworkProtocolUnknownErrorReply

        if request.url().toString() == "eric:home":
            return NetworkReply(request, self.__createHomePage(),
                                "text/html", self.parent())
        elif request.url().toString() == "eric:speeddial":
            return NetworkReply(request, self.__createSpeedDialPage(),
                                "text/html", self.parent())
        
        return NetworkProtocolUnknownErrorReply("eric", self.parent())
    
    def __createHomePage(self):
        """
        Private method to create the Home page.
        
        @return prepared home page (QByteArray)
        """
        if self._homePage is None:
            htmlFile = QFile(":/html/startPage.html")
            htmlFile.open(QFile.ReadOnly)
            html = htmlFile.readAll()
            
            html.replace("@IMAGE@", "qrc:icons/ericWeb32.png")
            html.replace("@FAVICON@", "qrc:icons/ericWeb16.png")
            
            self._homePage = html
        
        return QByteArray(self._homePage)
    
    def __createSpeedDialPage(self):
        """
        Private method to create the Speeddial page.
        
        @return prepared speeddial page (QByteArray)
        """
        if self._speedDialPage is None:
            htmlFile = QFile(":/html/speeddialPage.html")
            htmlFile.open(QFile.ReadOnly)
            html = htmlFile.readAll()
            
            html.replace("@FAVICON@", "qrc:icons/ericWeb16.png")
            html.replace("@IMG_PLUS@", "qrc:icons/plus.png")
            html.replace("@IMG_CLOSE@", "qrc:icons/close.png")
            html.replace("@IMG_EDIT@", "qrc:icons/edit.png")
            html.replace("@IMG_RELOAD@", "qrc:icons/reload.png")
            html.replace("@IMG_SETTINGS@", "qrc:icons/setting.png")
            html.replace("@LOADING-IMG@", "qrc:icons/loading.gif")
            html.replace("@BOX-BORDER@", "qrc:icons/box-border-small.png")
            
            html.replace("@JQUERY@", "qrc:javascript/jquery.js")
            html.replace("@JQUERY-UI@", "qrc:javascript/jquery-ui.js")
            
            html.replace("@SITE-TITLE@", self.tr("Speed Dial"))
            html.replace("@URL@", self.tr("URL"))
            html.replace("@TITLE@", self.tr("Title"))
            html.replace("@APPLY@", self.tr("Apply"))
            html.replace("@NEW-PAGE@", self.tr("New Page"))
            html.replace("@TITLE-EDIT@", self.tr("Edit"))
            html.replace("@TITLE-REMOVE@", self.tr("Remove"))
            html.replace("@TITLE-RELOAD@", self.tr("Reload"))
            html.replace(
                "@TITLE-FETCHTITLE@", self.tr("Load title from page"))
            html.replace(
                "@SETTINGS-TITLE@", self.tr("Speed Dial Settings"))
            html.replace("@ADD-TITLE@", self.tr("Add New Page"))
            html.replace(
                "@TXT_NRROWS@", self.tr("Maximum pages in a row:"))
            html.replace("@TXT_SDSIZE@", self.tr("Change size of pages:"))
            
            self._speedDialPage = html
        
        import Helpviewer.HelpWindow
        html = QByteArray(self._speedDialPage)
        dial = Helpviewer.HelpWindow.HelpWindow.speedDial()
        
        html.replace("@INITIAL-SCRIPT@", dial.initialScript())
        html.replace("@ROW-PAGES@", str(dial.pagesInRow()))
        html.replace("@SD-SIZE@", str(dial.sdSize()))
        
        return html
