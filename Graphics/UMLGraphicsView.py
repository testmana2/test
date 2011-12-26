# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a subclass of E5GraphicsView for our diagrams.
"""

from PyQt4.QtCore import pyqtSignal, Qt, QSignalMapper, QFileInfo
from PyQt4.QtGui import QAction, QToolBar, QDialog, QPrinter, QPrintDialog

from E5Graphics.E5GraphicsView import E5GraphicsView

from E5Gui import E5MessageBox, E5FileDialog

from .UMLItem import UMLItem
from .UMLSceneSizeDialog import UMLSceneSizeDialog
from .ZoomDialog import ZoomDialog

import UI.Config
import UI.PixmapCache

import Preferences


class UMLGraphicsView(E5GraphicsView):
    """
    Class implementing a specialized E5GraphicsView for our diagrams.
    
    @signal relayout() emitted to indicate a relayout of the diagram
        is requested
    """
    relayout = pyqtSignal()
    
    def __init__(self, scene, diagramName="Unnamed", parent=None, name=None):
        """
        Constructor
        
        @param scene reference to the scene object (QGraphicsScene)
        @param diagramName name of the diagram (string)
        @param parent parent widget of the view (QWidget)
        @param name name of the view widget (string)
        """
        E5GraphicsView.__init__(self, scene, parent)
        if name:
            self.setObjectName(name)
        
        self.diagramName = diagramName
        
        self.border = 10
        self.deltaSize = 100.0
        
        self.__initActions()
        
        scene.changed.connect(self.__sceneChanged)
        
    def __initActions(self):
        """
        Private method to initialize the view actions.
        """
        self.alignMapper = QSignalMapper(self)
        self.alignMapper.mapped[int].connect(self.__alignShapes)
        
        self.deleteShapeAct = \
            QAction(UI.PixmapCache.getIcon("deleteShape.png"),
                    self.trUtf8("Delete shapes"), self)
        self.deleteShapeAct.triggered[()].connect(self.__deleteShape)
        
        self.saveAct = \
            QAction(UI.PixmapCache.getIcon("fileSave.png"),
                    self.trUtf8("Save as PNG"), self)
        self.saveAct.triggered[()].connect(self.__saveImage)
        
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
        self.zoomInAct.triggered[()].connect(self.zoomIn)
        
        self.zoomOutAct = \
            QAction(UI.PixmapCache.getIcon("zoomOut.png"),
                    self.trUtf8("Zoom out"), self)
        self.zoomOutAct.triggered[()].connect(self.zoomOut)
        
        self.zoomAct = \
            QAction(UI.PixmapCache.getIcon("zoomTo.png"),
                    self.trUtf8("Zoom..."), self)
        self.zoomAct.triggered[()].connect(self.__zoom)
        
        self.zoomResetAct = \
            QAction(UI.PixmapCache.getIcon("zoomReset.png"),
                    self.trUtf8("Zoom reset"), self)
        self.zoomResetAct.triggered[()].connect(self.zoomReset)
        
        self.incWidthAct = \
            QAction(UI.PixmapCache.getIcon("sceneWidthInc.png"),
                    self.trUtf8("Increase width by {0} points").format(self.deltaSize),
                    self)
        self.incWidthAct.triggered[()].connect(self.__incWidth)
        
        self.incHeightAct = \
            QAction(UI.PixmapCache.getIcon("sceneHeightInc.png"),
                    self.trUtf8("Increase height by {0} points").format(self.deltaSize),
                    self)
        self.incHeightAct.triggered[()].connect(self.__incHeight)
        
        self.decWidthAct = \
            QAction(UI.PixmapCache.getIcon("sceneWidthDec.png"),
                    self.trUtf8("Decrease width by {0} points").format(self.deltaSize),
                    self)
        self.decWidthAct.triggered[()].connect(self.__decWidth)
        
        self.decHeightAct = \
            QAction(UI.PixmapCache.getIcon("sceneHeightDec.png"),
                    self.trUtf8("Decrease height by {0} points").format(self.deltaSize),
                    self)
        self.decHeightAct.triggered[()].connect(self.__decHeight)
        
        self.setSizeAct = \
            QAction(UI.PixmapCache.getIcon("sceneSize.png"),
                    self.trUtf8("Set size"), self)
        self.setSizeAct.triggered[()].connect(self.__setSize)
        
        self.relayoutAct = \
            QAction(UI.PixmapCache.getIcon("reload.png"),
                    self.trUtf8("Re-Layout"), self)
        self.relayoutAct.triggered[()].connect(self.__relayout)
        
        self.alignLeftAct = \
            QAction(UI.PixmapCache.getIcon("shapesAlignLeft.png"),
                    self.trUtf8("Align Left"), self)
        self.alignMapper.setMapping(self.alignLeftAct, Qt.AlignLeft)
        self.alignLeftAct.triggered[()].connect(self.alignMapper.map)
        
        self.alignHCenterAct = \
            QAction(UI.PixmapCache.getIcon("shapesAlignHCenter.png"),
                    self.trUtf8("Align Center Horizontal"), self)
        self.alignMapper.setMapping(self.alignHCenterAct, Qt.AlignHCenter)
        self.alignHCenterAct.triggered[()].connect(self.alignMapper.map)
        
        self.alignRightAct = \
            QAction(UI.PixmapCache.getIcon("shapesAlignRight.png"),
                    self.trUtf8("Align Right"), self)
        self.alignMapper.setMapping(self.alignRightAct, Qt.AlignRight)
        self.alignRightAct.triggered[()].connect(self.alignMapper.map)
        
        self.alignTopAct = \
            QAction(UI.PixmapCache.getIcon("shapesAlignTop.png"),
                    self.trUtf8("Align Top"), self)
        self.alignMapper.setMapping(self.alignTopAct, Qt.AlignTop)
        self.alignTopAct.triggered[()].connect(self.alignMapper.map)
        
        self.alignVCenterAct = \
            QAction(UI.PixmapCache.getIcon("shapesAlignVCenter.png"),
                    self.trUtf8("Align Center Vertical"), self)
        self.alignMapper.setMapping(self.alignVCenterAct, Qt.AlignVCenter)
        self.alignVCenterAct.triggered[()].connect(self.alignMapper.map)
        
        self.alignBottomAct = \
            QAction(UI.PixmapCache.getIcon("shapesAlignBottom.png"),
                    self.trUtf8("Align Bottom"), self)
        self.alignMapper.setMapping(self.alignBottomAct, Qt.AlignBottom)
        self.alignBottomAct.triggered[()].connect(self.alignMapper.map)
        
    def __checkSizeActions(self):
        """
        Private slot to set the enabled state of the size actions.
        """
        diagramSize = self._getDiagramSize(10)
        sceneRect = self.scene().sceneRect()
        if (sceneRect.width() - self.deltaSize) <= diagramSize.width():
            self.decWidthAct.setEnabled(False)
        else:
            self.decWidthAct.setEnabled(True)
        if (sceneRect.height() - self.deltaSize) <= diagramSize.height():
            self.decHeightAct.setEnabled(False)
        else:
            self.decHeightAct.setEnabled(True)
        
    def __sceneChanged(self, areas):
        """
        Private slot called when the scene changes.
        
        @param areas list of rectangles that contain changes (list of QRectF)
        """
        if len(self.scene().selectedItems()) > 0:
            self.deleteShapeAct.setEnabled(True)
        else:
            self.deleteShapeAct.setEnabled(False)
        
    def initToolBar(self):
        """
        Public method to populate a toolbar with our actions.
        
        @return the populated toolBar (QToolBar)
        """
        toolBar = QToolBar(self.trUtf8("Graphics"), self)
        toolBar.setIconSize(UI.Config.ToolBarIconSize)
        toolBar.addAction(self.deleteShapeAct)
        toolBar.addSeparator()
        toolBar.addAction(self.saveAct)
        toolBar.addSeparator()
        toolBar.addAction(self.printPreviewAct)
        toolBar.addAction(self.printAct)
        toolBar.addSeparator()
        toolBar.addAction(self.zoomInAct)
        toolBar.addAction(self.zoomOutAct)
        toolBar.addAction(self.zoomAct)
        toolBar.addAction(self.zoomResetAct)
        toolBar.addSeparator()
        toolBar.addAction(self.alignLeftAct)
        toolBar.addAction(self.alignHCenterAct)
        toolBar.addAction(self.alignRightAct)
        toolBar.addAction(self.alignTopAct)
        toolBar.addAction(self.alignVCenterAct)
        toolBar.addAction(self.alignBottomAct)
        toolBar.addSeparator()
        toolBar.addAction(self.incWidthAct)
        toolBar.addAction(self.incHeightAct)
        toolBar.addAction(self.decWidthAct)
        toolBar.addAction(self.decHeightAct)
        toolBar.addAction(self.setSizeAct)
        toolBar.addSeparator()
        toolBar.addAction(self.relayoutAct)
        
        return toolBar
        
    def filteredItems(self, items):
        """
        Public method to filter a list of items.
        
        @param items list of items as returned by the scene object
            (QGraphicsItem)
        @return list of interesting collision items (QGraphicsItem)
        """
        return [itm for itm in items if isinstance(itm, UMLItem)]
        
    def selectItems(self, items):
        """
        Public method to select the given items.
        
        @param items list of items to be selected (list of QGraphicsItemItem)
        """
        # step 1: deselect all items
        self.unselectItems()
        
        # step 2: select all given items
        for itm in items:
            if isinstance(itm, UMLItem):
                itm.setSelected(True)
        
    def selectItem(self, item):
        """
        Public method to select an item.
        
        @param item item to be selected (QGraphicsItemItem)
        """
        if isinstance(item, UMLItem):
            item.setSelected(not item.isSelected())
        
    def __deleteShape(self):
        """
        Private method to delete the selected shapes from the display.
        """
        for item in self.scene().selectedItems():
            item.removeAssociations()
            item.setSelected(False)
            self.scene().removeItem(item)
            del item
        
    def __incWidth(self):
        """
        Private method to handle the increase width context menu entry.
        """
        self.resizeScene(self.deltaSize, True)
        self.__checkSizeActions()
        
    def __incHeight(self):
        """
        Private method to handle the increase height context menu entry.
        """
        self.resizeScene(self.deltaSize, False)
        self.__checkSizeActions()
        
    def __decWidth(self):
        """
        Private method to handle the decrease width context menu entry.
        """
        self.resizeScene(-self.deltaSize, True)
        self.__checkSizeActions()
        
    def __decHeight(self):
        """
        Private method to handle the decrease height context menu entry.
        """
        self.resizeScene(-self.deltaSize, False)
        self.__checkSizeActions()
        
    def __setSize(self):
        """
        Private method to handle the set size context menu entry.
        """
        rect = self._getDiagramRect(10)
        sceneRect = self.scene().sceneRect()
        dlg = UMLSceneSizeDialog(sceneRect.width(), sceneRect.height(),
                                  rect.width(), rect.height(), self)
        if dlg.exec_() == QDialog.Accepted:
            width, height = dlg.getData()
            self.setSceneSize(width, height)
        self.__checkSizeActions()
        
    def __saveImage(self):
        """
        Private method to handle the save context menu entry.
        """
        fname, selectedFilter = E5FileDialog.getSaveFileNameAndFilter(
            self,
            self.trUtf8("Save Diagram"),
            "",
            self.trUtf8("Portable Network Graphics (*.png);;"
                        "Scalable Vector Graphics (*.svg)"),
            "",
            E5FileDialog.Options(E5FileDialog.DontConfirmOverwrite))
        if fname:
            ext = QFileInfo(fname).suffix()
            if not ext:
                ex = selectedFilter.split("(*")[1].split(")")[0]
                if ex:
                    fname += ex
            if QFileInfo(fname).exists():
                res = E5MessageBox.yesNo(self,
                    self.trUtf8("Save Diagram"),
                    self.trUtf8("<p>The file <b>{0}</b> already exists."
                                " Overwrite it?</p>").format(fname),
                    icon=E5MessageBox.Warning)
                if not res:
                    return
            
            success = self.saveImage(fname, QFileInfo(fname).suffix().upper())
            if not success:
                E5MessageBox.critical(self,
                    self.trUtf8("Save Diagram"),
                    self.trUtf8("""<p>The file <b>{0}</b> could not be saved.</p>""")
                        .format(fname))
        
    def __relayout(self):
        """
        Private method to handle the re-layout context menu entry.
        """
        scene = self.scene()
        for itm in list(scene.items())[:]:
            if itm.scene() == scene:
                scene.removeItem(itm)
        self.relayout.emit()
        
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
        printer.setPageMargins(
            Preferences.getPrinter("LeftMargin") * 10,
            Preferences.getPrinter("TopMargin") * 10,
            Preferences.getPrinter("RightMargin") * 10,
            Preferences.getPrinter("BottomMargin") * 10,
            QPrinter.Millimeter
        )
        printer.setPrinterName(Preferences.getPrinter("PrinterName"))
        
        printDialog = QPrintDialog(printer, self)
        if printDialog.exec_():
            self.printDiagram(printer, self.diagramName)
        
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
        preview.paintRequested[QPrinter].connect(self.printDiagram)
        preview.exec_()
        
    def __zoom(self):
        """
        Private method to handle the zoom context menu action.
        """
        dlg = ZoomDialog(self.zoom(), self)
        if dlg.exec_() == QDialog.Accepted:
            zoom = dlg.getZoomSize()
            self.setZoom(zoom)
        
    def setDiagramName(self, name):
        """
        Public slot to set the diagram name.
        
        @param name diagram name (string)
        """
        self.diagramName = name
        
    def __alignShapes(self, alignment):
        """
        Private slot to align the selected shapes.
        
        @param alignment alignment type (Qt.AlignmentFlag)
        """
        # step 1: get all selected items
        items = self.scene().selectedItems()
        if len(items) <= 1:
            return
        
        # step 2: find the index of the item to align in relation to
        amount = None
        for i, item in enumerate(items):
            rect = item.sceneBoundingRect()
            if alignment == Qt.AlignLeft:
                if amount is None or rect.x() < amount:
                    amount = rect.x()
                    index = i
            elif alignment == Qt.AlignRight:
                if amount is None or rect.x() + rect.width() > amount:
                    amount = rect.x() + rect.width()
                    index = i
            elif alignment == Qt.AlignHCenter:
                if amount is None or rect.width() > amount:
                    amount = rect.width()
                    index = i
            elif alignment == Qt.AlignTop:
                if amount is None or rect.y() < amount:
                    amount = rect.y()
                    index = i
            elif alignment == Qt.AlignBottom:
                if amount is None or rect.y() + rect.height() > amount:
                    amount = rect.y() + rect.height()
                    index = i
            elif alignment == Qt.AlignVCenter:
                if amount is None or rect.height() > amount:
                    amount = rect.height()
                    index = i
        rect = items[index].sceneBoundingRect()
        
        # step 3: move the other items
        for i, item in enumerate(items):
            if i == index:
                continue
            itemrect = item.sceneBoundingRect()
            xOffset = yOffset = 0
            if alignment == Qt.AlignLeft:
                xOffset = rect.x() - itemrect.x()
            elif alignment == Qt.AlignRight:
                xOffset = (rect.x() + rect.width()) - \
                          (itemrect.x() + itemrect.width())
            elif alignment == Qt.AlignHCenter:
                xOffset = (rect.x() + rect.width() // 2) - \
                          (itemrect.x() + itemrect.width() // 2)
            elif alignment == Qt.AlignTop:
                yOffset = rect.y() - itemrect.y()
            elif alignment == Qt.AlignBottom:
                yOffset = (rect.y() + rect.height()) - \
                          (itemrect.y() + itemrect.height())
            elif alignment == Qt.AlignVCenter:
                yOffset = (rect.y() + rect.height() // 2) - \
                          (itemrect.y() + itemrect.height() // 2)
            item.moveBy(xOffset, yOffset)
        
        self.scene().update()
    
    def wheelEvent(self, evt):
        """
        Protected method to handle wheel events.
        
        @param evt reference to the wheel event (QWheelEvent)
        """
        if evt.modifiers() & Qt.ControlModifier:
            if evt.delta()< 0:
                self.zoomOut()
            else:
                self.zoomIn()
            evt.accept()
            return
        
        super().wheelEvent(evt)
