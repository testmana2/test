# -*- coding: utf-8 -*-

# Copyright (c) 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show a list of applied and unapplied patches.
"""

import os

from PyQt4.QtCore import pyqtSlot, QProcess, Qt, QTimer
from PyQt4.QtGui import QDialog, QDialogButtonBox, QHeaderView, QTreeWidgetItem, \
    QLineEdit

from E5Gui import E5MessageBox

from .Ui_HgQueuesListDialog import Ui_HgQueuesListDialog

import Preferences


class HgQueuesListDialog(QDialog, Ui_HgQueuesListDialog):
    """
    Class implementing a dialog to show a list of applied and unapplied patches.
    """
    def __init__(self, vcs, parent=None):
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
        
        self.patchesList.header().setSortIndicator(0, Qt.AscendingOrder)
        
        self.process.finished.connect(self.__procFinished)
        self.process.readyReadStandardOutput.connect(self.__readStdout)
        self.process.readyReadStandardError.connect(self.__readStderr)
    
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
    
    def start(self, path):
        """
        Public slot to start the list command.
        
        @param path name of directory to be listed (string)
        """
        self.errorGroup.hide()
        
        self.intercept = False
        self.activateWindow()
        
        dname, fname = self.vcs.splitPath(path)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        self.__repodir = repodir
        self.__patchesCount = 0
        self.__getApplied()
    
    def __getApplied(self):
        """
        Private slot to get the list of applied patches.
        """
        self.__mode = "qapplied"
        
        args = []
        args.append('qapplied')
        args.append('--summary')
        
        self.process.kill()
        self.process.setWorkingDirectory(self.__repodir)
        
        self.process.start('hg', args)
        procStarted = self.process.waitForStarted()
        if not procStarted:
            self.inputGroup.setEnabled(False)
            self.inputGroup.hide()
            E5MessageBox.critical(self,
                self.trUtf8('Process Generation Error'),
                self.trUtf8(
                    'The process {0} could not be started. '
                    'Ensure, that it is in the search path.'
                ).format('hg'))
        else:
            self.inputGroup.setEnabled(True)
            self.inputGroup.show()
    
    def __getUnapplied(self):
        """
        Private slot to get the list of unapplied patches.
        """
        self.__mode = "qunapplied"
        
        args = []
        args.append('qunapplied')
        args.append('--summary')
        
        self.process.kill()
        self.process.setWorkingDirectory(self.__repodir)
        
        self.process.start('hg', args)
        procStarted = self.process.waitForStarted()
        if not procStarted:
            self.inputGroup.setEnabled(False)
            self.inputGroup.hide()
            E5MessageBox.critical(self,
                self.trUtf8('Process Generation Error'),
                self.trUtf8(
                    'The process {0} could not be started. '
                    'Ensure, that it is in the search path.'
                ).format('hg'))
        else:
            self.inputGroup.setEnabled(True)
            self.inputGroup.show()
    
    def __getTop(self):
        """
        Private slot to get patch at the top of the stack.
        """
        self.__mode = "qtop"
        
        args = []
        args.append('qtop')
        
        self.process.kill()
        self.process.setWorkingDirectory(self.__repodir)
        
        self.process.start('hg', args)
        procStarted = self.process.waitForStarted()
        if not procStarted:
            self.inputGroup.setEnabled(False)
            self.inputGroup.hide()
            E5MessageBox.critical(self,
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
        
        self.inputGroup.setEnabled(False)
        self.inputGroup.hide()
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        self.buttonBox.button(QDialogButtonBox.Close).setFocus(Qt.OtherFocusReason)
        
        self.process = None
        
        if self.patchesList.topLevelItemCount() == 0:
            # no bookmarks defined
            self.__generateItem(self.trUtf8("no patches found"), "", True)
        self.patchesList.doItemsLayout()
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
        if self.__mode == "qapplied":
            self.__getUnapplied()
        elif self.__mode == "qunapplied":
            self.__getTop()
        else:
            self.__finish()
    
    def __resort(self):
        """
        Private method to resort the tree.
        """
        self.patchesList.sortItems(self.patchesList.sortColumn(),
            self.patchesList.header().sortIndicatorOrder())
    
    def __resizeColumns(self):
        """
        Private method to resize the list columns.
        """
        self.patchesList.header().resizeSections(QHeaderView.ResizeToContents)
        self.patchesList.header().setStretchLastSection(True)
    
    def __generateItem(self, name, summary, error=False):
        """
        Private method to generate a patch item in the list of patches.
        
        @param name name of the patch (string)
        @param summary first line of the patch header (string)
        @param error flag indicating an error entry (boolean)
        """
        if error:
            itm = QTreeWidgetItem(self.patchesList, [
                "",
                name,
                "",
                summary
            ])
        else:
            self.__patchesCount += 1
            itm = QTreeWidgetItem(self.patchesList, [
                "{0:>7}".format(self.__patchesCount),
                name,
                self.__mode == "qapplied" and \
                    self.trUtf8("applied") or \
                    self.trUtf8("not applied"),
                summary
            ])
        itm.setTextAlignment(0, Qt.AlignRight)
        itm.setTextAlignment(2, Qt.AlignHCenter)
    
    def __markTopItem(self, name):
        """
        Private slot to mark the top patch entry.
        
        @param name name of the patch (string)
        """
        items = self.patchesList.findItems(name, Qt.MatchCaseSensitive, 1)
        if items:
            itm = items[0]
            for column in range(itm.columnCount()):
                font = itm.font(column)
                font.setBold(True)
                itm.setFont(column, font)
    
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
            if self.__mode == "qtop":
                self.__markTopItem(s)
            else:
                l = s.split(": ", 1)
                if len(l) == 1:
                    name, summary = l[0][:-1], ""
                else:
                    name, summary = l[0], l[1]
                self.__generateItem(name, summary)
    
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
