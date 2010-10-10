# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the label to show the web site icon.
"""

from PyQt4.QtCore import Qt, QPoint, QUrl, QMimeData
from PyQt4.QtGui import QLabel, QApplication, QDrag

import Helpviewer.HelpWindow

class FavIconLabel(QLabel):
    """
    Class implementing the label to show the web site icon.
    """
    def __init__(self, parent = None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        QLabel.__init__(self, parent)
        
        self.__browser = None
        self.__dragStartPos = QPoint()
        
        self.setFocusPolicy(Qt.NoFocus)
        self.setCursor(Qt.ArrowCursor)
        self.setMinimumSize(16, 16)
        self.resize(16, 16)
        
        self.__browserIconChanged()
    
    def __browserIconChanged(self):
        """
        Private slot to set the icon.
        """
        url = QUrl()
        if self.__browser:
            url = self.__browser.url()
        self.setPixmap(Helpviewer.HelpWindow.HelpWindow.icon(url).pixmap(16, 16))
    
    def setBrowser(self, browser):
        """
        Public method to set the browser connection.
        
        @param browser reference to the browser widegt (HelpBrowser)
        """
        self.__browser = browser
        self.__browser.loadFinished.connect(self.__browserIconChanged)
        self.__browser.iconChanged.connect(self.__browserIconChanged)
    
    def mousePressEvent(self, evt):
        """
        Protected method to handle mouse press events.
        
        @param evt reference to the mouse event (QMouseEvent)
        """
        if evt.button() == Qt.LeftButton:
            self.__dragStartPos = evt.pos()
        QLabel.mousePressEvent(self, evt)
    
    def mouseMoveEvent(self, evt):
        """
        Protected method to handle mouse move events.
        
        @param evt reference to the mouse event (QMouseEvent)
        """
        if evt.button() == Qt.LeftButton and \
           (evt.pos() - self.__dragStartPos).manhattanLength() > \
                QApplication.startDragDistance() and \
           self.__browser is not None:
            drag = QDrag(self)
            mimeData = QMimeData()
            title = self.__browser.title()
            if title == "":
                title = str(self.__browser.url().toEncoded(), encoding = "utf-8")
            mimeData.setText(title)
            mimeData.setUrls([self.__browser.url()])
            p = self.pixmap()
            if p:
                drag.setPixmap(p)
            drag.setMimeData(mimeData)
            drag.exec_()