# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the version control systems interface to Mercurial.
"""

import os
import shutil
import urllib.request, urllib.parse, urllib.error

from PyQt4.QtCore import QProcess, pyqtSignal, QFileInfo
from PyQt4.QtGui import QMessageBox, QApplication, QDialog, QInputDialog, QFileDialog

from E5Gui.E5Application import e5App
from E5Gui import E5MessageBox

from QScintilla.MiniEditor import MiniEditor

from VCS.VersionControl import VersionControl
from VCS.RepositoryInfoDialog import VcsRepositoryInfoDialog

from .HgDialog import HgDialog
from .HgCommitDialog import HgCommitDialog
from .HgOptionsDialog import HgOptionsDialog
from .HgNewProjectOptionsDialog import HgNewProjectOptionsDialog
from .HgCopyDialog import HgCopyDialog
from .HgLogDialog import HgLogDialog
from .HgLogBrowserDialog import HgLogBrowserDialog
from .HgDiffDialog import HgDiffDialog
from .HgRevisionsSelectionDialog import HgRevisionsSelectionDialog
from .HgRevisionSelectionDialog import HgRevisionSelectionDialog
from .HgMergeDialog import HgMergeDialog
from .HgStatusMonitorThread import HgStatusMonitorThread
from .HgStatusDialog import HgStatusDialog
from .HgAnnotateDialog import HgAnnotateDialog
from .HgTagDialog import HgTagDialog
from .HgTagBranchListDialog import HgTagBranchListDialog
from .HgCommandDialog import HgCommandDialog
from .HgBundleDialog import HgBundleDialog
from .HgBackoutDialog import HgBackoutDialog
from .HgServeDialog import HgServeDialog

from .ProjectBrowserHelper import HgProjectBrowserHelper

import Preferences
import Utilities

class Hg(VersionControl):
    """
    Class implementing the version control systems interface to Mercurial.
    
    @signal committed() emitted after the commit action has completed
    """
    committed = pyqtSignal()
    
    def __init__(self, plugin, parent = None, name = None):
        """
        Constructor
        
        @param plugin reference to the plugin object
        @param parent parent widget (QWidget)
        @param name name of this object (string)
        """
        VersionControl.__init__(self, parent, name)
        self.defaultOptions = {
            'global' :   [''],
            'commit' :   [''],
            'checkout' : [''],
            'update' :   [''],
            'add' :      [''],
            'remove' :   [''],
            'diff' :     [''],
            'log' :      [''],
            'history' :  [''],
            'status' :   [''],
            'tag' :      [''],
            'export' :   ['']
        }
        
        self.__plugin = plugin
        self.__ui = parent
        
        self.options = self.defaultOptions
        self.tagsList = []
        self.branchesList = []
        self.allTagsBranchesList = []
        self.showedTags = False
        self.showedBranches = False
        
        self.tagTypeList = [
            'tags', 
            'branches', 
        ]
        
        self.commandHistory = []
        
        if "HG_ASP_DOT_NET_HACK" in os.environ:
            self.adminDir = '_hg'
        else:
            self.adminDir = '.hg'
        
        self.log = None
        self.diff = None
        self.status = None
        self.tagbranchList = None
        self.annotate = None
        self.editor = None
        self.serveDlg = None
        self.bundleFile = None
        
        self.statusCache = {}
        
        self.__commitData = {}
        self.__commitDialog = None
        
        self.__forgotNames = []
    
    def getPlugin(self):
        """
        Public method to get a reference to the plugin object.
        
        @return reference to the plugin object (VcsMercurialPlugin)
        """
        return self.__plugin
    
    def vcsShutdown(self):
        """
        Public method used to shutdown the Mercurial interface.
        """
        if self.log is not None:
            self.log.close()
        if self.diff is not None:
            self.diff.close()
        if self.status is not None:
            self.status.close()
        if self.tagbranchList is not None:
            self.tagbranchList.close()
        if self.annotate is not None:
            self.annotate.close()
        if self.serveDlg is not None:
            self.serveDlg.close()
        
        if self.bundleFile and os.path.exists(self.bundleFile):
            os.remove(self.bundleFile)
    
    def vcsExists(self):
        """
        Public method used to test for the presence of the hg executable.
        
        @return flag indicating the existance (boolean) and an error message (string)
        """
        self.versionStr = ''
        errMsg = ""
        ioEncoding = Preferences.getSystem("IOEncoding")
        
        process = QProcess()
        process.start('hg', ['version'])
        procStarted = process.waitForStarted()
        if procStarted:
            finished = process.waitForFinished(30000)
            if finished and process.exitCode() == 0:
                output = \
                    str(process.readAllStandardOutput(), ioEncoding, 'replace')
                self.versionStr = output.splitlines()[0].split()[-1][0:-1]
                return True, errMsg
            else:
                if finished:
                    errMsg = \
                        self.trUtf8("The hg process finished with the exit code {0}")\
                        .format(process.exitCode())
                else:
                    errMsg = self.trUtf8("The hg process did not finish within 30s.")
        else:
            errMsg = self.trUtf8("Could not start the hg executable.")
        
        return False, errMsg
    
    def vcsInit(self, vcsDir, noDialog = False):
        """
        Public method used to initialize the mercurial repository.
        
        The initialization is done, when a project is converted into a Mercurial 
        controlled project. Therefore we always return TRUE without doing anything.
        
        @param vcsDir name of the VCS directory (string)
        @param noDialog flag indicating quiet operations (boolean)
        @return always TRUE
        """
        return True
    
    def vcsConvertProject(self, vcsDataDict, project):
        """
        Public method to convert an uncontrolled project to a version controlled project.
        
        @param vcsDataDict dictionary of data required for the conversion
        @param project reference to the project object
        """
        success = self.vcsImport(vcsDataDict, project.ppath)[0]
        if not success:
            E5MessageBox.critical(self.__ui,
                self.trUtf8("Create project repository"),
                self.trUtf8("""The project repository could not be created."""))
        else:
            pfn = project.pfile
            if not os.path.isfile(pfn):
                pfn += "z"
            project.closeProject()
            project.openProject(pfn)
    
    def vcsImport(self, vcsDataDict, projectDir, noDialog = False):
        """
        Public method used to import the project into the Subversion repository.
        
        @param vcsDataDict dictionary of data required for the import
        @param projectDir project directory (string)
        @param noDialog flag indicating quiet operations
        @return flag indicating an execution without errors (boolean)
            and a flag indicating the version controll status (boolean)
        """
        msg = vcsDataDict["message"]
        if not msg:
            msg = '***'
        
        args = []
        args.append('init')
        args.append(projectDir)
        dia = HgDialog(self.trUtf8('Creating Mercurial repository'))
        res = dia.startProcess(args)
        if res:
            dia.exec_()
        status = dia.normalExit()
        
        if status:
            status = self.hgCreateIgnoreFile(projectDir)
            
            if status:
                args = []
                args.append('commit')
                args.append('--addremove')
                args.append('--message')
                args.append(msg)
                args.append(projectDir)
                dia = HgDialog(self.trUtf8('Initial commit to Mercurial repository'))
                res = dia.startProcess(args)
                if res:
                    dia.exec_()
                status = dia.normalExit()
        
        return status, False
    
    def vcsCheckout(self, vcsDataDict, projectDir, noDialog = False):
        """
        Public method used to check the project out of a Mercurial repository (clone).
        
        @param vcsDataDict dictionary of data required for the checkout
        @param projectDir project directory to create (string)
        @param noDialog flag indicating quiet operations
        @return flag indicating an execution without errors (boolean)
        """
        noDialog = False
        try:
            rev = vcsDataDict["revision"]
        except KeyError:
            rev = None
        vcsUrl = self.hgNormalizeURL(vcsDataDict["url"])
        if vcsUrl.startswith('/'):
            vcsUrl = 'file://{0}'.format(vcsUrl)
        elif vcsUrl[1] in ['|', ':']:
            vcsUrl = 'file:///{0}'.format(vcsUrl)
        
        args = []
        args.append('clone')
        self.addArguments(args, self.options['global'])
        self.addArguments(args, self.options['checkout'])
        if rev:
            args.append("--rev")
            args.append(rev)
        args.append(self.__hgURL(vcsUrl))
        args.append(projectDir)
        
        if noDialog:
            return self.startSynchronizedProcess(QProcess(), 'hg', args)
        else:
            dia = HgDialog(self.trUtf8('Cloning project from a Mercurial repository'))
            res = dia.startProcess(args)
            if res:
                dia.exec_()
            return dia.normalExit()
    
    def vcsExport(self, vcsDataDict, projectDir):
        """
        Public method used to export a directory from the Subversion repository.
        
        @param vcsDataDict dictionary of data required for the checkout
        @param projectDir project directory to create (string)
        @return flag indicating an execution without errors (boolean)
        """
        status = self.vcsCheckout(vcsDataDict, projectDir)
        shutil.rmtree(os.path.join(projectDir, self.adminDir), True)
        if os.path.exists(os.path.join(projectDir, '.hgignore')):
            os.remove(os.path.join(projectDir, '.hgignore'))
        return status
    
    def vcsCommit(self, name, message, noDialog = False, closeBranch = False):
        """
        Public method used to make the change of a file/directory permanent in the
        Mercurial repository.
        
        @param name file/directory name to be committed (string or list of strings)
        @param message message for this operation (string)
        @param noDialog flag indicating quiet operations
        @keyparam closeBranch flag indicating a close branch commit (boolean)
        """
        msg = message
        
        if not noDialog and not msg:
            # call CommitDialog and get message from there
            if self.__commitDialog is None:
                self.__commitDialog = HgCommitDialog(self, self.__ui)
                self.__commitDialog.accepted.connect(self.__vcsCommit_Step2)
            self.__commitDialog.show()
            self.__commitDialog.raise_()
            self.__commitDialog.activateWindow()
        
        self.__commitData["name"] = name
        self.__commitData["msg"] = msg
        self.__commitData["noDialog"] = noDialog
        self.__commitData["closeBranch"] = closeBranch
        
        if noDialog:
            self.__vcsCommit_Step2()
    
    def __vcsCommit_Step2(self):
        """
        Private slot performing the second step of the commit action.
        """
        name = self.__commitData["name"]
        msg = self.__commitData["msg"]
        noDialog = self.__commitData["noDialog"]
        closeBranch = self.__commitData["closeBranch"]
        
        if self.__commitDialog is not None:
            msg = self.__commitDialog.logMessage()
            self.__commitDialog.accepted.disconnect(self.__vcsCommit_Step2)
            self.__commitDialog = None
        
        if not msg:
            msg = '***'
        
        args = []
        args.append('commit')
        self.addArguments(args, self.options['global'])
        self.addArguments(args, self.options['commit'])
        args.append("-v")
        if closeBranch:
            args.append("--close-branch")
        args.append("--message")
        args.append(msg)
        if isinstance(name, list):
            dname, fnames = self.splitPathList(name)
        else:
            dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        if isinstance(name, list):
            self.addArguments(args, fnames)
        else:
            if dname != repodir or fname != ".":
                args.append(fname)
        
        if noDialog:
            self.startSynchronizedProcess(QProcess(), "hg", args, dname)
        else:
            dia = HgDialog(self.trUtf8('Commiting changes to Mercurial repository'))
            res = dia.startProcess(args, dname)
            if res:
                dia.exec_()
        self.committed.emit()
        if self.__forgotNames:
            model = e5App().getObject("Project").getModel()
            for name in self.__forgotNames:
                model.updateVCSStatus(name)
            self.__forgotNames = []
        self.checkVCSStatus()
    
    def vcsUpdate(self, name, noDialog = False, revision = None):
        """
        Public method used to update a file/directory with the Mercurial repository.
        
        @param name file/directory name to be updated (string or list of strings)
        @param noDialog flag indicating quiet operations (boolean)
        @keyparam revision revision to update to (string)
        @return flag indicating, that the update contained an add
            or delete (boolean)
        """
        args = []
        args.append('update')
        self.addArguments(args, self.options['global'])
        self.addArguments(args, self.options['update'])
        if revision is not None:
            args.append("-r")
            args.append(revision)
        
        if isinstance(name, list):
            dname, fnames = self.splitPathList(name)
        else:
            dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return False
        
        if noDialog:
            self.startSynchronizedProcess(QProcess(), "hg", args, repodir)
            res = False
        else:
            dia = HgDialog(self.trUtf8('Synchronizing with the Mercurial repository'))
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
                res = dia.hasAddOrDelete()
        self.checkVCSStatus()
        return res
    
    def vcsAdd(self, name, isDir = False, noDialog = False):
        """
        Public method used to add a file/directory to the Mercurial repository.
        
        @param name file/directory name to be added (string)
        @param isDir flag indicating name is a directory (boolean)
        @param noDialog flag indicating quiet operations
        """
        args = []
        args.append('add')
        self.addArguments(args, self.options['global'])
        self.addArguments(args, self.options['add'])
        args.append("-v")
        
        if isinstance(name, list):
            if isDir:
                dname, fname = os.path.split(name[0])
            else:
                dname, fnames = self.splitPathList(name)
        else:
            if isDir:
                dname, fname = os.path.split(name)
            else:
                dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        if isinstance(name, list):
            self.addArguments(args, name)
        else:
            args.append(name)
        
        if noDialog:
            self.startSynchronizedProcess(QProcess(), "hg", args, repodir)
        else:
            dia = HgDialog(\
                self.trUtf8('Adding files/directories to the Mercurial repository'))
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
    
    def vcsAddBinary(self, name, isDir = False):
        """
        Public method used to add a file/directory in binary mode to the
        Mercurial repository.
        
        @param name file/directory name to be added (string)
        @param isDir flag indicating name is a directory (boolean)
        """
        self.vcsAdd(name, isDir)
    
    def vcsAddTree(self, path):
        """
        Public method to add a directory tree rooted at path to the Mercurial repository.
        
        @param path root directory of the tree to be added (string or list of strings))
        """
        self.vcsAdd(path, isDir = False)
    
    def vcsRemove(self, name, project = False, noDialog = False):
        """
        Public method used to remove a file/directory from the Mercurial repository.
        
        The default operation is to remove the local copy as well.
        
        @param name file/directory name to be removed (string or list of strings))
        @param project flag indicating deletion of a project tree (boolean) (not needed)
        @param noDialog flag indicating quiet operations
        @return flag indicating successfull operation (boolean)
        """
        args = []
        args.append('remove')
        self.addArguments(args, self.options['global'])
        self.addArguments(args, self.options['remove'])
        args.append("-v")
        if noDialog and '--force' not in args:
            args.append('--force')
        
        if isinstance(name, list):
            dname, fnames = self.splitPathList(name)
            self.addArguments(args, name)
        else:
            dname, fname = self.splitPath(name)
            args.append(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return False
        
        if noDialog:
            res = self.startSynchronizedProcess(QProcess(), "hg", args, repodir)
        else:
            dia = HgDialog(\
                self.trUtf8('Removing files/directories from the Mercurial repository'))
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
                res = dia.normalExitWithoutErrors()
        
        return res
    
    def vcsMove(self, name, project, target = None, noDialog = False):
        """
        Public method used to move a file/directory.
        
        @param name file/directory name to be moved (string)
        @param project reference to the project object
        @param target new name of the file/directory (string)
        @param noDialog flag indicating quiet operations
        @return flag indicating successfull operation (boolean)
        """
        isDir = os.path.isdir(name)
        opts = self.options['global'][:]
        force = '--force' in opts
        if force:
            opts.remove('--force')
        
        res = False
        if noDialog:
            if target is None:
                return False
            force = True
            accepted = True
        else:
            dlg = HgCopyDialog(name, None, True, force)
            accepted = dlg.exec_() == QDialog.Accepted
            if accepted:
                target, force = dlg.getData()
        
        if accepted:
            args = []
            args.append('rename')
            self.addArguments(args, opts)
            args.append("-v")
            if force:
                args.append('--force')
            args.append(name)
            args.append(target)
            
            dname, fname = self.splitPath(name)
            # find the root of the repo
            repodir = dname
            while not os.path.isdir(os.path.join(repodir, self.adminDir)):
                repodir = os.path.dirname(repodir)
                if repodir == os.sep:
                    return False
            
            if noDialog:
                res = self.startSynchronizedProcess(QProcess(), "hg", args, repodir)
            else:
                dia = HgDialog(self.trUtf8('Renaming {0}').format(name))
                res = dia.startProcess(args, repodir)
                if res:
                    dia.exec_()
                    res = dia.normalExit()
            if res:
                if target.startswith(project.getProjectPath()):
                    if isDir:
                        project.moveDirectory(name, target)
                    else:
                        project.renameFileInPdata(name, target)
                else:
                    if isDir:
                        project.removeDirectory(name)
                    else:
                        project.removeFile(name)
        return res
    
    def vcsLog(self, name):
        """
        Public method used to view the log of a file/directory from the 
        Mercurial repository.
        
        @param name file/directory name to show the log of (string)
        """
        self.log = HgLogDialog(self)
        self.log.show()
        self.log.start(name)
    
    def vcsDiff(self, name):
        """
        Public method used to view the difference of a file/directory to the 
        Mercurial repository.
        
        If name is a directory and is the project directory, all project files
        are saved first. If name is a file (or list of files), which is/are being edited 
        and has unsaved modification, they can be saved or the operation may be aborted.
        
        @param name file/directory name to be diffed (string)
        """
        if isinstance(name, list):
            names = name[:]
        else:
            names = [name]
        for nam in names:
            if os.path.isfile(nam):
                editor = e5App().getObject("ViewManager").getOpenEditor(nam)
                if editor and not editor.checkDirty() :
                    return
            else:
                project = e5App().getObject("Project")
                if nam == project.ppath and not project.saveAllScripts():
                    return
        self.diff = HgDiffDialog(self)
        self.diff.show()
        QApplication.processEvents()
        self.diff.start(name)
    
    def vcsStatus(self, name):
        """
        Public method used to view the status of files/directories in the 
        Mercurial repository.
        
        @param name file/directory name(s) to show the status of
            (string or list of strings)
        """
        self.status = HgStatusDialog(self)
        self.status.show()
        self.status.start(name)
    
    def vcsTag(self, name):
        """
        Public method used to set the tag in the Mercurial repository.
        
        @param name file/directory name to be tagged (string)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = str(dname)
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        dlg = HgTagDialog(self.tagsList)
        if dlg.exec_() == QDialog.Accepted:
            tag, tagOp = dlg.getParameters()
            if tag in self.tagsList:
                self.tagsList.remove(tag)
            self.tagsList.insert(0, tag)
        else:
            return
        
        args = []
        args.append('tag')
        if tagOp == HgTagDialog.CreateLocalTag:
            args.append('--local')
        elif tagOp == HgTagDialog.DeleteTag:
            args.append('--remove')
        args.append('--message')
        if tagOp != HgTagDialog.DeleteTag:
            tag = tag.strip().replace(" ", "_")
            args.append("Created tag <{0}>.".format(tag))
        else:
            args.append("Removed tag <{0}>.".format(tag))
        args.append(tag)
        
        dia = HgDialog(self.trUtf8('Taging in the Mercurial repository'))
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
    
    def vcsRevert(self, name):
        """
        Public method used to revert changes made to a file/directory.
        
        @param name file/directory name to be reverted (string)
        """
        args = []
        args.append('revert')
        self.addArguments(args, self.options['global'])
        args.append("--no-backup")
        args.append("-v")
        if isinstance(name, list):
            dname, fnames = self.splitPathList(name)
            self.addArguments(args, name)
        else:
            dname, fname = self.splitPath(name)
            args.append(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        dia = HgDialog(self.trUtf8('Reverting changes'))
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
        self.checkVCSStatus()
    
    def vcsMerge(self, name):
        """
        Public method used to merge a URL/revision into the local project.
        
        @param name file/directory name to be merged (string)
        """
        dname, fname = self.splitPath(name)
        
        opts = self.options['global'][:]
        force = '--force' in opts
        if force:
            del opts[opts.index('--force')]
        
        dlg = HgMergeDialog(force, self.tagsList, self.branchesList)
        if dlg.exec_() == QDialog.Accepted:
            rev, force = dlg.getParameters()
        else:
            return
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        args = []
        args.append('merge')
        self.addArguments(args, opts)
        if force:
            args.append("--force")
        if rev:
            args.append("--rev")
            args.append(rev)
        
        dia = HgDialog(self.trUtf8('Merging').format(name))
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
        self.checkVCSStatus()
    
    def vcsSwitch(self, name):
        """
        Public method used to switch a working directory to a different revision.
        
        @param name directory name to be switched (string)
        """
        dlg = HgRevisionSelectionDialog(self.tagsList, self.branchesList)
        if dlg.exec_() == QDialog.Accepted:
            rev = dlg.getRevision()
            self.vcsUpdate(name, revision = rev)

    def vcsRegisteredState(self, name):
        """
        Public method used to get the registered state of a file in the vcs.
        
        @param name filename to check (string)
        @return a combination of canBeCommited and canBeAdded
        """
        if name.endswith(os.sep):
            name = name[:-1]
        name = os.path.normcase(name)
        dname, fname = self.splitPath(name)
        
        if fname == '.' and os.path.isdir(os.path.join(dname, self.adminDir)):
            return self.canBeCommitted
        
        if name in self.statusCache:
            return self.statusCache[name]
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return 0
        
        ioEncoding = Preferences.getSystem("IOEncoding")
        process = QProcess()
        args = []
        args.append('status')
        args.append('--all')
        args.append('--noninteractive')
        process.setWorkingDirectory(repodir)
        process.start('hg', args)
        procStarted = process.waitForStarted()
        if procStarted:
            finished = process.waitForFinished(30000)
            if finished and process.exitCode() == 0:
                output = \
                    str(process.readAllStandardOutput(), ioEncoding, 'replace')
                for line in output.splitlines():
                    flag, path = line.split(" ", 1)
                    absname = os.path.join(repodir, os.path.normcase(path))
                    if flag not in "?I":
                        if fname == '.':
                            if absname.startswith(dname + os.path.sep):
                                return self.canBeCommitted
                            if absname == dname:
                                return self.canBeCommitted
                        else:
                            if absname == name:
                                return self.canBeCommitted
        
        return self.canBeAdded
    
    def vcsAllRegisteredStates(self, names, dname, shortcut = True):
        """
        Public method used to get the registered states of a number of files in the vcs.
        
        <b>Note:</b> If a shortcut is to be taken, the code will only check, if the named
        directory has been scanned already. If so, it is assumed, that the states for
        all files have been populated by the previous run.
        
        @param names dictionary with all filenames to be checked as keys
        @param dname directory to check in (string)
        @param shortcut flag indicating a shortcut should be taken (boolean)
        @return the received dictionary completed with a combination of 
            canBeCommited and canBeAdded or None in order to signal an error
        """
        if dname.endswith(os.sep):
            dname = dname[:-1]
        dname = os.path.normcase(dname)
        
        found = False
        for name in list(self.statusCache.keys()):
            if name in names:
                found = True
                names[name] = self.statusCache[name]
        
        if not found:
            # find the root of the repo
            repodir = dname
            while not os.path.isdir(os.path.join(repodir, self.adminDir)):
                repodir = os.path.dirname(repodir)
                if repodir == os.sep:
                    return names
        
            ioEncoding = Preferences.getSystem("IOEncoding")
            process = QProcess()
            args = []
            args.append('status')
            args.append('--all')
            args.append('--noninteractive')
            process.setWorkingDirectory(dname)
            process.start('hg', args)
            procStarted = process.waitForStarted()
            if procStarted:
                finished = process.waitForFinished(30000)
                if finished and process.exitCode() == 0:
                    dirs = [x for x in names.keys() if os.path.isdir(x)]
                    output = \
                        str(process.readAllStandardOutput(), ioEncoding, 'replace')
                    for line in output.splitlines():
                        flag, path = line.split(" ", 1)
                        name = os.path.normcase(os.path.join(repodir, path))
                        dirName = os.path.dirname(name)
                        if name.startswith(dname):
                            if flag not in "?I":
                                if name in names:
                                    names[name] = self.canBeCommitted
                                if dirName in names:
                                    names[dirName] = self.canBeCommitted
                                if dirs:
                                    for d in dirs:
                                        if name.startswith(d):
                                            names[d] = self.canBeCommitted
                                            dirs.remove(d)
                                            break
                        if flag not in "?I":
                            self.statusCache[name] = self.canBeCommitted
                            self.statusCache[dirName] = self.canBeCommitted
                        else:
                            self.statusCache[name] = self.canBeAdded
                            if dirName not in self.statusCache:
                                self.statusCache[dirName] = self.canBeAdded
        
        return names
    
    def clearStatusCache(self):
        """
        Public method to clear the status cache.
        """
        self.statusCache = {}
    
    def vcsName(self):
        """
        Public method returning the name of the vcs.
        
        @return always 'Mercurial' (string)
        """
        return "Mercurial"
    
    def vcsCleanup(self, name):
        """
        Public method used to cleanup the working directory.
        
        @param name directory name to be cleaned up (string)
        """
        patterns = ['*.orig', '*.rej']
        
        entries = []
        for pat in patterns:
            entries.extend(Utilities.direntries(name, True, pat))
        
        for entry in entries:
            try:
                os.remove(entry)
            except OSError:
                pass
    
    def vcsCommandLine(self, name):
        """
        Public method used to execute arbitrary mercurial commands.
        
        @param name directory name of the working directory (string)
        """
        dlg = HgCommandDialog(self.commandHistory, name)
        if dlg.exec_() == QDialog.Accepted:
            command = dlg.getData()
            commandList = Utilities.parseOptionString(command)
            
            # This moves any previous occurrence of these arguments to the head
            # of the list.
            if command in self.commandHistory:
                self.commandHistory.remove(command)
            self.commandHistory.insert(0, command)
            
            args = []
            self.addArguments(args, commandList)
            
            # find the root of the repo
            repodir = name
            while not os.path.isdir(os.path.join(repodir, self.adminDir)):
                repodir = os.path.dirname(repodir)
                if repodir == os.sep:
                    return
            
            dia = HgDialog(self.trUtf8('Mercurial command'))
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
    
    def vcsOptionsDialog(self, project, archive, editable = False, parent = None):
        """
        Public method to get a dialog to enter repository info.
        
        @param project reference to the project object
        @param archive name of the project in the repository (string)
        @param editable flag indicating that the project name is editable (boolean)
        @param parent parent widget (QWidget)
        """
        return HgOptionsDialog(self, project, parent)
    
    def vcsNewProjectOptionsDialog(self, parent = None):
        """
        Public method to get a dialog to enter repository info for getting a new project.
        
        @param parent parent widget (QWidget)
        """
        return HgNewProjectOptionsDialog(self, parent)
    
    def vcsRepositoryInfos(self, ppath):
        """
        Public method to retrieve information about the repository.
        
        @param ppath local path to get the repository infos (string)
        @return string with ready formated info for display (string)
        """
        info = []
        
        process = QProcess()
        args = []
        args.append('parents')
        args.append('--template')
        args.append('{rev}:{node|short}@@@{tags}@@@{author|xmlescape}@@@'
                    '{date|isodate}@@@{branches}\n')
        process.setWorkingDirectory(ppath)
        process.start('hg', args)
        procStarted = process.waitForStarted()
        if procStarted:
            finished = process.waitForFinished(30000)
            if finished and process.exitCode() == 0:
                output = str(process.readAllStandardOutput(), 
                    Preferences.getSystem("IOEncoding"), 'replace')
                index = 0
                for line in output.splitlines():
                    index += 1
                    changeset, tags, author, date, branches = line.split("@@@")
                    cdate, ctime = date.split()[:2]
                    info.append("""<p><table>""")
                    info.append(QApplication.translate("mercurial", 
                        """<tr><td><b>Parent #{0}</b></td><td></td></tr>\n"""
                        """<tr><td><b>Changeset</b></td><td>{1}</td></tr>""")\
                        .format(index, changeset))
                    if tags:
                        info.append(QApplication.translate("mercurial", 
                            """<tr><td><b>Tags</b></td><td>{0}</td></tr>""")\
                            .format('<br/>'.join(tags.split())))
                    if branches:
                        info.append(QApplication.translate("mercurial", 
                            """<tr><td><b>Branches</b></td><td>{0}</td></tr>""")\
                            .format('<br/>'.join(branches.split())))
                    info.append(QApplication.translate("mercurial", 
                        """<tr><td><b>Last author</b></td><td>{0}</td></tr>\n"""
                        """<tr><td><b>Committed date</b></td><td>{1}</td></tr>\n"""
                        """<tr><td><b>Committed time</b></td><td>{2}</td></tr>""")\
                        .format(author, cdate, ctime))
                    info.append("""</table></p>""")
        
        url = ""
        args =  []
        args.append('showconfig')
        args.append('paths.default')
        process.setWorkingDirectory(ppath)
        process.start('hg', args)
        procStarted = process.waitForStarted()
        if procStarted:
            finished = process.waitForFinished(30000)
            if finished and process.exitCode() == 0:
                output = str(process.readAllStandardOutput(), 
                    Preferences.getSystem("IOEncoding"), 'replace')
                if output:
                    url = output.splitlines()[0].strip()
                else:
                    url = ""
        
        return QApplication.translate('mercurial',
            """<h3>Repository information</h3>\n"""
            """<p><table>\n"""
            """<tr><td><b>Mercurial V.</b></td><td>{0}</td></tr>\n"""
            """<tr></tr>\n"""
            """<tr><td><b>URL</b></td><td>{1}</td></tr>\n"""
            """</table></p>\n"""
            """{2}"""
            ).format(self.versionStr, url, "\n".join(info))

    ############################################################################
    ## Private Subversion specific methods are below.
    ############################################################################
    
    def __hgURL(self, url):
        """
        Private method to format a url for Mercurial.
        
        @param url unformatted url string (string)
        @return properly formated url for subversion (string)
        """
        url = self.hgNormalizeURL(url)
        url = url.split(':', 2)
        if len(url) == 4:
            scheme = url[0]
            user = url[1]
            host = url[2]
            port, path = url[3].split("/",1)
            return "{0}:{1}:{2}:{3}/{4}".format(
                scheme, user, host, port, urllib.parse.quote(path))
        elif len(url) == 3:
            scheme = url[0]
            host = url[1]
            port, path = url[2].split("/",1)
            return "{0}:{1}:{2}/{3}".format(scheme, host, port, urllib.parse.quote(path))
        else:
            scheme = url[0]
            if scheme == "file":
                return "{0}:{1}".format(scheme, urllib.parse.quote(url[1]))
            else:
                host, path = url[1][2:].split("/",1)
                return "{0}://{1}/{2}".format(scheme, host, urllib.parse.quote(path))

    def hgNormalizeURL(self, url):
        """
        Public method to normalize a url for Mercurial.
        
        @param url url string (string)
        @return properly normalized url for subversion (string)
        """
        url = url.replace('\\', '/')
        if url.endswith('/'):
            url = url[:-1]
        urll = url.split('//')
        return "{0}//{1}".format(urll[0], '/'.join(urll[1:]))
    
    def hgCopy(self, name, project):
        """
        Public method used to copy a file/directory.
        
        @param name file/directory name to be copied (string)
        @param project reference to the project object
        @return flag indicating successfull operation (boolean)
        """
        dlg = HgCopyDialog(name)
        res = False
        if dlg.exec_() == QDialog.Accepted:
            target, force = dlg.getData()
            
            args = []
            args.append('copy')
            self.addArguments(args, self.options['global'])
            args.append("-v")
            args.append(name)
            args.append(target)
            
            dname, fname = self.splitPath(name)
            # find the root of the repo
            repodir = dname
            while not os.path.isdir(os.path.join(repodir, self.adminDir)):
                repodir = os.path.dirname(repodir)
                if repodir == os.sep:
                    return False
            
            dia = HgDialog(self.trUtf8('Copying {0}')
                .format(name))
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
                res = dia.normalExit()
                if res and \
                   target.startswith(project.getProjectPath()):
                    if os.path.isdir(name):
                        project.copyDirectory(name, target)
                    else:
                        project.appendFile(target)
        return res
    
    def hgListTagBranch(self, path, tags = True):
        """
        Public method used to list the available tags or branches.
        
        @param path directory name of the project (string)
        @param tags flag indicating listing of branches or tags
                (False = branches, True = tags)
        """
        self.tagbranchList = HgTagBranchListDialog(self)
        self.tagbranchList.show()
        if tags:
            if not self.showedTags:
                self.showedTags = True
                allTagsBranchesList = self.allTagsBranchesList
            else:
                self.tagsList = []
                allTagsBranchesList = None
            self.tagbranchList.start(path, tags, 
                                     self.tagsList, allTagsBranchesList)
        else:
            if not self.showedBranches:
                self.showedBranches = True
                allTagsBranchesList = self.allTagsBranchesList
            else:
                self.branchesList = []
                allTagsBranchesList = None
            self.tagbranchList.start(path, tags, 
                                     self.branchesList, self.allTagsBranchesList)
    
    def hgAnnotate(self, name):
        """
        Public method to show the output of the hg annotate command.
        
        @param name file name to show the annotations for (string)
        """
        self.annotate = HgAnnotateDialog(self)
        self.annotate.show()
        self.annotate.start(name)
    
    def hgExtendedDiff(self, name):
        """
        Public method used to view the difference of a file/directory to the 
        Mercurial repository.
        
        If name is a directory and is the project directory, all project files
        are saved first. If name is a file (or list of files), which is/are being edited 
        and has unsaved modification, they can be saved or the operation may be aborted.
        
        This method gives the chance to enter the revisions to be compared.
        
        @param name file/directory name to be diffed (string)
        """
        if isinstance(name, list):
            names = name[:]
        else:
            names = [name]
        for nam in names:
            if os.path.isfile(nam):
                editor = e5App().getObject("ViewManager").getOpenEditor(nam)
                if editor and not editor.checkDirty() :
                    return
            else:
                project = e5App().getObject("Project")
                if nam == project.ppath and not project.saveAllScripts():
                    return
        dlg = HgRevisionsSelectionDialog(self.tagsList, self.branchesList)
        if dlg.exec_() == QDialog.Accepted:
            revisions = dlg.getRevisions()
            self.diff = HgDiffDialog(self)
            self.diff.show()
            self.diff.start(name, revisions)
    
    def hgLogLimited(self, name):
        """
        Public method used to view the (limited) log of a file/directory from the 
        Mercurial repository.
        
        @param name file/directory name to show the log of (string)
        """
        noEntries, ok = QInputDialog.getInteger(\
            None,
            self.trUtf8("Mercurial Log"),
            self.trUtf8("Select number of entries to show."),
            self.getPlugin().getPreferences("LogLimit"), 1, 999999, 1)
        if ok:
            self.log = HgLogDialog(self)
            self.log.show()
            self.log.start(name, noEntries)
    
    def hgLogBrowser(self, path):
        """
        Public method used to browse the log of a file/directory from the 
        Mercurial repository.
        
        @param path file/directory name to show the log of (string)
        """
        self.logBrowser = HgLogBrowserDialog(self)
        self.logBrowser.show()
        self.logBrowser.start(path)
    
    def hgIncoming(self, name):
        """
        Public method used to view the log of incoming changes from the 
        Mercurial repository.
        
        @param name file/directory name to show the log of (string)
        """
        if self.getPlugin().getPreferences("UseLogBrowser"):
            self.logBrowser = HgLogBrowserDialog(self, mode = "incoming")
            self.logBrowser.show()
            self.logBrowser.start(name)
        else:
            self.log = HgLogDialog(self, mode = "incoming")
            self.log.show()
            self.log.start(name)
    
    def hgOutgoing(self, name):
        """
        Public method used to view the log of outgoing changes from the 
        Mercurial repository.
        
        @param name file/directory name to show the log of (string)
        """
        if self.getPlugin().getPreferences("UseLogBrowser"):
            self.logBrowser = HgLogBrowserDialog(self, mode = "outgoing")
            self.logBrowser.show()
            self.logBrowser.start(name)
        else:
            self.log = HgLogDialog(self, mode = "outgoing")
            self.log.show()
            self.log.start(name)
    
    def hgPull(self, name):
        """
        Public method used to pull changes from a remote Mercurial repository.
        
        @param name directory name of the project to be pulled to (string)
        """
        args = []
        args.append('pull')
        self.addArguments(args, self.options['global'])
        args.append('-v')
        if self.getPlugin().getPreferences("PullUpdate"):
            args.append('--update')
        
        # find the root of the repo
        repodir = self.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        dia = HgDialog(self.trUtf8('Pulling from a remote Mercurial repository'))
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
            res = dia.hasAddOrDelete()
        self.checkVCSStatus()
    
    def hgPush(self, name, force = False):
        """
        Public method used to push changes to a remote Mercurial repository.
        
        @param name directory name of the project to be pushed from (string)
        @keyparam force flag indicating a forced push (boolean)
        """
        args = []
        args.append('push')
        self.addArguments(args, self.options['global'])
        args.append('-v')
        if force:
            args.append('-f')
        
        # find the root of the repo
        repodir = self.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        dia = HgDialog(self.trUtf8('Pushing to a remote Mercurial repository'))
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
            res = dia.hasAddOrDelete()
        self.checkVCSStatus()
    
    def hgInfo(self, ppath, mode = "heads"):
        """
        Public method to show information about the heads of the repository.
        
        @param ppath local path to get the repository infos (string)
        @keyparam mode mode of the operation (string, one of heads, parents, tip)
        """
        if mode not in ("heads", "parents", "tip"):
            mode = "heads"
        
        info = []
        
        # find the root of the repo
        repodir = self.splitPath(ppath)[0]
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        process = QProcess()
        args = []
        args.append(mode)
        args.append('--template')
        args.append('{rev}:{node|short}@@@{tags}@@@{author|xmlescape}@@@'
                    '{date|isodate}@@@{branches}@@@{parents}\n')
        
        process.setWorkingDirectory(repodir)
        process.start('hg', args)
        procStarted = process.waitForStarted()
        if procStarted:
            finished = process.waitForFinished(30000)
            if finished and process.exitCode() == 0:
                output = str(process.readAllStandardOutput(), 
                    Preferences.getSystem("IOEncoding"), 'replace')
                index = 0
                for line in output.splitlines():
                    index += 1
                    changeset, tags, author, date, branches, parents = line.split("@@@")
                    cdate, ctime = date.split()[:2]
                    info.append("""<p><table>""")
                    if mode == "heads":
                        info.append(QApplication.translate("mercurial", 
                            """<tr><td><b>Head #{0}</b></td><td></td></tr>\n"""
                            .format(index, changeset)))
                    elif mode == "parents":
                        info.append(QApplication.translate("mercurial", 
                            """<tr><td><b>Parent #{0}</b></td><td></td></tr>\n"""
                            .format(index, changeset)))
                    elif mode == "tip":
                        info.append(QApplication.translate("mercurial", 
                            """<tr><td><b>Tip</b></td><td></td></tr>\n"""))
                    info.append(QApplication.translate("mercurial", 
                        """<tr><td><b>Changeset</b></td><td>{0}</td></tr>""")\
                        .format(changeset))
                    if tags:
                        info.append(QApplication.translate("mercurial", 
                            """<tr><td><b>Tags</b></td><td>{0}</td></tr>""")\
                            .format('<br/>'.join(tags.split())))
                    if branches:
                        info.append(QApplication.translate("mercurial", 
                            """<tr><td><b>Branches</b></td><td>{0}</td></tr>""")\
                            .format('<br/>'.join(branches.split())))
                    if parents:
                        info.append(QApplication.translate("mercurial", 
                            """<tr><td><b>Parents</b></td><td>{0}</td></tr>""")\
                            .format('<br/>'.join(parents.split())))
                    info.append(QApplication.translate("mercurial", 
                        """<tr><td><b>Last author</b></td><td>{0}</td></tr>\n"""
                        """<tr><td><b>Committed date</b></td><td>{1}</td></tr>\n"""
                        """<tr><td><b>Committed time</b></td><td>{2}</td></tr>\n"""
                        """</table></p>""")\
                        .format(author, cdate, ctime))
                
                dlg = VcsRepositoryInfoDialog(None, "\n".join(info))
                dlg.exec_()
    

    def hgResolve(self, name):
        """
        Public method used to resolve conflicts of a file/directory.
        
        @param name file/directory name to be resolved (string)
        """
        args = []
        args.append('resolve')
        self.addArguments(args, self.options['global'])
        args.append("--mark")
        
        if isinstance(name, list):
            dname, fnames = self.splitPathList(name)
            self.addArguments(args, name)
        else:
            dname, fname = self.splitPath(name)
            args.append(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return False
        
        dia = HgDialog(
            self.trUtf8('Resolving files/directories'))
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
        self.checkVCSStatus()
    
    def hgBranch(self, name):
        """
        Public method used to create a branch in the Mercurial repository.
        
        @param name file/directory name to be branched (string)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = str(dname)
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        name, ok = QInputDialog.getItem(
            None,
            self.trUtf8("Create Branch"),
            self.trUtf8("Enter branch name"),
            self.branchesList,
            0, True)
        if ok and name:
            args = []
            args.append('branch')
            args.append(name.strip().replace(" ", "_"))
            
            dia = HgDialog(self.trUtf8('Creating branch in the Mercurial repository'))
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
    
    def hgShowBranch(self, name):
        """
        Public method used to show the current branch the working directory.
        
        @param name file/directory name (string)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = str(dname)
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        args = []
        args.append("branch")
        
        dia = HgDialog(self.trUtf8('Showing current branch'))
        res = dia.startProcess(args, repodir, False)
        if res:
            dia.exec_()
    
    def hgEditConfig(self, name):
        """
        Public method used to edit the repository config file.
        
        @param name file/directory name (string)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = str(dname)
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        cfgFile = os.path.join(repodir, self.adminDir, "hgrc")
        if not os.path.exists(cfgFile):
            try:
                cfg = open(cfgFile, "w")
                cfg.close()
            except IOError:
                pass
        self.editor = MiniEditor(cfgFile, "Properties")
        self.editor.show()
    
    def hgVerify(self, name):
        """
        Public method to verify the integrity of the repository.
        
        @param name file/directory name (string)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = str(dname)
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        args = []
        args.append('verify')
        
        dia = HgDialog(self.trUtf8('Verifying the integrity of the Mercurial repository'))
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
    
    def hgShowConfig(self, name):
        """
        Public method to show the combined config.
        
        @param name file/directory name (string)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = str(dname)
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        args = []
        args.append('showconfig')
        args.append("--untrusted")
        
        dia = HgDialog(self.trUtf8('Showing the combined configuration settings'))
        res = dia.startProcess(args, repodir, False)
        if res:
            dia.exec_()
    
    def hgShowPaths(self, name):
        """
        Public method to show the path aliases for remote repositories.
        
        @param name file/directory name (string)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = str(dname)
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        args = []
        args.append('paths')
        
        dia = HgDialog(self.trUtf8('Showing aliases for remote repositories'))
        res = dia.startProcess(args, repodir, False)
        if res:
            dia.exec_()
    
    def hgRecover(self, name):
        """
        Public method to recover an interrupted transaction.
        
        @param name file/directory name (string)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = str(dname)
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        args = []
        args.append('recover')
        
        dia = HgDialog(self.trUtf8('Recovering from interrupted transaction'))
        res = dia.startProcess(args, repodir, False)
        if res:
            dia.exec_()
    
    def hgIdentify(self, name):
        """
        Public method to identify the current working directory.
        
        @param name file/directory name (string)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = str(dname)
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        args = []
        args.append('identify')
        
        dia = HgDialog(self.trUtf8('Identifying project directory'))
        res = dia.startProcess(args, repodir, False)
        if res:
            dia.exec_()
    
    def hgCreateIgnoreFile(self, name, autoAdd = False):
        """
        Public method to create the ignore file.
        
        @param name directory name to create the ignore file in (string)
        @param autoAdd flag indicating to add it automatically (boolean)
        @return flag indicating success
        """
        status = False
        ignorePatterns = [
            "glob:.eric5project", 
            "glob:.ropeproject", 
            "glob:.directory", 
            "glob:**.pyc", 
            "glob:**.orig", 
            "glob:**.bak", 
        ]
        
        ignoreName = os.path.join(name, ".hgignore")
        if os.path.exists(ignoreName):
            res = QMessageBox.warning(None,
                self.trUtf8("Create .hgignore file"),
                self.trUtf8("""<p>The file <b>{0}</b> exists already."""
                            """ Overwrite it?</p>""").format(ignoreName),
                QMessageBox.StandardButtons(\
                    QMessageBox.No | \
                    QMessageBox.Yes),
                QMessageBox.No)
        else:
            res = QMessageBox.Yes
        if res == QMessageBox.Yes:
            try:
                # create a .hgignore file
                ignore = open(ignoreName, "w")
                ignore.write("\n".join(ignorePatterns))
                ignore.write("\n")
                ignore.close()
                status = True
            except IOError:
                status = False
            
            if status and autoAdd:
                self.vcsAdd(ignoreName, noDialog = True)
                project = e5App().getObject("Project")
                project.appendFile(ignoreName)
        
        return status
    
    def hgBundle(self, name):
        """
        Public method to create a changegroup file.
        
        @param name file/directory name (string)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = str(dname)
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        dlg = HgBundleDialog(self.tagsList, self.branchesList)
        if dlg.exec_() == QDialog.Accepted:
            rev, compression, all = dlg.getParameters()
            
            fname, selectedFilter = QFileDialog.getSaveFileNameAndFilter(\
                None,
                self.trUtf8("Create changegroup"),
                repodir,
                self.trUtf8("Mercurial Changegroup Files (*.hg)"),
                None,
                QFileDialog.Options(QFileDialog.DontConfirmOverwrite))
            
            if not fname:
                return  # user aborted
            
            ext = QFileInfo(fname).suffix()
            if not ext:
                ex = selectedFilter.split("(*")[1].split(")")[0]
                if ex:
                    fname += ex
            if QFileInfo(fname).exists():
                res = QMessageBox.warning(None,
                    self.trUtf8("Create changegroup"),
                    self.trUtf8("<p>The Mercurial changegroup file <b>{0}</b> "
                                "already exists.</p>")
                        .format(fname),
                    QMessageBox.StandardButtons(\
                        QMessageBox.Abort | \
                        QMessageBox.Save),
                    QMessageBox.Abort)
                if res != QMessageBox.Save:
                    return
            fname = Utilities.toNativeSeparators(fname)
            
            args = []
            args.append('bundle')
            if all:
                args.append("--all")
            if rev:
                args.append("--rev")
                args.append(rev)
            if compression:
                args.append("--type")
                args.append(compression)
            args.append(fname)
            
            dia = HgDialog(self.trUtf8('Create changegroup'))
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
    
    def hgPreviewBundle(self, name):
        """
        Public method used to view the log of incoming changes from a
        changegroup file.
        
        @param name directory name on which to base the changegroup (string)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = str(dname)
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        file = QFileDialog.getOpenFileName(\
            None,
            self.trUtf8("Preview changegroup"),
            repodir,
            self.trUtf8("Mercurial Changegroup Files (*.hg);;All Files (*)"))
        if file:
            if self.getPlugin().getPreferences("UseLogBrowser"):
                self.logBrowser = \
                    HgLogBrowserDialog(self, mode = "incoming", bundle = file)
                self.logBrowser.show()
                self.logBrowser.start(name)
            else:
                self.log = HgLogDialog(self, mode = "incoming", bundle = file)
                self.log.show()
                self.log.start(name)
    
    def hgIdentifyBundle(self, name):
        """
        Public method used to identify a changegroup file.
        
        @param name directory name on which to base the changegroup (string)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = str(dname)
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        file = QFileDialog.getOpenFileName(\
            None,
            self.trUtf8("Preview changegroup"),
            repodir,
            self.trUtf8("Mercurial Changegroup Files (*.hg);;All Files (*)"))
        if file:
            args = []
            args.append('identify')
            args.append(file)
            
            dia = HgDialog(self.trUtf8('Identifying changegroup file'))
            res = dia.startProcess(args, repodir, False)
            if res:
                dia.exec_()
    
    def hgUnbundle(self, name):
        """
        Public method to apply changegroup files.
        
        @param name directory name (string)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = str(dname)
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        files = QFileDialog.getOpenFileNames(\
            None,
            self.trUtf8("Apply changegroups"),
            repodir,
            self.trUtf8("Mercurial Changegroup Files (*.hg);;All Files (*)"))
        if files:
            update = QMessageBox.question(None,
                self.trUtf8("Apply changegroups"),
                self.trUtf8("""Shall the working directory be updated?"""),
                QMessageBox.StandardButtons(\
                    QMessageBox.No | \
                    QMessageBox.Yes),
                QMessageBox.Yes) == QMessageBox.Yes
            
            args = []
            args.append('unbundle')
            if update:
                args.append("--update")
            args.extend(files)
            
            dia = HgDialog(self.trUtf8('Apply changegroups'))
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
    
    def hgBisect(self, name, subcommand):
        """
        Public method to perform bisect commands.
        
        @param name file/directory name (string)
        @param subcommand name of the subcommand (string, one of 'good', 'bad',
            'skip' or 'reset')
        """
        if subcommand not in ("good", "bad", "skip", "reset"):
            raise ValueError(
                self.trUtf8("Bisect subcommand ({0}) invalid.").format(subcommand))
        
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = str(dname)
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        rev = ""
        if subcommand in ("good", "bad"):
            dlg = HgRevisionSelectionDialog(self.tagsList, self.branchesList, 
                                            showNone =True)
            if dlg.exec_() == QDialog.Accepted:
                rev = dlg.getRevision()
            else:
                return
        
        args = []
        args.append("bisect")
        args.append("--{0}".format(subcommand))
        if rev:
            args.append(rev)
        
        dia = HgDialog(self.trUtf8('Mercurial Bisect ({0})').format(subcommand))
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
    
    def hgForget(self, name):
        """
        Public method used to remove a file from the Mercurial repository.
        
        This will not remove the file from the project directory.
        
        @param name file/directory name to be removed (string or list of strings))
        """
        args = []
        args.append('forget')
        self.addArguments(args, self.options['global'])
        args.append('-v')
        
        if isinstance(name, list):
            dname, fnames = self.splitPathList(name)
            self.addArguments(args, name)
        else:
            dname, fname = self.splitPath(name)
            args.append(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        dia = HgDialog(\
            self.trUtf8('Removing files from the Mercurial repository only'))
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
            if isinstance(name, list):
                self.__forgotNames.extend(name)
            else:
                self.__forgotNames.append(name)
    
    def hgBackout(self, name):
        """
        Public method used to backout an earlier changeset from the Mercurial repository.
        
        @param name directory name (string or list of strings))
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = str(dname)
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        dlg = HgBackoutDialog(self.tagsList, self.branchesList)
        if dlg.exec_() == QDialog.Accepted:
            rev, merge, date, user, message = dlg.getParameters()
            if not rev:
                QMessageBox.warning(None,
                    self.trUtf8("Backing out changeset"),
                    self.trUtf8("""No revision given. Aborting..."""))
                return
            
            args = []
            args.append('backout')
            args.append('-v')
            if merge:
                args.append('--merge')
            if date:
                args.append('--date')
                args.append(date)
            if user:
                args.append('--user')
                args.append(user)
            args.append('--message')
            args.append(message)
            args.append(rev)
            
            dia = HgDialog(self.trUtf8('Backing out changeset'))
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
    
    def hgServe(self, name):
        """
        Public method used to edit the repository config file.
        
        @param name directory name (string)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = str(dname)
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        self.serveDlg = HgServeDialog(self, repodir)
        self.serveDlg.show()
    
    ############################################################################
    ## Methods to get the helper objects are below.
    ############################################################################
    
    def vcsGetProjectBrowserHelper(self, browser, project, isTranslationsBrowser = False):
        """
        Public method to instanciate a helper object for the different project browsers.
        
        @param browser reference to the project browser object
        @param project reference to the project object
        @param isTranslationsBrowser flag indicating, the helper is requested for the
            translations browser (this needs some special treatment)
        @return the project browser helper object
        """
        return HgProjectBrowserHelper(self, browser, project, isTranslationsBrowser)
        
    def vcsGetProjectHelper(self, project):
        """
        Public method to instanciate a helper object for the project.
        
        @param project reference to the project object
        @return the project helper object
        """
        helper = self.__plugin.getProjectHelper()
        helper.setObjects(self, project)
        return helper

    ############################################################################
    ##  Status Monitor Thread methods
    ############################################################################

    def _createStatusMonitorThread(self, interval, project):
        """
        Protected method to create an instance of the VCS status monitor thread.
        
        @param project reference to the project object (Project)
        @param interval check interval for the monitor thread in seconds (integer)
        @return reference to the monitor thread (QThread)
        """
        return HgStatusMonitorThread(interval, project, self)