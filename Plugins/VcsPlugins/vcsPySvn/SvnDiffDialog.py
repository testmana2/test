# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show the output of the svn diff command process.
"""

import os

import pysvn

from PyQt4.QtCore import QMutexLocker, QFileInfo, QDateTime, Qt, pyqtSlot
from PyQt4.QtGui import QWidget, QColor, QCursor, QBrush, QApplication, QTextCursor, \
    QDialogButtonBox

from E5Gui.E5Application import e5App
from E5Gui import E5MessageBox, E5FileDialog

from .SvnDialogMixin import SvnDialogMixin
from .Ui_SvnDiffDialog import Ui_SvnDiffDialog

import Utilities


class SvnDiffDialog(QWidget, SvnDialogMixin, Ui_SvnDiffDialog):
    """
    Class implementing a dialog to show the output of the svn diff command.
    """
    def __init__(self, vcs, parent=None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param parent parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        SvnDialogMixin.__init__(self)
        
        self.buttonBox.button(QDialogButtonBox.Save).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.vcs = vcs
        
        if Utilities.isWindowsPlatform():
            self.contents.setFontFamily("Lucida Console")
        else:
            self.contents.setFontFamily("Monospace")
        
        self.cNormalFormat = self.contents.currentCharFormat()
        self.cAddedFormat = self.contents.currentCharFormat()
        self.cAddedFormat.setBackground(QBrush(QColor(190, 237, 190)))
        self.cRemovedFormat = self.contents.currentCharFormat()
        self.cRemovedFormat.setBackground(QBrush(QColor(237, 190, 190)))
        self.cLineNoFormat = self.contents.currentCharFormat()
        self.cLineNoFormat.setBackground(QBrush(QColor(255, 220, 168)))
        
        self.client = self.vcs.getClient()
        self.client.callback_cancel = \
            self._clientCancelCallback
        self.client.callback_get_login = \
            self._clientLoginCallback
        self.client.callback_ssl_server_trust_prompt = \
            self._clientSslServerTrustPromptCallback
        
    def __getVersionArg(self, version):
        """
        Private method to get a pysvn revision object for the given version number.
        
        @param version revision (integer or string)
        @return revision object (pysvn.Revision)
        """
        if isinstance(version, int):
            return pysvn.Revision(pysvn.opt_revision_kind.number, version)
        elif version.startswith("{"):
            dateStr = version[1:-1]
            secs = QDateTime.fromString(dateStr, Qt.ISODate).toTime_t()
            return pysvn.Revision(pysvn.opt_revision_kind.date, secs)
        elif version == "HEAD":
            return pysvn.Revision(pysvn.opt_revision_kind.head)
        elif version == "COMMITTED":
            return pysvn.Revision(pysvn.opt_revision_kind.committed)
        elif version == "BASE":
            return pysvn.Revision(pysvn.opt_revision_kind.base)
        elif version == "WORKING":
            return pysvn.Revision(pysvn.opt_revision_kind.working)
        elif version == "PREV":
            return pysvn.Revision(pysvn.opt_revision_kind.previous)
        else:
            return pysvn.Revision(pysvn.opt_revision_kind.unspecified)
        
    def __getDiffSummaryKind(self, summaryKind):
        """
        Private method to get a string descripion of the diff summary.
        
        @param summaryKind (pysvn.diff_summarize.summarize_kind)
        @return one letter string indicating the change type (string)
        """
        if summaryKind == pysvn.diff_summarize_kind.delete:
            return "D"
        elif summaryKind == pysvn.diff_summarize_kind.modified:
            return "M"
        elif summaryKind == pysvn.diff_summarize_kind.added:
            return "A"
        elif summaryKind == pysvn.diff_summarize_kind.normal:
            return "N"
        else:
            return " "
        
    def start(self, fn, versions=None, urls=None, summary=False, pegRev=None):
        """
        Public slot to start the svn diff command.
        
        @param fn filename to be diffed (string)
        @param versions list of versions to be diffed (list of up to 2 integer or None)
        @keyparam urls list of repository URLs (list of 2 strings)
        @keyparam summary flag indicating a summarizing diff
            (only valid for URL diffs) (boolean)
        @keyparam pegRev revision number the filename is valid (integer)
        """
        self.buttonBox.button(QDialogButtonBox.Save).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self._reset()
        self.errorGroup.hide()
        
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QApplication.processEvents()
        self.filename = fn
        
        self.contents.clear()
        self.paras = 0
        
        if Utilities.hasEnvironmentEntry('TEMP'):
            tmpdir = Utilities.getEnvironmentEntry('TEMP')
        elif Utilities.hasEnvironmentEntry('TMPDIR'):
            tmpdir = Utilities.getEnvironmentEntry('TMPDIR')
        elif Utilities.hasEnvironmentEntry('TMP'):
            tmpdir = Utilities.getEnvironmentEntry('TMP')
        elif os.path.exists('/var/tmp'):
            tmpdir = '/var/tmp'
        elif os.path.exists('/usr/tmp'):
            tmpdir = '/usr/tmp'
        elif os.path.exists('/tmp'):
            tmpdir = '/tmp'
        else:
            E5MessageBox.critical(self,
                self.trUtf8("Subversion Diff"),
                self.trUtf8("""There is no temporary directory available."""))
            return
        
        tmpdir = os.path.join(tmpdir, 'svn_tmp')
        if not os.path.exists(tmpdir):
            os.mkdir(tmpdir)
        
        opts = self.vcs.options['global'] + self.vcs.options['diff']
        recurse = "--non-recursive" not in opts
        
        if versions is not None:
            self.raise_()
            self.activateWindow()
            rev1 = self.__getVersionArg(versions[0])
            if len(versions) == 1:
                rev2 = self.__getVersionArg("WORKING")
            else:
                rev2 = self.__getVersionArg(versions[1])
        else:
            rev1 = self.__getVersionArg("BASE")
            rev2 = self.__getVersionArg("WORKING")
        
        if urls is not None:
            rev1 = self.__getVersionArg("HEAD")
            rev2 = self.__getVersionArg("HEAD")
        
        if isinstance(fn, list):
            dname, fnames = self.vcs.splitPathList(fn)
        else:
            dname, fname = self.vcs.splitPath(fn)
            fnames = [fname]
        
        locker = QMutexLocker(self.vcs.vcsExecutionMutex)
        cwd = os.getcwd()
        os.chdir(dname)
        try:
            dname = e5App().getObject('Project').getRelativePath(dname)
            if dname:
                dname += "/"
            for name in fnames:
                self.__showError(self.trUtf8("Processing file '{0}'...\n").format(name))
                if urls is not None:
                    url1 = "{0}/{1}{2}".format(urls[0], dname, name)
                    url2 = "{0}/{1}{2}".format(urls[1], dname, name)
                    if summary:
                        diff_summary = self.client.diff_summarize(
                            url1, revision1=rev1,
                            url_or_path2=url2, revision2=rev2,
                            recurse=recurse)
                        diff_list = []
                        for diff_sum in diff_summary:
                            diff_list.append("{0} {1}".format(
                                self.__getDiffSummaryKind(diff_sum['summarize_kind']),
                                diff_sum['path']))
                        diffText = os.linesep.join(diff_list)
                    else:
                        diffText = self.client.diff(tmpdir,
                            url1, revision1=rev1,
                            url_or_path2=url2, revision2=rev2,
                            recurse=recurse)
                else:
                    if pegRev is not None:
                        diffText = self.client.diff_peg(tmpdir, name,
                            peg_revision=self.__getVersionArg(pegRev),
                            revision_start=rev1, revision_end=rev2, recurse=recurse)
                    else:
                        diffText = self.client.diff(tmpdir, name,
                            revision1=rev1, revision2=rev2, recurse=recurse)
                counter = 0
                for line in diffText.splitlines():
                    self.__appendText("{0}{1}".format(line, os.linesep))
                    counter += 1
                    if counter == 30:
                        # check for cancel every 30 lines
                        counter = 0
                        if self._clientCancelCallback():
                            break
                if self._clientCancelCallback():
                    break
        except pysvn.ClientError as e:
            self.__showError(e.args[0])
        locker.unlock()
        os.chdir(cwd)
        self.__finish()
        
        if self.paras == 0:
            self.contents.insertPlainText(
                self.trUtf8('There is no difference.'))
            return
        
        self.buttonBox.button(QDialogButtonBox.Save).setEnabled(True)
        
    def __appendText(self, line):
        """
        Private method to append text to the end of the contents pane.
        
        @param line line of text to insert (string)
        """
        if line.startswith('+') or line.startswith('>') or line.startswith('A '):
            format = self.cAddedFormat
        elif line.startswith('-') or line.startswith('<') or line.startswith('D '):
            format = self.cRemovedFormat
        elif line.startswith('@@'):
            format = self.cLineNoFormat
        else:
            format = self.cNormalFormat
        
        tc = self.contents.textCursor()
        tc.movePosition(QTextCursor.End)
        self.contents.setTextCursor(tc)
        self.contents.setCurrentCharFormat(format)
        self.contents.insertPlainText(line)
        self.paras += 1
        
    def __finish(self):
        """
        Private slot called when the user pressed the button.
        """
        QApplication.restoreOverrideCursor()
        
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        
        tc = self.contents.textCursor()
        tc.movePosition(QTextCursor.Start)
        self.contents.setTextCursor(tc)
        self.contents.ensureCursorVisible()
        
        self._cancel()
        
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.buttonBox.button(QDialogButtonBox.Close):
            self.close()
        elif button == self.buttonBox.button(QDialogButtonBox.Cancel):
            self.__finish()
        elif button == self.buttonBox.button(QDialogButtonBox.Save):
            self.on_saveButton_clicked()
        
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
            self.trUtf8("Save Diff"),
            fname,
            self.trUtf8("Patch Files (*.diff)"),
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
            res = E5MessageBox.yesNo(self,
                self.trUtf8("Save Diff"),
                self.trUtf8("<p>The patch file <b>{0}</b> already exists."
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
            E5MessageBox.critical(self, self.trUtf8('Save Diff'),
                self.trUtf8('<p>The patch file <b>{0}</b> could not be saved.'
                    '<br>Reason: {1}</p>')
                    .format(fname, str(why)))
        
    def __showError(self, msg):
        """
        Private slot to show an error message.
        
        @param msg error message to show (string)
        """
        self.errorGroup.show()
        self.errors.insertPlainText(msg)
        self.errors.ensureCursorVisible()
