# -*- coding: utf-8 -*-

# Copyright (c) 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to select the action to be performed on the bookmark.
"""

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QDialog

from .Ui_BookmarkActionSelectionDialog import Ui_BookmarkActionSelectionDialog

import Helpviewer.HelpWindow

import UI.PixmapCache


class BookmarkActionSelectionDialog(QDialog, Ui_BookmarkActionSelectionDialog):
    """
    Class implementing a dialog to select the action to be performed on the bookmark.
    """
    Undefined = -1
    AddBookmark = 0
    EditBookmark = 1
    AddSpeeddial = 2
    RemoveSpeeddial = 3
    
    def __init__(self, url, parent=None):
        """
        Constructor
        
        @param url URL to be worked on (QUrl)
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        self.__action = self.Undefined
        
        self.icon.setPixmap(UI.PixmapCache.getPixmap("bookmark32.png"))
        
        if Helpviewer.HelpWindow.HelpWindow.bookmarksManager()\
           .bookmarkForUrl(url) is None:
            self.__bmAction = self.AddBookmark
            self.bookmarkPushButton.setText(self.trUtf8("Add Bookmark"))
        else:
            self.__bmAction = self.EditBookmark
            self.bookmarkPushButton.setText(self.trUtf8("Edit Bookmark"))
        
        if Helpviewer.HelpWindow.HelpWindow.speedDial().pageForUrl(url).url:
            self.__sdAction = self.RemoveSpeeddial
            self.speeddialPushButton.setText(self.trUtf8("Remove from Speed Dial"))
        else:
            self.__sdAction = self.AddSpeeddial
            self.speeddialPushButton.setText(self.trUtf8("Add to Speed Dial"))
    
    @pyqtSlot()
    def on_bookmarkPushButton_clicked(self):
        """
        Private slot handling selection of a bookmark action.
        """
        self.__action = self.__bmAction
        self.accept()
    
    @pyqtSlot()
    def on_speeddialPushButton_clicked(self):
        """
        Private slot handling selection of a speed dial action.
        """
        self.__action = self.__sdAction
        self.accept()
    
    def getAction(self):
        """
        Public method to get the selected action.
        """
        return self.__action
