# -*- coding: utf-8 -*-

# Copyright (c) 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a previewer widget for Qt style sheet files.
"""

import os

from PyQt4.QtGui import QWidget, QMenu

from .Ui_PreviewerQSS import Ui_PreviewerQSS

import Preferences


class PreviewerQSS(QWidget, Ui_PreviewerQSS):
    """
    Class implementing a previewer widget for Qt style sheet files.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        # menu for toolbutton
        self.__toolButtonMenu = QMenu(self);
        self.__toolButtonMenu.addAction("Item1")
        self.__toolButtonMenu.addSeparator()
        self.__toolButtonMenu.addAction("Item2")
        self.toolButton.setMenu(self.__toolButtonMenu)
        
        # TODO: some more initialisation
    
    def processEditor(self, editor=None):
        """
        Private slot to process an editor's text.
        
        @param editor editor to be processed (Editor)
        """
        if editor is not None:
            fn = editor.getFileName()
            
            if fn:
                extension = os.path.normcase(os.path.splitext(fn)[1][1:])
            else:
                extension = ""
            if extension in \
                    Preferences.getEditor("PreviewQssFileNameExtensions"):
                styleSheet = editor.text()
                if styleSheet:
                    self.scrollAreaWidgetContents.setStyleSheet(styleSheet)
                else:
                    self.scrollAreaWidgetContents.setStyleSheet("")
                self.toolButton.menu().setStyleSheet(
                    self.scrollAreaWidgetContents.styleSheet())
