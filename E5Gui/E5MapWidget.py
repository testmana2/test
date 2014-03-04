# -*- coding: utf-8 -*-

# Copyright (c) 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a base class for showing a document map.
"""

from PyQt4.QtCore import Qt, QSize, QRect
from PyQt4.QtGui import QWidget, QAbstractScrollArea, QColor, QBrush, QPainter


class E5MapWidget(QWidget):
    """
    Class implementing a base class for showing a document map.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        
        self.__width = 12
        self.__lineBorder = 2
        self.__lineHeight = 2
        self.__backgroundColor = QColor(Qt.lightGray).lighter(120)
        self.__sliderBorderColor = QColor(Qt.black)
        self.__sliderBackgroundColor = QColor(Qt.white)
        
        self.__master = None
        self.__enabled = False
        
        if parent is not None and isinstance(parent, QAbstractScrollArea):
            self.setMaster(parent)
    
    def __updateMasterViewportWidth(self):
        """
        Private method to update the master's viewport width.
        """
        if self.__master:
            if self.__enabled:
                width = self.__width
            else:
                width = 0
            self.__master.setViewportMargins(0, 0, width, 0)
    
    def setMaster(self, master):
        """
        Public method to set the map master widget.
        
        @param master map master widget (QAbstractScrollArea)
        """
        self.__master = master
        self.__master.verticalScrollBar().valueChanged.connect(self.repaint)
        self.__updateMasterViewportWidth()
    
    def setWidth(self, width):
        """
        Public method to set the widget width.
        
        @param width widget width (integer)
        """
        self.__width = width
    
    def width(self):
        """
        Public method to get the widget's width.
        
        @return widget width (integer)
        """
        return self.__width
    
    def setLineDimensions(self, border, height):
        """
        Public method to set the line (indicator) dimensions.
        
        @param border border width on each side in x-direction (integer)
        @param height height of the line in pixels (integer)
        """
        self.__lineBorder = border
        self.__lineHeight = max(2, height)  # min height is 2 pixels
    
    def lineDimensions(self):
        """
        Public method to get the line (indicator) dimensions.
        
        @return tuple with border width (integer) and line height (integer)
        """
        return self.__lineBorder, self.__lineHeight
    
    def setEnabled(self, enable):
        """
        Public method to set the enabled state.
        
        @param enable flag indicating the enabled state (boolean)
        """
        self.__enabled = enable
        self.setVisible(enable)
        self.__updateMasterViewportWidth()
    
    def isEnabled(self):
        """
        Public method to check the enabled state.
        
        @return flag indicating the enabled state (boolean)
        """
        return self.__enabled
    
    def setBackgroundColor(self, color):
        """
        Public method to set the widget background color.
        
        @param color color for the background (QColor)
        """
        self.__backgroundColor = color
    
    def backgroundColor(self):
        """
        Public method to get the background color.
        
        @return background color (QColor)
        """
        return QColor(self.__backgroundColor)
    
    def setSliderColors(self, border, background):
        """
        Public method to set the slider colors.
        
        @param border border color (QColor)
        @param background background color (QColor)
        """
        self.__sliderBorderColor = border
        self.__sliderBackgroundColor = background
    
    def sliderColors(self):
        """
        Public method to get the slider colors.
        
        @return tuple with the slider's border color (QColor) and
            background color (QColor)
        """
        return (QColor(self.__sliderBorderColor),
                QColor(self.__sliderBackgroundColor))
    
    def sizeHint(self):
        """
        Public method to give an indication about the preferred size.
        
        @return preferred size (QSize)
        """
        return QSize(self.__width, 0)
    
    def paintEvent(self, event):
        """
        Protected method to handle a paint event.
        
        @param event paint event (QPaintEvent)
        """
        # step 1: fill the whole painting area
        painter = QPainter(self)
        painter.fillRect(event.rect(), self.__backgroundColor)
        
        # step 2: paint the indicators
        self._paintIt(painter)
        
        # step 3: paint the slider
        if self.__master:
            penColor = self.__sliderBorderColor
            penColor.setAlphaF(0.8)
            painter.setPen(penColor)
            brushColor = self.__sliderBackgroundColor
            brushColor.setAlphaF(0.5)
            painter.setBrush(QBrush(brushColor))
            painter.drawRect(self.__generateSliderRange(
                self.__master.verticalScrollBar()))
    
    def _paintIt(self, painter):
        """
        Protected method for painting the widget's indicators.
        
        Note: This method should be implemented by subclasses.
        
        @param painter reference to the painter object (QPainter)
        """
        pass
    
    def mousePressEvent(self, event):
        """
        Protected method to handle a mouse button press.
        
        @param event mouse event (QMouseEvent)
        """
        if event.button() == Qt.LeftButton and self.__master:
            vsb = self.__master.verticalScrollBar()
            value = self.position2Value(event.pos().y() - 1)
            vsb.setValue(value - 0.5 * vsb.pageStep())  # center on page
    
    def calculateGeometry(self):
        """
        Public method to recalculate the map widget's geometry.
        """
        if self.__master:
            cr = self.__master.contentsRect()
            vsb = self.__master.verticalScrollBar()
            if vsb.isVisible():
                vsbw = vsb.contentsRect().width()
            else:
                vsbw = 0
            left, top, right, bottom = self.__master.getContentsMargins()
            if right > vsbw:
                vsbw = 0
            self.setGeometry(QRect(cr.right() - self.__width - vsbw, cr.top(),
                                   self.__width, cr.height()))
    
    def scaleFactor(self, slider=False):
        """
        Public method to determine the scrollbar's scale factor.
        
        @param slider flag indicating to calculate the result for the slider
            (boolean)
        @return scale factor (float)
        """
        if self.__master:
            delta = 0 if slider else 2
            vsb = self.__master.verticalScrollBar()
            posHeight = vsb.height() - delta - 1
            valHeight = vsb.maximum() - vsb.minimum() + vsb.pageStep()
            return posHeight / valHeight
        else:
            return 1.0
    
    def value2Position(self, value, slider=False):
        """
        Public method to convert a scrollbar value into a position.
        
        @param value value to convert (integer)
        @param slider flag indicating to calculate the result for the slider
            (boolean)
        @return position (integer)
        """
        if self.__master:
            offset = 0 if slider else 1
            vsb = self.__master.verticalScrollBar()
            return (value - vsb.minimum()) * self.scaleFactor(slider) + offset
        else:
            return value
    
    def position2Value(self, position, slider=False):
        """
        Public method to convert a position into a scrollbar value.
        
        @param position scrollbar position to convert (integer)
        @param slider flag indicating to calculate the result for the slider
            (boolean)
        @return scrollbar value (integer)
        """
        if self.__master:
            offset = 0 if slider else 1
            vsb = self.__master.verticalScrollBar()
            return vsb.minimum() + max(
                0, (position - offset) / self.scaleFactor(slider))
        else:
            return position
    
    def generateIndicatorRect(self, position):
        """
        Public method to generate an indicator rectangle.
        
        @param position indicator position (integer)
        @return indicator rectangle (QRect)
        """
        return QRect(self.__lineBorder, position - self.__lineHeight // 2,
                     self.__width - self.__lineBorder, self.__lineHeight)
    
    def __generateSliderRange(self, scrollbar):
        """
        Private method to generate the slider rectangle.
        
        @param scrollbar reference to the vertical scrollbar (QScrollBar)
        @return slider rectangle (QRect)
        """
        pos1 = self.value2Position(scrollbar.value(), slider=True)
        pos2 = self.value2Position(scrollbar.value() + scrollbar.pageStep(),
                                   slider=True)
        return QRect(1, pos1, self.__width - 2, pos2 - pos1 + 1)
        # TODO: check slider appearance and adjust to self.__width
