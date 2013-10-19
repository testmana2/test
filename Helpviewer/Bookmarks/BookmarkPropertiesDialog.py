# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show and edit bookmark properties.
"""

from PyQt4.QtGui import QDialog

from .Ui_BookmarkPropertiesDialog import Ui_BookmarkPropertiesDialog


class BookmarkPropertiesDialog(QDialog, Ui_BookmarkPropertiesDialog):
    """
    Class implementing a dialog to show and edit bookmark properties.
    """
    def __init__(self, node, parent=None):
        """
        Constructor
        
        @param node reference to the bookmark (BookmarkNode)
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        from .BookmarkNode import BookmarkNode
        self.__node = node
        if self.__node.type() == BookmarkNode.Folder:
            self.addressLabel.hide()
            self.addressEdit.hide()
        
        self.nameEdit.setText(self.__node.title)
        self.descriptionEdit.setPlainText(self.__node.desc)
        self.addressEdit.setText(self.__node.url)
    
    def accept(self):
        """
        Public slot handling the acceptance of the dialog.
        """
        from .BookmarkNode import BookmarkNode
        
        if (self.__node.type() == BookmarkNode.Bookmark and
            not self.addressEdit.text()) or \
           not self.nameEdit.text():
            super().accept()
            return
        
        import Helpviewer.HelpWindow
        bookmarksManager = Helpviewer.HelpWindow.HelpWindow.bookmarksManager()
        title = self.nameEdit.text()
        if title != self.__node.title:
            bookmarksManager.setTitle(self.__node, title)
        if self.__node.type() == BookmarkNode.Bookmark:
            url = self.addressEdit.text()
            if url != self.__node.url:
                bookmarksManager.setUrl(self.__node, url)
        description = self.descriptionEdit.toPlainText()
        if description != self.__node.desc:
            self.__node.desc = description
            bookmarksManager.setNodeChanged(self.__node)
        
        super().accept()
