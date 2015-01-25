# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show the output of the hg diff command process.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

import os

from PyQt5.QtCore import pyqtSlot, QProcess, QTimer, QFileInfo, Qt
from PyQt5.QtGui import QBrush, QColor, QTextCursor, QCursor
from PyQt5.QtWidgets import QWidget, QDialogButtonBox, QLineEdit, QApplication

from E5Gui import E5MessageBox, E5FileDialog
from E5Gui.E5Application import e5App

from .Ui_HgDiffDialog import Ui_HgDiffDialog

import Utilities
import Preferences


class HgDiffDialog(QWidget, Ui_HgDiffDialog):
    """
    Class implementing a dialog to show the output of the hg diff command
    process.
    """
    def __init__(self, vcs, parent=None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param parent parent widget (QWidget)
        """
        super(HgDiffDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.buttonBox.button(QDialogButtonBox.Save).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        
        self.process = QProcess()
        self.vcs = vcs
        self.__hgClient = self.vcs.getClient()
        
        font = Preferences.getEditorOtherFonts("MonospacedFont")
        self.contents.setFontFamily(font.family())
        self.contents.setFontPointSize(font.pointSize())
        
        self.cNormalFormat = self.contents.currentCharFormat()
        self.cAddedFormat = self.contents.currentCharFormat()
        self.cAddedFormat.setBackground(QBrush(QColor(190, 237, 190)))
        self.cRemovedFormat = self.contents.currentCharFormat()
        self.cRemovedFormat.setBackground(QBrush(QColor(237, 190, 190)))
        self.cLineNoFormat = self.contents.currentCharFormat()
        self.cLineNoFormat.setBackground(QBrush(QColor(255, 220, 168)))
        
        self.process.finished.connect(self.__procFinished)
        self.process.readyReadStandardOutput.connect(self.__readStdout)
        self.process.readyReadStandardError.connect(self.__readStderr)
    
    def closeEvent(self, e):
        """
        Protected slot implementing a close event handler.
        
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
    
    def __getVersionArg(self, version):
        """
        Private method to get a hg revision argument for the given revision.
        
        @param version revision (integer or string)
        @return version argument (string)
        """
        if version == "WORKING":
            return None
        else:
            return str(version)
    
    def start(self, fn, versions=None, bundle=None, qdiff=False):
        """
        Public slot to start the hg diff command.
        
        @param fn filename to be diffed (string)
        @param versions list of versions to be diffed (list of up to 2 strings
            or None)
        @param bundle name of a bundle file (string)
        @param qdiff flag indicating qdiff command shall be used (boolean)
        """
        self.errorGroup.hide()
        self.inputGroup.show()
        self.intercept = False
        self.filename = fn
        
        self.contents.clear()
        self.paras = 0
        
        self.filesCombo.clear()
        
        if qdiff:
            args = self.vcs.initCommand("qdiff")
            self.setWindowTitle(self.tr("Patch Contents"))
        else:
            args = self.vcs.initCommand("diff")
            
            if self.vcs.hasSubrepositories():
                args.append("--subrepos")
            
            if bundle:
                args.append('--repository')
                args.append(bundle)
            elif self.vcs.bundleFile and os.path.exists(self.vcs.bundleFile):
                args.append('--repository')
                args.append(self.vcs.bundleFile)
            
            if versions is not None:
                self.raise_()
                self.activateWindow()
                
                rev1 = self.__getVersionArg(versions[0])
                rev2 = None
                if len(versions) == 2:
                    rev2 = self.__getVersionArg(versions[1])
                
                if rev1 is not None or rev2 is not None:
                    args.append('-r')
                    if rev1 is not None and rev2 is not None:
                        args.append('{0}:{1}'.format(rev1, rev2))
                    elif rev2 is None:
                        args.append(rev1)
                    elif rev1 is None:
                        args.append(':{0}'.format(rev2))
        
        if isinstance(fn, list):
            dname, fnames = self.vcs.splitPathList(fn)
            self.vcs.addArguments(args, fn)
        else:
            dname, fname = self.vcs.splitPath(fn)
            args.append(fn)
        
        self.__oldFile = ""
        self.__oldFileLine = -1
        self.__fileSeparators = []
        
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        if self.__hgClient:
            self.inputGroup.setEnabled(False)
            self.inputGroup.hide()
            
            out, err = self.__hgClient.runcommand(args)
            
            if err:
                self.__showError(err)
            if out:
                for line in out.splitlines(True):
                    self.__processOutputLine(line)
                    if self.__hgClient.wasCanceled():
                        break
            
            self.__finish()
        else:
            # find the root of the repo
            repodir = dname
            while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
                repodir = os.path.dirname(repodir)
                if os.path.splitdrive(repodir)[1] == os.sep:
                    return
            
            self.process.kill()
            
            self.process.setWorkingDirectory(repodir)
            
            self.process.start('hg', args)
            procStarted = self.process.waitForStarted(5000)
            if not procStarted:
                QApplication.restoreOverrideCursor()
                self.inputGroup.setEnabled(False)
                self.inputGroup.hide()
                E5MessageBox.critical(
                    self,
                    self.tr('Process Generation Error'),
                    self.tr(
                        'The process {0} could not be started. '
                        'Ensure, that it is in the search path.'
                    ).format('hg'))
    
    def __procFinished(self, exitCode, exitStatus):
        """
        Private slot connected to the finished signal.
        
        @param exitCode exit code of the process (integer)
        @param exitStatus exit status of the process (QProcess.ExitStatus)
        """
        self.__finish()
    
    def __finish(self):
        """
        Private slot called when the process finished or the user pressed
        the button.
        """
        QApplication.restoreOverrideCursor()
        self.inputGroup.setEnabled(False)
        self.inputGroup.hide()
        
        if self.paras == 0:
            self.contents.setCurrentCharFormat(self.cNormalFormat)
            self.contents.setPlainText(
                self.tr('There is no difference.'))
        
        self.buttonBox.button(QDialogButtonBox.Save).setEnabled(self.paras > 0)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        self.buttonBox.button(QDialogButtonBox.Close).setFocus(
            Qt.OtherFocusReason)
        
        tc = self.contents.textCursor()
        tc.movePosition(QTextCursor.Start)
        self.contents.setTextCursor(tc)
        self.contents.ensureCursorVisible()
        
        self.filesCombo.addItem(self.tr("<Start>"), 0)
        self.filesCombo.addItem(self.tr("<End>"), -1)
        for oldFile, newFile, pos in sorted(self.__fileSeparators):
            if oldFile != newFile:
                self.filesCombo.addItem(
                    "{0}\n{1}".format(oldFile, newFile), pos)
            else:
                self.filesCombo.addItem(oldFile, pos)
    
    def __appendText(self, txt, format):
        """
        Private method to append text to the end of the contents pane.
        
        @param txt text to insert (string)
        @param format text format to be used (QTextCharFormat)
        """
        tc = self.contents.textCursor()
        tc.movePosition(QTextCursor.End)
        self.contents.setTextCursor(tc)
        self.contents.setCurrentCharFormat(format)
        self.contents.insertPlainText(txt)
    
    def __extractFileName(self, line):
        """
        Private method to extract the file name out of a file separator line.
        
        @param line line to be processed (string)
        @return extracted file name (string)
        """
        f = line.split(None, 1)[1]
        f = f.rsplit(None, 6)[0]
        f = f.split("/", 1)[1]
        return f
    
    def __processFileLine(self, line):
        """
        Private slot to process a line giving the old/new file.
        
        @param line line to be processed (string)
        """
        if line.startswith('---'):
            self.__oldFileLine = self.paras
            self.__oldFile = self.__extractFileName(line)
        else:
            self.__fileSeparators.append(
                (self.__oldFile, self.__extractFileName(line),
                 self.__oldFileLine))
    
    def __processOutputLine(self, line):
        """
        Private method to process the lines of output.
        
        @param line output line to be processed (string)
        """
        if line.startswith("--- ") or \
           line.startswith("+++ "):
            self.__processFileLine(line)
        
        if line.startswith('+'):
            format = self.cAddedFormat
        elif line.startswith('-'):
            format = self.cRemovedFormat
        elif line.startswith('@@'):
            format = self.cLineNoFormat
        else:
            format = self.cNormalFormat
        self.__appendText(line, format)
        self.paras += 1
    
    def __readStdout(self):
        """
        Private slot to handle the readyReadStandardOutput signal.
        
        It reads the output of the process, formats it and inserts it into
        the contents pane.
        """
        self.process.setReadChannel(QProcess.StandardOutput)
        
        while self.process.canReadLine():
            line = str(self.process.readLine(), self.vcs.getEncoding(),
                       'replace')
            self.__processOutputLine(line)
    
    def __readStderr(self):
        """
        Private slot to handle the readyReadStandardError signal.
        
        It reads the error output of the process and inserts it into the
        error pane.
        """
        if self.process is not None:
            s = str(self.process.readAllStandardError(),
                    self.vcs.getEncoding(), 'replace')
            self.__showError(s)
    
    def __showError(self, out):
        """
        Private slot to show some error.
        
        @param out error to be shown (string)
        """
        self.errorGroup.show()
        self.errors.insertPlainText(out)
        self.errors.ensureCursorVisible()
    
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.buttonBox.button(QDialogButtonBox.Save):
            self.on_saveButton_clicked()
    
    @pyqtSlot(int)
    def on_filesCombo_activated(self, index):
        """
        Private slot to handle the selection of a file.
        
        @param index activated row (integer)
        """
        para = self.filesCombo.itemData(index)
        
        if para == 0:
            tc = self.contents.textCursor()
            tc.movePosition(QTextCursor.Start)
            self.contents.setTextCursor(tc)
            self.contents.ensureCursorVisible()
        elif para == -1:
            tc = self.contents.textCursor()
            tc.movePosition(QTextCursor.End)
            self.contents.setTextCursor(tc)
            self.contents.ensureCursorVisible()
        else:
            # step 1: move cursor to end
            tc = self.contents.textCursor()
            tc.movePosition(QTextCursor.End)
            self.contents.setTextCursor(tc)
            self.contents.ensureCursorVisible()
            
            # step 2: move cursor to desired line
            tc = self.contents.textCursor()
            delta = tc.blockNumber() - para
            tc.movePosition(QTextCursor.PreviousBlock, QTextCursor.MoveAnchor,
                            delta)
            self.contents.setTextCursor(tc)
            self.contents.ensureCursorVisible()
    
    @pyqtSlot()
    def on_saveButton_clicked(self):
        """
        Private slot to handle the Save button press.
        
        It saves the diff shown in the dialog to a file in the local
        filesystem.
        """
        if isinstance(self.filename, list):
            if len(self.filename) > 1:
                fname = self.vcs.splitPathList(self.filename)[0]
            else:
                dname, fname = self.vcs.splitPath(self.filename[0])
                if fname != '.':
                    fname = "{0}.diff".format(self.filename[0])
                else:
                    fname = dname
        else:
            fname = self.vcs.splitPath(self.filename)[0]
        
        fname, selectedFilter = E5FileDialog.getSaveFileNameAndFilter(
            self,
            self.tr("Save Diff"),
            fname,
            self.tr("Patch Files (*.diff)"),
            None,
            E5FileDialog.Options(E5FileDialog.DontConfirmOverwrite))
        
        if not fname:
            return  # user aborted
        
        ext = QFileInfo(fname).suffix()
        if not ext:
            ex = selectedFilter.split("(*")[1].split(")")[0]
            if ex:
                fname += ex
        if QFileInfo(fname).exists():
            res = E5MessageBox.yesNo(
                self,
                self.tr("Save Diff"),
                self.tr("<p>The patch file <b>{0}</b> already exists."
                        " Overwrite it?</p>").format(fname),
                icon=E5MessageBox.Warning)
            if not res:
                return
        fname = Utilities.toNativeSeparators(fname)
        
        eol = e5App().getObject("Project").getEolString()
        try:
            f = open(fname, "w", encoding="utf-8", newline="")
            f.write(eol.join(self.contents.toPlainText().splitlines()))
            f.close()
        except IOError as why:
            E5MessageBox.critical(
                self, self.tr('Save Diff'),
                self.tr(
                    '<p>The patch file <b>{0}</b> could not be saved.'
                    '<br>Reason: {1}</p>')
                .format(fname, str(why)))
    
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
        super(HgDiffDialog, self).keyPressEvent(evt)
