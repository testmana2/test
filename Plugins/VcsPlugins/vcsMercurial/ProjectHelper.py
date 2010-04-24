# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the VCS project helper for Mercurial.
"""

import os

from PyQt4.QtCore import SIGNAL
from PyQt4.QtGui import QMenu

from E5Gui.E5Application import e5App

from VCS.ProjectHelper import VcsProjectHelper

from E5Gui.E5Action import E5Action

import UI.PixmapCache
import Preferences

class HgProjectHelper(VcsProjectHelper):
    """
    Class implementing the VCS project helper for Mercurial.
    """
    def __init__(self, vcsObject, projectObject, parent = None, name = None):
        """
        Constructor
        
        @param vcsObject reference to the vcs object
        @param projectObject reference to the project object
        @param parent parent widget (QWidget)
        @param name name of this object (string)
        """
        VcsProjectHelper.__init__(self, vcsObject, projectObject, parent, name)
    
    def getActions(self):
        """
        Public method to get a list of all actions.
        
        @return list of all actions (list of E5Action)
        """
        return self.actions[:]
    
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
        self.connect(self.vcsNewAct, SIGNAL('triggered()'), self._vcsCheckout)
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
        self.connect(self.hgIncomingAct, SIGNAL('triggered()'), self.__hgIncoming)
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
        self.connect(self.hgPullAct, SIGNAL('triggered()'), self.__hgPull)
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
        self.connect(self.vcsUpdateAct, SIGNAL('triggered()'), self._vcsUpdate)
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
        self.connect(self.vcsCommitAct, SIGNAL('triggered()'), self._vcsCommit)
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
        self.connect(self.hgOutgoingAct, SIGNAL('triggered()'), self.__hgOutgoing)
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
        self.connect(self.hgPushAct, SIGNAL('triggered()'), self.__hgPush)
        self.actions.append(self.hgPushAct)
        
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
        self.connect(self.vcsExportAct, SIGNAL('triggered()'), self._vcsExport)
        self.actions.append(self.vcsExportAct)
        
        self.vcsAddAct = E5Action(self.trUtf8('Add to repository'),
                UI.PixmapCache.getIcon("vcsAdd.png"),
                self.trUtf8('&Add to repository...'), 0, 0, self, 'mercurial_add')
        self.vcsAddAct.setStatusTip(self.trUtf8(
            'Add the local project to the repository'
        ))
        self.vcsAddAct.setWhatsThis(self.trUtf8(
            """<b>Add to repository</b>"""
            """<p>This adds (imports) the local project to the repository.</p>"""
        ))
        self.connect(self.vcsAddAct, SIGNAL('triggered()'), self._vcsImport)
        self.actions.append(self.vcsAddAct)
        
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
        self.connect(self.vcsRemoveAct, SIGNAL('triggered()'), self._vcsRemove)
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
        self.connect(self.vcsLogAct, SIGNAL('triggered()'), self._vcsLog)
        self.actions.append(self.vcsLogAct)
        
        self.hgLogLimitedAct = E5Action(self.trUtf8('Show limited log'),
                UI.PixmapCache.getIcon("vcsLog.png"),
                self.trUtf8('Show limited log'),
                0, 0, self, 'mercurial_log_limited')
        self.hgLogLimitedAct.setStatusTip(self.trUtf8(
            'Show a limited log of the local project'
        ))
        self.hgLogLimitedAct.setWhatsThis(self.trUtf8(
            """<b>Show limited log</b>"""
            """<p>This shows the log of the local project limited to a selectable"""
            """ number of entries.</p>"""
        ))
        self.connect(self.hgLogLimitedAct, SIGNAL('triggered()'), self.__hgLogLimited)
        self.actions.append(self.hgLogLimitedAct)
        
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
        self.connect(self.hgLogBrowserAct, SIGNAL('triggered()'), self.__hgLogBrowser)
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
        self.connect(self.vcsDiffAct, SIGNAL('triggered()'), self._vcsDiff)
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
        self.connect(self.hgExtDiffAct, SIGNAL('triggered()'), self.__hgExtendedDiff)
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
        self.connect(self.vcsStatusAct, SIGNAL('triggered()'), self._vcsStatus)
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
        self.connect(self.hgHeadsAct, SIGNAL('triggered()'), self.__hgHeads)
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
        self.connect(self.hgParentsAct, SIGNAL('triggered()'), self.__hgParents)
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
        self.connect(self.hgTipAct, SIGNAL('triggered()'), self.__hgTip)
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
        self.connect(self.vcsRevertAct, SIGNAL('triggered()'), self._vcsRevert)
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
        self.connect(self.vcsMergeAct, SIGNAL('triggered()'), self._vcsMerge)
        self.actions.append(self.vcsMergeAct)
    
        self.vcsResolveAct = E5Action(self.trUtf8('Resolve conflicts'),
                self.trUtf8('Resolve con&flicts'),
                0, 0, self, 'mercurial_resolve')
        self.vcsResolveAct.setStatusTip(self.trUtf8(
            'Resolve all conflicts of the local project'
        ))
        self.vcsResolveAct.setWhatsThis(self.trUtf8(
            """<b>Resolve conflicts</b>"""
            """<p>This resolves all conflicts of the local project.</p>"""
        ))
        self.connect(self.vcsResolveAct, SIGNAL('triggered()'), self.__hgResolve)
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
        self.connect(self.vcsTagAct, SIGNAL('triggered()'), self._vcsTag)
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
        self.connect(self.hgTagListAct, SIGNAL('triggered()'), self.__hgTagList)
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
        self.connect(self.hgBranchListAct, SIGNAL('triggered()'), self.__hgBranchList)
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
        self.connect(self.hgBranchAct, SIGNAL('triggered()'), self.__hgBranch)
        self.actions.append(self.hgBranchAct)
        
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
        self.connect(self.hgCloseBranchAct, SIGNAL('triggered()'), self.__hgCloseBranch)
        self.actions.append(self.hgCloseBranchAct)
        
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
        self.connect(self.vcsSwitchAct, SIGNAL('triggered()'), self._vcsSwitch)
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
        self.connect(self.vcsCleanupAct, SIGNAL('triggered()'), self._vcsCleanup)
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
        self.connect(self.vcsCommandAct, SIGNAL('triggered()'), self._vcsCommand)
        self.actions.append(self.vcsCommandAct)
        
        self.vcsPropsAct = E5Action(self.trUtf8('Command options'),
                self.trUtf8('Command &options...'),0,0,self,
                'mercurial_options')
        self.vcsPropsAct.setStatusTip(self.trUtf8('Show the Mercurial command options'))
        self.vcsPropsAct.setWhatsThis(self.trUtf8(
            """<b>Command options...</b>"""
            """<p>This shows a dialog to edit the Mercurial command options.</p>"""
        ))
        self.connect(self.vcsPropsAct, SIGNAL('triggered()'), self._vcsCommandOptions)
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
        self.connect(self.hgConfigAct, SIGNAL('triggered()'), self.__hgConfigure)
        self.actions.append(self.hgConfigAct)
        
        self.hgRepoConfigAct = E5Action(self.trUtf8('Edit repository config'),
                self.trUtf8('Edit repository config...'),
                0, 0, self, 'mercurial_repo_configure')
        self.hgRepoConfigAct.setStatusTip(self.trUtf8(
            'Show an editor to edit the repository config file'
        ))
        self.hgRepoConfigAct.setWhatsThis(self.trUtf8(
            """<b>Edit repository config</b>"""
            """<p>Show an editor to edit the repository config file.</p>"""
        ))
        self.connect(self.hgRepoConfigAct, SIGNAL('triggered()'), self.__hgEditRepoConfig)
        self.actions.append(self.hgRepoConfigAct)
        
        self.hgShowConfigAct = E5Action(self.trUtf8('Show combined config settings'),
                self.trUtf8('Show combined config settings...'),
                0, 0, self, 'mercurial_show_config')
        self.hgShowConfigAct.setStatusTip(self.trUtf8(
            'Show the combined config settings from all config files'
        ))
        self.hgShowConfigAct.setWhatsThis(self.trUtf8(
            """<b>Show combined config settings</b>"""
            """<p>This shows the combined config settings from all config files.</p>"""
        ))
        self.connect(self.hgShowConfigAct, SIGNAL('triggered()'), self.__hgShowConfig)
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
        self.connect(self.hgShowPathsAct, SIGNAL('triggered()'), self.__hgShowPaths)
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
        self.connect(self.hgVerifyAct, SIGNAL('triggered()'), self.__hgVerify)
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
        self.connect(self.hgRecoverAct, SIGNAL('triggered()'), self.__hgRecover)
        self.actions.append(self.hgRecoverAct)
        
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
        self.connect(self.hgCreateIgnoreAct, SIGNAL('triggered()'), self.__hgCreateIgnore)
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
        self.connect(self.hgBundleAct, SIGNAL('triggered()'), self.__hgBundle)
        self.actions.append(self.hgBundleAct)
        
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
        self.connect(self.hgUnbundleAct, SIGNAL('triggered()'), self.__hgUnbundle)
        self.actions.append(self.hgUnbundleAct)
    
    def initMenu(self, menu):
        """
        Public method to generate the VCS menu.
        
        @param menu reference to the menu to be populated (QMenu)
        """
        menu.clear()
        
        adminMenu = QMenu(self.trUtf8("Repository Administration"), menu)
        adminMenu.addAction(self.hgHeadsAct)
        adminMenu.addAction(self.hgParentsAct)
        adminMenu.addAction(self.hgTipAct)
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
        adminMenu.addAction(self.hgVerifyAct)
        
        bundleMenu = QMenu(self.trUtf8("Changegroup Management"), menu)
        bundleMenu.addAction(self.hgBundleAct)
        bundleMenu.addAction(self.hgUnbundleAct)
        
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
        menu.addMenu(bundleMenu)
        menu.addSeparator()
        menu.addAction(self.vcsNewAct)
        menu.addAction(self.vcsExportAct)
        menu.addSeparator()
        menu.addAction(self.vcsAddAct)
        menu.addAction(self.vcsRemoveAct)
        menu.addSeparator()
        menu.addAction(self.vcsTagAct)
        menu.addAction(self.hgTagListAct)
        menu.addAction(self.hgBranchAct)
        menu.addAction(self.hgCloseBranchAct)
        menu.addAction(self.hgBranchListAct)
        menu.addSeparator()
        menu.addAction(self.vcsLogAct)
        menu.addAction(self.hgLogLimitedAct)
        menu.addAction(self.hgLogBrowserAct)
        menu.addSeparator()
        menu.addAction(self.vcsStatusAct)
        menu.addSeparator()
        menu.addAction(self.vcsDiffAct)
        menu.addAction(self.hgExtDiffAct)
        menu.addSeparator()
        menu.addAction(self.vcsRevertAct)
        menu.addAction(self.vcsMergeAct)
        menu.addAction(self.vcsResolveAct)
        menu.addSeparator()
        menu.addAction(self.vcsSwitchAct)
        menu.addSeparator()
        menu.addAction(self.vcsCleanupAct)
        menu.addSeparator()
        menu.addAction(self.vcsCommandAct)
        menu.addSeparator()
        menu.addMenu(adminMenu)
        menu.addSeparator()
        menu.addAction(self.vcsPropsAct)
        menu.addSeparator()
        menu.addAction(self.hgConfigAct)
    
    def __hgExtendedDiff(self):
        """
        Private slot used to perform a hg diff with the selection of revisions.
        """
        self.vcs.hgExtendedDiff(self.project.ppath)
    
    def __hgLogLimited(self):
        """
        Private slot used to perform a hg log --limit.
        """
        self.vcs.hgLogLimited(self.project.ppath)
    
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
        self.vcs.hgPull(self.project.ppath)
    
    def __hgPush(self):
        """
        Private slot used to push changes to a remote repository.
        """
        self.vcs.hgPush(self.project.ppath)
    
    def __hgHeads(self):
        """
        Private slot used to show the heads of the repository.
        """
        self.vcs.hgInfo(self.project.ppath, mode = "heads")
    
    def __hgParents(self):
        """
        Private slot used to show the parents of the repository.
        """
        self.vcs.hgInfo(self.project.ppath, mode = "parents")
    
    def __hgTip(self):
        """
        Private slot used to show the tip of the repository.
        """
        self.vcs.hgInfo(self.project.ppath, mode = "tip")
    
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
    
    def __hgConfigure(self):
        """
        Private method to open the configuration dialog.
        """
        e5App().getObject("UserInterface").showPreferences("zzz_mercurialPage")
    
    def __hgCloseBranch(self):
        """
        Protected slot used to close the current branch of the local project.
        """
        if Preferences.getVCS("AutoSaveProject"):
            self.project.saveProject()
        if Preferences.getVCS("AutoSaveFiles"):
            self.project.saveAllScripts()
        self.vcs.vcsCommit(self.project.ppath, '', closeBranch = True)
    
    def __hgEditRepoConfig(self):
        """
        Protected slot used to edit the repository config file.
        """
        self.vcs.hgEditConfig(self.project.ppath)
    
    def __hgShowConfig(self):
        """
        Protected slot used to show the combined config.
        """
        self.vcs.hgShowConfig(self.project.ppath)
    
    def __hgVerify(self):
        """
        Protected slot used to verify the integrity of the repository.
        """
        self.vcs.hgVerify(self.project.ppath)
    
    def __hgShowPaths(self):
        """
        Protected slot used to show the aliases for remote repositories.
        """
        self.vcs.hgShowPaths(self.project.ppath)
    
    def __hgRecover(self):
        """
        Protected slot used to recover from an interrupted transaction.
        """
        self.vcs.hgRecover(self.project.ppath)
    
    def __hgCreateIgnore(self):
        """
        Protected slot used to create a .hgignore file for the project.
        """
        self.vcs.hgCreateIgnoreFile(self.project.ppath, autoAdd = True)
    
    def __hgBundle(self):
        """
        Protected slot used to create a changegroup file.
        """
        self.vcs.hgBundle(self.project.ppath)
    
    def __hgUnbundle(self):
        """
        Protected slot used to apply changegroup files.
        """
        self.vcs.hgUnbundle(self.project.ppath)
