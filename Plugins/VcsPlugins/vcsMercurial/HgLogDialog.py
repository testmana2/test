# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show the output of the hg log command process.
"""

import os

from PyQt4.QtCore import pyqtSlot, QProcess, SIGNAL, QTimer, QUrl, QByteArray
from PyQt4.QtGui import QWidget, QDialogButtonBox, QApplication, QMessageBox, \
    QLineEdit, QTextCursor

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
    def __init__(self, vcs, mode = "log", parent = None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param mode mode of the dialog (string; one of log, incoming, outgoing)
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
        
        self.contents.setHtml(\
            self.trUtf8('<b>Processing your request, please wait...</b>'))
        
        self.connect(self.process, SIGNAL('finished(int, QProcess::ExitStatus)'),
            self.__procFinished)
        self.connect(self.process, SIGNAL('readyReadStandardOutput()'),
            self.__readStdout)
        self.connect(self.process, SIGNAL('readyReadStandardError()'),
            self.__readStderr)
        
        self.connect(self.contents, SIGNAL('anchorClicked(const QUrl&)'),
            self.__sourceChanged)
        
        self.revisions = []  # stack of remembered revisions
        self.revString = self.trUtf8('Revision')
        
        self.buf = []        # buffer for stdout
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
        repodir = self.dname
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        self.process.kill()
        
        self.activateWindow()
        self.raise_()
        
        args = []
        args.append(self.mode)
        self.vcs.addArguments(args, self.vcs.options['global'])
        self.vcs.addArguments(args, self.vcs.options['log'])
        if noEntries:
            args.append('--limit')
            args.append(str(noEntries))
        args.append('--template')
        args.append("change|{rev}:{node|short}\n"
                    "branches|{branches}\n"
                    "tags|{tags}\n"
                    "parents|{parents}\n"
                    "user|{author}\n"
                    "date|{date|isodate}\n"
                    "description|{desc}\n"
                    "file_adds|{file_adds}\n"
                    "files_mods|{file_mods}\n"
                    "file_dels|{file_dels}\n"
                    "@@@\n")
        if self.fname != "." or self.dname != repodir:
            args.append(self.filename)
        
        self.process.setWorkingDirectory(repodir)
        
        self.process.start('hg', args)
        procStarted = self.process.waitForStarted()
        if not procStarted:
            self.inputGroup.setEnabled(False)
            QMessageBox.critical(None,
                self.trUtf8('Process Generation Error'),
                self.trUtf8(
                    'The process {0} could not be started. '
                    'Ensure, that it is in the search path.'
                ).format('hg'))
    
    def __procFinished(self, exitCode, exitStatus):
        """
        Private slot connected to the finished signal.
        
        @param exitCode exit code of the process (integer)
        @param exitStatus exit status of the process (QProcess.ExitStatus)
        """
        self.inputGroup.setEnabled(False)
        self.inputGroup.hide()
        
        self.contents.clear()
        
        if not self.buf:
            self.errors.append(self.trUtf8("No log available for '{0}'")\
                               .format(self.filename))
            self.errorGroup.show()
            return
        
        hasInitialText = 0  # three states flag (-1, 0, 1)
        lvers = 1
        for s in self.buf:
            if s == "@@@\n":
                self.contents.insertHtml('</p>{0}<br/>\n'.format(80 * "="))
            else:
                try:
                    key, value = s.split("|", 1)
                except ValueError:
                    key = ""
                    value = s
                if key == "change":
                    if hasInitialText == 1:
                        self.contents.insertHtml('{0}<br/>\n'.format(80 * "="))
                        hasInitialText = -1
                    rev, hexRev = value.split(":")
                    dstr = '<p><b>{0} {1}</b>'.format(self.revString, value)
                    try:
                        lv = self.revisions[lvers]
                        lvers += 1
                        url = QUrl()
                        url.setScheme("file")
                        url.setPath(self.filename)
                        query = QByteArray()
                        query.append(lv.split(":")[0]).append('_').append(rev)
                        url.setEncodedQuery(query)
                        dstr += ' [<a href="{0}" name="{1}" id="{1}">{2}</a>]'.format(
                            url.toString(), 
                            str(query, encoding="ascii"), 
                            self.trUtf8('diff to {0}').format(lv), 
                        )
                    except IndexError:
                        pass
                    dstr += '<br />\n'
                    self.contents.insertHtml(dstr)
                elif key == "branches":
                    if value.strip():
                        self.contents.insertHtml(self.trUtf8("Branches: {0}<br />\n")\
                            .format(value.strip()))
                elif key == "tags":
                    if value.strip():
                        self.contents.insertHtml(self.trUtf8("Tags: {0}<br />\n")\
                            .format(value.strip()))
                elif key == "parents":
                    if value.strip():
                        self.contents.insertHtml(self.trUtf8("Parents: {0}<br />\n")\
                            .format(value.strip()))
                elif key == "user":
                    dstr = self.contents.insertHtml(
                        self.trUtf8('<i>Author: {0}</i><br />\n').format(value.strip()))
                elif key == "date":
                    date, time = value.strip().split()[:2]
                    dstr = self.contents.insertHtml(
                        self.trUtf8('<i>Date: {0}, {1}</i><br />\n')\
                            .format(date, time))
                elif key == "description":
                    self.contents.insertHtml(Utilities.html_encode(value.strip()))
                    self.contents.insertHtml('<br />\n')
                elif key == "file_adds":
                    if value.strip():
                        self.contents.insertHtml('<br />\n')
                        for f in value.strip().split():
                            self.contents.insertHtml(
                                self.trUtf8('Added {0}<br />\n')\
                                    .format(Utilities.html_encode(f)))
                elif key == "files_mods":
                    if value.strip():
                        self.contents.insertHtml('<br />\n')
                        for f in value.strip().split():
                            self.contents.insertHtml(
                                self.trUtf8('Modified {0}<br />\n')\
                                    .format(Utilities.html_encode(f)))
                elif key == "file_dels":
                    if value.strip():
                        self.contents.insertHtml('<br />\n')
                        for f in value.strip().split():
                            self.contents.insertHtml(
                                self.trUtf8('Deleted {0}<br />\n')\
                                    .format(Utilities.html_encode(f)))
                else:
                    if value.strip():
                        self.contents.insertHtml(Utilities.html_encode(value.strip()))
                    self.contents.insertHtml('<br />\n')
                    if hasInitialText == 0:
                        hasInitialText = 1
        
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
            line = str(self.process.readLine(), 
                        Preferences.getSystem("IOEncoding"), 
                        'replace')
            self.buf.append(line)
            
            if line.startswith("change|"):
                ver = line[7:]
                # save revision number for later use
                self.revisions.append(ver)
    
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
        
        if self.diff:
            del self.diff
        self.diff = HgDiffDialog(self.vcs)
        self.diff.show()
        self.diff.start(filename, [v1, v2])
    
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
