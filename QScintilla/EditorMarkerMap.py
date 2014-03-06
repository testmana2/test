# -*- coding: utf-8 -*-

# Copyright (c) 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a class for showing an editor marker map.
"""

from PyQt4.QtGui import QColor

from E5Gui.E5MapWidget import E5MapWidget


class EditorMarkerMap(E5MapWidget):
    """
    Class implementing a class for showing an editor marker map.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        
        # initialize colors for various markers
        # TODO: make these colors configurable via Preferences
        self.__bookmarkColor = QColor("#f8c700")
        self.__errorColor = QColor("#dd0000")
        self.__warningColor = QColor("#606000")
        self.__breakpointColor = QColor("#f55c07")
        self.__taskColor = QColor("#2278f8")
        self.__coverageColor = QColor("#ad3636")
        self.__changeColor = QColor("#00b000")
        self.__currentLineMarker = QColor("#000000")
    
    def __drawIndicator(self, line, painter, color):
        """
        Private method to draw an indicator.
        
        @param line line number (integer)
        @param painter reference to the painter (QPainter)
        @param color color to be used (QColor)
        """
        position = self.value2Position(line)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(self.generateIndicatorRect(position))
    
    def _paintIt(self, painter):
        """
        Protected method for painting the widget's indicators.
        
        @param painter reference to the painter object (QPainter)
        """
        # draw indicators in reverse order of priority
        
        # 1. changes
        for line in self._master.getChangeLines():
            self.__drawIndicator(line, painter, self.__changeColor)
        
        # 2. coverage
        for line in self._master.getCoverageLines():
            self.__drawIndicator(line, painter, self.__coverageColor)
        
        # 3. tasks
        for line in self._master.getTaskLines():
            self.__drawIndicator(line, painter, self.__taskColor)
        
        # 4. breakpoints
        for line in self._master.getBreakpointLines():
            self.__drawIndicator(line, painter, self.__breakpointColor)
        
        # 5. bookmarks
        for line in self._master.getBookmarkLines():
            self.__drawIndicator(line, painter, self.__bookmarkColor)
        
        # 6. warnings
        for line in self._master.getWarningLines():
            self.__drawIndicator(line, painter, self.__warningColor)
        
        # 7. errors
        for line in self._master.getSyntaxErrorLines():
            self.__drawIndicator(line, painter, self.__errorColor)
        
        # 8. current line
        self.__drawIndicator(self._master.getCursorPosition()[0], painter,
                             self.__currentLineMarker)
