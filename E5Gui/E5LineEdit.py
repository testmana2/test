# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing specialized line edits. 
"""

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QLineEdit, QStyleOptionFrameV2, QStyle, QPainter, QPalette

class E5LineEdit(QLineEdit):
    """
    Class implementing a line edit widget showing some inactive text.
    """
    def __init__(self, parent = None, inactiveText = ""):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        @param inactiveText text to be shown on inactivity (string)
        """
        QLineEdit.__init__(self, parent)
        
        self.__inactiveText = inactiveText
    
    def inactiveText(self):
        """
        Public method to get the inactive text.
        
        return inactive text (string)
        """
        return self.__inactiveText
    
    def setInactiveText(self, inactiveText):
        """
        Public method to set the inactive text.
        
        @param inactiveText text to be shown on inactivity (string)
        """
        self.__inactiveText = inactiveText
        self.update()
    
    def paintEvent(self, evt):
        """
        Protected method handling a paint event.
        
        @param evt reference to the paint event (QPaintEvent)
        """
        QLineEdit.paintEvent(self, evt)
        if not self.text() and \
           self.__inactiveText and \
           not self.hasFocus():
            panel = QStyleOptionFrameV2()
            self.initStyleOption(panel)
            textRect = \
                self.style().subElementRect(QStyle.SE_LineEditContents, panel, self)
            textRect.adjust(2, 0, 0, 0)
            painter = QPainter(self)
            painter.setPen(self.palette().brush(QPalette.Disabled, QPalette.Text).color())
            painter.drawText(textRect, Qt.AlignLeft | Qt.AlignVCenter, self.__inactiveText)