# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the label to show some SSL info.
"""

from PyQt4.QtCore import Qt, pyqtSignal
from PyQt4.QtGui import QLabel

class SslLabel(QLabel):
    """
    Class implementing the label to show some SSL info.
    """
    clicked = pyqtSignal()
    
    def __init__(self, parent = None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        QLabel.__init__(self, parent)
        
        self.setFocusPolicy(Qt.NoFocus)
        self.setCursor(Qt.ArrowCursor)
    
    def mouseReleaseEvent(self, evt):
        """
        Protected method to handle mouse release events.
        
        @param evt reference to the mouse event (QMouseEvent)
        """
        if evt.button() == Qt.LeftButton:
            self.clicked.emit()
        else:
            QLabel.mouseReleaseEvent(self, evt)
    
    def mouseDoubleClickEvent(self, evt):
        """
        Protected method to handle mouse double click events.
        
        @param evt reference to the mouse event (QMouseEvent)
        """
        if evt.button() == Qt.LeftButton:
            self.clicked.emit()
        else:
            QLabel.mouseDoubleClickEvent(self, evt)
