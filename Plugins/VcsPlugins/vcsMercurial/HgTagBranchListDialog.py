# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show a list of tags or branches.
"""

import os

from PyQt4.QtCore import pyqtSlot, SIGNAL, QProcess, Qt, QTimer
from PyQt4.QtGui import QDialog, QDialogButtonBox, QHeaderView, QTreeWidgetItem, \
    QMessageBox, QLineEdit

from .Ui_HgTagBranchListDialog import Ui_HgTagBranchListDialog

import Preferences

class HgTagBranchListDialog(QDialog, Ui_HgTagBranchListDialog):
    """
    Class implementing a dialog to show a list of tags or branches.
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
        self.tagsList = None
        self.allTagsList = None
        
        self.tagList.headerItem().setText(self.tagList.columnCount(), "")
        self.tagList.header().setSortIndicator(3, Qt.AscendingOrder)
        
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
    
    def start(self, path, tags, tagsList, allTagsList):
        """
        Public slot to start the tags command.
        
        @param path name of directory to be listed (string)
        @param tags flag indicating a list of tags is requested
                (False = branches, True = tags)
        @param tagsList reference to string list receiving the tags (list of strings)
        @param allsTagsList reference to string list all tags (list of strings)
        """
        self.errorGroup.hide()
        
        self.intercept = False
        self.tagsMode = tags
        if not tags:
            self.setWindowTitle(self.trUtf8("Mercurial Branches List"))
            self.tagList.headerItem().setText(2, self.trUtf8("Status"))
        self.activateWindow()
        
        self.tagsList = tagsList
        self.allTagsList = allTagsList
        dname, fname = self.vcs.splitPath(path)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        args = []
        if self.tagsMode:
            args.append('tags')
            args.append('--verbose')
        else:
            args.append('branches')
            args.append('--closed')
        
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
        
        self.tagList.doItemsLayout()
        self.__resizeColumns()
        self.__resort()
    
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
    
    def __resort(self):
        """
        Private method to resort the tree.
        """
        self.tagList.sortItems(self.tagList.sortColumn(), 
            self.tagList.header().sortIndicatorOrder())
    
    def __resizeColumns(self):
        """
        Private method to resize the list columns.
        """
        self.tagList.header().resizeSections(QHeaderView.ResizeToContents)
        self.tagList.header().setStretchLastSection(True)
    
    def __generateItem(self, revision, changeset, status, name):
        """
        Private method to generate a tag item in the tag list.
        
        @param revision revision of the tag/branch (string)
        @param changeset changeset of the tag/branch (string)
        @param status of the tag/branch (string)
        @param name name of the tag/branch (string)
        """
        itm = QTreeWidgetItem(self.tagList, [
            "{0:>7}".format(revision), 
            changeset, 
            status, 
            name])
        itm.setTextAlignment(0, Qt.AlignRight)
        itm.setTextAlignment(1, Qt.AlignRight)
        itm.setTextAlignment(2, Qt.AlignHCenter)
    
    def __readStdout(self):
        """
        Private slot to handle the readyReadStdout signal.
        
        It reads the output of the process, formats it and inserts it into
        the contents pane.
        """
        self.process.setReadChannel(QProcess.StandardOutput)
        
        while self.process.canReadLine():
            s = str(self.process.readLine(), 
                    Preferences.getSystem("IOEncoding"), 
                    'replace').strip()
            l = s.split()
            if l[-1][0] in "1234567890":
                # last element is a rev:changeset
                if self.tagsMode:
                    status = ""
                else:
                    status = self.trUtf8("active")
                rev, changeset = l[-1].split(":", 1)
                del l[-1]
            else:
                if self.tagsMode:
                    status = self.trUtf8("yes")
                else:
                    status = l[-1][1:-1]
                rev, changeset = l[-2].split(":", 1)
                del l[-2:]
            name = " ".join(l)
            self.__generateItem(rev, changeset, status, name)
            if name not in ["tip", "default"]:
                if self.tagsList is not None:
                    self.tagsList.append(name)
                if self.allTagsList is not None:
                    self.allTagsList.append(name)
    
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
