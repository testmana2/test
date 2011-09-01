# -*- coding: utf-8 -*-

# Copyright (c) 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show all guards for all patches.
"""

import os

from PyQt4.QtCore import QProcess, QCoreApplication
from PyQt4.QtGui import QDialog, QTreeWidgetItem

from .Ui_HgQueuesListAllGuardsDialog import Ui_HgQueuesListAllGuardsDialog

import Preferences
import UI.PixmapCache


class HgQueuesListAllGuardsDialog(QDialog, Ui_HgQueuesListAllGuardsDialog):
    """
    Class implementing a dialog to show all guards for all patches.
    """
    def __init__(self, vcs, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        self.vcs = vcs
        self.__hgClient = vcs.getClient()
        
        self.show()
        QCoreApplication.processEvents()
    
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
            if repodir == os.sep:
                return
        
        args = []
        args.append("qguard")
        args.append("--list")
        
        output = ""
        if self.__hgClient:
            output = self.__hgClient.runcommand(args)[0]
        else:
            ioEncoding = Preferences.getSystem("IOEncoding")
            process = QProcess()
            process.setWorkingDirectory(repodir)
            process.start('hg', args)
            procStarted = process.waitForStarted()
            if procStarted:
                finished = process.waitForFinished(30000)
                if finished and process.exitCode() == 0:
                    output = \
                        str(process.readAllStandardOutput(), ioEncoding, 'replace')
        
        if output:
            guardsDict = {}
            for line in output.splitlines():
                if line:
                    patchName, guards = line.strip().split(":", 1)
                    guardsDict[patchName] = guards.strip().split()
            for patchName in sorted(guardsDict.keys()):
                patchItm = QTreeWidgetItem(self.guardsTree, [patchName])
                patchItm.setExpanded(True)
                for guard in guardsDict[patchName]:
                    if guard.startswith("+"):
                        icon = UI.PixmapCache.getIcon("plus.png")
                        guard = guard[1:]
                    elif guard.startswith("-"):
                        icon = UI.PixmapCache.getIcon("minus.png")
                        guard = guard[1:]
                    else:
                        icon = None
                        guard = self.trUtf8("Unguarded")
                    itm = QTreeWidgetItem(patchItm, [guard])
                    if icon:
                        itm.setIcon(0, icon)
        else:
            QTreeWidgetItem(self.guardsTree, [self.trUtf8("no patches found")])
