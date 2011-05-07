# -*- coding: utf-8 -*-

# Copyright (c) 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show a list of incoming or outgoing bookmarks.
"""

import os

from PyQt4.QtCore import pyqtSlot, QProcess, Qt, QTimer
from PyQt4.QtGui import QDialog, QDialogButtonBox, QHeaderView, QTreeWidgetItem, \
    QLineEdit

from E5Gui import E5MessageBox

from .Ui_HgBookmarksInOutDialog import Ui_HgBookmarksInOutDialog

import Preferences


class HgBookmarksInOutDialog(QDialog, Ui_HgBookmarksInOutDialog):
    """
    Class implementing a dialog to show a list of incoming or outgoing bookmarks.
    """
    INCOMING = 0
    OUTGOING = 1
    
    def __init__(self, vcs, mode, parent=None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param mode mode of the dialog (HgBookmarksInOutDialog.INCOMING,
            HgBookmarksInOutDialog.OUTGOING)
        @param parent reference to the parent widget (QWidget)
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        if mode not in [self.INCOMING, self.OUTGOING]:
            raise ValueError("Bad value for mode")
        if mode == self.INCOMING:
            self.setWindowTitle(self.trUtf8("Mercurial Incoming Bookmarks"))
        elif mode == self.OUTGOING:
            self.setWindowTitle(self.trUtf8("Mercurial Outgoing Bookmarks"))
        
        self.process = QProcess()
        self.vcs = vcs
        self.mode = mode
        
        self.bookmarksList.headerItem().setText(self.bookmarksList.columnCount(), "")
        self.bookmarksList.header().setSortIndicator(3, Qt.AscendingOrder)
        
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
        Public slot to start the bookmarks command.
        
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
        
        args = []
        if self.mode == self.INCOMING:
            args.append('incoming')
        elif self.mode == self.OUTGOING:
            args.append('outgoing')
        else:
            raise ValueError("Bad value for mode")
        args.append('--bookmarks')
        
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
            self.__generateItem(self.trUtf8("no bookmarks found"), "")
        self.bookmarksList.doItemsLayout()
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
        self.bookmarksList.sortItems(self.bookmarksList.sortColumn(),
            self.bookmarksList.header().sortIndicatorOrder())
    
    def __resizeColumns(self):
        """
        Private method to resize the list columns.
        """
        self.bookmarksList.header().resizeSections(QHeaderView.ResizeToContents)
        self.bookmarksList.header().setStretchLastSection(True)
    
    def __generateItem(self, changeset, name):
        """
        Private method to generate a bookmark item in the bookmarks list.
        
        @param changeset changeset of the bookmark (string)
        @param name name of the bookmark (string)
        """
        itm = QTreeWidgetItem(self.bookmarksList, [
            name,
            changeset])
        itm.setTextAlignment(1, Qt.AlignRight)
    
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
                    'replace')
            if s.startswith(" "):
                l = s.strip().split()
                changeset = l[-1]
                del l[-1]
                name = " ".join(l)
                self.__generateItem(changeset, name)
    
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
