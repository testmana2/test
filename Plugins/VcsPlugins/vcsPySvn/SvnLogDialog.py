# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show the output of the svn log command process.
"""

import os
import sys

import pysvn

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from .SvnUtilities import formatTime

from .SvnDialogMixin import SvnDialogMixin
from .Ui_SvnLogDialog import Ui_SvnLogDialog
from .SvnDiffDialog import SvnDiffDialog

import Utilities

class SvnLogDialog(QWidget, SvnDialogMixin, Ui_SvnLogDialog):
    """
    Class implementing a dialog to show the output of the svn log command.
    
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
        SvnDialogMixin.__init__(self)
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.vcs = vcs
        
        self.contents.setHtml(\
            self.trUtf8('<b>Processing your request, please wait...</b>'))
        
        self.connect(self.contents, SIGNAL('anchorClicked(const QUrl&)'),
            self.__sourceChanged)
        
        self.flags = {
            'A' : self.trUtf8('Added'),
            'D' : self.trUtf8('Deleted'),
            'M' : self.trUtf8('Modified')
        }
        
        self.revString = self.trUtf8('revision')
        self.diff = None
        
        self.client = self.vcs.getClient()
        self.client.callback_cancel = \
            self._clientCancelCallback
        self.client.callback_get_login = \
            self._clientLoginCallback
        self.client.callback_ssl_server_trust_prompt = \
            self._clientSslServerTrustPromptCallback
        
    def start(self, fn, noEntries = 0):
        """
        Public slot to start the svn log command.
        
        @param fn filename to show the log for (string)
        @param noEntries number of entries to show (integer)
        """
        self.errorGroup.hide()
        
        fetchLimit = 10
        
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QApplication.processEvents()
        
        self.filename = fn
        dname, fname = self.vcs.splitPath(fn)
        
        opts = self.vcs.options['global'] + self.vcs.options['log']
        verbose = "--verbose" in opts
        
        self.activateWindow()
        self.raise_()
        
        locker = QMutexLocker(self.vcs.vcsExecutionMutex)
        cwd = os.getcwd()
        os.chdir(dname)
        try:
            fetched = 0
            logs = []
            limit = noEntries or 9999999
            while fetched < limit:
                flimit = min(fetchLimit, limit - fetched)
                if fetched == 0:
                    revstart = pysvn.Revision(pysvn.opt_revision_kind.head)
                else:
                    revstart = pysvn.Revision(\
                        pysvn.opt_revision_kind.number, nextRev)
                allLogs = self.client.log(fname, 
                                          revision_start = revstart, 
                                          discover_changed_paths = verbose,
                                          limit = flimit + 1,
                                          strict_node_history = False)
                if len(allLogs) <= flimit or self._clientCancelCallback():
                    logs.extend(allLogs)
                    break
                else:
                    logs.extend(allLogs[:-1])
                    nextRev = allLogs[-1]["revision"].number
                    fetched += fetchLimit
            locker.unlock()
            
            self.contents.clear()
            self.__pegRev = None
            for log in logs:
                ver = "%d" % log["revision"].number
                dstr = '<b>{0} {1}</b>'.format(self.revString, ver)
                if self.__pegRev is None:
                    self.__pegRev = int(ver)
                try:
                    lv = "%d" % logs[logs.index(log) + 1]["revision"].number
                    url = QUrl()
                    url.setScheme("file")
                    url.setPath(self.filename)
                    query = QByteArray()
                    query.append(lv).append('_').append(ver)
                    url.setEncodedQuery(query)
                    dstr += ' [<a href="%s" name="%s">%s</a>]' % (
                        url.toString(), query, self.trUtf8('diff to {0}').format(lv)
                    )
                except IndexError:
                    pass
                dstr += '<br />\n'
                self.contents.insertHtml(dstr)
                
                dstr = self.trUtf8('<i>author: {0}</i><br />\n').format(log["author"])
                self.contents.insertHtml(dstr)
                
                dstr = self.trUtf8('<i>date: {0}</i><br />\n')\
                    .format(formatTime(log["date"]))
                self.contents.insertHtml(dstr)
                
                self.contents.insertHtml('<br />\n')
                
                for line in log["message"].splitlines():
                    self.contents.insertHtml(Utilities.html_encode(line))
                    self.contents.insertHtml('<br />\n')
                
                if len(log['changed_paths']) > 0:
                    self.contents.insertHtml('<br />\n')
                    for changeInfo in log['changed_paths']:
                        dstr = '{0} {1}'\
                               .format(self.flags[changeInfo["action"]], 
                                       changeInfo["path"])
                        if changeInfo["copyfrom_path"] is not None:
                            dstr += self.trUtf8(" (copied from {0}, revision {1})")\
                                        .format(changeInfo["copyfrom_path"], 
                                                changeInfo["copyfrom_revision"].number)
                        dstr += '<br />\n'
                        self.contents.insertHtml(dstr)
                
                self.contents.insertHtml('<hr /><br />\n')
        except pysvn.ClientError as e:
            locker.unlock()
            self.__showError(e.args[0])
        os.chdir(cwd)
        self.__finish()
        
    def __finish(self):
        """
        Private slot called when the user pressed the button.
        """
        QApplication.restoreOverrideCursor()
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(False)
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
        ver = str(url.encodedQuery())
        v1 = ver.split('_')[0]
        v2 = ver.split('_')[1]
        if not v1 or not v2:
            return
        try:
            v1 = int(v1)
            v2 = int(v2)
        except ValueError:
            return
        self.contents.scrollToAnchor(ver)
        
        if self.diff is None:
            self.diff = SvnDiffDialog(self.vcs)
        self.diff.show()
        self.diff.start(filename, [v1, v2], pegRev = self.__pegRev)
        
    def __showError(self, msg):
        """
        Private slot to show an error message.
        
        @param msg error message to show (string or QString)
        """
        self.errorGroup.show()
        self.errors.insertPlainText(msg)
        self.errors.ensureCursorVisible()
