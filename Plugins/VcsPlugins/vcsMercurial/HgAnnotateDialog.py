# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show the output of the hg annotate command.
"""

import os

from PyQt4.QtCore import pyqtSlot, SIGNAL, QProcess, QTimer, Qt
from PyQt4.QtGui import QDialog, QDialogButtonBox, QFont, QMessageBox, QHeaderView, \
    QTreeWidgetItem, QLineEdit

from .Ui_HgAnnotateDialog import Ui_HgAnnotateDialog

import Preferences
import Utilities

class HgAnnotateDialog(QDialog, Ui_HgAnnotateDialog):
    """
    Class implementing a dialog to show the output of the hg annotate command.
    """
    def __init__(self, vcs, parent = None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param parent parent widget (QWidget)
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.process = QProcess()
        self.vcs = vcs
        
        self.annotateList.headerItem().setText(self.annotateList.columnCount(), "")
        font = QFont(self.annotateList.font())
        if Utilities.isWindowsPlatform():
            font.setFamily("Lucida Console")
        else:
            font.setFamily("Monospace")
        self.annotateList.setFont(font)
        
        self.__ioEncoding = Preferences.getSystem("IOEncoding")
        
        self.connect(self.process, SIGNAL('finished(int, QProcess::ExitStatus)'),
            self.__procFinished)
        self.connect(self.process, SIGNAL('readyReadStandardOutput()'),
            self.__readStdout)
        self.connect(self.process, SIGNAL('readyReadStandardError()'),
            self.__readStderr)
    
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
    
    def start(self, fn):
        """
        Public slot to start the annotate command.
        
        @param fn filename to show the log for (string)
        """
        self.errorGroup.hide()
        self.intercept = False
        self.activateWindow()
        self.lineno = 1
        
        dname, fname = self.vcs.splitPath(fn)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        args = []
        args.append('annotate')
        args.append('--follow')
        args.append('--user')
        args.append('--date')
        args.append('--number')
        args.append('--changeset')
        args.append('--quiet')
        args.append(fn)
        
        self.process.kill()
        self.process.setWorkingDirectory(repodir)
        
        self.process.start('hg', args)
        procStarted = self.process.waitForStarted()
        if not procStarted:
            self.inputGroup.setEnabled(False)
            self.inputGroup.hide()
            QMessageBox.critical(None,
                self.trUtf8('Process Generation Error'),
                self.trUtf8(
                    'The process {0} could not be started. '
                    'Ensure, that it is in the search path.'
                ).format('hg'))
        else:
            self.inputGroup.setEnabled(True)
            self.inputGroup.show()
    
    def __finish(self):
        """
        Private slot called when the process finished or the user pressed the button.
        """
        if self.process is not None and \
           self.process.state() != QProcess.NotRunning:
            self.process.terminate()
            QTimer.singleShot(2000, self.process.kill)
            self.process.waitForFinished(3000)
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        
        self.inputGroup.setEnabled(False)
        self.inputGroup.hide()
        
        self.process = None
        
        self.annotateList.doItemsLayout()
        self.__resizeColumns()
    
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.buttonBox.button(QDialogButtonBox.Close):
            self.close()
        elif button == self.buttonBox.button(QDialogButtonBox.Cancel):
            self.__finish()
    
    def __procFinished(self, exitCode, exitStatus):
        """
        Private slot connected to the finished signal.
        
        @param exitCode exit code of the process (integer)
        @param exitStatus exit status of the process (QProcess.ExitStatus)
        """
        self.__finish()
    
    def __resizeColumns(self):
        """
        Private method to resize the list columns.
        """
        self.annotateList.header().resizeSections(QHeaderView.ResizeToContents)
    
    def __generateItem(self, revision, changeset, author, date, text):
        """
        Private method to generate a tag item in the taglist.
        
        @param revision revision string (string)
        @param changeset changeset string (string)
        @param author author of the change (string)
        @param date date of the tag (string)
        @param name name (path) of the tag (string)
        """
        itm = QTreeWidgetItem(self.annotateList, 
            [revision, changeset, author, date, "%d" % self.lineno, text])
        self.lineno += 1
        itm.setTextAlignment(0, Qt.AlignRight)
        itm.setTextAlignment(4, Qt.AlignRight)
    
    def __readStdout(self):
        """
        Private slot to handle the readyReadStdout signal.
        
        It reads the output of the process, formats it and inserts it into
        the annotation list.
        """
        self.process.setReadChannel(QProcess.StandardOutput)
        
        while self.process.canReadLine():
            s = str(self.process.readLine(), self.__ioEncoding, 'replace').strip()
            try:
                info, text = s.split(": ", 1)
            except ValueError:
                info = s[:-2]
                text = ""
            author, rev, changeset, date, file = info.split()
            self.__generateItem(rev, changeset, author, date, text)
    
    def __readStderr(self):
        """
        Private slot to handle the readyReadStderr signal.
        
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
        QDialog.keyPressEvent(self, evt)