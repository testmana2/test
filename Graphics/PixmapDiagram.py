# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog showing a pixmap.
"""

from PyQt4.QtCore import Qt, QSize, QEvent
from PyQt4.QtGui import QLabel, QPalette, QSizePolicy, QScrollArea, QAction, QMenu, \
    QToolBar, QImage, QPixmap, QDialog, QPrinter, QPrintDialog, QPainter, QFont, QColor

from E5Gui import E5MessageBox
from E5Gui.E5MainWindow import E5MainWindow

from .ZoomDialog import ZoomDialog

import UI.Config

import Preferences


class PixmapDiagram(E5MainWindow):
    """
    Class implementing a dialog showing a pixmap.
    """
    def __init__(self, pixmap, parent=None, name=None):
        """
        Constructor
        
        @param pixmap filename of a graphics file to show (string)
        @param parent parent widget of the view (QWidget)
        @param name name of the view widget (string)
        """
        super().__init__(parent)
        if name:
            self.setObjectName(name)
        else:
            self.setObjectName("PixmapDiagram")
        self.setWindowTitle(self.trUtf8("Pixmap-Viewer"))
        
        self.pixmapLabel = QLabel()
        self.pixmapLabel.setObjectName("pixmapLabel")
        self.pixmapLabel.setBackgroundRole(QPalette.Base)
        self.pixmapLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.pixmapLabel.setScaledContents(True)
        
        self.pixmapView = QScrollArea()
        self.pixmapView.setObjectName("pixmapView")
        self.pixmapView.setBackgroundRole(QPalette.Dark)
        self.pixmapView.setWidget(self.pixmapLabel)
        
        self.setCentralWidget(self.pixmapView)
        
        # polish up the dialog
        self.resize(QSize(800, 600).expandedTo(self.minimumSizeHint()))
        
        self.zoom = 1.0
        self.pixmapfile = pixmap
        self.status = self.__showPixmap(self.pixmapfile)
        
        self.__initActions()
        self.__initContextMenu()
        self.__initToolBars()
        
        self.grabGesture(Qt.PinchGesture)
    
    def __initActions(self):
        """
        Private method to initialize the view actions.
        """
        self.closeAct = \
            QAction(UI.PixmapCache.getIcon("close.png"),
                    self.trUtf8("Close"), self)
        self.closeAct.triggered[()].connect(self.close)
        
        self.printAct = \
            QAction(UI.PixmapCache.getIcon("print.png"),
                    self.trUtf8("Print"), self)
        self.printAct.triggered[()].connect(self.__printDiagram)
        
        self.printPreviewAct = \
            QAction(UI.PixmapCache.getIcon("printPreview.png"),
                    self.trUtf8("Print Preview"), self)
        self.printPreviewAct.triggered[()].connect(self.__printPreviewDiagram)
        
        self.zoomInAct = \
            QAction(UI.PixmapCache.getIcon("zoomIn.png"),
                    self.trUtf8("Zoom in"), self)
        self.zoomInAct.triggered[()].connect(self.__zoomIn)
        
        self.zoomOutAct = \
            QAction(UI.PixmapCache.getIcon("zoomOut.png"),
                    self.trUtf8("Zoom out"), self)
        self.zoomOutAct.triggered[()].connect(self.__zoomOut)
        
        self.zoomAct = \
            QAction(UI.PixmapCache.getIcon("zoomTo.png"),
                    self.trUtf8("Zoom..."), self)
        self.zoomAct.triggered[()].connect(self.__zoom)
        
        self.zoomResetAct = \
            QAction(UI.PixmapCache.getIcon("zoomReset.png"),
                    self.trUtf8("Zoom reset"), self)
        self.zoomResetAct.triggered[()].connect(self.__zoomReset)
        
    def __initContextMenu(self):
        """
        Private method to initialize the context menu.
        """
        self.__menu = QMenu(self)
        self.__menu.addAction(self.closeAct)
        self.__menu.addSeparator()
        self.__menu.addAction(self.printPreviewAct)
        self.__menu.addAction(self.printAct)
        self.__menu.addSeparator()
        self.__menu.addAction(self.zoomInAct)
        self.__menu.addAction(self.zoomOutAct)
        self.__menu.addAction(self.zoomAct)
        self.__menu.addAction(self.zoomResetAct)
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__showContextMenu)
        
    def __showContextMenu(self, coord):
        """
        Private slot to show the context menu of the listview.
        
        @param coord the position of the mouse pointer (QPoint)
        """
        self.__menu.popup(self.mapToGlobal(coord))
        
    def __initToolBars(self):
        """
        Private method to populate the toolbars with our actions.
        """
        self.windowToolBar = QToolBar(self.trUtf8("Window"), self)
        self.windowToolBar.setIconSize(UI.Config.ToolBarIconSize)
        self.windowToolBar.addAction(self.closeAct)
        
        self.graphicsToolBar = QToolBar(self.trUtf8("Graphics"), self)
        self.graphicsToolBar.setIconSize(UI.Config.ToolBarIconSize)
        self.graphicsToolBar.addAction(self.printPreviewAct)
        self.graphicsToolBar.addAction(self.printAct)
        self.graphicsToolBar.addSeparator()
        self.graphicsToolBar.addAction(self.zoomInAct)
        self.graphicsToolBar.addAction(self.zoomOutAct)
        self.graphicsToolBar.addAction(self.zoomAct)
        self.graphicsToolBar.addAction(self.zoomResetAct)
        
        self.addToolBar(Qt.TopToolBarArea, self.windowToolBar)
        self.addToolBar(Qt.TopToolBarArea, self.graphicsToolBar)
        
    def __showPixmap(self, filename):
        """
        Private method to show a file.
        
        @param filename name of the file to be shown (string)
        @return flag indicating success (boolean)
        """
        image = QImage(filename)
        if image.isNull():
            E5MessageBox.warning(self,
                self.trUtf8("Pixmap-Viewer"),
                self.trUtf8("""<p>The file <b>{0}</b> cannot be displayed."""
                    """ The format is not supported.</p>""").format(filename))
            return False
        
        self.pixmapLabel.setPixmap(QPixmap.fromImage(image))
        self.pixmapLabel.adjustSize()
        return True
        
    def getDiagramName(self):
        """
        Method to retrieve a name for the diagram.
        
        @return name for the diagram
        """
        return self.pixmapfile
        
    def getStatus(self):
        """
        Method to retrieve the status of the canvas.
        
        @return flag indicating a successful pixmap loading (boolean)
        """
        return self.status
    
    def wheelEvent(self, evt):
        """
        Protected method to handle wheel events.
        
        @param evt reference to the wheel event (QWheelEvent)
        """
        if evt.modifiers() & Qt.ControlModifier:
            if evt.delta() < 0:
                self.__zoomOut()
            else:
                self.__zoomIn()
            evt.accept()
            return
        
        super().wheelEvent(evt)
    
    def event(self, evt):
        """
        Protected method handling events.
        
        @param evt reference to the event (QEvent)
        @return flag indicating, if the event was handled (boolean)
        """
        if evt.type() == QEvent.Gesture:
            self.gestureEvent(evt)
            return True
        
        return super().event(evt)
    
    def gestureEvent(self, evt):
        """
        Protected method handling gesture events.
        
        @param evt reference to the gesture event (QGestureEvent
        """
        pinch = evt.gesture(Qt.PinchGesture)
        if pinch:
            if pinch.state() == Qt.GestureStarted:
                pinch.setScaleFactor(self.zoom)
            else:
                self.__doZoom(pinch.scaleFactor() / self.zoom)
            evt.accept()
    
    ############################################################################
    ## Private menu handling methods below.
    ############################################################################
    
    def __adjustScrollBar(self, scrollBar, factor):
        """
        Private method to adjust a scrollbar by a certain factor.
        
        @param scrollBar reference to the scrollbar object (QScrollBar)
        @param factor factor to adjust by (float)
        """
        scrollBar.setValue(int(factor * scrollBar.value()
                                + ((factor - 1) * scrollBar.pageStep() / 2)))
        
    def __doZoom(self, factor):
        """
        Private method to perform the zooming.
        
        @param factor zoom factor (float)
        """
        self.zoom *= factor
        self.pixmapLabel.resize(self.zoom * self.pixmapLabel.pixmap().size())
        
        self.__adjustScrollBar(self.pixmapView.horizontalScrollBar(), factor)
        self.__adjustScrollBar(self.pixmapView.verticalScrollBar(), factor)
        
    def __zoomIn(self):
        """
        Private method to handle the zoom in context menu entry.
        """
        self.__doZoom(1.25)
        
    def __zoomOut(self):
        """
        Private method to handle the zoom out context menu entry.
        """
        self.__doZoom(0.8)
        
    def __zoomReset(self):
        """
        Private method to handle the reset zoom context menu entry.
        """
        self.zoom = 1.0
        self.pixmapLabel.adjustSize()
        
    def __zoom(self):
        """
        Private method to handle the zoom context menu action.
        """
        dlg = ZoomDialog(self.zoom, self)
        if dlg.exec_() == QDialog.Accepted:
            zoom = dlg.getZoomSize()
            factor = zoom / self.zoom
            self.__doZoom(factor)
        
    def __printDiagram(self):
        """
        Private slot called to print the diagram.
        """
        printer = QPrinter(mode=QPrinter.ScreenResolution)
        printer.setFullPage(True)
        if Preferences.getPrinter("ColorMode"):
            printer.setColorMode(QPrinter.Color)
        else:
            printer.setColorMode(QPrinter.GrayScale)
        if Preferences.getPrinter("FirstPageFirst"):
            printer.setPageOrder(QPrinter.FirstPageFirst)
        else:
            printer.setPageOrder(QPrinter.LastPageFirst)
        printer.setPrinterName(Preferences.getPrinter("PrinterName"))
        
        printDialog = QPrintDialog(printer, self)
        if printDialog.exec_():
            self.__print(printer)
        
    def __printPreviewDiagram(self):
        """
        Private slot called to show a print preview of the diagram.
        """
        from PyQt4.QtGui import QPrintPreviewDialog
        
        printer = QPrinter(mode=QPrinter.ScreenResolution)
        printer.setFullPage(True)
        if Preferences.getPrinter("ColorMode"):
            printer.setColorMode(QPrinter.Color)
        else:
            printer.setColorMode(QPrinter.GrayScale)
        if Preferences.getPrinter("FirstPageFirst"):
            printer.setPageOrder(QPrinter.FirstPageFirst)
        else:
            printer.setPageOrder(QPrinter.LastPageFirst)
        printer.setPageMargins(
            Preferences.getPrinter("LeftMargin") * 10,
            Preferences.getPrinter("TopMargin") * 10,
            Preferences.getPrinter("RightMargin") * 10,
            Preferences.getPrinter("BottomMargin") * 10,
            QPrinter.Millimeter
        )
        printer.setPrinterName(Preferences.getPrinter("PrinterName"))
        
        preview = QPrintPreviewDialog(printer, self)
        preview.paintRequested[QPrinter].connect(self.__print)
        preview.exec_()
        
    def __print(self, printer):
        """
        Private slot to the actual printing.
        
        @param printer reference to the printer object (QPrinter)
        """
        painter = QPainter()
        painter.begin(printer)

        # calculate margin and width of printout
        font = QFont("times", 10)
        painter.setFont(font)
        fm = painter.fontMetrics()
        fontHeight = fm.lineSpacing()
        marginX = printer.pageRect().x() - printer.paperRect().x()
        marginX = \
            Preferences.getPrinter("LeftMargin") * int(printer.resolution() / 2.54) \
            - marginX
        marginY = printer.pageRect().y() - printer.paperRect().y()
        marginY = \
            Preferences.getPrinter("TopMargin") * int(printer.resolution() / 2.54) \
            - marginY

        width = printer.width() - marginX \
            - Preferences.getPrinter("RightMargin") * int(printer.resolution() / 2.54)
        height = printer.height() - fontHeight - 4 - marginY \
            - Preferences.getPrinter("BottomMargin") * int(printer.resolution() / 2.54)

        # write a foot note
        s = self.trUtf8("Diagram: {0}").format(self.getDiagramName())
        tc = QColor(50, 50, 50)
        painter.setPen(tc)
        painter.drawRect(marginX, marginY, width, height)
        painter.drawLine(marginX, marginY + height + 2,
                   marginX + width, marginY + height + 2)
        painter.setFont(font)
        painter.drawText(marginX, marginY + height + 4, width,
                   fontHeight, Qt.AlignRight, s)

        # render the diagram
        size = self.pixmapLabel.pixmap().size()
        size.scale(QSize(width - 10, height - 10),  # 5 px inner margin
            Qt.KeepAspectRatio)
        painter.setViewport(marginX + 5, marginY + 5, size.width(), size.height())
        painter.setWindow(self.pixmapLabel.pixmap().rect())
        painter.drawPixmap(0, 0, self.pixmapLabel.pixmap())
        painter.end()
