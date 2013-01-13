# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog for importing bookmarks from other sources.
"""

import os

from PyQt4.QtCore import pyqtSlot, Qt, QSize
from PyQt4.QtGui import QDialog, QListWidgetItem

from E5Gui import E5FileDialog, E5MessageBox

from .Ui_BookmarksImportDialog import Ui_BookmarksImportDialog

from . import BookmarksImporters

import Utilities
import Globals


class BookmarksImportDialog(QDialog, Ui_BookmarksImportDialog):
    """
    Class implementing a dialog for importing bookmarks from other sources.
    """
    SourcesListIdRole = Qt.UserRole
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        self.sourcesList.setIconSize(QSize(48, 48))
        for icon, displayText, idText in BookmarksImporters.getImporters():
            itm = QListWidgetItem(icon, displayText, self.sourcesList)
            itm.setData(self.SourcesListIdRole, idText)
        
        self.__currentPage = 0
        self.__selectedSource = ""
        self.__topLevelBookmarkNode = None
        self.__sourceFile = ""
        self.__sourceDir = ""
        
        self.pagesWidget.setCurrentIndex(self.__currentPage)
        self.__enableNextButton()
    
    def __enableNextButton(self):
        """
        Private slot to set the enabled state of the next button.
        """
        if self.__currentPage == 0:
            self.nextButton.setEnabled(len(self.sourcesList.selectedItems()) == 1)
        elif self.__currentPage == 1:
            self.nextButton.setEnabled(self.fileEdit.text() != "")
    
    @pyqtSlot()
    def on_sourcesList_itemSelectionChanged(self):
        """
        Private slot to handle changes of the selection of the import source.
        """
        self.__enableNextButton()
    
    @pyqtSlot(str)
    def on_fileEdit_textChanged(self, txt):
        """
        Private slot handling changes of the file to import bookmarks from.
        
        @param txt text of the line edit (string)
        """
        self.__enableNextButton()
    
    @pyqtSlot()
    def on_chooseButton_clicked(self):
        """
        Private slot to choose the bookmarks file or directory.
        """
        if self.__selectedSource == "ie":
            path = E5FileDialog.getExistingDirectory(
                self,
                self.trUtf8("Choose Directory ..."),
                self.__sourceDir,
                E5FileDialog.Options(E5FileDialog.Option(0)))
        else:
            if Globals.isMacPlatform():
                filter = "*{0}".format(os.path.splitext(self.__sourceFile)[1])
            else:
                filter = self.__sourceFile
            path = E5FileDialog.getOpenFileName(
                self,
                self.trUtf8("Choose File ..."),
                self.__sourceDir,
                filter)
        
        if path:
            self.fileEdit.setText(Utilities.toNativeSeparators(path))
    
    @pyqtSlot()
    def on_nextButton_clicked(self):
        """
        Private slot to switch to the next page.
        """
        if self.sourcesList.currentItem() is None:
            return
        
        if self.__currentPage == 0:
            self.__selectedSource = self.sourcesList.currentItem().data(
                self.SourcesListIdRole)
            pixmap, sourceName, self.__sourceFile, info, prompt, self.__sourceDir = \
                BookmarksImporters.getImporterInfo(self.__selectedSource)
            
            self.iconLabel.setPixmap(pixmap)
            self.importingFromLabel.setText(
                self.trUtf8("<b>Importing from {0}</b>").format(sourceName))
            self.fileLabel1.setText(info)
            self.fileLabel2.setText(prompt)
            self.standardDirLabel.setText("<i>{0}</i>".format(self.__sourceDir))
            
            self.nextButton.setText(self.trUtf8("Finish"))
            
            self.__currentPage += 1
            self.pagesWidget.setCurrentIndex(self.__currentPage)
            self.__enableNextButton()
        
        elif self.__currentPage == 1:
            if self.fileEdit.text() == "":
                return
            
            importer = BookmarksImporters.getImporter(self.__selectedSource)
            importer.setPath(self.fileEdit.text())
            if importer.open():
                self.__topLevelBookmarkNode = importer.importedBookmarks()
            if importer.error():
                E5MessageBox.critical(self,
                    self.trUtf8("Error importing bookmarks"),
                    importer.errorString())
                return
            
            self.accept()
    
    @pyqtSlot()
    def on_cancelButton_clicked(self):
        """
        Slot documentation goes here.
        """
        self.reject()
    
    def getImportedBookmarks(self):
        """
        Public method to get the imported bookmarks.
        
        @return top level bookmark (BookmarkNode)
        """
        return self.__topLevelBookmarkNode
