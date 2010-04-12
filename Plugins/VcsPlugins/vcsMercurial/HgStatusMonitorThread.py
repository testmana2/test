# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the VCS status monitor thread class for Mercurial.
"""

from PyQt4.QtCore import QProcess

from VCS.StatusMonitorThread import VcsStatusMonitorThread

import Preferences

class HgStatusMonitorThread(VcsStatusMonitorThread):
    """
    Class implementing the VCS status monitor thread class for Mercurial.
    """
    def __init__(self, interval, projectDir, vcs, parent = None):
        """
        Constructor
        
        @param interval new interval in seconds (integer)
        @param projectDir project directory to monitor (string)
        @param vcs reference to the version control object
        @param parent reference to the parent object (QObject)
        """
        VcsStatusMonitorThread.__init__(self, interval, projectDir, vcs, parent)
        
        self.__ioEncoding = Preferences.getSystem("IOEncoding")
    
    def _performMonitor(self):
        """
        Protected method implementing the monitoring action.
        
        This method populates the statusList member variable
        with a list of strings giving the status in the first column and the
        path relative to the project directory starting with the third column.
        The allowed status flags are:
        <ul>
            <li>"A" path was added but not yet comitted</li>
            <li>"M" path has local changes</li>
            <li>"R" path was deleted and then re-added</li>
            <li>"U" path needs an update</li>
            <li>"Z" path contains a conflict</li>
            <li>" " path is back at normal</li>
        </ul>
        
        @return tuple of flag indicating successful operation (boolean) and 
            a status message in case of non successful operation (string)
        """
        self.shouldUpdate = False
        
        process = QProcess()
        args = []
        args.append('status')
        args.append('--noninteractive')
        args.append('--all')
##        args.append('.')
        process.setWorkingDirectory(self.projectDir)
        process.start('hg', args)
        procStarted = process.waitForStarted()
        if procStarted:
            finished = process.waitForFinished(300000)
            if finished and process.exitCode() == 0:
                output = \
                    str(process.readAllStandardOutput(), self.__ioEncoding, 'replace')
                states = {}
                for line in output.splitlines():
                    if not line.startswith("  "):
                        flag, name = line.split(" ", 1)
                        if flag in "AM":
                            status = flag
                            states[name] = status
                
                args = []
                args.append('resolve')
                args.append('--list')
                process.setWorkingDirectory(self.projectDir)
                process.start('hg', args)
                procStarted = process.waitForStarted()
                if procStarted:
                    finished = process.waitForFinished(300000)
                    if finished and process.exitCode() == 0:
                        output = str(
                            process.readAllStandardOutput(), self.__ioEncoding, 'replace')
                        for line in output.splitlines():
                            flag, name = line.split(" ", 1)
                            if flag == "U":
                                states[name] = "Z" # conflict
                
                for name in states:
                    try:
                        if self.reportedStates[name] != states[name]:
                            self.statusList.append("%s %s" % (states[name], name))
                    except KeyError:
                        self.statusList.append("%s %s" % (states[name], name))
                for name in self.reportedStates.keys():
                    if name not in states:
                        self.statusList.append("  %s" % name)
                self.reportedStates = states
                return True, \
                       self.trUtf8("Mercurial status checked successfully")
            else:
                process.kill()
                process.waitForFinished()
                return False, \
                       str(process.readAllStandardError(), 
                            Preferences.getSystem("IOEncoding"), 
                            'replace')
        else:
            process.kill()
            process.waitForFinished()
            return False, self.trUtf8("Could not start the Mercurial process.")
