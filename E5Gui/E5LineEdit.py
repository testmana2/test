# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing specialized line edits. 
"""

from PyQt4.QtCore import pyqtSignal, Qt, QEvent
from PyQt4.QtGui import QLineEdit, QStyleOptionFrameV2, QStyle, QPainter, QPalette, \
    QWidget, QHBoxLayout, QBoxLayout, QLayout, QApplication, QSpacerItem, QSizePolicy

class SideWidget(QWidget):
    """
    Class implementing the side widgets for the line edit class.
    """
    sizeHintChanged = pyqtSignal()
    
    def __init__(self, parent = None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        QWidget.__init__(self, parent)
    
    def event(self, evt):
        """
        Protected method to handle events.
        
        @param reference to the event (QEvent)
        @return flag indicating, whether the event was recognized (boolean)
        """
        if evt.type() == QEvent.LayoutRequest:
            self.sizeHintChanged.emit()
        return QWidget.event(self, evt)

class E5LineEdit(QLineEdit):
    """
    Class implementing a line edit widget showing some inactive text.
    """
    LeftSide  = 0
    RightSide = 1
    
    def __init__(self, parent = None, inactiveText = ""):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        @param inactiveText text to be shown on inactivity (string)
        """
        QLineEdit.__init__(self, parent)
        
        self.setMinimumHeight(22)
        
        self.__inactiveText = inactiveText
        
        self.__leftWidget = SideWidget(self)
        self.__leftWidget.resize(0, 0)
        self.__leftLayout = QHBoxLayout(self.__leftWidget)
        self.__leftLayout.setContentsMargins(0, 0, 0, 0)
        if QApplication.isRightToLeft():
            self.__leftLayout.setDirection(QBoxLayout.RightToLeft)
        else:
            self.__leftLayout.setDirection(QBoxLayout.LeftToRight)
        self.__leftLayout.setSizeConstraint(QLayout.SetFixedSize)
        
        self.__rightWidget = SideWidget(self)
        self.__rightWidget.resize(0, 0)
        self.__rightLayout = QHBoxLayout(self.__rightWidget)
        self.__rightLayout.setContentsMargins(0, 0, 0, 0)
        if self.isRightToLeft():
            self.__rightLayout.setDirection(QBoxLayout.RightToLeft)
        else:
            self.__rightLayout.setDirection(QBoxLayout.LeftToRight)
        horizontalSpacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.__rightLayout.addItem(horizontalSpacer)
        
        self.setWidgetSpacing(3)
        self.__leftWidget.sizeHintChanged.connect(self._updateTextMargins)
        self.__rightWidget.sizeHintChanged.connect(self._updateTextMargins)
    
    def event(self, evt):
        """
        Protected method to handle events.
        
        @param reference to the event (QEvent)
        @return flag indicating, whether the event was recognized (boolean)
        """
        if evt.type() == QEvent.LayoutDirectionChange:
            if self.isRightToLeft():
                self.__leftLayout.setDirection(QBoxLayout.RightToLeft)
                self.__rightLayout.setDirection(QBoxLayout.RightToLeft)
            else:
                self.__leftLayout.setDirection(QBoxLayout.LeftToRight)
                self.__rightLayout.setDirection(QBoxLayout.LeftToRight)
        return QLineEdit.event(self, evt)
    
    def resizeEvent(self, evt):
        """
        Protected method to handle resize events.
        
        @param evt reference to the resize event (QResizeEvent)
        """
        self.__updateSideWidgetLocations()
        QLineEdit.resizeEvent(self, evt)
    
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
            left = self.textMargin(self.LeftSide)
            right = self.textMargin(self.RightSide)
            textRect.adjust(left, 0, -right, 0)
            painter = QPainter(self)
            painter.setPen(self.palette().brush(QPalette.Disabled, QPalette.Text).color())
            painter.drawText(
                textRect, Qt.AlignLeft | Qt.AlignVCenter, self.__inactiveText)
    
    def __updateSideWidgetLocations(self):
        """
        Private method to update the side widget locations.
        """
        opt = QStyleOptionFrameV2()
        self.initStyleOption(opt)
        textRect = \
            self.style().subElementRect(QStyle.SE_LineEditContents, opt, self)
        textRect.adjust(2, 0, 0, 0)
        
        left = self.textMargin(self.LeftSide)
        
        midHeight = textRect.center().y() + 1
        
        if self.__leftLayout.count() > 0:
            leftHeight = midHeight - self.__leftWidget.height() // 2
            leftWidth = self.__leftWidget.width()
            if leftWidth == 0:
                leftHeight = midHeight - self.__leftWidget.sizeHint().height() // 2
            self.__leftWidget.move(textRect.x(), leftHeight)
        
        textRect.setX(left)
        textRect.setY(midHeight - self.__rightWidget.sizeHint().height() // 2)
        textRect.setHeight(self.__rightWidget.sizeHint().height())
        self.__rightWidget.setGeometry(textRect)
    
    def _updateTextMargins(self):
        """
        Protected slot to update the text margins.
        """
        left = self.textMargin(self.LeftSide)
        right = self.textMargin(self.RightSide)
        self.setTextMargins(left, 0, right, 0)
        self.__updateSideWidgetLocations()
    
    def addWidget(self, widget, position):
        """
        Public method to add a widget to a side.
        
        @param widget reference to the widget to add (QWidget)
        @param position position to add to (E5LineEdit.LeftSide, E5LineEdit.RightSide)
        """
        if widget is None:
            return
        
        if self.isRightToLeft():
            if position == self.LeftSide:
                position = self.RightSide
            else:
                position = self.LeftSide
        if position == self.LeftSide:
            self.__leftLayout.addWidget(widget)
        else:
            self.__rightLayout.insertWidget(1, widget)
    
    def removeWidget(self, widget):
        """
        Public method to remove a widget from a side.
        
        @param widget reference to the widget to remove (QWidget)
        """
        if widget is None:
            return
        
        self.__leftLayout.removeWidget(widget)
        self.__rightLayout.removeWidget(widget)
        widget.hide()
    
    def widgetSpacing(self):
        """
        Public method to get the side widget spacing.
        
        @return side widget spacing (integer)
        """
        return self.__leftLayout.spacing()
    
    def setWidgetSpacing(self, spacing):
        """
        Public method to set the side widget spacing.
        
        @param spacing side widget spacing (integer)
        """
        self.__leftLayout.setSpacing(spacing)
        self.__rightLayout.setSpacing(spacing)
        self._updateTextMargins()
    
    def textMargin(self, position):
        """
        Public method to get the text margin for a side.
        
        @param position side to get margin for (E5LineEdit.LeftSide, E5LineEdit.RightSide)
        """
        spacing = self.__rightLayout.spacing()
        w = 0
        if position == self.LeftSide:
            w = self.__leftWidget.sizeHint().width()
        else:
            w = self.__rightWidget.sizeHint().width()
        if w == 0:
            return 0
        return w + spacing * 2
    
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
