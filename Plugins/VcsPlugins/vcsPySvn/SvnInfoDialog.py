# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show repository related information for a
file/directory.
"""

from __future__ import unicode_literals    # __IGNORE_WARNING__

import os

import pysvn

from PyQt4.QtCore import QMutexLocker
from PyQt4.QtGui import QDialog, QApplication

from .SvnUtilities import formatTime
from .SvnDialogMixin import SvnDialogMixin
from VCS.Ui_RepositoryInfoDialog import Ui_VcsRepositoryInfoDialog


class SvnInfoDialog(QDialog, SvnDialogMixin, Ui_VcsRepositoryInfoDialog):
    """
    Class implementing a dialog to show repository related information
    for a file/directory.
    """
    def __init__(self, vcs, parent=None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param parent parent widget (QWidget)
        """
        super(SvnInfoDialog, self).__init__(parent)
        self.setupUi(self)
        SvnDialogMixin.__init__(self)
        
        self.vcs = vcs
        
        self.client = self.vcs.getClient()
        self.client.callback_cancel = \
            self._clientCancelCallback
        self.client.callback_get_login = \
            self._clientLoginCallback
        self.client.callback_ssl_server_trust_prompt = \
            self._clientSslServerTrustPromptCallback
        
        self.show()
        QApplication.processEvents()
        
    def start(self, projectPath, fn):
        """
        Public slot to start the svn info command.
        
        @param projectPath path name of the project (string)
        @param fn file or directory name relative to the project (string)
        """
        locker = QMutexLocker(self.vcs.vcsExecutionMutex)
        cwd = os.getcwd()
        os.chdir(projectPath)
        try:
            entries = self.client.info2(fn, recurse=False)
            infoStr = "<table>"
            for path, info in entries:
                infoStr += self.trUtf8(
                    "<tr><td><b>Path (relative to project):</b></td>"
                    "<td>{0}</td></tr>").format(path)
                if info['URL']:
                    infoStr += self.trUtf8(
                        "<tr><td><b>Url:</b></td><td>{0}</td></tr>")\
                        .format(info['URL'])
                if info['rev']:
                    infoStr += self.trUtf8(
                        "<tr><td><b>Revision:</b></td><td>{0}</td></tr>")\
                        .format(info['rev'].number)
                if info['repos_root_URL']:
                    infoStr += self.trUtf8(
                        "<tr><td><b>Repository root URL:</b></td>"
                        "<td>{0}</td></tr>").format(info['repos_root_URL'])
                if info['repos_UUID']:
                    infoStr += self.trUtf8(
                        "<tr><td><b>Repository UUID:</b></td>"
                        "<td>{0}</td></tr>").format(info['repos_UUID'])
                if info['last_changed_author']:
                    infoStr += self.trUtf8(
                        "<tr><td><b>Last changed author:</b></td>"
                        "<td>{0}</td></tr>")\
                        .format(info['last_changed_author'])
                if info['last_changed_date']:
                    infoStr += self.trUtf8(
                        "<tr><td><b>Last Changed Date:</b></td>"
                        "<td>{0}</td></tr>")\
                        .format(formatTime(info['last_changed_date']))
                if info['last_changed_rev'] and \
                        info['last_changed_rev'].kind == \
                            pysvn.opt_revision_kind.number:
                    infoStr += self.trUtf8(
                        "<tr><td><b>Last changed revision:</b></td>"
                        "<td>{0}</td></tr>")\
                        .format(info['last_changed_rev'].number)
                if info['kind']:
                    if info['kind'] == pysvn.node_kind.file:
                        nodeKind = self.trUtf8("file")
                    elif info['kind'] == pysvn.node_kind.dir:
                        nodeKind = self.trUtf8("directory")
                    elif info['kind'] == pysvn.node_kind.none:
                        nodeKind = self.trUtf8("none")
                    else:
                        nodeKind = self.trUtf8("unknown")
                    infoStr += self.trUtf8(
                        "<tr><td><b>Node kind:</b></td><td>{0}</td></tr>")\
                        .format(nodeKind)
                if info['lock']:
                    lockInfo = info['lock']
                    infoStr += self.trUtf8(
                        "<tr><td><b>Lock Owner:</b></td><td>{0}</td></tr>")\
                        .format(lockInfo['owner'])
                    infoStr += self.trUtf8(
                        "<tr><td><b>Lock Creation Date:</b></td>"
                        "<td>{0}</td></tr>")\
                        .format(formatTime(lockInfo['creation_date']))
                    if lockInfo['expiration_date'] is not None:
                        infoStr += \
                            self.trUtf8(
                            "<tr><td><b>Lock Expiration Date:</b></td>"
                            "<td>{0}</td></tr>")\
                            .format(formatTime(lockInfo['expiration_date']))
                    infoStr += self.trUtf8(
                        "<tr><td><b>Lock Token:</b></td><td>{0}</td></tr>")\
                        .format(lockInfo['token'])
                    infoStr += self.trUtf8(
                        "<tr><td><b>Lock Comment:</b></td><td>{0}</td></tr>")\
                        .format(lockInfo['comment'])
                if info['wc_info']:
                    wcInfo = info['wc_info']
                    if wcInfo['schedule']:
                        if wcInfo['schedule'] == pysvn.wc_schedule.normal:
                            schedule = self.trUtf8("normal")
                        elif wcInfo['schedule'] == pysvn.wc_schedule.add:
                            schedule = self.trUtf8("add")
                        elif wcInfo['schedule'] == pysvn.wc_schedule.delete:
                            schedule = self.trUtf8("delete")
                        elif wcInfo['schedule'] == pysvn.wc_schedule.replace:
                            schedule = self.trUtf8("replace")
                        infoStr += self.trUtf8(
                            "<tr><td><b>Schedule:</b></td><td>{0}</td></tr>")\
                            .format(schedule)
                    if wcInfo['copyfrom_url']:
                        infoStr += self.trUtf8(
                            "<tr><td><b>Copied From URL:</b></td>"
                            "<td>{0}</td></tr>")\
                            .format(wcInfo['copyfrom_url'])
                        infoStr += self.trUtf8(
                            "<tr><td><b>Copied From Rev:</b></td>"
                            "<td>{0}</td></tr>")\
                            .format(wcInfo['copyfrom_rev'].number)
                    if wcInfo['text_time']:
                        infoStr += self.trUtf8(
                            "<tr><td><b>Text Last Updated:</b></td>"
                            "<td>{0}</td></tr>")\
                            .format(formatTime(wcInfo['text_time']))
                    if wcInfo['prop_time']:
                        infoStr += self.trUtf8(
                            "<tr><td><b>Properties Last Updated:</b></td>"
                            "<td>{0}</td></tr>")\
                            .format(formatTime(wcInfo['prop_time']))
                    if wcInfo['checksum']:
                        infoStr += self.trUtf8(
                            "<tr><td><b>Checksum:</b></td><td>{0}</td></tr>")\
                            .format(wcInfo['checksum'])
            infoStr += "</table>"
            self.infoBrowser.setHtml(infoStr)
        except pysvn.ClientError as e:
            self.__showError(e.args[0])
        locker.unlock()
        os.chdir(cwd)
        
    def __showError(self, msg):
        """
        Private slot to show an error message.
        
        @param msg error message to show (string)
        """
        infoStr = "<p>{0}</p>".format(msg)
        self.infoBrowser.setHtml(infoStr)
