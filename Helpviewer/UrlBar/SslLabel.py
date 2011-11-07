# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
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
    
    okStyle = "QLabel { color : white; background-color : green; }"
    nokStyle = "QLabel { color : white; background-color : red; }"
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        
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
            super().mouseReleaseEvent(evt)
    
    def mouseDoubleClickEvent(self, evt):
        """
        Protected method to handle mouse double click events.
        
        @param evt reference to the mouse event (QMouseEvent)
        """
        if evt.button() == Qt.LeftButton:
            self.clicked.emit()
        else:
            super().mouseDoubleClickEvent(evt)
    
    def setValidity(self, valid):
        """
        Public method to set the validity indication.
        
        @param valid flag indicating the certificate validity (boolean)
        """
        if valid:
            self.setStyleSheet(SslLabel.okStyle)
        else:
            self.setStyleSheet(SslLabel.nokStyle)
