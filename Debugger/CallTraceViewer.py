# -*- coding: utf-8 -*-

# Copyright (c) 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Call Trace viewer widget.
"""

from PyQt4.QtCore import pyqtSlot, pyqtSignal
from PyQt4.QtGui import QWidget,  QTreeWidgetItem

from .Ui_CallTraceViewer import Ui_CallTraceViewer

import UI.PixmapCache
import Preferences


class CallTraceViewer(QWidget, Ui_CallTraceViewer):
    """
    Class implementing the Call Trace viewer widget.
    
    @signal sourceFile(str, int) emitted to show the source of a call/return point
    """
    sourceFile = pyqtSignal(str, int)
    
    def __init__(self, debugServer, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        self.__dbs = debugServer
        
        self.startTraceButton.setIcon(UI.PixmapCache.getIcon("callTraceStart.png"))
        self.stopTraceButton.setIcon(UI.PixmapCache.getIcon("callTraceStop.png"))
        self.resizeButton.setIcon(UI.PixmapCache.getIcon("resizeColumns.png"))
        self.clearButton.setIcon(UI.PixmapCache.getIcon("editDelete.png"))
        self.saveButton.setIcon(UI.PixmapCache.getIcon("fileSave.png"))
        
        self.__headerItem = QTreeWidgetItem(["", self.trUtf8("From"), self.trUtf8("To")])
        self.__headerItem.setIcon(0, UI.PixmapCache.getIcon("callReturn.png"))
        self.callTrace.setHeaderItem(self.__headerItem)
        
        self.__callStack = []
        
        self.__entryFormat = "{0}:{1} ({2})"
        
        self.__callTraceEnabled = Preferences.toBool(
            Preferences.Prefs.settings.value("CallTrace/Enabled", False))
        
        if self.__callTraceEnabled:
            self.stopTraceButton.setEnabled(False)
        else:
            self.startTraceButton.setEnabled(False)
        
        self.__dbs.callTraceInfo.connect(self.__addCallTraceInfo)
    
    @pyqtSlot()
    def on_startTraceButton_clicked(self):
        """
        Private slot to start call tracing.
        """
        self.__dbs.setCallTraceEnabled(True)
        self.stopTraceButton.setEnabled(True)
        self.startTraceButton.setEnabled(False)
        Preferences.Prefs.settings.setValue("CallTrace/Enabled", True)
    
    @pyqtSlot()
    def on_stopTraceButton_clicked(self):
        """
        Private slot to start call tracing.
        """
        self.__dbs.setCallTraceEnabled(False)
        self.stopTraceButton.setEnabled(False)
        self.startTraceButton.setEnabled(True)
        Preferences.Prefs.settings.setValue("CallTrace/Enabled", False)
    
    @pyqtSlot()
    def on_resizeButton_clicked(self):
        """
        Private slot to resize the columns of the call trace to their contents.
        """
        for column in range(self.callTrace.columnCount()):
            self.callTrace.resizeColumnToContents(column)
    
    @pyqtSlot()
    def on_clearButton_clicked(self):
        """
        Private slot to clear the call trace.
        """
        self.clear()
    
    @pyqtSlot()
    def on_saveButton_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError
    
    @pyqtSlot(QTreeWidgetItem, int)
    def on_callTrace_itemDoubleClicked(self, item, column):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError
    
    def clear(self):
        """
        Public slot to clear the call trace info.
        """
        self.callTrace.clear()
        self.__callStack = []
    
    def __addCallTraceInfo(self, isCall, fromFile, fromLine, fromFunction,
                           toFile, toLine, toFunction):
        """
        Private method to add an entry to the call trace viewer.
        
        @param isCall flag indicating a 'call' (boolean)
        @param fromFile name of the originating file (string)
        @param fromLine line number in the originating file (string)
        @param fromFunction name of the originating function (string)
        @param toFile name of the target file (string)
        @param toLine line number in the target file (string)
        @param toFunction name of the target function (string)
        """
        if isCall:
            icon = UI.PixmapCache.getIcon("forward.png")
        else:
            icon = UI.PixmapCache.getIcon("back.png")
        parentItem = self.__callStack[-1] if self.__callStack else self.callTrace
        
        itm = QTreeWidgetItem(parentItem, ["",
            self.__entryFormat.format(fromFile, fromLine, fromFunction),
            self.__entryFormat.format(toFile, toLine, toFunction)])
        itm.setIcon(0, icon)
        itm.setExpanded(True)
        
        if isCall:
            self.__callStack.append(itm)
        else:
            self.__callStack.pop(-1)
    
    def isCallTraceEnabled(self):
        """
        Public method to get the state of the call trace function.
        
        @return flag indicating the state of the call trace function (boolean)
        """
        return self.__callTraceEnabled
