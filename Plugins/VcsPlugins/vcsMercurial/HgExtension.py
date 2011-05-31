# -*- coding: utf-8 -*-

# Copyright (c) 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the base class for Mercurial extension interfaces.
"""

from PyQt4.QtCore import QObject


class HgExtension(QObject):
    """
    Class implementing the base class for Mercurial extension interfaces.
    """
    def __init__(self, vcs):
        """
        Constructor
        
        @param vcs reference to the Mercurial vcs object
        """
        QObject.__init__(self, vcs)
        
        self.vcs = vcs
    
    def shutdown(self):
        """
        Public method used to shutdown the extension interface.
        
        The method of this base class does nothing.
        """
        pass
