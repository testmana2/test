# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show the output of the hg log command process.
"""

import os

from PyQt4.QtCore import pyqtSlot, QProcess, QTimer, QUrl, QByteArray
from PyQt4.QtGui import QWidget, QDialogButtonBox, QApplication, \
    QLineEdit, QTextCursor

from E5Gui.E5Application import e5App
from E5Gui import E5MessageBox

from .Ui_HgLogDialog import Ui_HgLogDialog
from .HgDiffDialog import HgDiffDialog

import Utilities
import Preferences

class HgLogDialog(QWidget, Ui_HgLogDialog):
    """
    Class implementing a dialog to show the output of the hg log command process.
    
    The dialog is nonmodal. Clicking a link in the upper text pane shows 
    a diff of the revisions.
    """
    def __init__(self, vcs, mode = "log", bundle = None, parent = None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param mode mode of the dialog (string; one of log, incoming, outgoing)
        @param bundle name of a bundle file (string)
        @param parent parent widget (QWidget)
        """
        QWidget.__init__(self, parent)
        self.setupUi(self)
        
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        
        self.process = QProcess()
        self.vcs = vcs
        if mode in ("log", "incoming", "outgoing"):
            self.mode = mode
        else:
            self.mode = "log"
        self.bundle = bundle
        
        self.contents.setHtml(
            self.trUtf8('<b>Processing your request, please wait...</b>'))
        
        self.process.finished.connect(self.__procFinished)
        self.process.readyReadStandardOutput.connect(self.__readStdout)
        self.process.readyReadStandardError.connect(self.__readStderr)
        
        self.contents.anchorClicked.connect(self.__sourceChanged)
        
        self.revisions = []  # stack of remembered revisions
        self.revString = self.trUtf8('Revision')
        self.projectMode = False
        
        self.logEntries = []        # list of log entries
        self.lastLogEntry = {}
        self.fileCopies = {}
        self.endInitialText = False
        self.initialText = []
        
        self.diff = None
    
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
    
    def start(self, fn, noEntries = 0):
        """
        Public slot to start the hg log command.
        
        @param fn filename to show the log for (string)
        @param noEntries number of entries to show (integer)
        """
        self.errorGroup.hide()
        QApplication.processEvents()
        
        self.intercept = False
        self.filename = fn
        self.dname, self.fname = self.vcs.splitPath(fn)
        
        # find the root of the repo
        self.repodir = self.dname
        while not os.path.isdir(os.path.join(self.repodir, self.vcs.adminDir)):
            self.repodir = os.path.dirname(self.repodir)
            if os.path.splitdrive(self.repodir)[1] == os.sep:
                return
        
        self.projectMode = (self.fname == "." and self.dname == self.repodir)
        
        self.process.kill()
        
        self.activateWindow()
        self.raise_()
        
        args = []
        args.append(self.mode)
        self.vcs.addArguments(args, self.vcs.options['global'])
        self.vcs.addArguments(args, self.vcs.options['log'])
        if noEntries and self.mode == "log":
            args.append('--limit')
            args.append(str(noEntries))
        if self.mode in ("incoming", "outgoing"):
            args.append("--newest-first")
        if self.mode == "log":
            args.append('--copies')
        args.append('--style')
        args.append(os.path.join(os.path.dirname(__file__), "styles", "logDialog.style"))
        if self.mode == "incoming":
            if self.bundle:
                args.append(self.bundle)
            else:
                project = e5App().getObject("Project")
                self.vcs.bundleFile = os.path.join(
                    project.getProjectManagementDir(), "hg-bundle.hg")
                args.append('--bundle')
                args.append(self.vcs.bundleFile)
        if not self.projectMode:
            args.append(self.filename)
        
        self.process.setWorkingDirectory(self.repodir)
        
        self.process.start('hg', args)
        procStarted = self.process.waitForStarted()
        if not procStarted:
            self.inputGroup.setEnabled(False)
            E5MessageBox.critical(self,
                self.trUtf8('Process Generation Error'),
                self.trUtf8(
                    'The process {0} could not be started. '
                    'Ensure, that it is in the search path.'
                ).format('hg'))
    
    def __getParents(self, rev):
        """
        Private method to get the parents of the currently viewed file/directory.
        
        @param rev revision number to get parents for (string)
        @return list of parent revisions (list of strings)
        """
        errMsg = ""
        parents = []
        
        process = QProcess()
        args = []
        args.append("parents")
        if self.mode == "incoming":
            if self.bundle:
                args.append("--repository")
                args.append(self.bundle)
            elif self.vcs.bundleFile and os.path.exists(self.vcs.bundleFile):
                args.append("--repository")
                args.append(self.vcs.bundleFile)
        args.append("--template")
        args.append("{rev}:{node|short}\n")
        args.append("-r")
        args.append(rev)
        if not self.projectMode:
            args.append(self.filename)
        
        process.setWorkingDirectory(self.repodir)
        process.start('hg', args)
        procStarted = process.waitForStarted()
        if procStarted:
            finished = process.waitForFinished(30000)
            if finished and process.exitCode() == 0:
                output = \
                    str(process.readAllStandardOutput(), 
                        Preferences.getSystem("IOEncoding"), 
                        'replace')
                parents = [p for p in output.strip().splitlines()]
            else:
                if not finished:
                    errMsg = self.trUtf8("The hg process did not finish within 30s.")
        else:
            errMsg = self.trUtf8("Could not start the hg executable.")
        
        if errMsg:
            E5MessageBox.critical(self,
                self.trUtf8("Mercurial Error"),
                errMsg)
        
        return parents
    
    def __procFinished(self, exitCode, exitStatus):
        """
        Private slot connected to the finished signal.
        
        @param exitCode exit code of the process (integer)
        @param exitStatus exit status of the process (QProcess.ExitStatus)
        """
        self.inputGroup.setEnabled(False)
        self.inputGroup.hide()
        
        self.contents.clear()
        
        if not self.logEntries:
            self.errors.append(self.trUtf8("No log available for '{0}'")\
                               .format(self.filename))
            self.errorGroup.show()
            return
        
        html = ""
        
        if self.initialText:
            for line in self.initialText:
                html += Utilities.html_encode(line.strip())
                html += '<br />\n'
            html += '{0}<br/>\n'.format(80 * "=")
            
        for entry in self.logEntries:
            fileCopies = {}
            if entry["file_copies"]:
                for fentry in entry["file_copies"].split(", "):
                    newName, oldName = fentry[:-1].split(" (")
                    fileCopies[newName] = oldName
            
            rev, hexRev = entry["change"].split(":")
            dstr = '<p><b>{0} {1}</b>'.format(self.revString, entry["change"])
            if entry["parents"]:
                parents = entry["parents"].split()
            else:
                parents = self.__getParents(rev)
            for parent in parents:
                url = QUrl()
                url.setScheme("file")
                url.setPath(self.filename)
                query = QByteArray()
                query.append(parent.split(":")[0]).append('_').append(rev)
                url.setEncodedQuery(query)
                dstr += ' [<a href="{0}" name="{1}" id="{1}">{2}</a>]'.format(
                    url.toString(), 
                    str(query, encoding="ascii"), 
                    self.trUtf8('diff to {0}').format(parent), 
                )
            dstr += '<br />\n'
            html += dstr
            
            html += self.trUtf8("Branches: {0}<br />\n").format(entry["branches"])
            
            html += self.trUtf8("Tags: {0}<br />\n").format(entry["tags"])
            
            html += self.trUtf8("Parents: {0}<br />\n").format(entry["parents"])
            
            html += self.trUtf8('<i>Author: {0}</i><br />\n').format(entry["user"])
            
            date, time = entry["date"].split()[:2]
            html += self.trUtf8('<i>Date: {0}, {1}</i><br />\n').format(date, time)
            
            for line in entry["description"]:
                html += Utilities.html_encode(line.strip())
                html += '<br />\n'
            
            if entry["file_adds"]:
                html += '<br />\n'
                for f in entry["file_adds"].strip().split(", "):
                    if f in fileCopies:
                        html += self.trUtf8('Added {0} (copied from {1})<br />\n')\
                                .format(Utilities.html_encode(f), 
                                        Utilities.html_encode(fileCopies[f]))
                    else:
                        html += self.trUtf8('Added {0}<br />\n')\
                                .format(Utilities.html_encode(f))
            
            if entry["files_mods"]:
                html += '<br />\n'
                for f in entry["files_mods"].strip().split(", "):
                    html += self.trUtf8('Modified {0}<br />\n')\
                            .format(Utilities.html_encode(f))
            
            if entry["file_dels"]:
                html += '<br />\n'
                for f in entry["file_dels"].strip().split(", "):
                    html += self.trUtf8('Deleted {0}<br />\n')\
                            .format(Utilities.html_encode(f))
            
            html += '</p>{0}<br/>\n'.format(80 * "=")
        
        self.contents.setHtml(html)
        tc = self.contents.textCursor()
        tc.movePosition(QTextCursor.Start)
        self.contents.setTextCursor(tc)
        self.contents.ensureCursorVisible()
    
    def __readStdout(self):
        """
        Private slot to handle the readyReadStandardOutput signal. 
        
        It reads the output of the process and inserts it into a buffer.
        """
        self.process.setReadChannel(QProcess.StandardOutput)
        
        while self.process.canReadLine():
            s = str(self.process.readLine(), 
                        Preferences.getSystem("IOEncoding"), 
                        'replace')
            
            if s == "@@@\n":
                self.logEntries.append(self.lastLogEntry)
                self.lastLogEntry = {}
                self.fileCopies = {}
            else:
                try:
                    key, value = s.split("|", 1)
                except ValueError:
                    key = ""
                    value = s
                if key == "change":
                    self.endInitialText = True
                if key in ("change", "branches", "tags", "parents", "user",
                            "date", "file_copies", "file_adds", "files_mods",
                            "file_dels"):
                    self.lastLogEntry[key] = value.strip()
                elif key == "description":
                    self.lastLogEntry[key] = [value.strip()]
                else:
                    if self.endInitialText:
                        self.lastLogEntry["description"].append(value.strip())
                    else:
                        self.initialText.append(value)
    
    def __readStderr(self):
        """
        Private slot to handle the readyReadStandardError signal.
        
        It reads the error output of the process and inserts it into the
        error pane.
        """
        if self.process is not None:
            self.errorGroup.show()
            s = str(self.process.readAllStandardError(), 
                     Preferences.getSystem("IOEncoding"), 
                     'replace')
            self.errors.insertPlainText(s)
            self.errors.ensureCursorVisible()
    
    def __sourceChanged(self, url):
        """
        Private slot to handle the sourceChanged signal of the contents pane.
        
        @param url the url that was clicked (QUrl)
        """
        filename = url.path()
        if Utilities.isWindowsPlatform():
            if filename.startswith("/"):
                filename = filename[1:]
        ver = bytes(url.encodedQuery()).decode()
        v1, v2 = ver.split('_')
        if v1 == "" or v2 == "":
            return
        self.contents.scrollToAnchor(ver)
        
        if self.diff is None:
            self.diff = HgDiffDialog(self.vcs)
        self.diff.show()
        self.diff.start(filename, [v1, v2], self.bundle)
    
    def on_passwordCheckBox_toggled(self, isOn):
        """
        Private slot to handle the password checkbox toggled.
        
        @param isOn flag indicating the status of the check box (boolean)
        """
        if isOn:
            self.input.setEchoMode(QLineEdit.Password)
        else:
            self.input.setEchoMode(QLineEdit.Normal)
    
    @pyqtSlot()
    def on_sendButton_clicked(self):
        """
        Private slot to send the input to the hg process.
        """
        input = self.input.text()
        input += os.linesep
        
        if self.passwordCheckBox.isChecked():
            self.errors.insertPlainText(os.linesep)
            self.errors.ensureCursorVisible()
        else:
            self.errors.insertPlainText(input)
            self.errors.ensureCursorVisible()
        
        self.process.write(input)
        
        self.passwordCheckBox.setChecked(False)
        self.input.clear()
    
    def on_input_returnPressed(self):
        """
        Private slot to handle the press of the return key in the input field.
        """
        self.intercept = True
        self.on_sendButton_clicked()
    
    def keyPressEvent(self, evt):
        """
        Protected slot to handle a key press event.
        
        @param evt the key press event (QKeyEvent)
        """
        if self.intercept:
            self.intercept = False
            evt.accept()
            return
        QWidget.keyPressEvent(self, evt)