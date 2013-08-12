# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show the output of the hg status command process.
"""

from __future__ import unicode_literals    # __IGNORE_WARNING__
try:
    str = unicode
except (NameError):
    pass

import os

from PyQt4.QtCore import pyqtSlot, Qt, QProcess, QTimer
from PyQt4.QtGui import QWidget, QDialogButtonBox, QMenu, QHeaderView, QTreeWidgetItem, \
    QLineEdit

from E5Gui.E5Application import e5App
from E5Gui import E5MessageBox

from .Ui_HgStatusDialog import Ui_HgStatusDialog

import Preferences


class HgStatusDialog(QWidget, Ui_HgStatusDialog):
    """
    Class implementing a dialog to show the output of the hg status command process.
    """
    def __init__(self, vcs, mq=False, parent=None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param mq flag indicating to show a queue repo status (boolean)
        @param parent parent widget (QWidget)
        """
        super(HgStatusDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.__toBeCommittedColumn = 0
        self.__statusColumn = 1
        self.__pathColumn = 2
        self.__lastColumn = self.statusList.columnCount()
        
        self.refreshButton = \
            self.buttonBox.addButton(self.trUtf8("Refresh"), QDialogButtonBox.ActionRole)
        self.refreshButton.setToolTip(self.trUtf8("Press to refresh the status display"))
        self.refreshButton.setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.diff = None
        self.process = None
        self.vcs = vcs
        self.vcs.committed.connect(self.__committed)
        self.__hgClient = self.vcs.getClient()
        self.__mq = mq
        
        self.statusList.headerItem().setText(self.__lastColumn, "")
        self.statusList.header().setSortIndicator(self.__pathColumn, Qt.AscendingOrder)
        
        if mq:
            self.buttonsLine.setVisible(False)
            self.addButton.setVisible(False)
            self.diffButton.setVisible(False)
            self.sbsDiffButton.setVisible(False)
            self.revertButton.setVisible(False)
            self.forgetButton.setVisible(False)
            self.restoreButton.setVisible(False)
        
        self.menuactions = []
        self.menu = QMenu()
        if not mq:
            self.menuactions.append(self.menu.addAction(
                self.trUtf8("Commit changes to repository..."), self.__commit))
            self.menuactions.append(self.menu.addAction(
                self.trUtf8("Select all for commit"), self.__commitSelectAll))
            self.menuactions.append(self.menu.addAction(
                self.trUtf8("Deselect all from commit"), self.__commitDeselectAll))
            self.menu.addSeparator()
            self.menuactions.append(self.menu.addAction(
                self.trUtf8("Add to repository"), self.__add))
            self.menuactions.append(self.menu.addAction(
                self.trUtf8("Show differences"), self.__diff))
            self.menuactions.append(self.menu.addAction(
                self.trUtf8("Show differences side-by-side"), self.__sbsDiff))
            self.menuactions.append(self.menu.addAction(
                self.trUtf8("Remove from repository"), self.__forget))
            self.menuactions.append(self.menu.addAction(
                self.trUtf8("Revert changes"), self.__revert))
            self.menuactions.append(self.menu.addAction(
                self.trUtf8("Restore missing"), self.__restoreMissing))
            self.menu.addSeparator()
            self.menuactions.append(self.menu.addAction(
                self.trUtf8("Adjust column sizes"), self.__resizeColumns))
            for act in self.menuactions:
                act.setEnabled(False)
            
            self.statusList.setContextMenuPolicy(Qt.CustomContextMenu)
            self.statusList.customContextMenuRequested.connect(self.__showContextMenu)
        
        self.modifiedIndicators = [
            self.trUtf8('added'),
            self.trUtf8('modified'),
            self.trUtf8('removed'),
        ]
        
        self.unversionedIndicators = [
            self.trUtf8('not tracked'),
        ]
        
        self.missingIndicators = [
            self.trUtf8('missing')
        ]
        
        self.status = {
            'A': self.trUtf8('added'),
            'C': self.trUtf8('normal'),
            'I': self.trUtf8('ignored'),
            'M': self.trUtf8('modified'),
            'R': self.trUtf8('removed'),
            '?': self.trUtf8('not tracked'),
            '!': self.trUtf8('missing'),
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
        statusText = self.status[status]
        itm = QTreeWidgetItem(self.statusList, [
            "",
            statusText,
            path,
        ])
        
        itm.setTextAlignment(1, Qt.AlignHCenter)
        itm.setTextAlignment(2, Qt.AlignLeft)
    
        if status in "AMR":
            itm.setFlags(itm.flags() | Qt.ItemIsUserCheckable)
            itm.setCheckState(self.__toBeCommittedColumn, Qt.Checked)
        else:
            itm.setFlags(itm.flags() & ~Qt.ItemIsUserCheckable)
        
        if statusText not in self.__statusFilters:
            self.__statusFilters.append(statusText)
        
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
    
    def start(self, fn):
        """
        Public slot to start the hg status command.
        
        @param fn filename(s)/directoryname(s) to show the status of
            (string or list of strings)
        """
        self.errorGroup.hide()
        self.intercept = False
        self.args = fn
        
        for act in self.menuactions:
            act.setEnabled(False)
        
        self.addButton.setEnabled(False)
        self.commitButton.setEnabled(False)
        self.diffButton.setEnabled(False)
        self.sbsDiffButton.setEnabled(False)
        self.revertButton.setEnabled(False)
        self.forgetButton.setEnabled(False)
        self.restoreButton.setEnabled(False)
        
        self.statusFilterCombo.clear()
        self.__statusFilters = []
        
        if self.__mq:
            self.setWindowTitle(self.trUtf8("Mercurial Queue Repository Status"))
        else:
            self.setWindowTitle(self.trUtf8('Mercurial Status'))
        
        args = []
        args.append('status')
        self.vcs.addArguments(args, self.vcs.options['global'])
        if self.__mq:
            args.append('--mq')
            if isinstance(fn, list):
                self.dname, fnames = self.vcs.splitPathList(fn)
            else:
                self.dname, fname = self.vcs.splitPath(fn)
        else:
            self.vcs.addArguments(args, self.vcs.options['status'])
            
            if self.vcs.hasSubrepositories():
                args.append("--subrepos")
            
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
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
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
            if self.process:
                self.process.kill()
            else:
                self.process = QProcess()
                self.process.finished.connect(self.__procFinished)
                self.process.readyReadStandardOutput.connect(self.__readStdout)
                self.process.readyReadStandardError.connect(self.__readStderr)
            
            self.process.setWorkingDirectory(repodir)
            
            self.process.start('hg', args)
            procStarted = self.process.waitForStarted(5000)
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
        self.refreshButton.setEnabled(True)
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        self.buttonBox.button(QDialogButtonBox.Close).setFocus(Qt.OtherFocusReason)
        
        self.__statusFilters.sort()
        self.__statusFilters.insert(0, "<{0}>".format(self.trUtf8("all")))
        self.statusFilterCombo.addItems(self.__statusFilters)
        
        for act in self.menuactions:
            act.setEnabled(True)
        
        self.process = None
        
        self.__resort()
        self.__resizeColumns()
        
        self.__updateButtons()
        self.__updateCommitButton()
    
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
                self.__processOutputLine(line)
    
    def __processOutputLine(self, line):
        """
        Private method to process the lines of output.
        
        @param line output line to be processed (string)
        """
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
        super(HgStatusDialog, self).keyPressEvent(evt)
    
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
        
        self.statusList.clear()
        
        self.start(self.args)
    
    def __updateButtons(self):
        """
        Private method to update the VCS buttons status.
        """
        modified = len(self.__getModifiedItems())
        unversioned = len(self.__getUnversionedItems())
        missing = len(self.__getMissingItems())

        self.addButton.setEnabled(unversioned)
        self.diffButton.setEnabled(modified)
        self.sbsDiffButton.setEnabled(modified == 1)
        self.revertButton.setEnabled(modified)
        self.forgetButton.setEnabled(missing)
        self.restoreButton.setEnabled(missing)
    
    def __updateCommitButton(self):
        """
        Private method to update the Commit button status.
        """
        commitable = len(self.__getCommitableItems())
        self.commitButton.setEnabled(commitable)
    
    @pyqtSlot(str)
    def on_statusFilterCombo_activated(self, txt):
        """
        Private slot to react to the selection of a status filter.
        
        @param txt selected status filter (string)
        """
        if txt == "<{0}>".format(self.trUtf8("all")):
            for topIndex in range(self.statusList.topLevelItemCount()):
                topItem = self.statusList.topLevelItem(topIndex)
                topItem.setHidden(False)
        else:
            for topIndex in range(self.statusList.topLevelItemCount()):
                topItem = self.statusList.topLevelItem(topIndex)
                topItem.setHidden(topItem.text(self.__statusColumn) != txt)
    
    @pyqtSlot(QTreeWidgetItem, int)
    def on_statusList_itemChanged(self, item, column):
        """
        Private slot to act upon item changes.
        
        @param item reference to the changed item (QTreeWidgetItem)
        @param column index of column that changed (integer)
        """
        if column == self.__toBeCommittedColumn:
            self.__updateCommitButton()
    
    @pyqtSlot()
    def on_statusList_itemSelectionChanged(self):
        """
        Private slot to act upon changes of selected items.
        """
        self.__updateButtons()
    
    @pyqtSlot()
    def on_commitButton_clicked(self):
        """
        Private slot to handle the press of the Commit button.
        """
        self.__commit()
    
    @pyqtSlot()
    def on_addButton_clicked(self):
        """
        Private slot to handle the press of the Add button.
        """
        self.__add()
    
    @pyqtSlot()
    def on_diffButton_clicked(self):
        """
        Private slot to handle the press of the Differences button.
        """
        self.__diff()
    
    @pyqtSlot()
    def on_sbsDiffButton_clicked(self):
        """
        Private slot to handle the press of the Side-by-Side Diff button.
        """
        self.__sbsDiff()
    
    @pyqtSlot()
    def on_revertButton_clicked(self):
        """
        Private slot to handle the press of the Revert button.
        """
        self.__revert()
    
    @pyqtSlot()
    def on_forgetButton_clicked(self):
        """
        Private slot to handle the press of the Forget button.
        """
        self.__forget()
    
    @pyqtSlot()
    def on_restoreButton_clicked(self):
        """
        Private slot to handle the press of the Restore button.
        """
        self.__restoreMissing()
    
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
        if self.__mq:
            self.vcs.vcsCommit(self.dname, "", mq=True)
        else:
            names = [os.path.join(self.dname, itm.text(self.__pathColumn)) \
                     for itm in self.__getCommitableItems()]
            if not names:
                E5MessageBox.information(self,
                    self.trUtf8("Commit"),
                    self.trUtf8("""There are no entries selected to be"""
                                """ committed."""))
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
    
    def __commitSelectAll(self):
        """
        Private slot to select all entries for commit.
        """
        self.__commitSelect(True)
    
    def __commitDeselectAll(self):
        """
        Private slot to deselect all entries from commit.
        """
        self.__commitSelect(False)
    
    def __add(self):
        """
        Private slot to handle the Add context menu entry.
        """
        names = [os.path.join(self.dname, itm.text(self.__pathColumn)) \
                 for itm in self.__getUnversionedItems()]
        if not names:
            E5MessageBox.information(self,
                self.trUtf8("Add"),
                self.trUtf8("""There are no unversioned entries"""
                            """ available/selected."""))
            return
        
        self.vcs.vcsAdd(names)
        self.on_refreshButton_clicked()
        
        project = e5App().getObject("Project")
        for name in names:
            project.getModel().updateVCSStatus(name)
        self.vcs.checkVCSStatus()
    
    def __forget(self):
        """
        Private slot to handle the Remove context menu entry.
        """
        names = [os.path.join(self.dname, itm.text(self.__pathColumn)) \
                 for itm in self.__getMissingItems()]
        if not names:
            E5MessageBox.information(self,
                self.trUtf8("Remove"),
                self.trUtf8("""There are no missing entries"""
                            """ available/selected."""))
            return
        
        self.vcs.hgForget(names)
        self.on_refreshButton_clicked()
    
    def __revert(self):
        """
        Private slot to handle the Revert context menu entry.
        """
        names = [os.path.join(self.dname, itm.text(self.__pathColumn)) \
                 for itm in self.__getModifiedItems()]
        if not names:
            E5MessageBox.information(self,
                self.trUtf8("Revert"),
                self.trUtf8("""There are no uncommitted changes"""
                            """ available/selected."""))
            return
        
        self.vcs.hgRevert(names)
        self.raise_()
        self.activateWindow()
        self.on_refreshButton_clicked()
        
        project = e5App().getObject("Project")
        for name in names:
            project.getModel().updateVCSStatus(name)
        self.vcs.checkVCSStatus()
    
    def __restoreMissing(self):
        """
        Private slot to handle the Restore Missing context menu entry.
        """
        names = [os.path.join(self.dname, itm.text(self.__pathColumn))
                 for itm in self.__getMissingItems()]
        if not names:
            E5MessageBox.information(self,
                self.trUtf8("Revert"),
                self.trUtf8("""There are no missing entries"""
                            """ available/selected."""))
            return
        
        self.vcs.hgRevert(names)
        self.on_refreshButton_clicked()
        self.vcs.checkVCSStatus()
        
    def __diff(self):
        """
        Private slot to handle the Diff context menu entry.
        """
        names = [os.path.join(self.dname, itm.text(self.__pathColumn))
                 for itm in self.__getModifiedItems()]
        if not names:
            E5MessageBox.information(self,
                self.trUtf8("Differences"),
                self.trUtf8("""There are no uncommitted changes"""
                            """ available/selected."""))
            return
        
        if self.diff is None:
            from .HgDiffDialog import HgDiffDialog
            self.diff = HgDiffDialog(self.vcs)
        self.diff.show()
        self.diff.start(names)
    
    def __sbsDiff(self):
        """
        Private slot to handle the Diff context menu entry.
        """
        names = [os.path.join(self.dname, itm.text(self.__pathColumn))
                 for itm in self.__getModifiedItems()]
        if not names:
            E5MessageBox.information(self,
                self.trUtf8("Side-by-Side Diff"),
                self.trUtf8("""There are no uncommitted changes"""
                            """ available/selected."""))
            return
        elif len(names) > 1:
            E5MessageBox.information(self,
                self.trUtf8("Side-by-Side Diff"),
                self.trUtf8("""Only one file with uncommitted changes"""
                            """ must be selected."""))
            return
        
        self.vcs.hgSbsDiff(names[0])
    
    def __getCommitableItems(self):
        """
        Private method to retrieve all entries the user wants to commit.
        
        @return list of all items, the user has checked
        """
        commitableItems = []
        for index in range(self.statusList.topLevelItemCount()):
            itm = self.statusList.topLevelItem(index)
            if itm.checkState(self.__toBeCommittedColumn) == Qt.Checked:
                commitableItems.append(itm)
        return commitableItems
    
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
    
    def __getMissingItems(self):
        """
        Private method to retrieve all entries, that have a missing status.
        
        @return list of all items with a missing status
        """
        missingItems = []
        for itm in self.statusList.selectedItems():
            if itm.text(self.__statusColumn) in self.missingIndicators:
                missingItems.append(itm)
        return missingItems
    
    def __commitSelect(self, selected):
        """
        Private slot to select or deselect all entries.
        
        @param selected commit selection state to be set (boolean)
        """
        for index in range(self.statusList.topLevelItemCount()):
            itm = self.statusList.topLevelItem(index)
            if itm.flags() & Qt.ItemIsUserCheckable:
                if selected:
                    itm.setCheckState(self.__toBeCommittedColumn, Qt.Checked)
                else:
                    itm.setCheckState(self.__toBeCommittedColumn, Qt.Unchecked)
