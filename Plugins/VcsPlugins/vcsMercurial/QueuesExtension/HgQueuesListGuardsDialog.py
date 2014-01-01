# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show the guards of a selected patch.
"""

import os

from PyQt4.QtCore import pyqtSlot, QProcess, QTimer, QCoreApplication
from PyQt4.QtGui import QDialog, QListWidgetItem

from .Ui_HgQueuesListGuardsDialog import Ui_HgQueuesListGuardsDialog

import Preferences
import UI.PixmapCache


class HgQueuesListGuardsDialog(QDialog, Ui_HgQueuesListGuardsDialog):
    """
    Class implementing a dialog to show the guards of a selected patch.
    """
    def __init__(self, vcs, patchesList, parent=None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param patchesList list of patches (list of strings)
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        self.process = QProcess()
        self.vcs = vcs
        self.__hgClient = vcs.getClient()
        
        self.patchSelector.addItems([""] + patchesList)
        
        self.show()
        QCoreApplication.processEvents()
    
    def closeEvent(self, e):
        """
        Private slot implementing a close event handler.
        
        @param e close event (QCloseEvent)
        """
        if self.__hgClient:
            if self.__hgClient.isExecuting():
                self.__hgClient.cancel()
        else:
            if self.process is not None and \
               self.process.state() != QProcess.NotRunning:
                self.process.terminate()
                QTimer.singleShot(2000, self.process.kill)
                self.process.waitForFinished(3000)
        
        e.accept()
    
    def start(self, path):
        """
        Public slot to start the list command.
        
        @param path name of directory to be listed (string)
        """
        dname, fname = self.vcs.splitPath(path)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        self.__repodir = repodir
        self.on_patchSelector_activated("")
    
    @pyqtSlot(str)
    def on_patchSelector_activated(self, patch):
        """
        Private slot to get the list of guards for the given patch name.
        
        @param patch selected patch name (empty for current patch)
        """
        self.guardsList.clear()
        self.patchNameLabel.setText("")
        
        args = []
        args.append("qguard")
        if patch:
            args.append(patch)
        
        output = ""
        if self.__hgClient:
            output = self.__hgClient.runcommand(args)[0].strip()
        else:
            ioEncoding = Preferences.getSystem("IOEncoding")
            process = QProcess()
            process.setWorkingDirectory(self.__repodir)
            process.start('hg', args)
            procStarted = process.waitForStarted()
            if procStarted:
                finished = process.waitForFinished(30000)
                if finished and process.exitCode() == 0:
                    output = \
                        str(process.readAllStandardOutput(),
                            ioEncoding, 'replace').strip()
        
        if output:
            patchName, guards = output.split(":", 1)
            self.patchNameLabel.setText(patchName)
            guardsList = guards.strip().split()
            for guard in guardsList:
                if guard.startswith("+"):
                    icon = UI.PixmapCache.getIcon("plus.png")
                    guard = guard[1:]
                elif guard.startswith("-"):
                    icon = UI.PixmapCache.getIcon("minus.png")
                    guard = guard[1:]
                else:
                    icon = None
                    guard = self.trUtf8("Unguarded")
                itm = QListWidgetItem(guard, self.guardsList)
                if icon:
                    itm.setIcon(icon)
