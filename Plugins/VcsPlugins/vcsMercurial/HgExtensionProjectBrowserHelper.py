# -*- coding: utf-8 -*-

# Copyright (c) 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the project browser helper base for Mercurial extension
interfaces.
"""

from PyQt4.QtCore import QObject


class HgExtensionProjectBrowserHelper(QObject):
    """
    Class implementing the project browser helper base for Mercurial extension
    interfaces.
    
    Note: The methods initMenus() and menuTitle() have to be reimplemented by
    derived classes.
    """
    def __init__(self, vcsObject, browserObject, projectObject):
        """
        Constructor
        
        @param vcsObject reference to the vcs object
        @param browserObject reference to the project browser object
        @param projectObject reference to the project object
        """
        super().__init__()
        
        self.vcs = vcsObject
        self.browser = browserObject
        self.project = projectObject
    
    def initMenus(self):
        """
        Public method to generate the extension menus.
        
        Note: Derived class must implement this method.
        
        @ireturn dictionary of populated menu (dict of QMenu). The dict
            must have the keys 'mainMenu', 'multiMenu', 'backMenu', 'dirMenu'
            and 'dirMultiMenu'. 
        @exception NotImplementedError raised if the class has not been
            reimplemented
        """
        raise NotImplementedError
    
    def menuTitle(self):
        """
        Public method to get the menu title.
        
        Note: Derived class must implement this method.
        
        @ireturn title of the menu (string)
        @exception NotImplementedError raised if the class has not been
            reimplemented
        """
        raise NotImplementedError
