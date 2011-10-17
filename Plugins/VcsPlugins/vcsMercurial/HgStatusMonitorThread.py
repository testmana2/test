# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the VCS status monitor thread class for Mercurial.
"""

from PyQt4.QtCore import QProcess

from VCS.StatusMonitorThread import VcsStatusMonitorThread
from .HgClient import HgClient

import Preferences


class HgStatusMonitorThread(VcsStatusMonitorThread):
    """
    Class implementing the VCS status monitor thread class for Mercurial.
    """
    def __init__(self, interval, project, vcs, parent=None):
        """
        Constructor
        
        @param interval new interval in seconds (integer)
        @param project reference to the project object (Project)
        @param vcs reference to the version control object
        @param parent reference to the parent object (QObject)
        """
        VcsStatusMonitorThread.__init__(self, interval, project, vcs, parent)
        
        self.__ioEncoding = Preferences.getSystem("IOEncoding")
        
        self.__client = None
        self.__useCommandLine = False
    
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
            <li>"O" path was removed</li>
            <li>"R" path was deleted and then re-added</li>
            <li>"U" path needs an update</li>
            <li>"Z" path contains a conflict</li>
            <li>" " path is back at normal</li>
        </ul>
        
        @return tuple of flag indicating successful operation (boolean) and
            a status message in case of non successful operation (string)
        """
        self.shouldUpdate = False
        
        if self.__client is None and not self.__useCommandLine:
            if self.vcs.version >= (1, 9, 5):
                # versions below that have a bug causing a second
                # to not recognize changes to the status
                client = HgClient(self.projectDir, "utf-8")
                ok, err = client.startServer()
                if ok:
                    self.__client = client
                else:
                    self.__useCommandLine = True
            else:
                self.__useCommandLine = True
        
        # step 1: get overall status
        args = []
        args.append('status')
        args.append('--noninteractive')
        args.append('--all')
        
        output = ""
        error = ""
        if self.__client:
            output, error = self.__client.runcommand(args)
        else:
            process = QProcess()
            process.setWorkingDirectory(self.projectDir)
            process.start('hg', args)
            procStarted = process.waitForStarted()
            if procStarted:
                finished = process.waitForFinished(300000)
                if finished and process.exitCode() == 0:
                    output = \
                        str(process.readAllStandardOutput(), self.__ioEncoding, 'replace')
                else:
                    process.kill()
                    process.waitForFinished()
                    error = \
                        str(process.readAllStandardError(), self.__ioEncoding, 'replace')
            else:
                process.kill()
                process.waitForFinished()
                error = self.trUtf8("Could not start the Mercurial process.")
        
        if error:
            return False, error
        
        states = {}
        for line in output.splitlines():
            if not line.startswith("  "):
                flag, name = line.split(" ", 1)
                if flag in "AMR":
                    if flag == "R":
                        status = "O"
                    else:
                        status = flag
                    states[name] = status
        
        # step 2: get conflicting changes
        args = []
        args.append('resolve')
        args.append('--list')
        
        output = ""
        error = ""
        if self.__client:
            output, error = self.__client.runcommand(args)
        else:
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
                states[name] = "Z"  # conflict
        
        # step 3: collect the status to be reported back
        for name in states:
            try:
                if self.reportedStates[name] != states[name]:
                    self.statusList.append("{0} {1}".format(states[name], name))
            except KeyError:
                self.statusList.append("{0} {1}".format(states[name], name))
        for name in self.reportedStates.keys():
            if name not in states:
                self.statusList.append("  {0}".format(name))
        self.reportedStates = states
        
        return True, \
               self.trUtf8("Mercurial status checked successfully")
    
    def _shutdown(self):
        """
        Protected method performing shutdown actions.
        """
        if self.__client:
            self.__client.stopServer()
