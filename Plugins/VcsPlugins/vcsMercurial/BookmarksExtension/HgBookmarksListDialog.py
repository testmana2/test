# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show a list of bookmarks.
"""

import os

from PyQt4.QtCore import pyqtSlot, QProcess, Qt, QTimer, QCoreApplication
from PyQt4.QtGui import QDialog, QDialogButtonBox, QHeaderView, QTreeWidgetItem, \
    QLineEdit

from E5Gui import E5MessageBox

from .Ui_HgBookmarksListDialog import Ui_HgBookmarksListDialog

import Preferences


class HgBookmarksListDialog(QDialog, Ui_HgBookmarksListDialog):
    """
    Class implementing a dialog to show a list of bookmarks.
    """
    def __init__(self, vcs, parent=None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param parent parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.process = QProcess()
        self.vcs = vcs
        self.__bookmarksList = None
        self.__hgClient = vcs.getClient()
        
        self.bookmarksList.headerItem().setText(self.bookmarksList.columnCount(), "")
        self.bookmarksList.header().setSortIndicator(3, Qt.AscendingOrder)
        
        self.process.finished.connect(self.__procFinished)
        self.process.readyReadStandardOutput.connect(self.__readStdout)
        self.process.readyReadStandardError.connect(self.__readStderr)
        
        self.show()
        QCoreApplication.processEvents()
    
    def closeEvent(self, e):
        """
        Private slot implementing a close event handler.
        
        @param e close event (QCloseEvent)
        """
        if self.__hgClient:
            if self.__hgClient.isExecuting():
                self.__hgClient.cancel()
        else:
            if self.process is not None and \
               self.process.state() != QProcess.NotRunning:
                self.process.terminate()
                QTimer.singleShot(2000, self.process.kill)
                self.process.waitForFinished(3000)
        
        e.accept()
    
    def start(self, path, bookmarksList):
        """
        Public slot to start the bookmarks command.
        
        @param path name of directory to be listed (string)
        @param bookmarksList reference to string list receiving the bookmarks
            (list of strings)
        """
        self.errorGroup.hide()
        
        self.intercept = False
        self.activateWindow()
        
        self.__bookmarksList = bookmarksList
        dname, fname = self.vcs.splitPath(path)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        args = []
        args.append('bookmarks')
        
        if self.__hgClient:
            self.inputGroup.setEnabled(False)
            self.inputGroup.hide()
            
            out, err = self.__hgClient.runcommand(args)
            if err:
                self.__showError(err)
            if out:
                for line in out.splitlines():
                    self.__processOutputLine(line)
                    if self.__hgClient.wasCanceled():
                        break
            self.__finish()
        else:
            self.process.kill()
            self.process.setWorkingDirectory(repodir)
            
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
        
        if self.bookmarksList.topLevelItemCount() == 0:
            # no bookmarks defined
            self.__generateItem(self.trUtf8("no bookmarks defined"), "", "", "")
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
            if self.__hgClient:
                self.__hgClient.cancel()
            else:
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
        self.bookmarksList.sortItems(self.bookmarksList.sortColumn(),
            self.bookmarksList.header().sortIndicatorOrder())
    
    def __resizeColumns(self):
        """
        Private method to resize the list columns.
        """
        self.bookmarksList.header().resizeSections(QHeaderView.ResizeToContents)
        self.bookmarksList.header().setStretchLastSection(True)
    
    def __generateItem(self, revision, changeset, status, name):
        """
        Private method to generate a bookmark item in the bookmarks list.
        
        @param revision revision of the bookmark (string)
        @param changeset changeset of the bookmark (string)
        @param status of the bookmark (string)
        @param name name of the bookmark (string)
        """
        itm = QTreeWidgetItem(self.bookmarksList, [
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
            self.__processOutputLine(s)
    
    def __processOutputLine(self, line):
        """
        Private method to process the lines of output.
        
        @param line output line to be processed (string)
        """
        l = line.split()
        if l[-1][0] in "1234567890":
            # last element is a rev:changeset
            rev, changeset = l[-1].split(":", 1)
            del l[-1]
            if l[0] == "*":
                status = "current"
                del l[0]
            else:
                status = ""
            name = " ".join(l)
            self.__generateItem(rev, changeset, status, name)
            if self.__bookmarksList is not None:
                self.__bookmarksList.append(name)
    
    def __readStderr(self):
        """
        Private slot to handle the readyReadStderr signal.
        
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
        super().keyPressEvent(evt)
