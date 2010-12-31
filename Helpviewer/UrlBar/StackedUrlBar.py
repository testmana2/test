# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a widget to stack url bars.
"""

from PyQt4.QtGui import QStackedWidget, QSizePolicy

class StackedUrlBar(QStackedWidget):
    """
    Class implementing a widget to stack url bars.
    """
    def __init__(self, parent = None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        QStackedWidget.__init__(self, parent)
        
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(6)
        sizePolicy.setVerticalStretch(0)
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(200, 22)
    
    def currentUrlBar(self):
        """
        Public method to get a reference to the current url bar.
        
        @return reference to the current url bar (UrlBar)
        """
        return self.urlBar(self.currentIndex())
    
    def urlBar(self, index):
        """
        Public method to get a reference to the url bar for a given index.
        
        @return reference to the url bar for the given index (UrlBar)
        """
        return self.widget(index)
    
    def moveBar(self, from_, to_):
        """
        Public slot to move a url bar.
        
        @param from_ index of url bar to be moved (integer)
        @param to_ into to move the url bar to (integer)
        """
        fromBar = self.widget(from_)
        self.removeWidget(fromBar)
        self.insertWidget(to_, fromBar)
    
    def urlBars(self):
        """
        Public method to get a list of references to all url bars.
        
        @return list of references to url bars (list of UrlBar)
        """
        l = []
        for index in range(self.count()):
            l.append(self.widget(index))
        return l
