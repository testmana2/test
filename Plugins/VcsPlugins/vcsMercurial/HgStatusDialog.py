# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show the output of the hg status command process.
"""

import os

from PyQt4.QtCore import pyqtSlot, SIGNAL, Qt, QProcess, QTimer
from PyQt4.QtGui import QWidget, QDialogButtonBox, QMenu, QHeaderView, QTreeWidgetItem, \
    QMessageBox, QLineEdit

from E5Gui.E5Application import e5App

from .Ui_HgStatusDialog import Ui_HgStatusDialog

import Preferences

class HgStatusDialog(QWidget, Ui_HgStatusDialog):
    """
    Class implementing a dialog to show the output of the hg status command process.
    """
    def __init__(self, vcs, parent = None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param parent parent widget (QWidget)
        """
        QWidget.__init__(self, parent)
        self.setupUi(self)
        
        self.__statusColumn = 0
        self.__pathColumn = 1
        self.__lastColumn = self.statusList.columnCount()
        
        self.refreshButton = \
            self.buttonBox.addButton(self.trUtf8("Refresh"), QDialogButtonBox.ActionRole)
        self.refreshButton.setToolTip(self.trUtf8("Press to refresh the status display"))
        self.refreshButton.setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.process = None
        self.vcs = vcs
        self.connect(self.vcs, SIGNAL("committed()"), self.__committed)
        
        self.statusList.headerItem().setText(self.__lastColumn, "")
        self.statusList.header().setSortIndicator(self.__pathColumn, Qt.AscendingOrder)
        
        self.menuactions = []
        self.menu = QMenu()
        self.menuactions.append(self.menu.addAction(\
            self.trUtf8("Commit changes to repository..."), self.__commit))
        self.menu.addSeparator()
        self.menuactions.append(self.menu.addAction(\
            self.trUtf8("Add to repository"), self.__add))
        self.menuactions.append(self.menu.addAction(\
            self.trUtf8("Revert changes"), self.__revert))
        self.menu.addSeparator()
        self.menuactions.append(self.menu.addAction(self.trUtf8("Adjust column sizes"),
            self.__resizeColumns))
        for act in self.menuactions:
            act.setEnabled(False)
        
        self.statusList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.connect(self.statusList, 
                     SIGNAL("customContextMenuRequested(const QPoint &)"),
                     self.__showContextMenu)
        
        self.modifiedIndicators = [
            self.trUtf8('added'), 
            self.trUtf8('modified'), 
            self.trUtf8('removed'), 
        ]
        
        self.unversionedIndicators = [
            self.trUtf8('not tracked'), 
        ]
        
        self.status = {
            'A' : self.trUtf8('added'),
            'C' : self.trUtf8('normal'),
            'I' : self.trUtf8('ignored'),
            'M' : self.trUtf8('modified'),
            'R' : self.trUtf8('removed'),
            '?' : self.trUtf8('not tracked'),
            '!' : self.trUtf8('missing'),
        }
    
    def __resort(self):
        """
        Private method to resort the tree.
        """
        self.statusList.sortItems(self.statusList.sortColumn(), 
            self.statusList.header().sortIndicatorOrder())
    
    def __resizeColumns(self):
        """
        Private method to resize the list columns.
        """
        self.statusList.header().resizeSections(QHeaderView.ResizeToContents)
        self.statusList.header().setStretchLastSection(True)
    
    def __generateItem(self, status, path):
        """
        Private method to generate a status item in the status list.
        
        @param status status indicator (string)
        @param path path of the file or directory (string)
        """
        itm = QTreeWidgetItem(self.statusList, [
            self.status[status], 
            path, 
        ])
        
        itm.setTextAlignment(0, Qt.AlignHCenter)
        itm.setTextAlignment(1, Qt.AlignLeft)
    
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
        Public slot to start the hg status command.
        
        @param fn filename(s)/directoryname(s) to show the status of
            (string or list of strings)
        """
        self.errorGroup.hide()
        self.intercept = False
        self.args = fn
        
        if self.process:
            self.process.kill()
        else:
            self.process = QProcess()
            self.connect(self.process, SIGNAL('finished(int, QProcess::ExitStatus)'),
                self.__procFinished)
            self.connect(self.process, SIGNAL('readyReadStandardOutput()'),
                self.__readStdout)
            self.connect(self.process, SIGNAL('readyReadStandardError()'),
                self.__readStderr)
        
        args = []
        args.append('status')
        self.vcs.addArguments(args, self.vcs.options['global'])
        self.vcs.addArguments(args, self.vcs.options['status'])
        
        if isinstance(fn, list):
            self.dname, fnames = self.vcs.splitPathList(fn)
            self.vcs.addArguments(args, fn)
        else:
            self.dname, fname = self.vcs.splitPath(fn)
            args.append(fn)
        
        # find the root of the repo
        repodir = self.dname
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        self.process.setWorkingDirectory(repodir)
        
        self.setWindowTitle(self.trUtf8('Mercurial Status'))
        
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
        self.refreshButton.setEnabled(True)
        
        for act in self.menuactions:
            act.setEnabled(True)
        
        self.process = None
        
        self.statusList.doItemsLayout()
        self.__resort()
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
        elif button == self.refreshButton:
            self.on_refreshButton_clicked()
    
    def __procFinished(self, exitCode, exitStatus):
        """
        Private slot connected to the finished signal.
        
        @param exitCode exit code of the process (integer)
        @param exitStatus exit status of the process (QProcess.ExitStatus)
        """
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
                line = str(self.process.readLine(), 
                        Preferences.getSystem("IOEncoding"), 
                        'replace')
                if line[0] in "ACIMR?!" and line[1] == " ":
                    status, path = line.strip().split(" ", 1)
                    self.__generateItem(status, path)
    
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
    
    @pyqtSlot()
    def on_refreshButton_clicked(self):
        """
        Private slot to refresh the status display.
        """
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.inputGroup.setEnabled(True)
        self.inputGroup.show()
        self.refreshButton.setEnabled(False)
        
        for act in self.menuactions:
            act.setEnabled(False)
        
        self.statusList.clear()
        
        self.start(self.args)
    
    ############################################################################
    ## Context menu handling methods
    ############################################################################
    
    def __showContextMenu(self, coord):
        """
        Protected slot to show the context menu of the status list.
        
        @param coord the position of the mouse pointer (QPoint)
        """
        self.menu.popup(self.mapToGlobal(coord))
    
    def __commit(self):
        """
        Private slot to handle the Commit context menu entry.
        """
        names = [os.path.join(self.dname, itm.text(self.__pathColumn)) \
                 for itm in self.__getModifiedItems()]
        if not names:
            QMessageBox.information(self,
                self.trUtf8("Commit"),
                self.trUtf8("""There are no uncommitted changes available/selected."""))
            return
        
        if Preferences.getVCS("AutoSaveFiles"):
            vm = e5App().getObject("ViewManager")
            for name in names:
                vm.saveEditor(name)
        self.vcs.vcsCommit(names, '')
    
    def __committed(self):
        """
        Private slot called after the commit has finished.
        """
        if self.isVisible():
            self.on_refreshButton_clicked()
            self.vcs.checkVCSStatus()
    
    def __add(self):
        """
        Private slot to handle the Add context menu entry.
        """
        names = [os.path.join(self.dname, itm.text(self.__pathColumn)) \
                 for itm in self.__getUnversionedItems()]
        if not names:
            QMessageBox.information(self,
                self.trUtf8("Add"),
                self.trUtf8("""There are no unversioned entries available/selected."""))
            return
        
        self.vcs.vcsAdd(names)
        self.on_refreshButton_clicked()
        
        project = e5App().getObject("Project")
        for name in names:
            project.getModel().updateVCSStatus(name)
        self.vcs.checkVCSStatus()
    
    def __revert(self):
        """
        Private slot to handle the Revert context menu entry.
        """
        names = [os.path.join(self.dname, itm.text(self.__pathColumn)) \
                 for itm in self.__getModifiedItems()]
        if not names:
            QMessageBox.information(self,
                self.trUtf8("Revert"),
                self.trUtf8("""There are no uncommitted changes available/selected."""))
            return
        
        self.vcs.vcsRevert(names)
        self.on_refreshButton_clicked()
        
        project = e5App().getObject("Project")
        for name in names:
            project.getModel().updateVCSStatus(name)
        self.vcs.checkVCSStatus()
    
    def __getModifiedItems(self):
        """
        Private method to retrieve all entries, that have a modified status.
        
        @return list of all items with a modified status
        """
        modifiedItems = []
        for itm in self.statusList.selectedItems():
            if itm.text(self.__statusColumn) in self.modifiedIndicators:
                modifiedItems.append(itm)
        return modifiedItems
    
    def __getUnversionedItems(self):
        """
        Private method to retrieve all entries, that have an unversioned status.
        
        @return list of all items with an unversioned status
        """
        unversionedItems = []
        for itm in self.statusList.selectedItems():
            if itm.text(self.__statusColumn) in self.unversionedIndicators:
                unversionedItems.append(itm)
        return unversionedItems
