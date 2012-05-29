# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the VCS project helper for Mercurial.
"""

import os

from PyQt4.QtGui import QMenu

from E5Gui import E5MessageBox
from E5Gui.E5Application import e5App

from VCS.ProjectHelper import VcsProjectHelper

from .BookmarksExtension.ProjectHelper import BookmarksProjectHelper
from .QueuesExtension.ProjectHelper import QueuesProjectHelper
from .FetchExtension.ProjectHelper import FetchProjectHelper
from .PurgeExtension.ProjectHelper import PurgeProjectHelper
from .GpgExtension.ProjectHelper import GpgProjectHelper
from .TransplantExtension.ProjectHelper import TransplantProjectHelper
from .RebaseExtension.ProjectHelper import RebaseProjectHelper

from E5Gui.E5Action import E5Action

import UI.PixmapCache
import Preferences


class HgProjectHelper(VcsProjectHelper):
    """
    Class implementing the VCS project helper for Mercurial.
    """
    def __init__(self, vcsObject, projectObject, parent=None, name=None):
        """
        Constructor
        
        @param vcsObject reference to the vcs object
        @param projectObject reference to the project object
        @param parent parent widget (QWidget)
        @param name name of this object (string)
        """
        VcsProjectHelper.__init__(self, vcsObject, projectObject, parent, name)
        
        # instantiate the extensions
        self.__extensions = {
            "bookmarks": BookmarksProjectHelper(),
            "mq": QueuesProjectHelper(),
            "fetch": FetchProjectHelper(),
            "purge": PurgeProjectHelper(),
            "gpg": GpgProjectHelper(),
            "transplant": TransplantProjectHelper(),
            "rebase": RebaseProjectHelper(),
        }
        
        self.__extensionMenuTitles = {}
        for extension in self.__extensions:
            self.__extensionMenuTitles[self.__extensions[extension].menuTitle()] = \
                extension
    
    def setObjects(self, vcsObject, projectObject):
        """
        Public method to set references to the vcs and project objects.
        
        @param vcsObject reference to the vcs object
        @param projectObject reference to the project object
        """
        self.vcs = vcsObject
        self.project = projectObject
        
        for extension in self.__extensions.values():
            extension.setObjects(vcsObject, projectObject)
    
    def getActions(self):
        """
        Public method to get a list of all actions.
        
        @return list of all actions (list of E5Action)
        """
        actions = self.actions[:]
        for extension in self.__extensions.values():
            actions.extend(extension.getActions())
        return actions
    
    def initActions(self):
        """
        Public method to generate the action objects.
        """
        self.vcsNewAct = E5Action(self.trUtf8('New from repository'),
                UI.PixmapCache.getIcon("vcsCheckout.png"),
                self.trUtf8('&New from repository...'), 0, 0, self, 'mercurial_new')
        self.vcsNewAct.setStatusTip(self.trUtf8(
            'Create (clone) a new project from a Mercurial repository'
        ))
        self.vcsNewAct.setWhatsThis(self.trUtf8(
            """<b>New from repository</b>"""
            """<p>This creates (clones) a new local project from """
            """a Mercurial repository.</p>"""
        ))
        self.vcsNewAct.triggered[()].connect(self._vcsCheckout)
        self.actions.append(self.vcsNewAct)
        
        self.hgIncomingAct = E5Action(self.trUtf8('Show incoming log'),
                UI.PixmapCache.getIcon("vcsUpdate.png"),
                self.trUtf8('Show incoming log'),
                0, 0, self, 'mercurial_incoming')
        self.hgIncomingAct.setStatusTip(self.trUtf8(
            'Show the log of incoming changes'
        ))
        self.hgIncomingAct.setWhatsThis(self.trUtf8(
            """<b>Show incoming log</b>"""
            """<p>This shows the log of changes coming into the repository.</p>"""
        ))
        self.hgIncomingAct.triggered[()].connect(self.__hgIncoming)
        self.actions.append(self.hgIncomingAct)
        
        self.hgPullAct = E5Action(self.trUtf8('Pull changes'),
                UI.PixmapCache.getIcon("vcsUpdate.png"),
                self.trUtf8('Pull changes'),
                0, 0, self, 'mercurial_pull')
        self.hgPullAct.setStatusTip(self.trUtf8(
            'Pull changes from a remote repository'
        ))
        self.hgPullAct.setWhatsThis(self.trUtf8(
            """<b>Pull changes</b>"""
            """<p>This pulls changes from a remote repository into the """
            """local repository.</p>"""
        ))
        self.hgPullAct.triggered[()].connect(self.__hgPull)
        self.actions.append(self.hgPullAct)
        
        self.vcsUpdateAct = E5Action(self.trUtf8('Update from repository'),
                UI.PixmapCache.getIcon("vcsUpdate.png"),
                self.trUtf8('&Update from repository'), 0, 0, self,
                'mercurial_update')
        self.vcsUpdateAct.setStatusTip(self.trUtf8(
            'Update the local project from the Mercurial repository'
        ))
        self.vcsUpdateAct.setWhatsThis(self.trUtf8(
            """<b>Update from repository</b>"""
            """<p>This updates the local project from the Mercurial repository.</p>"""
        ))
        self.vcsUpdateAct.triggered[()].connect(self._vcsUpdate)
        self.actions.append(self.vcsUpdateAct)
        
        self.vcsCommitAct = E5Action(self.trUtf8('Commit changes to repository'),
                UI.PixmapCache.getIcon("vcsCommit.png"),
                self.trUtf8('&Commit changes to repository...'), 0, 0, self,
                'mercurial_commit')
        self.vcsCommitAct.setStatusTip(self.trUtf8(
            'Commit changes to the local project to the Mercurial repository'
        ))
        self.vcsCommitAct.setWhatsThis(self.trUtf8(
            """<b>Commit changes to repository</b>"""
            """<p>This commits changes to the local project to the """
            """Mercurial repository.</p>"""
        ))
        self.vcsCommitAct.triggered[()].connect(self._vcsCommit)
        self.actions.append(self.vcsCommitAct)
        
        self.hgOutgoingAct = E5Action(self.trUtf8('Show outgoing log'),
                UI.PixmapCache.getIcon("vcsCommit.png"),
                self.trUtf8('Show outgoing log'),
                0, 0, self, 'mercurial_outgoing')
        self.hgOutgoingAct.setStatusTip(self.trUtf8(
            'Show the log of outgoing changes'
        ))
        self.hgOutgoingAct.setWhatsThis(self.trUtf8(
            """<b>Show outgoing log</b>"""
            """<p>This shows the log of changes outgoing out of the repository.</p>"""
        ))
        self.hgOutgoingAct.triggered[()].connect(self.__hgOutgoing)
        self.actions.append(self.hgOutgoingAct)
        
        self.hgPushAct = E5Action(self.trUtf8('Push changes'),
                UI.PixmapCache.getIcon("vcsCommit.png"),
                self.trUtf8('Push changes'),
                0, 0, self, 'mercurial_push')
        self.hgPushAct.setStatusTip(self.trUtf8(
            'Push changes to a remote repository'
        ))
        self.hgPushAct.setWhatsThis(self.trUtf8(
            """<b>Push changes</b>"""
            """<p>This pushes changes from the local repository to a """
            """remote repository.</p>"""
        ))
        self.hgPushAct.triggered[()].connect(self.__hgPush)
        self.actions.append(self.hgPushAct)
        
        self.hgPushForcedAct = E5Action(self.trUtf8('Push changes (force)'),
                UI.PixmapCache.getIcon("vcsCommit.png"),
                self.trUtf8('Push changes (force)'),
                0, 0, self, 'mercurial_push_forced')
        self.hgPushForcedAct.setStatusTip(self.trUtf8(
            'Push changes to a remote repository with force option'
        ))
        self.hgPushForcedAct.setWhatsThis(self.trUtf8(
            """<b>Push changes (force)</b>"""
            """<p>This pushes changes from the local repository to a """
            """remote repository using the 'force' option.</p>"""
        ))
        self.hgPushForcedAct.triggered[()].connect(self.__hgPushForced)
        self.actions.append(self.hgPushForcedAct)
        
        self.vcsExportAct = E5Action(self.trUtf8('Export from repository'),
                UI.PixmapCache.getIcon("vcsExport.png"),
                self.trUtf8('&Export from repository...'),
                0, 0, self, 'subversion_export')
        self.vcsExportAct.setStatusTip(self.trUtf8(
            'Export a project from the repository'
        ))
        self.vcsExportAct.setWhatsThis(self.trUtf8(
            """<b>Export from repository</b>"""
            """<p>This exports a project from the repository.</p>"""
        ))
        self.vcsExportAct.triggered[()].connect(self._vcsExport)
        self.actions.append(self.vcsExportAct)
        
        self.vcsRemoveAct = E5Action(self.trUtf8('Remove from repository (and disk)'),
                UI.PixmapCache.getIcon("vcsRemove.png"),
                self.trUtf8('&Remove from repository (and disk)'),
                0, 0, self, 'mercurial_remove')
        self.vcsRemoveAct.setStatusTip(self.trUtf8(
            'Remove the local project from the repository (and  disk)'
        ))
        self.vcsRemoveAct.setWhatsThis(self.trUtf8(
            """<b>Remove from repository</b>"""
            """<p>This removes the local project from the repository"""
            """ (and disk).</p>"""
        ))
        self.vcsRemoveAct.triggered[()].connect(self._vcsRemove)
        self.actions.append(self.vcsRemoveAct)
        
        self.vcsLogAct = E5Action(self.trUtf8('Show log'),
                UI.PixmapCache.getIcon("vcsLog.png"),
                self.trUtf8('Show &log'),
                0, 0, self, 'mercurial_log')
        self.vcsLogAct.setStatusTip(self.trUtf8(
            'Show the log of the local project'
        ))
        self.vcsLogAct.setWhatsThis(self.trUtf8(
            """<b>Show log</b>"""
            """<p>This shows the log of the local project.</p>"""
        ))
        self.vcsLogAct.triggered[()].connect(self._vcsLog)
        self.actions.append(self.vcsLogAct)
        
        self.hgLogBrowserAct = E5Action(self.trUtf8('Show log browser'),
                UI.PixmapCache.getIcon("vcsLog.png"),
                self.trUtf8('Show log browser'),
                0, 0, self, 'mercurial_log_browser')
        self.hgLogBrowserAct.setStatusTip(self.trUtf8(
            'Show a dialog to browse the log of the local project'
        ))
        self.hgLogBrowserAct.setWhatsThis(self.trUtf8(
            """<b>Show log browser</b>"""
            """<p>This shows a dialog to browse the log of the local project."""
            """ A limited number of entries is shown first. More can be"""
            """ retrieved later on.</p>"""
        ))
        self.hgLogBrowserAct.triggered[()].connect(self.__hgLogBrowser)
        self.actions.append(self.hgLogBrowserAct)
        
        self.vcsDiffAct = E5Action(self.trUtf8('Show difference'),
                UI.PixmapCache.getIcon("vcsDiff.png"),
                self.trUtf8('Show &difference'),
                0, 0, self, 'mercurial_diff')
        self.vcsDiffAct.setStatusTip(self.trUtf8(
            'Show the difference of the local project to the repository'
        ))
        self.vcsDiffAct.setWhatsThis(self.trUtf8(
            """<b>Show difference</b>"""
            """<p>This shows the difference of the local project to the repository.</p>"""
        ))
        self.vcsDiffAct.triggered[()].connect(self._vcsDiff)
        self.actions.append(self.vcsDiffAct)
        
        self.hgExtDiffAct = E5Action(self.trUtf8('Show difference (extended)'),
                UI.PixmapCache.getIcon("vcsDiff.png"),
                self.trUtf8('Show difference (extended)'),
                0, 0, self, 'mercurial_extendeddiff')
        self.hgExtDiffAct.setStatusTip(self.trUtf8(
            'Show the difference of revisions of the project to the repository'
        ))
        self.hgExtDiffAct.setWhatsThis(self.trUtf8(
            """<b>Show difference (extended)</b>"""
            """<p>This shows the difference of selectable revisions of the project.</p>"""
        ))
        self.hgExtDiffAct.triggered[()].connect(self.__hgExtendedDiff)
        self.actions.append(self.hgExtDiffAct)
        
        self.vcsStatusAct = E5Action(self.trUtf8('Show status'),
                UI.PixmapCache.getIcon("vcsStatus.png"),
                self.trUtf8('Show &status'),
                0, 0, self, 'mercurial_status')
        self.vcsStatusAct.setStatusTip(self.trUtf8(
            'Show the status of the local project'
        ))
        self.vcsStatusAct.setWhatsThis(self.trUtf8(
            """<b>Show status</b>"""
            """<p>This shows the status of the local project.</p>"""
        ))
        self.vcsStatusAct.triggered[()].connect(self._vcsStatus)
        self.actions.append(self.vcsStatusAct)
        
        self.hgHeadsAct = E5Action(self.trUtf8('Show heads'),
                self.trUtf8('Show heads'),
                0, 0, self, 'mercurial_heads')
        self.hgHeadsAct.setStatusTip(self.trUtf8(
            'Show the heads of the repository'
        ))
        self.hgHeadsAct.setWhatsThis(self.trUtf8(
            """<b>Show heads</b>"""
            """<p>This shows the heads of the repository.</p>"""
        ))
        self.hgHeadsAct.triggered[()].connect(self.__hgHeads)
        self.actions.append(self.hgHeadsAct)
        
        self.hgParentsAct = E5Action(self.trUtf8('Show parents'),
                self.trUtf8('Show parents'),
                0, 0, self, 'mercurial_parents')
        self.hgParentsAct.setStatusTip(self.trUtf8(
            'Show the parents of the repository'
        ))
        self.hgParentsAct.setWhatsThis(self.trUtf8(
            """<b>Show parents</b>"""
            """<p>This shows the parents of the repository.</p>"""
        ))
        self.hgParentsAct.triggered[()].connect(self.__hgParents)
        self.actions.append(self.hgParentsAct)
        
        self.hgTipAct = E5Action(self.trUtf8('Show tip'),
                self.trUtf8('Show tip'),
                0, 0, self, 'mercurial_tip')
        self.hgTipAct.setStatusTip(self.trUtf8(
            'Show the tip of the repository'
        ))
        self.hgTipAct.setWhatsThis(self.trUtf8(
            """<b>Show tip</b>"""
            """<p>This shows the tip of the repository.</p>"""
        ))
        self.hgTipAct.triggered[()].connect(self.__hgTip)
        self.actions.append(self.hgTipAct)
        
        self.vcsRevertAct = E5Action(self.trUtf8('Revert changes'),
                UI.PixmapCache.getIcon("vcsRevert.png"),
                self.trUtf8('Re&vert changes'),
                0, 0, self, 'mercurial_revert')
        self.vcsRevertAct.setStatusTip(self.trUtf8(
            'Revert all changes made to the local project'
        ))
        self.vcsRevertAct.setWhatsThis(self.trUtf8(
            """<b>Revert changes</b>"""
            """<p>This reverts all changes made to the local project.</p>"""
        ))
        self.vcsRevertAct.triggered[()].connect(self.__hgRevert)
        self.actions.append(self.vcsRevertAct)
        
        self.vcsMergeAct = E5Action(self.trUtf8('Merge'),
                UI.PixmapCache.getIcon("vcsMerge.png"),
                self.trUtf8('Mer&ge changes...'),
                0, 0, self, 'mercurial_merge')
        self.vcsMergeAct.setStatusTip(self.trUtf8(
            'Merge changes of a revision into the local project'
        ))
        self.vcsMergeAct.setWhatsThis(self.trUtf8(
            """<b>Merge</b>"""
            """<p>This merges changes of a revision into the local project.</p>"""
        ))
        self.vcsMergeAct.triggered[()].connect(self._vcsMerge)
        self.actions.append(self.vcsMergeAct)
        
        self.vcsResolveAct = E5Action(self.trUtf8('Conflicts resolved'),
                self.trUtf8('Con&flicts resolved'),
                0, 0, self, 'mercurial_resolve')
        self.vcsResolveAct.setStatusTip(self.trUtf8(
            'Mark all conflicts of the local project as resolved'
        ))
        self.vcsResolveAct.setWhatsThis(self.trUtf8(
            """<b>Conflicts resolved</b>"""
            """<p>This marks all conflicts of the local project as resolved.</p>"""
        ))
        self.vcsResolveAct.triggered[()].connect(self.__hgResolve)
        self.actions.append(self.vcsResolveAct)
        
        self.vcsTagAct = E5Action(self.trUtf8('Tag in repository'),
                UI.PixmapCache.getIcon("vcsTag.png"),
                self.trUtf8('&Tag in repository...'),
                0, 0, self, 'mercurial_tag')
        self.vcsTagAct.setStatusTip(self.trUtf8(
            'Tag the local project in the repository'
        ))
        self.vcsTagAct.setWhatsThis(self.trUtf8(
            """<b>Tag in repository</b>"""
            """<p>This tags the local project in the repository.</p>"""
        ))
        self.vcsTagAct.triggered[()].connect(self._vcsTag)
        self.actions.append(self.vcsTagAct)
        
        self.hgTagListAct = E5Action(self.trUtf8('List tags'),
                self.trUtf8('List tags...'),
                0, 0, self, 'mercurial_list_tags')
        self.hgTagListAct.setStatusTip(self.trUtf8(
            'List tags of the project'
        ))
        self.hgTagListAct.setWhatsThis(self.trUtf8(
            """<b>List tags</b>"""
            """<p>This lists the tags of the project.</p>"""
        ))
        self.hgTagListAct.triggered[()].connect(self.__hgTagList)
        self.actions.append(self.hgTagListAct)
        
        self.hgBranchListAct = E5Action(self.trUtf8('List branches'),
                self.trUtf8('List branches...'),
                0, 0, self, 'mercurial_list_branches')
        self.hgBranchListAct.setStatusTip(self.trUtf8(
            'List branches of the project'
        ))
        self.hgBranchListAct.setWhatsThis(self.trUtf8(
            """<b>List branches</b>"""
            """<p>This lists the branches of the project.</p>"""
        ))
        self.hgBranchListAct.triggered[()].connect(self.__hgBranchList)
        self.actions.append(self.hgBranchListAct)
        
        self.hgBranchAct = E5Action(self.trUtf8('Create branch'),
                UI.PixmapCache.getIcon("vcsBranch.png"),
                self.trUtf8('Create &branch...'),
                0, 0, self, 'mercurial_branch')
        self.hgBranchAct.setStatusTip(self.trUtf8(
            'Create a new branch for the local project in the repository'
        ))
        self.hgBranchAct.setWhatsThis(self.trUtf8(
            """<b>Create branch</b>"""
            """<p>This creates a new branch for the local project """
            """in the repository.</p>"""
        ))
        self.hgBranchAct.triggered[()].connect(self.__hgBranch)
        self.actions.append(self.hgBranchAct)
        
        self.hgPushBranchAct = E5Action(self.trUtf8('Push new branch'),
                self.trUtf8('Push new branch'),
                0, 0, self, 'mercurial_push_branch')
        self.hgPushBranchAct.setStatusTip(self.trUtf8(
            'Push the current branch of the local project as a new named branch'
        ))
        self.hgPushBranchAct.setWhatsThis(self.trUtf8(
            """<b>Push new branch</b>"""
            """<p>This pushes the current branch of the local project"""
            """ as a new named branch.</p>"""
        ))
        self.hgPushBranchAct.triggered[()].connect(self.__hgPushNewBranch)
        self.actions.append(self.hgPushBranchAct)
        
        self.hgCloseBranchAct = E5Action(self.trUtf8('Close branch'),
                self.trUtf8('Close branch'),
                0, 0, self, 'mercurial_close_branch')
        self.hgCloseBranchAct.setStatusTip(self.trUtf8(
            'Close the current branch of the local project'
        ))
        self.hgCloseBranchAct.setWhatsThis(self.trUtf8(
            """<b>Close branch</b>"""
            """<p>This closes the current branch of the local project.</p>"""
        ))
        self.hgCloseBranchAct.triggered[()].connect(self.__hgCloseBranch)
        self.actions.append(self.hgCloseBranchAct)
        
        self.hgShowBranchAct = E5Action(self.trUtf8('Show current branch'),
                self.trUtf8('Show current branch'),
                0, 0, self, 'mercurial_show_branch')
        self.hgShowBranchAct.setStatusTip(self.trUtf8(
            'Show the current branch of the project'
        ))
        self.hgShowBranchAct.setWhatsThis(self.trUtf8(
            """<b>Show current branch</b>"""
            """<p>This shows the current branch of the project.</p>"""
        ))
        self.hgShowBranchAct.triggered[()].connect(self.__hgShowBranch)
        self.actions.append(self.hgShowBranchAct)
        
        self.vcsSwitchAct = E5Action(self.trUtf8('Switch'),
                UI.PixmapCache.getIcon("vcsSwitch.png"),
                self.trUtf8('S&witch...'),
                0, 0, self, 'mercurial_switch')
        self.vcsSwitchAct.setStatusTip(self.trUtf8(
            'Switch the working directory to another revision'
        ))
        self.vcsSwitchAct.setWhatsThis(self.trUtf8(
            """<b>Switch</b>"""
            """<p>This switches the working directory to another revision.</p>"""
        ))
        self.vcsSwitchAct.triggered[()].connect(self._vcsSwitch)
        self.actions.append(self.vcsSwitchAct)
        
        self.vcsCleanupAct = E5Action(self.trUtf8('Cleanup'),
                self.trUtf8('Cleanu&p'),
                0, 0, self, 'mercurial_cleanup')
        self.vcsCleanupAct.setStatusTip(self.trUtf8(
            'Cleanup the local project'
        ))
        self.vcsCleanupAct.setWhatsThis(self.trUtf8(
            """<b>Cleanup</b>"""
            """<p>This performs a cleanup of the local project.</p>"""
        ))
        self.vcsCleanupAct.triggered[()].connect(self._vcsCleanup)
        self.actions.append(self.vcsCleanupAct)
        
        self.vcsCommandAct = E5Action(self.trUtf8('Execute command'),
                self.trUtf8('E&xecute command...'),
                0, 0, self, 'mercurial_command')
        self.vcsCommandAct.setStatusTip(self.trUtf8(
            'Execute an arbitrary Mercurial command'
        ))
        self.vcsCommandAct.setWhatsThis(self.trUtf8(
            """<b>Execute command</b>"""
            """<p>This opens a dialog to enter an arbitrary Mercurial command.</p>"""
        ))
        self.vcsCommandAct.triggered[()].connect(self._vcsCommand)
        self.actions.append(self.vcsCommandAct)
        
        self.vcsPropsAct = E5Action(self.trUtf8('Command options'),
                self.trUtf8('Command &options...'), 0, 0, self,
                'mercurial_options')
        self.vcsPropsAct.setStatusTip(self.trUtf8('Show the Mercurial command options'))
        self.vcsPropsAct.setWhatsThis(self.trUtf8(
            """<b>Command options...</b>"""
            """<p>This shows a dialog to edit the Mercurial command options.</p>"""
        ))
        self.vcsPropsAct.triggered[()].connect(self._vcsCommandOptions)
        self.actions.append(self.vcsPropsAct)
        
        self.hgConfigAct = E5Action(self.trUtf8('Configure'),
                self.trUtf8('Configure...'),
                0, 0, self, 'mercurial_configure')
        self.hgConfigAct.setStatusTip(self.trUtf8(
            'Show the configuration dialog with the Mercurial page selected'
        ))
        self.hgConfigAct.setWhatsThis(self.trUtf8(
            """<b>Configure</b>"""
            """<p>Show the configuration dialog with the Mercurial page selected.</p>"""
        ))
        self.hgConfigAct.triggered[()].connect(self.__hgConfigure)
        self.actions.append(self.hgConfigAct)
        
        self.hgEditUserConfigAct = E5Action(self.trUtf8('Edit user configuration'),
                self.trUtf8('Edit user configuration...'),
                0, 0, self, 'mercurial_user_configure')
        self.hgEditUserConfigAct.setStatusTip(self.trUtf8(
            'Show an editor to edit the user configuration file'
        ))
        self.hgEditUserConfigAct.setWhatsThis(self.trUtf8(
            """<b>Edit user configuration</b>"""
            """<p>Show an editor to edit the user configuration file.</p>"""
        ))
        self.hgEditUserConfigAct.triggered[()].connect(self.__hgEditUserConfig)
        self.actions.append(self.hgEditUserConfigAct)
        
        self.hgRepoConfigAct = E5Action(self.trUtf8('Edit repository configuration'),
                self.trUtf8('Edit repository configuration...'),
                0, 0, self, 'mercurial_repo_configure')
        self.hgRepoConfigAct.setStatusTip(self.trUtf8(
            'Show an editor to edit the repository configuration file'
        ))
        self.hgRepoConfigAct.setWhatsThis(self.trUtf8(
            """<b>Edit repository configuration</b>"""
            """<p>Show an editor to edit the repository configuration file.</p>"""
        ))
        self.hgRepoConfigAct.triggered[()].connect(self.__hgEditRepoConfig)
        self.actions.append(self.hgRepoConfigAct)
        
        self.hgShowConfigAct = E5Action(
                self.trUtf8('Show combined configuration settings'),
                self.trUtf8('Show combined configuration settings...'),
                0, 0, self, 'mercurial_show_config')
        self.hgShowConfigAct.setStatusTip(self.trUtf8(
            'Show the combined configuration settings from all configuration files'
        ))
        self.hgShowConfigAct.setWhatsThis(self.trUtf8(
            """<b>Show combined configuration settings</b>"""
            """<p>This shows the combined configuration settings"""
            """ from all configuration files.</p>"""
        ))
        self.hgShowConfigAct.triggered[()].connect(self.__hgShowConfig)
        self.actions.append(self.hgShowConfigAct)
        
        self.hgShowPathsAct = E5Action(self.trUtf8('Show paths'),
                self.trUtf8('Show paths...'),
                0, 0, self, 'mercurial_show_paths')
        self.hgShowPathsAct.setStatusTip(self.trUtf8(
            'Show the aliases for remote repositories'
        ))
        self.hgShowPathsAct.setWhatsThis(self.trUtf8(
            """<b>Show paths</b>"""
            """<p>This shows the aliases for remote repositories.</p>"""
        ))
        self.hgShowPathsAct.triggered[()].connect(self.__hgShowPaths)
        self.actions.append(self.hgShowPathsAct)
        
        self.hgVerifyAct = E5Action(self.trUtf8('Verify repository'),
                self.trUtf8('Verify repository...'),
                0, 0, self, 'mercurial_verify')
        self.hgVerifyAct.setStatusTip(self.trUtf8(
            'Verify the integrity of the repository'
        ))
        self.hgVerifyAct.setWhatsThis(self.trUtf8(
            """<b>Verify repository</b>"""
            """<p>This verifies the integrity of the repository.</p>"""
        ))
        self.hgVerifyAct.triggered[()].connect(self.__hgVerify)
        self.actions.append(self.hgVerifyAct)
        
        self.hgRecoverAct = E5Action(self.trUtf8('Recover'),
                self.trUtf8('Recover...'),
                0, 0, self, 'mercurial_recover')
        self.hgRecoverAct.setStatusTip(self.trUtf8(
            'Recover from an interrupted transaction'
        ))
        self.hgRecoverAct.setWhatsThis(self.trUtf8(
            """<b>Recover</b>"""
            """<p>This recovers from an interrupted transaction.</p>"""
        ))
        self.hgRecoverAct.triggered[()].connect(self.__hgRecover)
        self.actions.append(self.hgRecoverAct)
        
        self.hgIdentifyAct = E5Action(self.trUtf8('Identify'),
                self.trUtf8('Identify...'),
                0, 0, self, 'mercurial_identify')
        self.hgIdentifyAct.setStatusTip(self.trUtf8(
            'Identify the project directory'
        ))
        self.hgIdentifyAct.setWhatsThis(self.trUtf8(
            """<b>Identify</b>"""
            """<p>This identifies the project directory.</p>"""
        ))
        self.hgIdentifyAct.triggered[()].connect(self.__hgIdentify)
        self.actions.append(self.hgIdentifyAct)
        
        self.hgCreateIgnoreAct = E5Action(self.trUtf8('Create .hgignore'),
                self.trUtf8('Create .hgignore'),
                0, 0, self, 'mercurial_create ignore')
        self.hgCreateIgnoreAct.setStatusTip(self.trUtf8(
            'Create a .hgignore file with default values'
        ))
        self.hgCreateIgnoreAct.setWhatsThis(self.trUtf8(
            """<b>Create .hgignore</b>"""
            """<p>This creates a .hgignore file with default values.</p>"""
        ))
        self.hgCreateIgnoreAct.triggered[()].connect(self.__hgCreateIgnore)
        self.actions.append(self.hgCreateIgnoreAct)
        
        self.hgBundleAct = E5Action(self.trUtf8('Create changegroup'),
                self.trUtf8('Create changegroup...'),
                0, 0, self, 'mercurial_bundle')
        self.hgBundleAct.setStatusTip(self.trUtf8(
            'Create changegroup file collecting changesets'
        ))
        self.hgBundleAct.setWhatsThis(self.trUtf8(
            """<b>Create changegroup</b>"""
            """<p>This creates a changegroup file collecting selected changesets"""
            """ (hg bundle).</p>"""
        ))
        self.hgBundleAct.triggered[()].connect(self.__hgBundle)
        self.actions.append(self.hgBundleAct)
        
        self.hgPreviewBundleAct = E5Action(self.trUtf8('Preview changegroup'),
                self.trUtf8('Preview changegroup...'),
                0, 0, self, 'mercurial_preview_bundle')
        self.hgPreviewBundleAct.setStatusTip(self.trUtf8(
            'Preview a changegroup file containing a collection of changesets'
        ))
        self.hgPreviewBundleAct.setWhatsThis(self.trUtf8(
            """<b>Preview changegroup</b>"""
            """<p>This previews a changegroup file containing a collection of"""
            """ changesets.</p>"""
        ))
        self.hgPreviewBundleAct.triggered[()].connect(self.__hgPreviewBundle)
        self.actions.append(self.hgPreviewBundleAct)
        
        self.hgIdentifyBundleAct = E5Action(self.trUtf8('Identify changegroup'),
                self.trUtf8('Identify changegroup...'),
                0, 0, self, 'mercurial_identify_bundle')
        self.hgIdentifyBundleAct.setStatusTip(self.trUtf8(
            'Identify a changegroup file containing a collection of changesets'
        ))
        self.hgIdentifyBundleAct.setWhatsThis(self.trUtf8(
            """<b>Identify changegroup</b>"""
            """<p>This identifies a changegroup file containing a collection of"""
            """ changesets.</p>"""
        ))
        self.hgIdentifyBundleAct.triggered[()].connect(self.__hgIdentifyBundle)
        self.actions.append(self.hgIdentifyBundleAct)
        
        self.hgUnbundleAct = E5Action(self.trUtf8('Apply changegroups'),
                self.trUtf8('Apply changegroups...'),
                0, 0, self, 'mercurial_unbundle')
        self.hgUnbundleAct.setStatusTip(self.trUtf8(
            'Apply one or several changegroup files'
        ))
        self.hgUnbundleAct.setWhatsThis(self.trUtf8(
            """<b>Apply changegroups</b>"""
            """<p>This applies one or several changegroup files generated by"""
            """ the 'Create changegroup' action (hg unbundle).</p>"""
        ))
        self.hgUnbundleAct.triggered[()].connect(self.__hgUnbundle)
        self.actions.append(self.hgUnbundleAct)
        
        self.hgBisectGoodAct = E5Action(self.trUtf8('Mark as "good"'),
                self.trUtf8('Mark as "good"...'),
                0, 0, self, 'mercurial_bisect_good')
        self.hgBisectGoodAct.setStatusTip(self.trUtf8(
            'Mark a selectable changeset as good'
        ))
        self.hgBisectGoodAct.setWhatsThis(self.trUtf8(
            """<b>Mark as good</b>"""
            """<p>This marks a selectable changeset as good.</p>"""
        ))
        self.hgBisectGoodAct.triggered[()].connect(self.__hgBisectGood)
        self.actions.append(self.hgBisectGoodAct)
        
        self.hgBisectBadAct = E5Action(self.trUtf8('Mark as "bad"'),
                self.trUtf8('Mark as "bad"...'),
                0, 0, self, 'mercurial_bisect_bad')
        self.hgBisectBadAct.setStatusTip(self.trUtf8(
            'Mark a selectable changeset as bad'
        ))
        self.hgBisectBadAct.setWhatsThis(self.trUtf8(
            """<b>Mark as bad</b>"""
            """<p>This marks a selectable changeset as bad.</p>"""
        ))
        self.hgBisectBadAct.triggered[()].connect(self.__hgBisectBad)
        self.actions.append(self.hgBisectBadAct)
        
        self.hgBisectSkipAct = E5Action(self.trUtf8('Skip'),
                self.trUtf8('Skip...'),
                0, 0, self, 'mercurial_bisect_skip')
        self.hgBisectSkipAct.setStatusTip(self.trUtf8(
            'Skip a selectable changeset'
        ))
        self.hgBisectSkipAct.setWhatsThis(self.trUtf8(
            """<b>Skip</b>"""
            """<p>This skips a selectable changeset.</p>"""
        ))
        self.hgBisectSkipAct.triggered[()].connect(self.__hgBisectSkip)
        self.actions.append(self.hgBisectSkipAct)
        
        self.hgBisectResetAct = E5Action(self.trUtf8('Reset'),
                self.trUtf8('Reset'),
                0, 0, self, 'mercurial_bisect_reset')
        self.hgBisectResetAct.setStatusTip(self.trUtf8(
            'Reset the bisect search data'
        ))
        self.hgBisectResetAct.setWhatsThis(self.trUtf8(
            """<b>Reset</b>"""
            """<p>This resets the bisect search data.</p>"""
        ))
        self.hgBisectResetAct.triggered[()].connect(self.__hgBisectReset)
        self.actions.append(self.hgBisectResetAct)
        
        self.hgBackoutAct = E5Action(self.trUtf8('Back out changeset'),
                self.trUtf8('Back out changeset'),
                0, 0, self, 'mercurial_backout')
        self.hgBackoutAct.setStatusTip(self.trUtf8(
            'Back out changes of an earlier changeset'
        ))
        self.hgBackoutAct.setWhatsThis(self.trUtf8(
            """<b>Back out changeset</b>"""
            """<p>This backs out changes of an earlier changeset.</p>"""
        ))
        self.hgBackoutAct.triggered[()].connect(self.__hgBackout)
        self.actions.append(self.hgBackoutAct)
        
        self.hgRollbackAct = E5Action(self.trUtf8('Rollback last transaction'),
                self.trUtf8('Rollback last transaction'),
                0, 0, self, 'mercurial_rollback')
        self.hgRollbackAct.setStatusTip(self.trUtf8(
            'Rollback the last transaction'
        ))
        self.hgRollbackAct.setWhatsThis(self.trUtf8(
            """<b>Rollback last transaction</b>"""
            """<p>This performs a rollback of the last transaction. Transactions"""
            """ are used to encapsulate the effects of all commands that create new"""
            """ changesets or propagate existing changesets into a repository."""
            """ For example, the following commands are transactional, and"""
            """ their effects can be rolled back:<ul>"""
            """<li>commit</li>"""
            """<li>import</li>"""
            """<li>pull</li>"""
            """<li>push (with this repository as the destination)</li>"""
            """<li>unbundle</li>"""
            """</ul>"""
            """</p><p><strong>This command is dangerous. Please use with care."""
            """</strong></p>"""
        ))
        self.hgRollbackAct.triggered[()].connect(self.__hgRollback)
        self.actions.append(self.hgRollbackAct)
        
        self.hgServeAct = E5Action(self.trUtf8('Serve project repository'),
                self.trUtf8('Serve project repository...'),
                0, 0, self, 'mercurial_serve')
        self.hgServeAct.setStatusTip(self.trUtf8(
            'Serve the project repository'
        ))
        self.hgServeAct.setWhatsThis(self.trUtf8(
            """<b>Serve project repository</b>"""
            """<p>This serves the project repository.</p>"""
        ))
        self.hgServeAct.triggered[()].connect(self.__hgServe)
        self.actions.append(self.hgServeAct)
        
        self.hgImportAct = E5Action(self.trUtf8('Import Patch'),
                self.trUtf8('Import Patch...'),
                0, 0, self, 'mercurial_import')
        self.hgImportAct.setStatusTip(self.trUtf8(
            'Import a patch from a patch file'
        ))
        self.hgImportAct.setWhatsThis(self.trUtf8(
            """<b>Import Patch</b>"""
            """<p>This imports a patch from a patch file into the project.</p>"""
        ))
        self.hgImportAct.triggered[()].connect(self.__hgImport)
        self.actions.append(self.hgImportAct)
        
        self.hgExportAct = E5Action(self.trUtf8('Export Patches'),
                self.trUtf8('Export Patches...'),
                0, 0, self, 'mercurial_export')
        self.hgExportAct.setStatusTip(self.trUtf8(
            'Export revisions to patch files'
        ))
        self.hgExportAct.setWhatsThis(self.trUtf8(
            """<b>Export Patches</b>"""
            """<p>This exports revisions of the project to patch files.</p>"""
        ))
        self.hgExportAct.triggered[()].connect(self.__hgExport)
        self.actions.append(self.hgExportAct)
        
        self.hgPhaseAct = E5Action(self.trUtf8('Change Phase'),
                self.trUtf8('Change Phase...'),
                0, 0, self, 'mercurial_change_phase')
        self.hgPhaseAct.setStatusTip(self.trUtf8(
            'Change the phase of revisions'
        ))
        self.hgPhaseAct.setWhatsThis(self.trUtf8(
            """<b>Change Phase</b>"""
            """<p>This changes the phase of revisions.</p>"""
        ))
        self.hgPhaseAct.triggered[()].connect(self.__hgPhase)
        self.actions.append(self.hgPhaseAct)
        
        self.hgGraftAct = E5Action(self.trUtf8('Copy Changesets'),
                UI.PixmapCache.getIcon("vcsGraft.png"),
                self.trUtf8('Copy Changesets'),
                0, 0, self, 'mercurial_graft')
        self.hgGraftAct.setStatusTip(self.trUtf8(
            'Copies changesets from another branch'
        ))
        self.hgGraftAct.setWhatsThis(self.trUtf8(
            """<b>Copy Changesets</b>"""
            """<p>This copies changesets from another branch on top of the"""
            """ current working directory with the user, date and description"""
            """ of the original changeset.</p>"""
        ))
        self.hgGraftAct.triggered[()].connect(self.__hgGraft)
        self.actions.append(self.hgGraftAct)
        
        self.hgGraftContinueAct = E5Action(
                self.trUtf8('Continue Copying Session'),
                self.trUtf8('Continue Copying Session'),
                0, 0, self, 'mercurial_graft_continue')
        self.hgGraftContinueAct.setStatusTip(self.trUtf8(
            'Continue the last copying session after conflicts were resolved'
        ))
        self.hgGraftContinueAct.setWhatsThis(self.trUtf8(
            """<b>Continue Copying Session</b>"""
            """<p>This continues the last copying session after conflicts were"""
            """ resolved.</p>"""
        ))
        self.hgGraftContinueAct.triggered[()].connect(self.__hgGraftContinue)
        self.actions.append(self.hgGraftContinueAct)
    
    def initMenu(self, menu):
        """
        Public method to generate the VCS menu.
        
        @param menu reference to the menu to be populated (QMenu)
        """
        menu.clear()
        
        self.subMenus = []
        
        adminMenu = QMenu(self.trUtf8("Repository Administration"), menu)
        adminMenu.setTearOffEnabled(True)
        adminMenu.addAction(self.hgHeadsAct)
        adminMenu.addAction(self.hgParentsAct)
        adminMenu.addAction(self.hgTipAct)
        adminMenu.addAction(self.hgShowBranchAct)
        adminMenu.addAction(self.hgIdentifyAct)
        adminMenu.addSeparator()
        adminMenu.addAction(self.hgShowPathsAct)
        adminMenu.addSeparator()
        adminMenu.addAction(self.hgShowConfigAct)
        adminMenu.addAction(self.hgRepoConfigAct)
        adminMenu.addSeparator()
        adminMenu.addAction(self.hgCreateIgnoreAct)
        adminMenu.addSeparator()
        adminMenu.addAction(self.hgRecoverAct)
        adminMenu.addSeparator()
        adminMenu.addAction(self.hgBackoutAct)
        adminMenu.addAction(self.hgRollbackAct)
        adminMenu.addSeparator()
        adminMenu.addAction(self.hgVerifyAct)
        self.subMenus.append(adminMenu)
        
        specialsMenu = QMenu(self.trUtf8("Specials"), menu)
        specialsMenu.setTearOffEnabled(True)
        specialsMenu.addAction(self.hgPushForcedAct)
        specialsMenu.addSeparator()
        specialsMenu.addAction(self.hgServeAct)
        self.subMenus.append(specialsMenu)
        
        bundleMenu = QMenu(self.trUtf8("Changegroup Management"), menu)
        bundleMenu.setTearOffEnabled(True)
        bundleMenu.addAction(self.hgBundleAct)
        bundleMenu.addAction(self.hgIdentifyBundleAct)
        bundleMenu.addAction(self.hgPreviewBundleAct)
        bundleMenu.addAction(self.hgUnbundleAct)
        self.subMenus.append(bundleMenu)
        
        patchMenu = QMenu(self.trUtf8("Patch Management"), menu)
        patchMenu.setTearOffEnabled(True)
        patchMenu.addAction(self.hgImportAct)
        patchMenu.addAction(self.hgExportAct)
        self.subMenus.append(patchMenu)
        
        bisectMenu = QMenu(self.trUtf8("Bisect"), menu)
        bisectMenu.setTearOffEnabled(True)
        bisectMenu.addAction(self.hgBisectGoodAct)
        bisectMenu.addAction(self.hgBisectBadAct)
        bisectMenu.addAction(self.hgBisectSkipAct)
        bisectMenu.addAction(self.hgBisectResetAct)
        self.subMenus.append(bisectMenu)
        
        self.__extensionsMenu = QMenu(self.trUtf8("Extensions"), menu)
        self.__extensionsMenu.setTearOffEnabled(True)
        self.__extensionsMenu.aboutToShow.connect(self.__showExtensionMenu)
        self.extensionMenus = {}
        for extensionMenuTitle in sorted(self.__extensionMenuTitles):
            extensionName = self.__extensionMenuTitles[extensionMenuTitle]
            self.extensionMenus[extensionName] = self.__extensionsMenu.addMenu(
                self.__extensions[extensionName].initMenu(self.__extensionsMenu))
        self.vcs.activeExtensionsChanged.connect(self.__showExtensionMenu)
        
        if self.vcs.version >= (2, 0):
            graftMenu = QMenu(self.trUtf8("Graft"), menu)
            graftMenu.setIcon(UI.PixmapCache.getIcon("vcsGraft.png"))
            graftMenu.setTearOffEnabled(True)
            graftMenu.addAction(self.hgGraftAct)
            graftMenu.addAction(self.hgGraftContinueAct)
        else:
            graftMenu = None
        
        act = menu.addAction(
            UI.PixmapCache.getIcon(
                os.path.join("VcsPlugins", "vcsMercurial", "icons", "mercurial.png")),
            self.vcs.vcsName(), self._vcsInfoDisplay)
        font = act.font()
        font.setBold(True)
        act.setFont(font)
        menu.addSeparator()
        
        menu.addAction(self.hgIncomingAct)
        menu.addAction(self.hgPullAct)
        menu.addAction(self.vcsUpdateAct)
        menu.addSeparator()
        menu.addAction(self.vcsCommitAct)
        menu.addAction(self.hgOutgoingAct)
        menu.addAction(self.hgPushAct)
        menu.addSeparator()
        if graftMenu is not None:
            menu.addMenu(graftMenu)
            menu.addSeparator()
        menu.addMenu(bundleMenu)
        menu.addMenu(patchMenu)
        menu.addSeparator()
        menu.addMenu(self.__extensionsMenu)
        menu.addSeparator()
        menu.addAction(self.vcsNewAct)
        menu.addAction(self.vcsExportAct)
        menu.addSeparator()
        menu.addAction(self.vcsRemoveAct)
        menu.addSeparator()
        menu.addAction(self.vcsTagAct)
        menu.addAction(self.hgTagListAct)
        menu.addAction(self.hgBranchAct)
        if self.vcs.version >= (1, 6):
            menu.addAction(self.hgPushBranchAct)
        menu.addAction(self.hgCloseBranchAct)
        menu.addAction(self.hgBranchListAct)
        menu.addSeparator()
        menu.addAction(self.vcsLogAct)
        menu.addAction(self.hgLogBrowserAct)
        menu.addSeparator()
        menu.addAction(self.vcsStatusAct)
        menu.addSeparator()
        menu.addAction(self.vcsDiffAct)
        menu.addAction(self.hgExtDiffAct)
        menu.addSeparator()
        if self.vcs.version >= (2, 1):
            menu.addAction(self.hgPhaseAct)
            menu.addSeparator()
        menu.addAction(self.vcsRevertAct)
        menu.addAction(self.vcsMergeAct)
        menu.addAction(self.vcsResolveAct)
        menu.addSeparator()
        menu.addAction(self.vcsSwitchAct)
        menu.addSeparator()
        menu.addMenu(bisectMenu)
        menu.addSeparator()
        menu.addAction(self.vcsCleanupAct)
        menu.addSeparator()
        menu.addAction(self.vcsCommandAct)
        menu.addSeparator()
        menu.addMenu(adminMenu)
        menu.addMenu(specialsMenu)
        menu.addSeparator()
        menu.addAction(self.vcsPropsAct)
        menu.addSeparator()
        menu.addAction(self.hgEditUserConfigAct)
        menu.addAction(self.hgConfigAct)
    
    def shutdown(self):
        """
        Public method to perform shutdown actions.
        """
        self.vcs.activeExtensionsChanged.disconnect(self.__showExtensionMenu)
        
        # close torn off sub menus
        for menu in self.subMenus:
            if menu.isTearOffMenuVisible():
                menu.hideTearOffMenu()
        
        # close torn off extension menus
        for extensionName in self.extensionMenus:
            menu = self.extensionMenus[extensionName].menu()
            if menu.isTearOffMenuVisible():
                menu.hideTearOffMenu()
        
        if self.__extensionsMenu.isTearOffMenuVisible():
            self.__extensionsMenu.hideTearOffMenu()
    
    def __showExtensionMenu(self):
        """
        Private slot showing the extensions menu.
        """
        for extensionName in self.extensionMenus:
            self.extensionMenus[extensionName].setEnabled(
                self.vcs.isExtensionActive(extensionName))
            if not self.extensionMenus[extensionName].isEnabled() and \
               self.extensionMenus[extensionName].menu().isTearOffMenuVisible():
                self.extensionMenus[extensionName].menu().hideTearOffMenu()
    
    def __hgExtendedDiff(self):
        """
        Private slot used to perform a hg diff with the selection of revisions.
        """
        self.vcs.hgExtendedDiff(self.project.ppath)
    
    def __hgLogBrowser(self):
        """
        Private slot used to browse the log of the current project.
        """
        self.vcs.hgLogBrowser(self.project.ppath)
    
    def __hgIncoming(self):
        """
        Private slot used to show the log of changes coming into the repository.
        """
        self.vcs.hgIncoming(self.project.ppath)
    
    def __hgOutgoing(self):
        """
        Private slot used to show the log of changes going out of the repository.
        """
        self.vcs.hgOutgoing(self.project.ppath)
    
    def __hgPull(self):
        """
        Private slot used to pull changes from a remote repository.
        """
        shouldReopen = self.vcs.hgPull(self.project.ppath)
        if shouldReopen:
            res = E5MessageBox.yesNo(self.parent(),
                self.trUtf8("Pull"),
                self.trUtf8("""The project should be reread. Do this now?"""),
                yesDefault=True)
            if res:
                self.project.reopenProject()
    
    def __hgPush(self):
        """
        Private slot used to push changes to a remote repository.
        """
        self.vcs.hgPush(self.project.ppath)
    
    def __hgPushForced(self):
        """
        Private slot used to push changes to a remote repository using
        the force option.
        """
        self.vcs.hgPush(self.project.ppath, force=True)
    
    def __hgHeads(self):
        """
        Private slot used to show the heads of the repository.
        """
        self.vcs.hgInfo(self.project.ppath, mode="heads")
    
    def __hgParents(self):
        """
        Private slot used to show the parents of the repository.
        """
        self.vcs.hgInfo(self.project.ppath, mode="parents")
    
    def __hgTip(self):
        """
        Private slot used to show the tip of the repository.
        """
        self.vcs.hgInfo(self.project.ppath, mode="tip")
    
    def __hgResolve(self):
        """
        Private slot used to resolve conflicts of the local project.
        """
        self.vcs.hgResolve(self.project.ppath)
    
    def __hgTagList(self):
        """
        Private slot used to list the tags of the project.
        """
        self.vcs.hgListTagBranch(self.project.ppath, True)
    
    def __hgBranchList(self):
        """
        Private slot used to list the branches of the project.
        """
        self.vcs.hgListTagBranch(self.project.ppath, False)
    
    def __hgBranch(self):
        """
        Private slot used to create a new branch for the project.
        """
        self.vcs.hgBranch(self.project.ppath)
    
    def __hgShowBranch(self):
        """
        Private slot used to show the current branch for the project.
        """
        self.vcs.hgShowBranch(self.project.ppath)
    
    def __hgConfigure(self):
        """
        Private method to open the configuration dialog.
        """
        e5App().getObject("UserInterface").showPreferences("zzz_mercurialPage")
    
    def __hgCloseBranch(self):
        """
        Private slot used to close the current branch of the local project.
        """
        if Preferences.getVCS("AutoSaveProject"):
            self.project.saveProject()
        if Preferences.getVCS("AutoSaveFiles"):
            self.project.saveAllScripts()
        self.vcs.vcsCommit(self.project.ppath, '', closeBranch=True)
    
    def __hgPushNewBranch(self):
        """
        Private slot to push a new named branch.
        """
        self.vcs.hgPush(self.project.ppath, newBranch=True)
    
    def __hgEditUserConfig(self):
        """
        Private slot used to edit the repository configuration file.
        """
        self.vcs.hgEditUserConfig()
    
    def __hgEditRepoConfig(self):
        """
        Private slot used to edit the repository configuration file.
        """
        self.vcs.hgEditConfig(self.project.ppath)
    
    def __hgShowConfig(self):
        """
        Private slot used to show the combined configuration.
        """
        self.vcs.hgShowConfig(self.project.ppath)
    
    def __hgVerify(self):
        """
        Private slot used to verify the integrity of the repository.
        """
        self.vcs.hgVerify(self.project.ppath)
    
    def __hgShowPaths(self):
        """
        Private slot used to show the aliases for remote repositories.
        """
        self.vcs.hgShowPaths(self.project.ppath)
    
    def __hgRecover(self):
        """
        Private slot used to recover from an interrupted transaction.
        """
        self.vcs.hgRecover(self.project.ppath)
    
    def __hgIdentify(self):
        """
        Private slot used to identify the project directory.
        """
        self.vcs.hgIdentify(self.project.ppath)
    
    def __hgCreateIgnore(self):
        """
        Private slot used to create a .hgignore file for the project.
        """
        self.vcs.hgCreateIgnoreFile(self.project.ppath, autoAdd=True)
    
    def __hgBundle(self):
        """
        Private slot used to create a changegroup file.
        """
        self.vcs.hgBundle(self.project.ppath)
    
    def __hgPreviewBundle(self):
        """
        Private slot used to preview a changegroup file.
        """
        self.vcs.hgPreviewBundle(self.project.ppath)
    
    def __hgIdentifyBundle(self):
        """
        Private slot used to identify a changegroup file.
        """
        self.vcs.hgIdentifyBundle(self.project.ppath)
    
    def __hgUnbundle(self):
        """
        Private slot used to apply changegroup files.
        """
        shouldReopen = self.vcs.hgUnbundle(self.project.ppath)
        if shouldReopen:
            res = E5MessageBox.yesNo(self.parent(),
                self.trUtf8("Apply changegroups"),
                self.trUtf8("""The project should be reread. Do this now?"""),
                yesDefault=True)
            if res:
                self.project.reopenProject()
    
    def __hgBisectGood(self):
        """
        Private slot used to execute the bisect --good command.
        """
        self.vcs.hgBisect(self.project.ppath, "good")
    
    def __hgBisectBad(self):
        """
        Private slot used to execute the bisect --bad command.
        """
        self.vcs.hgBisect(self.project.ppath, "bad")
    
    def __hgBisectSkip(self):
        """
        Private slot used to execute the bisect --skip command.
        """
        self.vcs.hgBisect(self.project.ppath, "skip")
    
    def __hgBisectReset(self):
        """
        Private slot used to execute the bisect --reset command.
        """
        self.vcs.hgBisect(self.project.ppath, "reset")
    
    def __hgBackout(self):
        """
        Private slot used to back out changes of a changeset.
        """
        self.vcs.hgBackout(self.project.ppath)
    
    def __hgRollback(self):
        """
        Private slot used to rollback the last transaction.
        """
        self.vcs.hgRollback(self.project.ppath)
    
    def __hgServe(self):
        """
        Private slot used to serve the project.
        """
        self.vcs.hgServe(self.project.ppath)
    
    def __hgImport(self):
        """
        Private slot used to import a patch file.
        """
        shouldReopen = self.vcs.hgImport(self.project.ppath)
        if shouldReopen:
            res = E5MessageBox.yesNo(self.parent(),
                self.trUtf8("Import Patch"),
                self.trUtf8("""The project should be reread. Do this now?"""),
                yesDefault=True)
            if res:
                self.project.reopenProject()
    
    def __hgExport(self):
        """
        Private slot used to export revisions to patch files.
        """
        self.vcs.hgExport(self.project.ppath)
    
    def __hgRevert(self):
        """
        Private slot used to revert changes made to the local project.
        """
        shouldReopen = self.vcs.hgRevert(self.project.ppath)
        if shouldReopen:
            res = E5MessageBox.yesNo(self.parent(),
                self.trUtf8("Revert Changes"),
                self.trUtf8("""The project should be reread. Do this now?"""),
                yesDefault=True)
            if res:
                self.project.reopenProject()
    
    def __hgPhase(self):
        """
        Private slot used to change the phase of revisions.
        """
        self.vcs.hgPhase(self.project.ppath)
    
    def __hgGraft(self):
        """
        Private slot used to copy changesets from another branch.
        """
        shouldReopen = self.vcs.hgGraft(self.project.getProjectPath())
        if shouldReopen:
            res = E5MessageBox.yesNo(None,
                self.trUtf8("Copy Changesets"),
                self.trUtf8("""The project should be reread. Do this now?"""),
                yesDefault=True)
            if res:
                self.project.reopenProject()
    
    def __hgGraftContinue(self):
        """
        Private slot used to continue the last copying session after conflicts
        were resolved.
        """
        shouldReopen = self.vcs.hgGraftContinue(self.project.getProjectPath())
        if shouldReopen:
            res = E5MessageBox.yesNo(None,
                self.trUtf8("Copy Changesets (Continue)"),
                self.trUtf8("""The project should be reread. Do this now?"""),
                yesDefault=True)
            if res:
                self.project.reopenProject()
