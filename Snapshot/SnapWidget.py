# -*- coding: utf-8 -*-

# Copyright (c) 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the snapshot widget.
"""

from PyQt4.QtCore import pyqtSlot, QFile, QFileInfo
from PyQt4.QtGui import QWidget, QImageWriter, QApplication

from E5Gui import E5FileDialog, E5MessageBox

from .Ui_SnapWidget import Ui_SnapWidget

from .SnapshotRegionGrabber import SnapshotRegionGrabber

import UI.PixmapCache
import Preferences


class SnapWidget(QWidget, Ui_SnapWidget):
    """
    Class implementing the snapshot widget.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        self.saveButton.setIcon(UI.PixmapCache.getIcon("fileSaveAs.png"))
        self.takeButton.setIcon(UI.PixmapCache.getIcon("cameraPhoto.png"))
        self.copyButton.setIcon(UI.PixmapCache.getIcon("editCopy.png"))
        self.setWindowIcon(UI.PixmapCache.getIcon("ericSnap.png"))
        
        self.modeCombo.addItem(self.trUtf8("Fullscreen"),
                               SnapshotRegionGrabber.ModeFullscreen)
        self.modeCombo.addItem(self.trUtf8("Rectangular Selection"),
                               SnapshotRegionGrabber.ModeRectangle)
        mode = int(Preferences.Prefs.settings.value("Snapshot/Mode", 0))
        index = self.modeCombo.findData(mode)
        self.modeCombo.setCurrentIndex(index)
        
        self.delaySpin.setValue(int(Preferences.Prefs.settings.value(
            "Snapshot/Delay", 0)))
        
        self.__grabber = None
        
        self.__initFileFilters()
    
    def __initFileFilters(self):
        """
        Private method to define the supported image file filters.
        """
        filters = {
            'bmp': self.trUtf8("Windows Bitmap File (*.bmp)"),
            'gif': self.trUtf8("Graphic Interchange Format File (*.gif)"),
            'ico': self.trUtf8("Windows Icon File (*.ico)"),
            'jpg': self.trUtf8("JPEG File (*.jpg)"),
            'mng': self.trUtf8("Multiple-Image Network Graphics File (*.mng)"),
            'pbm': self.trUtf8("Portable Bitmap File (*.pbm)"),
            'pcx': self.trUtf8("Paintbrush Bitmap File (*.pcx)"),
            'pgm': self.trUtf8("Portable Graymap File (*.pgm)"),
            'png': self.trUtf8("Portable Network Graphics File (*.png)"),
            'ppm': self.trUtf8("Portable Pixmap File (*.ppm)"),
            'sgi': self.trUtf8("Silicon Graphics Image File (*.sgi)"),
            'svg': self.trUtf8("Scalable Vector Graphics File (*.svg)"),
            'tga': self.trUtf8("Targa Graphic File (*.tga)"),
            'tif': self.trUtf8("TIFF File (*.tif)"),
            'xbm': self.trUtf8("X11 Bitmap File (*.xbm)"),
            'xpm': self.trUtf8("X11 Pixmap File (*.xpm)"),
        }
        
        outputFormats = []
        writeFormats = QImageWriter.supportedImageFormats()
        for writeFormat in writeFormats:
            try:
                outputFormats.append(filters[bytes(writeFormat).decode()])
            except KeyError:
                pass
        outputFormats.sort()
        self.__outputFilter = ';;'.join(outputFormats)
        
        self.__defaultFilter = filters['png']
    
    @pyqtSlot(bool)
    def on_saveButton_clicked(self, checked):
        """
        Private slot to save the snapshot.
        """
        fileName, selectedFilter = E5FileDialog.getSaveFileNameAndFilter(
            self,
            self.trUtf8("Save Snapshot"),
            "",
            self.__outputFilter,
            self.__defaultFilter,
            E5FileDialog.Options(E5FileDialog.DontConfirmOverwrite))
        if not fileName:
            return
        
        ext = QFileInfo(fileName).suffix()
        if not ext:
            ex = selectedFilter.split("(*")[1].split(")")[0]
            if ex:
                fileName += ex
        if QFileInfo(fileName).exists():
            res = E5MessageBox.yesNo(self,
                self.trUtf8("Save Snapshot"),
                self.trUtf8("<p>The file <b>{0}</b> already exists."
                            " Overwrite it?</p>").format(fileName),
                icon=E5MessageBox.Warning)
            if not res:
                return
        
        file = QFile(fileName)
        if not file.open(QFile.WriteOnly):
            E5MessageBox.warning(self, self.trUtf8("Save Snapshot"),
                                self.trUtf8("Cannot write file '{0}:\n{1}.")\
                                    .format(fileName, file.errorString()))
            return
        
        res = self.preview.pixmap().save(file)
        file.close()
        
        if not res:
            E5MessageBox.warning(self, self.trUtf8("Save Snapshot"),
                                self.trUtf8("Cannot write file '{0}:\n{1}.")\
                                    .format(fileName, file.errorString()))
    
    @pyqtSlot(bool)
    def on_takeButton_clicked(self, checked):
        """
        Private slot to take a snapshot.
        """
        mode = self.modeCombo.itemData(self.modeCombo.currentIndex())
        delay = self.delaySpin.value()
        
        Preferences.Prefs.settings.setValue("Snapshot/Delay", delay)
        Preferences.Prefs.settings.setValue("Snapshot/Mode", mode)
        
        self.hide()
        
        self.__grabber = SnapshotRegionGrabber(mode, delay)
        self.__grabber.grabbed.connect(self.__captured)
    
    @pyqtSlot()
    def on_copyButton_clicked(self):
        """
        Private slot to copy the snapshot to the clipboard.
        """
        QApplication.clipboard().setPixmap(self.preview.pixmap())
    
    def __captured(self, pixmap):
        """
        Private slot to show a preview of the snapshot.
        
        @param pixmap pixmap of the snapshot (QPixmap)
        """
        self.__grabber.close()
        self.preview.setPixmap(pixmap)
        
        self.__grabber = None
        
        self.saveButton.setEnabled(True)
        self.copyButton.setEnabled(True)
        self.show()
