# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show the output of the svn log command process.
"""

import os

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from .Ui_SvnLogDialog import Ui_SvnLogDialog
from .SvnDiffDialog import SvnDiffDialog

import Utilities
import Preferences

class SvnLogDialog(QWidget, Ui_SvnLogDialog):
    """
    Class implementing a dialog to show the output of the svn log command process.
    
    The dialog is nonmodal. Clicking a link in the upper text pane shows 
    a diff of the versions.
    """
    def __init__(self, vcs, parent = None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param parent parent widget (QWidget)
        """
        QWidget.__init__(self, parent)
        self.setupUi(self)
        
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        
        self.process = QProcess()
        self.vcs = vcs
        
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
        
        self.rx_sep = QRegExp('\\-+\\s*')
        self.rx_sep2 = QRegExp('=+\\s*')
        self.rx_rev = QRegExp('rev ([0-9]+):  ([^|]*) \| ([^|]*) \| ([0-9]+) .*')
        # "rev" followed by one or more decimals followed by a colon followed
        # anything up to " | " (twice) followed by one or more decimals followed
        # by anything
        self.rx_rev2 = QRegExp('r([0-9]+) \| ([^|]*) \| ([^|]*) \| ([0-9]+) .*')
        # "r" followed by one or more decimals followed by " | " followed
        # anything up to " | " (twice) followed by one or more decimals followed
        # by anything
        self.rx_flags = QRegExp('   ([ADM])( .*)\\s*')
        # three blanks followed by A or D or M
        self.rx_changed = QRegExp('Changed .*\\s*')
        
        self.flags = {
            'A' : self.trUtf8('Added'),
            'D' : self.trUtf8('Deleted'),
            'M' : self.trUtf8('Modified')
        }
        
        self.revisions = []  # stack of remembered revisions
        self.revString = self.trUtf8('revision')
        
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
            QTimer.singleShot(2000, self.process, SLOT('kill()'))
            self.process.waitForFinished(3000)
        
        e.accept()
        
    def start(self, fn, noEntries = 0):
        """
        Public slot to start the cvs log command.
        
        @param fn filename to show the log for (string)
        @param noEntries number of entries to show (integer)
        """
        self.errorGroup.hide()
        QApplication.processEvents()
        
        self.intercept = False
        self.filename = fn
        self.dname, self.fname = self.vcs.splitPath(fn)
        
        self.process.kill()
        
        args = []
        args.append('log')
        self.vcs.addArguments(args, self.vcs.options['global'])
        self.vcs.addArguments(args, self.vcs.options['log'])
        if noEntries:
            args.append('--limit')
            args.append(str(noEntries))
        self.activateWindow()
        self.raise_()
        args.append(self.fname)
        
        self.process.setWorkingDirectory(self.dname)
        
        self.process.start('svn', args)
        procStarted = self.process.waitForStarted()
        if not procStarted:
            self.inputGroup.setEnabled(False)
            QMessageBox.critical(None,
                self.trUtf8('Process Generation Error'),
                self.trUtf8(
                    'The process {0} could not be started. '
                    'Ensure, that it is in the search path.'
                ).format('svn'))
        
    def __procFinished(self, exitCode, exitStatus):
        """
        Private slot connected to the finished signal.
        
        @param exitCode exit code of the process (integer)
        @param exitStatus exit status of the process (QProcess.ExitStatus)
        """
        self.inputGroup.setEnabled(False)
        
        self.contents.clear()
        
        lvers = 1
        for s in self.buf:
            rev_match = False
            if self.rx_rev.exactMatch(s):
                ver = self.rx_rev.cap(1)
                author = self.rx_rev.cap(2)
                date = self.rx_rev.cap(3)
                # number of lines is ignored
                rev_match = True
            elif self.rx_rev2.exactMatch(s):
                ver = self.rx_rev2.cap(1)
                author = self.rx_rev2.cap(2)
                date = self.rx_rev2.cap(3)
                # number of lines is ignored
                rev_match = True
            
            if rev_match:
                dstr = '<b>{0} {1}</b>'.format(self.revString, ver)
                try:
                    lv = self.revisions[lvers]
                    lvers += 1
                    url = QUrl()
                    url.setScheme("file")
                    url.setPath(self.filename)
                    query = QByteArray()
                    query.append(lv).append('_').append(ver)
                    url.setEncodedQuery(query)
                    dstr += ' [<a href="%s" name="%s">%s</a>]' % (
                        url.toString(), 
                        query, 
                        self.trUtf8('diff to {0}').format(lv), 
                    )
                except IndexError:
                    pass
                dstr += '<br />\n'
                self.contents.insertHtml(dstr)
                
                dstr = self.trUtf8('<i>author: {0}</i><br />\n').format(author)
                self.contents.insertHtml(dstr)
                
                dstr = self.trUtf8('<i>date: {0}</i><br />\n').format(date)
                self.contents.insertHtml(dstr)
            
            elif self.rx_sep.exactMatch(s) or self.rx_sep2.exactMatch(s):
                self.contents.insertHtml('<hr />\n')
            
            elif self.rx_flags.exactMatch(s):
                dstr = self.flags[self.rx_flags.cap(1)]
                dstr += self.rx_flags.cap(2)
                dstr += '<br />\n'
                self.contents.insertHtml(dstr)
            
            elif self.rx_changed.exactMatch(s):
                dstr = '<br />{0}<br />\n'.format(s)
                self.contents.insertHtml(dstr)
            
            else:
                if s == "":
                    s = self.contents.insertHtml('<br />\n')
                else:
                    self.contents.insertHtml(Utilities.html_encode(s))
                    self.contents.insertHtml('<br />\n')
        
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
            if self.rx_rev.exactMatch(line):
                ver = self.rx_rev.cap(1)
                # save revision number for later use
                self.revisions.append(ver)
            elif self.rx_rev2.exactMatch(line):
                ver = self.rx_rev2.cap(1)
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
        self.contents.setSource(QUrl(''))
        filename = url.path()
        if Utilities.isWindowsPlatform():
            if filename.startswith("/"):
                filename = filename[1:]
        ver = bytes(url.encodedQuery()).decode()
        v1 = ver.split('_')[0]
        v2 = ver.split('_')[1]
        if v1 == "" or v2 == "":
            return
        self.contents.scrollToAnchor(ver)
        
        if self.diff:
            del self.diff
        self.diff = SvnDiffDialog(self.vcs)
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
        Private slot to send the input to the subversion process.
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
