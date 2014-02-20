# -*- coding: utf-8 -*-

# Copyright (c) 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the shelve extension interface.
"""

from ..HgExtension import HgExtension
##from ..HgDialog import HgDialog


class Shelve(HgExtension):
    """
    Class implementing the shelve extension interface.
    """
    def __init__(self, vcs):
        """
        Constructor
        
        @param vcs reference to the Mercurial vcs object
        """
        super().__init__(vcs)
    
    def shutdown(self):
        """
        Public method used to shutdown the shelve interface.
        """
