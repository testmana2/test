# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show some summary information of the working
directory state.
"""

import os

from PyQt4.QtCore import pyqtSlot, QProcess, QTimer
from PyQt4.QtGui import QDialog, QDialogButtonBox

from E5Gui import E5MessageBox

from .HgUtilities import prepareProcess

from .Ui_HgSummaryDialog import Ui_HgSummaryDialog

import Preferences


class HgSummaryDialog(QDialog, Ui_HgSummaryDialog):
    """
    Class implementing a dialog to show some summary information of the working
    directory state.
    """
    def __init__(self, vcs, parent=None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param parent parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        self.refreshButton = self.buttonBox.addButton(
            self.trUtf8("Refresh"), QDialogButtonBox.ActionRole)
        self.refreshButton.setToolTip(
            self.trUtf8("Press to refresh the summary display"))
        self.refreshButton.setEnabled(False)
        
        self.process = None
        self.vcs = vcs
        self.vcs.committed.connect(self.__committed)
    
    def closeEvent(self, e):
        """
        Private slot implementing a close event handler.
        
        @param e close event (QCloseEvent)
        """
        if self.process is not None and \
           self.process.state() != QProcess.NotRunning:
            self.process.terminate()
            QTimer.singleShot(2000, self.process.kill)
            self.process.waitForFinished(3000)
        
        e.accept()
    
    def start(self, path, mq=False):
        """
        Public slot to start the hg summary command.
        
        @param path path name of the working directory (string)
        @param mq flag indicating to show the queue status as well (boolean)
        """
        self.errorGroup.hide()
        self.__path = path
        self.__mq = mq
        
        args = []
        args.append('summary')
        self.vcs.addArguments(args, self.vcs.options['global'])
        args.append("--remote")
        if self.__mq:
            args.append("--mq")
        
        # find the root of the repo
        repodir = self.__path
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        if self.process:
            self.process.kill()
        else:
            self.process = QProcess()
            prepareProcess(self.process, Preferences.getSystem("IOEncoding"),
                           "C")
            self.process.finished.connect(self.__procFinished)
            self.process.readyReadStandardOutput.connect(self.__readStdout)
            self.process.readyReadStandardError.connect(self.__readStderr)
        
        self.process.setWorkingDirectory(repodir)
        
        self.__buffer = []
        
        self.process.start('hg', args)
        procStarted = self.process.waitForStarted(5000)
        if not procStarted:
            E5MessageBox.critical(
                self,
                self.trUtf8('Process Generation Error'),
                self.trUtf8(
                    'The process {0} could not be started. '
                    'Ensure, that it is in the search path.'
                ).format('hg'))
    
    def __finish(self):
        """
        Private slot called when the process finished or the user pressed
        the button.
        """
        if self.process is not None and \
           self.process.state() != QProcess.NotRunning:
            self.process.terminate()
            QTimer.singleShot(2000, self.process.kill)
            self.process.waitForFinished(3000)
        
        self.refreshButton.setEnabled(True)
        self.process = None
    
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.buttonBox.button(QDialogButtonBox.Close):
            self.close()
        elif button == self.refreshButton:
            self.on_refreshButton_clicked()
    
    def __procFinished(self, exitCode, exitStatus):
        """
        Private slot connected to the finished signal.
        
        @param exitCode exit code of the process (integer)
        @param exitStatus exit status of the process (QProcess.ExitStatus)
        """
        self.__processOutput(self.__buffer)
        self.__finish()
    
    def __readStdout(self):
        """
        Private slot to handle the readyReadStandardOutput signal.
        
        It reads the output of the process, formats it and inserts it into
        the contents pane.
        """
        if self.process is not None:
            self.process.setReadChannel(QProcess.StandardOutput)
            
            while self.process.canReadLine():
                line = str(
                    self.process.readLine(),
                    Preferences.getSystem("IOEncoding"),
                    'replace')
                self.__buffer.append(line)
    
    def __readStderr(self):
        """
        Private slot to handle the readyReadStandardError signal.
        
        It reads the error output of the process and inserts it into the
        error pane.
        """
        if self.process is not None:
            s = str(self.process.readAllStandardError(),
                    Preferences.getSystem("IOEncoding"),
                    'replace')
            self.__showError(s)
    
    def __showError(self, out):
        """
        Private slot to show some error.
        
        @param out error to be shown (string)
        """
        self.errorGroup.show()
        self.errors.insertPlainText(out)
        self.errors.ensureCursorVisible()
    
    @pyqtSlot()
    def on_refreshButton_clicked(self):
        """
        Private slot to refresh the status display.
        """
        self.refreshButton.setEnabled(False)
        self.summary.clear()
        
        self.start(self.__path, mq=self.__mq)
    
    def __committed(self):
        """
        Private slot called after the commit has finished.
        """
        if self.isVisible():
            self.on_refreshButton_clicked()
    
    def __processOutput(self, output):
        """
        Private method to process the output into nice readable text.
        
        @param output output from the summary command (string)
        """
        infoDict = {}
        
        # step 1: parse the output
        while output:
            line = output.pop(0)
            name, value = line.split(": ", 1)
            value = value.strip()
            
            if name == "parent":
                if " " in value:
                    parent, tags = value.split(" ", 1)
                else:
                    parent = value
                    tags = ""
                rev, node = parent.split(":")
                
                remarks = []
                if tags:
                    if " (empty repository)" in tags:
                        remarks.append("@EMPTY@")
                        tags = tags.replace(" (empty repository)", "")
                    if " (no revision checked out)" in tags:
                        remarks.append("@NO_REVISION@")
                        tags = tags.replace(" (no revision checked out)", "")
                else:
                    tags = None
                
                value = infoDict.get(name, [])
                
                if rev == "-1":
                    value.append((int(rev), node, tags, None, remarks))
                else:
                    message = output.pop(0).strip()
                    value.append((int(rev), node, tags, message, remarks))
            elif name == "branch":
                pass
            elif name == "bookmarks":
                pass
            elif name == "commit":
                stateDict = {}
                if "(" in value:
                    if value.startswith("("):
                        states = ""
                        remark = value[1:-1]
                    else:
                        states, remark = value.rsplit(" (", 1)
                        remark = remark[:-1]
                else:
                    states = value
                    remark = ""
                states = states.split(", ")
                for state in states:
                    if state:
                        count, category = state.split(" ")
                        stateDict[category] = count
                value = (stateDict, remark)
            elif name == "update":
                if value.endswith("(current)"):
                    value = ("@CURRENT@", 0, 0)
                elif value.endswith("(update)"):
                    value = ("@UPDATE@", value.split(" ", 1)[0], 0)
                elif value.endswith("(merge)"):
                    parts = value.split(", ")
                    value = ("@MERGE@", parts[0].split(" ", 1)[0],
                             parts[1].split(" ", 1)[0])
                else:
                    value = ("@UNKNOWN@", 0, 0)
            elif name == "remote":
                if value == "(synced)":
                    value = (0, 0, 0, 0)
                else:
                    inc = incb = outg = outgb = 0
                    for val in value.split(", "):
                        count, category = val.split(" ", 1)
                        if category == "outgoing":
                            outg = int(count)
                        elif category.endswith("incoming"):
                            inc = int(count)
                        elif category == "incoming bookmarks":
                            incb = int(count)
                        elif category == "outgoing bookmarks":
                            outgb = int(count)
                    value = (inc, outg, incb, outgb)
            elif name == "mq":
                if value == "(empty queue)":
                    value = (0, 0)
                else:
                    applied = unapplied = 0
                    for val in value.split(", "):
                        count, category = val.split(" ", 1)
                        if category == "applied":
                            applied = int(count)
                        elif category == "unapplied":
                            unapplied = int(count)
                    value = (applied, unapplied)
            else:
                # ignore unknown entries
                continue
            
            infoDict[name] = value
        
        # step 2: build the output
        if infoDict:
            info = ["<table>"]
            pindex = 0
            for rev, node, tags, message, remarks in infoDict["parent"]:
                pindex += 1
                changeset = "{0}:{1}".format(rev, node)
                if len(infoDict["parent"]) > 1:
                    info.append(self.trUtf8(
                        "<tr><td><b>Parent #{0}</b></td><td>{1}</td></tr>")
                        .format(pindex, changeset))
                else:
                    info.append(self.trUtf8(
                        "<tr><td><b>Parent</b></td><td>{0}</td></tr>")
                        .format(changeset))
                if tags:
                    info.append(self.trUtf8(
                        "<tr><td><b>Tags</b></td><td>{0}</td></tr>")
                        .format('<br/>'.join(tags.split())))
                if message:
                    info.append(self.trUtf8(
                        "<tr><td><b>Commit Message</b></td><td>{0}</td></tr>")
                        .format(message))
                if remarks:
                    rem = []
                    if "@EMPTY@" in remarks:
                        rem.append(self.trUtf8("empty repository"))
                    if "@NO_REVISION@" in remarks:
                        rem.append(self.trUtf8("no revision checked out"))
                    info.append(self.trUtf8(
                        "<tr><td><b>Remarks</b></td><td>{0}</td></tr>")
                        .format(", ".join(rem)))
            if "branch" in infoDict:
                info.append(self.trUtf8(
                    "<tr><td><b>Branch</b></td><td>{0}</td></tr>")
                    .format(infoDict["branch"]))
            if "bookmarks" in infoDict:
                bookmarks = infoDict["bookmarks"].split()
                for i in range(len(bookmarks)):
                    if bookmarks[i].startswith("*"):
                        bookmarks[i] = "<b>{0}</b>".format(bookmarks[i])
                info.append(self.trUtf8(
                    "<tr><td><b>Bookmarks</b></td><td>{0}</td></tr>")
                    .format('<br/>'.join(bookmarks)))
            if "commit" in infoDict:
                cinfo = []
                for category, count in infoDict["commit"][0].items():
                    if category == "modified":
                        cinfo.append(self.trUtf8("{0} modified").format(count))
                    elif category == "added":
                        cinfo.append(self.trUtf8("{0} added").format(count))
                    elif category == "removed":
                        cinfo.append(self.trUtf8("{0} removed").format(count))
                    elif category == "renamed":
                        cinfo.append(self.trUtf8("{0} renamed").format(count))
                    elif category == "copied":
                        cinfo.append(self.trUtf8("{0} copied").format(count))
                    elif category == "deleted":
                        cinfo.append(self.trUtf8("{0} deleted").format(count))
                    elif category == "unknown":
                        cinfo.append(self.trUtf8("{0} unknown").format(count))
                    elif category == "ignored":
                        cinfo.append(self.trUtf8("{0} ignored").format(count))
                    elif category == "unresolved":
                        cinfo.append(
                            self.trUtf8("{0} unresolved").format(count))
                    elif category == "subrepos":
                        cinfo.append(self.trUtf8("{0} subrepos").format(count))
                remark = infoDict["commit"][1]
                if remark == "merge":
                    cinfo.append(self.trUtf8("Merge needed"))
                elif remark == "new branch":
                    cinfo.append(self.trUtf8("New Branch"))
                elif remark == "head closed":
                    cinfo.append(self.trUtf8("Head is closed"))
                elif remark == "clean":
                    cinfo.append(self.trUtf8("No commit required"))
                elif remark == "new branch head":
                    cinfo.append(self.trUtf8("New Branch Head"))
                info.append(self.trUtf8(
                    "<tr><td><b>Commit Status</b></td><td>{0}</td></tr>")
                    .format("<br/>".join(cinfo)))
            if "update" in infoDict:
                if infoDict["update"][0] == "@CURRENT@":
                    uinfo = self.trUtf8("current")
                elif infoDict["update"][0] == "@UPDATE@":
                    uinfo = self.trUtf8(
                        "%n new changeset(s)<br/>Update required", "",
                        infoDict["update"][1])
                elif infoDict["update"][0] == "@MERGE@":
                    uinfo1 = self.trUtf8(
                        "%n new changeset(s)", "", infoDict["update"][1])
                    uinfo2 = self.trUtf8(
                        "%n branch head(s)", "", infoDict["update"][2])
                    uinfo = self.trUtf8(
                        "{0}<br/>{1}<br/>Merge required",
                        "0 is changesets, 1 is branch heads")\
                        .format(uinfo1, uinfo2)
                else:
                    uinfo = self.trUtf8("unknown status")
                info.append(self.trUtf8(
                    "<tr><td><b>Update Status</b></td><td>{0}</td></tr>")
                    .format(uinfo))
            if "remote" in infoDict:
                if infoDict["remote"] == (0, 0, 0, 0):
                    rinfo = self.trUtf8("synched")
                else:
                    li = []
                    if infoDict["remote"][0]:
                        li.append(self.trUtf8("1 or more incoming"))
                    if infoDict["remote"][1]:
                        li.append(self.trUtf8("{0} outgoing")
                                  .format(infoDict["remote"][1]))
                    if infoDict["remote"][2]:
                        li.append(self.trUtf8("%n incoming bookmark(s)", "",
                                  infoDict["remote"][2]))
                    if infoDict["remote"][3]:
                        li.append(self.trUtf8("%n outgoing bookmark(s)", "",
                                  infoDict["remote"][3]))
                    rinfo = "<br/>".join(li)
                info.append(self.trUtf8(
                    "<tr><td><b>Remote Status</b></td><td>{0}</td></tr>")
                    .format(rinfo))
            if "mq" in infoDict:
                if infoDict["mq"] == (0, 0):
                    qinfo = self.trUtf8("empty queue")
                else:
                    li = []
                    if infoDict["mq"][0]:
                        li.append(self.trUtf8("{0} applied")
                                  .format(infoDict["mq"][0]))
                    if infoDict["mq"][1]:
                        li.append(self.trUtf8("{0} unapplied")
                                  .format(infoDict["mq"][1]))
                    qinfo = "<br/>".join(li)
                info.append(self.trUtf8(
                    "<tr><td><b>Queues Status</b></td><td>{0}</td></tr>")
                    .format(qinfo))
            info.append("</table>")
        else:
            info = [self.trUtf8("<p>No status information available.</p>")]
        
        self.summary.insertHtml("\n".join(info))
