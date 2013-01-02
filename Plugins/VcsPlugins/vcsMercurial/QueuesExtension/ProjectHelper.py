# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the queues extension project helper.
"""

from PyQt4.QtGui import QMenu

from E5Gui.E5Action import E5Action
from E5Gui import E5MessageBox

from ..HgExtensionProjectHelper import HgExtensionProjectHelper

from .queues import Queues


class QueuesProjectHelper(HgExtensionProjectHelper):
    """
    Class implementing the queues extension project helper.
    """
    def __init__(self):
        """
        Constructor
        """
        super().__init__()
    
    def initActions(self):
        """
        Public method to generate the action objects.
        """
        self.hgQueueNewAct = E5Action(self.trUtf8('New Patch'),
                self.trUtf8('New Patch...'),
                0, 0, self, 'mercurial_queues_new')
        self.hgQueueNewAct.setStatusTip(self.trUtf8(
            'Create a new patch'
        ))
        self.hgQueueNewAct.setWhatsThis(self.trUtf8(
            """<b>New Patch</b>"""
            """<p>This creates a new named patch.</p>"""
        ))
        self.hgQueueNewAct.triggered[()].connect(self.__hgQueueNewPatch)
        self.actions.append(self.hgQueueNewAct)
        
        self.hgQueueRefreshAct = E5Action(self.trUtf8('Update Current Patch'),
                self.trUtf8('Update Current Patch'),
                0, 0, self, 'mercurial_queues_refresh')
        self.hgQueueRefreshAct.setStatusTip(self.trUtf8(
            'Update the current patch'
        ))
        self.hgQueueRefreshAct.setWhatsThis(self.trUtf8(
            """<b>Update Current Patch</b>"""
            """<p>This updates the current patch.</p>"""
        ))
        self.hgQueueRefreshAct.triggered[()].connect(self.__hgQueueRefreshPatch)
        self.actions.append(self.hgQueueRefreshAct)
        
        self.hgQueueRefreshMessageAct = E5Action(
                self.trUtf8('Update Current Patch (with Message)'),
                self.trUtf8('Update Current Patch (with Message)'),
                0, 0, self, 'mercurial_queues_refresh_message')
        self.hgQueueRefreshMessageAct.setStatusTip(self.trUtf8(
            'Update the current patch and edit commit message'
        ))
        self.hgQueueRefreshMessageAct.setWhatsThis(self.trUtf8(
            """<b>Update Current Patch (with Message)</b>"""
            """<p>This updates the current patch after giving the chance to change"""
            """ the current commit message.</p>"""
        ))
        self.hgQueueRefreshMessageAct.triggered[()].connect(
            self.__hgQueueRefreshPatchMessage)
        self.actions.append(self.hgQueueRefreshMessageAct)
        
        self.hgQueueDiffAct = E5Action(self.trUtf8('Show Current Patch'),
                self.trUtf8('Show Current Patch...'),
                0, 0, self, 'mercurial_queues_show')
        self.hgQueueDiffAct.setStatusTip(self.trUtf8(
            'Show the contents the current patch'
        ))
        self.hgQueueDiffAct.setWhatsThis(self.trUtf8(
            """<b>Show Current Patch</b>"""
            """<p>This shows the contents of the current patch including"""
            """ any changes which have been made in the working directory"""
            """ since the last refresh.</p>"""
        ))
        self.hgQueueDiffAct.triggered[()].connect(self.__hgQueueShowPatch)
        self.actions.append(self.hgQueueDiffAct)
        
        self.hgQueueHeaderAct = E5Action(self.trUtf8('Show Current Message'),
                self.trUtf8('Show Current Message...'),
                0, 0, self, 'mercurial_queues_show_message')
        self.hgQueueHeaderAct.setStatusTip(self.trUtf8(
            'Show the commit message of the current patch'
        ))
        self.hgQueueHeaderAct.setWhatsThis(self.trUtf8(
            """<b>Show Current Message</b>"""
            """<p>This shows the commit message of the current patch.</p>"""
        ))
        self.hgQueueHeaderAct.triggered[()].connect(self.__hgQueueShowHeader)
        self.actions.append(self.hgQueueHeaderAct)
        
        self.hgQueueListAct = E5Action(self.trUtf8('List Patches'),
                self.trUtf8('List Patches...'),
                0, 0, self, 'mercurial_queues_list')
        self.hgQueueListAct.setStatusTip(self.trUtf8(
            'List applied and unapplied patches'
        ))
        self.hgQueueListAct.setWhatsThis(self.trUtf8(
            """<b>List Patches</b>"""
            """<p>This lists all applied and unapplied patches.</p>"""
        ))
        self.hgQueueListAct.triggered[()].connect(self.__hgQueueListPatches)
        self.actions.append(self.hgQueueListAct)
        
        self.hgQueueFinishAct = E5Action(self.trUtf8('Finish Applied Patches'),
                self.trUtf8('Finish Applied Patches'),
                0, 0, self, 'mercurial_queues_finish_applied')
        self.hgQueueFinishAct.setStatusTip(self.trUtf8(
            'Finish applied patches'
        ))
        self.hgQueueFinishAct.setWhatsThis(self.trUtf8(
            """<b>Finish Applied Patches</b>"""
            """<p>This finishes the applied patches by moving them out of"""
            """ mq control into regular repository history.</p>"""
        ))
        self.hgQueueFinishAct.triggered[()].connect(self.__hgQueueFinishAppliedPatches)
        self.actions.append(self.hgQueueFinishAct)
        
        self.hgQueueRenameAct = E5Action(self.trUtf8('Rename Patch'),
                self.trUtf8('Rename Patch'),
                0, 0, self, 'mercurial_queues_rename')
        self.hgQueueRenameAct.setStatusTip(self.trUtf8(
            'Rename a patch'
        ))
        self.hgQueueRenameAct.setWhatsThis(self.trUtf8(
            """<b>Rename Patch</b>"""
            """<p>This renames the current or a named patch.</p>"""
        ))
        self.hgQueueRenameAct.triggered[()].connect(self.__hgQueueRenamePatch)
        self.actions.append(self.hgQueueRenameAct)
        
        self.hgQueueDeleteAct = E5Action(self.trUtf8('Delete Patch'),
                self.trUtf8('Delete Patch'),
                0, 0, self, 'mercurial_queues_delete')
        self.hgQueueDeleteAct.setStatusTip(self.trUtf8(
            'Delete unapplied patch'
        ))
        self.hgQueueDeleteAct.setWhatsThis(self.trUtf8(
            """<b>Delete Patch</b>"""
            """<p>This deletes an unapplied patch.</p>"""
        ))
        self.hgQueueDeleteAct.triggered[()].connect(self.__hgQueueDeletePatch)
        self.actions.append(self.hgQueueDeleteAct)
        
        self.hgQueueFoldAct = E5Action(self.trUtf8('Fold Patches'),
                self.trUtf8('Fold Patches'),
                0, 0, self, 'mercurial_queues_fold')
        self.hgQueueFoldAct.setStatusTip(self.trUtf8(
            'Fold unapplied patches into the current patch'
        ))
        self.hgQueueFoldAct.setWhatsThis(self.trUtf8(
            """<b>Fold Patches</b>"""
            """<p>This folds unapplied patches into the current patch.</p>"""
        ))
        self.hgQueueFoldAct.triggered[()].connect(self.__hgQueueFoldUnappliedPatches)
        self.actions.append(self.hgQueueFoldAct)
        
        self.__initPushPopActions()
        self.__initPushPopForceActions()
        self.__initGuardsActions()
        self.__initQueuesMgmtActions()
    
    def __initPushPopActions(self):
        """
        Public method to generate the push and pop action objects.
        """
        self.hgQueuePushAct = E5Action(self.trUtf8('Push Next Patch'),
                self.trUtf8('Push Next Patch'),
                0, 0, self, 'mercurial_queues_push_next')
        self.hgQueuePushAct.setStatusTip(self.trUtf8(
            'Push the next patch onto the stack'
        ))
        self.hgQueuePushAct.setWhatsThis(self.trUtf8(
            """<b>Push Next Patch</b>"""
            """<p>This pushes the next patch onto the stack of applied patches.</p>"""
        ))
        self.hgQueuePushAct.triggered[()].connect(self.__hgQueuePushPatch)
        self.actions.append(self.hgQueuePushAct)
        
        self.hgQueuePushAllAct = E5Action(self.trUtf8('Push All Patches'),
                self.trUtf8('Push All Patches'),
                0, 0, self, 'mercurial_queues_push_all')
        self.hgQueuePushAllAct.setStatusTip(self.trUtf8(
            'Push all patches onto the stack'
        ))
        self.hgQueuePushAllAct.setWhatsThis(self.trUtf8(
            """<b>Push All Patches</b>"""
            """<p>This pushes all patches onto the stack of applied patches.</p>"""
        ))
        self.hgQueuePushAllAct.triggered[()].connect(self.__hgQueuePushAllPatches)
        self.actions.append(self.hgQueuePushAllAct)
        
        self.hgQueuePushUntilAct = E5Action(self.trUtf8('Push Patches'),
                self.trUtf8('Push Patches'),
                0, 0, self, 'mercurial_queues_push_until')
        self.hgQueuePushUntilAct.setStatusTip(self.trUtf8(
            'Push patches onto the stack'
        ))
        self.hgQueuePushUntilAct.setWhatsThis(self.trUtf8(
            """<b>Push Patches</b>"""
            """<p>This pushes patches onto the stack of applied patches until"""
            """ a named patch is at the top of the stack.</p>"""
        ))
        self.hgQueuePushUntilAct.triggered[()].connect(self.__hgQueuePushPatches)
        self.actions.append(self.hgQueuePushUntilAct)
        
        self.hgQueuePopAct = E5Action(self.trUtf8('Pop Current Patch'),
                self.trUtf8('Pop Current Patch'),
                0, 0, self, 'mercurial_queues_pop_current')
        self.hgQueuePopAct.setStatusTip(self.trUtf8(
            'Pop the current patch off the stack'
        ))
        self.hgQueuePopAct.setWhatsThis(self.trUtf8(
            """<b>Pop Current Patch</b>"""
            """<p>This pops the current patch off the stack of applied patches.</p>"""
        ))
        self.hgQueuePopAct.triggered[()].connect(self.__hgQueuePopPatch)
        self.actions.append(self.hgQueuePopAct)
        
        self.hgQueuePopAllAct = E5Action(self.trUtf8('Pop All Patches'),
                self.trUtf8('Pop All Patches'),
                0, 0, self, 'mercurial_queues_pop_all')
        self.hgQueuePopAllAct.setStatusTip(self.trUtf8(
            'Pop all patches off the stack'
        ))
        self.hgQueuePopAllAct.setWhatsThis(self.trUtf8(
            """<b>Pop All Patches</b>"""
            """<p>This pops all patches off the stack of applied patches.</p>"""
        ))
        self.hgQueuePopAllAct.triggered[()].connect(self.__hgQueuePopAllPatches)
        self.actions.append(self.hgQueuePopAllAct)
        
        self.hgQueuePopUntilAct = E5Action(self.trUtf8('Pop Patches'),
                self.trUtf8('Pop Patches'),
                0, 0, self, 'mercurial_queues_pop_until')
        self.hgQueuePopUntilAct.setStatusTip(self.trUtf8(
            'Pop patches off the stack'
        ))
        self.hgQueuePopUntilAct.setWhatsThis(self.trUtf8(
            """<b>Pop Patches</b>"""
            """<p>This pops patches off the stack of applied patches until a named"""
            """ patch is at the top of the stack.</p>"""
        ))
        self.hgQueuePopUntilAct.triggered[()].connect(self.__hgQueuePopPatches)
        self.actions.append(self.hgQueuePopUntilAct)
        
        self.hgQueueGotoAct = E5Action(self.trUtf8('Go to Patch'),
                self.trUtf8('Go to Patch'),
                0, 0, self, 'mercurial_queues_goto')
        self.hgQueueGotoAct.setStatusTip(self.trUtf8(
            'Push or pop patches until named patch is at top of stack'
        ))
        self.hgQueueGotoAct.setWhatsThis(self.trUtf8(
            """<b>Go to Patch</b>"""
            """<p>This pushes or pops patches until a named patch is at the"""
            """ top of the stack.</p>"""
        ))
        self.hgQueueGotoAct.triggered[()].connect(self.__hgQueueGotoPatch)
        self.actions.append(self.hgQueueGotoAct)
    
    def __initPushPopForceActions(self):
        """
        Public method to generate the push and pop (force) action objects.
        """
        self.hgQueuePushForceAct = E5Action(self.trUtf8('Push Next Patch'),
                self.trUtf8('Push Next Patch'),
                0, 0, self, 'mercurial_queues_push_next_force')
        self.hgQueuePushForceAct.setStatusTip(self.trUtf8(
            'Push the next patch onto the stack on top of local changes'
        ))
        self.hgQueuePushForceAct.setWhatsThis(self.trUtf8(
            """<b>Push Next Patch</b>"""
            """<p>This pushes the next patch onto the stack of applied patches"""
            """ on top of local changes.</p>"""
        ))
        self.hgQueuePushForceAct.triggered[()].connect(self.__hgQueuePushPatchForced)
        self.actions.append(self.hgQueuePushForceAct)
        
        self.hgQueuePushAllForceAct = E5Action(self.trUtf8('Push All Patches'),
                self.trUtf8('Push All Patches'),
                0, 0, self, 'mercurial_queues_push_all_force')
        self.hgQueuePushAllForceAct.setStatusTip(self.trUtf8(
            'Push all patches onto the stack on top of local changes'
        ))
        self.hgQueuePushAllForceAct.setWhatsThis(self.trUtf8(
            """<b>Push All Patches</b>"""
            """<p>This pushes all patches onto the stack of applied patches"""
            """ on top of local changes.</p>"""
        ))
        self.hgQueuePushAllForceAct.triggered[()].connect(
            self.__hgQueuePushAllPatchesForced)
        self.actions.append(self.hgQueuePushAllForceAct)
        
        self.hgQueuePushUntilForceAct = E5Action(self.trUtf8('Push Patches'),
                self.trUtf8('Push Patches'),
                0, 0, self, 'mercurial_queues_push_until_force')
        self.hgQueuePushUntilForceAct.setStatusTip(self.trUtf8(
            'Push patches onto the stack on top of local changes'
        ))
        self.hgQueuePushUntilForceAct.setWhatsThis(self.trUtf8(
            """<b>Push Patches</b>"""
            """<p>This pushes patches onto the stack  of applied patches until"""
            """ a named patch is at the top of the stack on top of local changes.</p>"""
        ))
        self.hgQueuePushUntilForceAct.triggered[()].connect(
            self.__hgQueuePushPatchesForced)
        self.actions.append(self.hgQueuePushUntilForceAct)
        
        self.hgQueuePopForceAct = E5Action(self.trUtf8('Pop Current Patch'),
                self.trUtf8('Pop Current Patch'),
                0, 0, self, 'mercurial_queues_pop_current_force')
        self.hgQueuePopForceAct.setStatusTip(self.trUtf8(
            'Pop the current patch off the stack forgetting local changes'
        ))
        self.hgQueuePopForceAct.setWhatsThis(self.trUtf8(
            """<b>Pop Current Patch</b>"""
            """<p>This pops the current patch off the stack of applied patches"""
            """ forgetting local changes.</p>"""
        ))
        self.hgQueuePopForceAct.triggered[()].connect(self.__hgQueuePopPatchForced)
        self.actions.append(self.hgQueuePopForceAct)
        
        self.hgQueuePopAllForceAct = E5Action(self.trUtf8('Pop All Patches'),
                self.trUtf8('Pop All Patches'),
                0, 0, self, 'mercurial_queues_pop_all_force')
        self.hgQueuePopAllForceAct.setStatusTip(self.trUtf8(
            'Pop all patches off the stack forgetting local changes'
        ))
        self.hgQueuePopAllForceAct.setWhatsThis(self.trUtf8(
            """<b>Pop All Patches</b>"""
            """<p>This pops all patches off the stack of applied patches"""
            """  forgetting local changes.</p>"""
        ))
        self.hgQueuePopAllForceAct.triggered[()].connect(
            self.__hgQueuePopAllPatchesForced)
        self.actions.append(self.hgQueuePopAllForceAct)
        
        self.hgQueuePopUntilForceAct = E5Action(self.trUtf8('Pop Patches'),
                self.trUtf8('Pop Patches'),
                0, 0, self, 'mercurial_queues_pop_until_force')
        self.hgQueuePopUntilForceAct.setStatusTip(self.trUtf8(
            'Pop patches off the stack forgetting local changes'
        ))
        self.hgQueuePopUntilForceAct.setWhatsThis(self.trUtf8(
            """<b>Pop Patches</b>"""
            """<p>This pops patches off the stack of applied patches until a named"""
            """ patch is at the top of the stack forgetting local changes.</p>"""
        ))
        self.hgQueuePopUntilForceAct.triggered[()].connect(self.__hgQueuePopPatchesForced)
        self.actions.append(self.hgQueuePopUntilForceAct)
        
        self.hgQueueGotoForceAct = E5Action(self.trUtf8('Go to Patch'),
                self.trUtf8('Go to Patch'),
                0, 0, self, 'mercurial_queues_goto_force')
        self.hgQueueGotoForceAct.setStatusTip(self.trUtf8(
            'Push or pop patches until named patch is at top of stack overwriting'
            ' any local changes'
        ))
        self.hgQueueGotoForceAct.setWhatsThis(self.trUtf8(
            """<b>Go to Patch</b>"""
            """<p>This pushes or pops patches until a named patch is at the"""
            """ top of the stack overwriting any local changes.</p>"""
        ))
        self.hgQueueGotoForceAct.triggered[()].connect(self.__hgQueueGotoPatchForced)
        self.actions.append(self.hgQueueGotoForceAct)
    
    
    def __initGuardsActions(self):
        """
        Public method to generate the guards action objects.
        """
        self.hgQueueDefineGuardsAct = E5Action(self.trUtf8('Define Guards'),
                self.trUtf8('Define Guards...'),
                0, 0, self, 'mercurial_queues_guards_define')
        self.hgQueueDefineGuardsAct.setStatusTip(self.trUtf8(
            'Define guards for the current or a named patch'
        ))
        self.hgQueueDefineGuardsAct.setWhatsThis(self.trUtf8(
            """<b>Define Guards</b>"""
            """<p>This opens a dialog to define guards for the current"""
            """ or a named patch.</p>"""
        ))
        self.hgQueueDefineGuardsAct.triggered[()].connect(self.__hgQueueGuardsDefine)
        self.actions.append(self.hgQueueDefineGuardsAct)
        
        self.hgQueueDropAllGuardsAct = E5Action(self.trUtf8('Drop All Guards'),
                self.trUtf8('Drop All Guards...'),
                0, 0, self, 'mercurial_queues_guards_drop_all')
        self.hgQueueDropAllGuardsAct.setStatusTip(self.trUtf8(
            'Drop all guards of the current or a named patch'
        ))
        self.hgQueueDropAllGuardsAct.setWhatsThis(self.trUtf8(
            """<b>Drop All Guards</b>"""
            """<p>This drops all guards of the current or a named patch.</p>"""
        ))
        self.hgQueueDropAllGuardsAct.triggered[()].connect(self.__hgQueueGuardsDropAll)
        self.actions.append(self.hgQueueDropAllGuardsAct)
        
        self.hgQueueListGuardsAct = E5Action(self.trUtf8('List Guards'),
                self.trUtf8('List Guards...'),
                0, 0, self, 'mercurial_queues_guards_list')
        self.hgQueueListGuardsAct.setStatusTip(self.trUtf8(
            'List guards of the current or a named patch'
        ))
        self.hgQueueListGuardsAct.setWhatsThis(self.trUtf8(
            """<b>List Guards</b>"""
            """<p>This lists the guards of the current or a named patch.</p>"""
        ))
        self.hgQueueListGuardsAct.triggered[()].connect(self.__hgQueueGuardsList)
        self.actions.append(self.hgQueueListGuardsAct)
        
        self.hgQueueListAllGuardsAct = E5Action(self.trUtf8('List All Guards'),
                self.trUtf8('List All Guards...'),
                0, 0, self, 'mercurial_queues_guards_list_all')
        self.hgQueueListAllGuardsAct.setStatusTip(self.trUtf8(
            'List all guards of all patches'
        ))
        self.hgQueueListAllGuardsAct.setWhatsThis(self.trUtf8(
            """<b>List All Guards</b>"""
            """<p>This lists all guards of all patches.</p>"""
        ))
        self.hgQueueListAllGuardsAct.triggered[()].connect(self.__hgQueueGuardsListAll)
        self.actions.append(self.hgQueueListAllGuardsAct)
        
        self.hgQueueActivateGuardsAct = E5Action(self.trUtf8('Set Active Guards'),
                self.trUtf8('Set Active Guards...'),
                0, 0, self, 'mercurial_queues_guards_set_active')
        self.hgQueueActivateGuardsAct.setStatusTip(self.trUtf8(
            'Set the list of active guards'
        ))
        self.hgQueueActivateGuardsAct.setWhatsThis(self.trUtf8(
            """<b>Set Active Guards</b>"""
            """<p>This opens a dialog to set the active guards.</p>"""
        ))
        self.hgQueueActivateGuardsAct.triggered[()].connect(self.__hgQueueGuardsSetActive)
        self.actions.append(self.hgQueueActivateGuardsAct)
        
        self.hgQueueDeactivateGuardsAct = E5Action(self.trUtf8('Deactivate Guards'),
                self.trUtf8('Deactivate Guards...'),
                0, 0, self, 'mercurial_queues_guards_deactivate')
        self.hgQueueDeactivateGuardsAct.setStatusTip(self.trUtf8(
            'Deactivate all active guards'
        ))
        self.hgQueueDeactivateGuardsAct.setWhatsThis(self.trUtf8(
            """<b>Deactivate Guards</b>"""
            """<p>This deactivates all active guards.</p>"""
        ))
        self.hgQueueDeactivateGuardsAct.triggered[()].connect(
            self.__hgQueueGuardsDeactivate)
        self.actions.append(self.hgQueueDeactivateGuardsAct)
        
        self.hgQueueIdentifyActiveGuardsAct = E5Action(
                self.trUtf8('Identify Active Guards'),
                self.trUtf8('Identify Active Guards...'),
                0, 0, self, 'mercurial_queues_guards_identify_active')
        self.hgQueueIdentifyActiveGuardsAct.setStatusTip(self.trUtf8(
            'Show a list of active guards'
        ))
        self.hgQueueIdentifyActiveGuardsAct.setWhatsThis(self.trUtf8(
            """<b>Identify Active Guards</b>"""
            """<p>This opens a dialog showing a list of active guards.</p>"""
        ))
        self.hgQueueIdentifyActiveGuardsAct.triggered[()].connect(
            self.__hgQueueGuardsIdentifyActive)
        self.actions.append(self.hgQueueIdentifyActiveGuardsAct)
    
    def __initQueuesMgmtActions(self):
        """
        Public method to generate the queues management action objects.
        """
        self.hgQueueCreateQueueAct = E5Action(self.trUtf8('Create Queue'),
                self.trUtf8('Create Queue'),
                0, 0, self, 'mercurial_queues_create_queue')
        self.hgQueueCreateQueueAct.setStatusTip(self.trUtf8(
            'Create a new patch queue'
        ))
        self.hgQueueCreateQueueAct.setWhatsThis(self.trUtf8(
            """<b>Create Queue</b>"""
            """<p>This creates a new patch queue.</p>"""
        ))
        self.hgQueueCreateQueueAct.triggered[()].connect(
            self.__hgQueueCreateQueue)
        self.actions.append(self.hgQueueCreateQueueAct)
        
        self.hgQueueRenameQueueAct = E5Action(self.trUtf8('Rename Queue'),
                self.trUtf8('Rename Queue'),
                0, 0, self, 'mercurial_queues_rename_queue')
        self.hgQueueRenameQueueAct.setStatusTip(self.trUtf8(
            'Rename the active patch queue'
        ))
        self.hgQueueRenameQueueAct.setWhatsThis(self.trUtf8(
            """<b>Rename Queue</b>"""
            """<p>This renames the active patch queue.</p>"""
        ))
        self.hgQueueRenameQueueAct.triggered[()].connect(
            self.__hgQueueRenameQueue)
        self.actions.append(self.hgQueueRenameQueueAct)
        
        self.hgQueueDeleteQueueAct = E5Action(self.trUtf8('Delete Queue'),
                self.trUtf8('Delete Queue'),
                0, 0, self, 'mercurial_queues_delete_queue')
        self.hgQueueDeleteQueueAct.setStatusTip(self.trUtf8(
            'Delete the reference to a patch queue'
        ))
        self.hgQueueDeleteQueueAct.setWhatsThis(self.trUtf8(
            """<b>Delete Queue</b>"""
            """<p>This deletes the reference to a patch queue.</p>"""
        ))
        self.hgQueueDeleteQueueAct.triggered[()].connect(
            self.__hgQueueDeleteQueue)
        self.actions.append(self.hgQueueDeleteQueueAct)
        
        self.hgQueuePurgeQueueAct = E5Action(self.trUtf8('Purge Queue'),
                self.trUtf8('Purge Queue'),
                0, 0, self, 'mercurial_queues_purge_queue')
        self.hgQueuePurgeQueueAct.setStatusTip(self.trUtf8(
            'Delete the reference to a patch queue and remove the patch directory'
        ))
        self.hgQueuePurgeQueueAct.setWhatsThis(self.trUtf8(
            """<b>Purge Queue</b>"""
            """<p>This deletes the reference to a patch queue and removes"""
            """ the patch directory.</p>"""
        ))
        self.hgQueuePurgeQueueAct.triggered[()].connect(
            self.__hgQueuePurgeQueue)
        self.actions.append(self.hgQueuePurgeQueueAct)
        
        self.hgQueueActivateQueueAct = E5Action(self.trUtf8('Activate Queue'),
                self.trUtf8('Activate Queue'),
                0, 0, self, 'mercurial_queues_activate_queue')
        self.hgQueueActivateQueueAct.setStatusTip(self.trUtf8(
            'Set the active queue'
        ))
        self.hgQueueActivateQueueAct.setWhatsThis(self.trUtf8(
            """<b>Activate Queue</b>"""
            """<p>This sets the active queue.</p>"""
        ))
        self.hgQueueActivateQueueAct.triggered[()].connect(
            self.__hgQueueActivateQueue)
        self.actions.append(self.hgQueueActivateQueueAct)
        
        self.hgQueueListQueuesAct = E5Action(self.trUtf8('List Queues'),
                self.trUtf8('List Queues...'),
                0, 0, self, 'mercurial_queues_list_queues')
        self.hgQueueListQueuesAct.setStatusTip(self.trUtf8(
            'List the available queues'
        ))
        self.hgQueueListQueuesAct.setWhatsThis(self.trUtf8(
            """<b>List Queues</b>"""
            """<p>This opens a dialog showing all available queues.</p>"""
        ))
        self.hgQueueListQueuesAct.triggered[()].connect(
            self.__hgQueueListQueues)
        self.actions.append(self.hgQueueListQueuesAct)
    
    def initMenu(self, mainMenu):
        """
        Public method to generate the extension menu.
        
        @param mainMenu reference to the main menu (QMenu)
        @return populated menu (QMenu)
        """
        menu = QMenu(self.menuTitle(), mainMenu)
        menu.setTearOffEnabled(True)
        
        pushPopMenu = QMenu(self.trUtf8("Push/Pop"), menu)
        pushPopMenu.setTearOffEnabled(True)
        pushPopMenu.addAction(self.hgQueuePushAct)
        pushPopMenu.addAction(self.hgQueuePushUntilAct)
        pushPopMenu.addAction(self.hgQueuePushAllAct)
        pushPopMenu.addSeparator()
        pushPopMenu.addAction(self.hgQueuePopAct)
        pushPopMenu.addAction(self.hgQueuePopUntilAct)
        pushPopMenu.addAction(self.hgQueuePopAllAct)
        pushPopMenu.addSeparator()
        pushPopMenu.addAction(self.hgQueueGotoAct)
        
        pushPopForceMenu = QMenu(self.trUtf8("Push/Pop (force)"), menu)
        pushPopForceMenu.setTearOffEnabled(True)
        pushPopForceMenu.addAction(self.hgQueuePushForceAct)
        pushPopForceMenu.addAction(self.hgQueuePushUntilForceAct)
        pushPopForceMenu.addAction(self.hgQueuePushAllForceAct)
        pushPopForceMenu.addSeparator()
        pushPopForceMenu.addAction(self.hgQueuePopForceAct)
        pushPopForceMenu.addAction(self.hgQueuePopUntilForceAct)
        pushPopForceMenu.addAction(self.hgQueuePopAllForceAct)
        pushPopForceMenu.addSeparator()
        pushPopForceMenu.addAction(self.hgQueueGotoForceAct)
        
        guardsMenu = QMenu(self.trUtf8("Guards"), menu)
        guardsMenu.setTearOffEnabled(True)
        guardsMenu.addAction(self.hgQueueDefineGuardsAct)
        guardsMenu.addAction(self.hgQueueDropAllGuardsAct)
        guardsMenu.addSeparator()
        guardsMenu.addAction(self.hgQueueListGuardsAct)
        guardsMenu.addAction(self.hgQueueListAllGuardsAct)
        guardsMenu.addSeparator()
        guardsMenu.addAction(self.hgQueueActivateGuardsAct)
        guardsMenu.addAction(self.hgQueueDeactivateGuardsAct)
        guardsMenu.addSeparator()
        guardsMenu.addAction(self.hgQueueIdentifyActiveGuardsAct)
        
        queuesMenu = QMenu(self.trUtf8("Queue Management"), menu)
        queuesMenu.setTearOffEnabled(True)
        queuesMenu.addAction(self.hgQueueCreateQueueAct)
        queuesMenu.addAction(self.hgQueueRenameQueueAct)
        queuesMenu.addAction(self.hgQueueDeleteQueueAct)
        queuesMenu.addAction(self.hgQueuePurgeQueueAct)
        queuesMenu.addSeparator()
        queuesMenu.addAction(self.hgQueueActivateQueueAct)
        queuesMenu.addSeparator()
        queuesMenu.addAction(self.hgQueueListQueuesAct)
        
        menu.addAction(self.hgQueueNewAct)
        menu.addAction(self.hgQueueRefreshAct)
        menu.addAction(self.hgQueueRefreshMessageAct)
        menu.addAction(self.hgQueueFinishAct)
        menu.addSeparator()
        menu.addAction(self.hgQueueDiffAct)
        menu.addAction(self.hgQueueHeaderAct)
        menu.addSeparator()
        menu.addAction(self.hgQueueListAct)
        menu.addSeparator()
        menu.addMenu(pushPopMenu)
        menu.addMenu(pushPopForceMenu)
        menu.addSeparator()
        menu.addAction(self.hgQueueRenameAct)
        menu.addAction(self.hgQueueDeleteAct)
        menu.addSeparator()
        menu.addAction(self.hgQueueFoldAct)
        menu.addSeparator()
        menu.addMenu(guardsMenu)
        menu.addSeparator()
        menu.addMenu(queuesMenu)
        
        return menu
    
    def menuTitle(self):
        """
        Public method to get the menu title.
        
        @return title of the menu (string)
        """
        return self.trUtf8("Queues")
    
    def __hgQueueNewPatch(self):
        """
        Private slot used to create a new named patch.
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueueNewPatch(self.project.getProjectPath())
    
    def __hgQueueRefreshPatch(self):
        """
        Private slot used to refresh the current patch.
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueueRefreshPatch(self.project.getProjectPath())
    
    def __hgQueueRefreshPatchMessage(self):
        """
        Private slot used to refresh the current patch and it's commit message.
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueueRefreshPatch(self.project.getProjectPath(), editMessage=True)
    
    def __hgQueueShowPatch(self):
        """
        Private slot used to show the contents of the current patch.
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueueShowPatch(self.project.getProjectPath())
    
    def __hgQueueShowHeader(self):
        """
        Private slot used to show the commit message of the current patch.
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueueShowHeader(self.project.getProjectPath())
    
    
    def __hgQueuePushPopPatches(self, name, operation, all=False, named=False,
                                force=False):
        """
        Private method to push patches onto the stack or pop patches off the stack.
        
        @param name file/directory name (string)
        @param operation operation type to be performed (Queues.POP,
            Queues.PUSH, Queues.GOTO)
        @keyparam all flag indicating to push/pop all (boolean)
        @keyparam named flag indicating to push/pop until a named patch
            is at the top of the stack (boolean)
        @keyparam force flag indicating a forceful pop (boolean)
        @return flag indicating that the project should be reread (boolean)
        """
        shouldReopen = self.vcs.getExtensionObject("mq")\
            .hgQueuePushPopPatches(name, operation=operation, all=all, named=named,
                force=force)
        if shouldReopen:
            res = E5MessageBox.yesNo(None,
                self.trUtf8("Changing Applied Patches"),
                self.trUtf8("""The project should be reread. Do this now?"""),
                yesDefault=True)
            if res:
                self.project.reopenProject()
    
    def __hgQueuePushPatch(self):
        """
        Private slot used to push the next patch onto the stack.
        """
        self.__hgQueuePushPopPatches(self.project.getProjectPath(),
                operation=Queues.PUSH, all=False, named=False)
    
    def __hgQueuePushPatchForced(self):
        """
        Private slot used to push the next patch onto the stack on top
        of local changes.
        """
        self.__hgQueuePushPopPatches(self.project.getProjectPath(),
                operation=Queues.PUSH, all=False, named=False, force=True)
    
    def __hgQueuePushAllPatches(self):
        """
        Private slot used to push all patches onto the stack.
        """
        self.__hgQueuePushPopPatches(self.project.getProjectPath(),
                operation=Queues.PUSH, all=True, named=False)
    
    def __hgQueuePushAllPatchesForced(self):
        """
        Private slot used to push all patches onto the stack on top
        of local changes.
        """
        self.__hgQueuePushPopPatches(self.project.getProjectPath(),
                operation=Queues.PUSH, all=True, named=False, force=True)
    
    def __hgQueuePushPatches(self):
        """
        Private slot used to push patches onto the stack until a named
        one is at the top.
        """
        self.__hgQueuePushPopPatches(self.project.getProjectPath(),
                operation=Queues.PUSH, all=False, named=True)
    
    def __hgQueuePushPatchesForced(self):
        """
        Private slot used to push patches onto the stack until a named
        one is at the top on top of local changes.
        """
        self.__hgQueuePushPopPatches(self.project.getProjectPath(),
                operation=Queues.PUSH, all=False, named=True, force=True)
    
    def __hgQueuePopPatch(self):
        """
        Private slot used to pop the current patch off the stack.
        """
        self.__hgQueuePushPopPatches(self.project.getProjectPath(),
                operation=Queues.POP, all=False, named=False)
    
    def __hgQueuePopPatchForced(self):
        """
        Private slot used to pop the current patch off the stack forgetting
        any local changes to patched files.
        """
        self.__hgQueuePushPopPatches(self.project.getProjectPath(),
                operation=Queues.POP, all=False, named=False, force=True)
    
    def __hgQueuePopAllPatches(self):
        """
        Private slot used to pop all patches off the stack.
        """
        self.__hgQueuePushPopPatches(self.project.getProjectPath(),
                operation=Queues.POP, all=True, named=False)
    
    def __hgQueuePopAllPatchesForced(self):
        """
        Private slot used to pop all patches off the stack forgetting
        any local changes to patched files.
        """
        self.__hgQueuePushPopPatches(self.project.getProjectPath(),
                operation=Queues.POP, all=True, named=False, force=True)
    
    def __hgQueuePopPatches(self):
        """
        Private slot used to pop patches off the stack until a named
        one is at the top.
        """
        self.__hgQueuePushPopPatches(self.project.getProjectPath(),
                operation=Queues.POP, all=False, named=True)
    
    def __hgQueuePopPatchesForced(self):
        """
        Private slot used to pop patches off the stack until a named
        one is at the top forgetting any local changes to patched files.
        """
        self.__hgQueuePushPopPatches(self.project.getProjectPath(),
                operation=Queues.POP, all=False, named=True, force=True)
    
    def __hgQueueGotoPatch(self):
        """
        Private slot used to push or pop patches until the a named one
        is at the top of the stack.
        """
        self.__hgQueuePushPopPatches(self.project.getProjectPath(),
                operation=Queues.GOTO, all=False, named=True)
    
    def __hgQueueGotoPatchForced(self):
        """
        Private slot used to push or pop patches until the a named one
        is at the top of the stack overwriting local changes.
        """
        self.__hgQueuePushPopPatches(self.project.getProjectPath(),
                operation=Queues.GOTO, all=False, named=True, force=True)
    
    def __hgQueueListPatches(self):
        """
        Private slot used to show a list of applied and unapplied patches.
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueueListPatches(self.project.getProjectPath())
    
    def __hgQueueFinishAppliedPatches(self):
        """
        Private slot used to finish all applied patches.
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueueFinishAppliedPatches(self.project.getProjectPath())
    
    def __hgQueueRenamePatch(self):
        """
        Private slot used to rename a patch.
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueueRenamePatch(self.project.getProjectPath())
    
    def __hgQueueDeletePatch(self):
        """
        Private slot used to delete a patch.
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueueDeletePatch(self.project.getProjectPath())
    
    def __hgQueueFoldUnappliedPatches(self):
        """
        Private slot used to fold patches into the current patch.
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueueFoldUnappliedPatches(self.project.getProjectPath())
    
    def __hgQueueGuardsDefine(self):
        """
        Private slot used to define guards for the current or a named patch.
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueueGuardsDefine(self.project.getProjectPath())
    
    def __hgQueueGuardsDropAll(self):
        """
        Private slot used to drop all guards of the current or a named patch.
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueueGuardsDropAll(self.project.getProjectPath())
    
    def __hgQueueGuardsList(self):
        """
        Private slot used to list the guards for the current or a named patch.
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueueGuardsList(self.project.getProjectPath())
    
    def __hgQueueGuardsListAll(self):
        """
        Private slot used to list all guards of all patches.
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueueGuardsListAll(self.project.getProjectPath())
    
    def __hgQueueGuardsSetActive(self):
        """
        Private slot used to set the active guards.
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueueGuardsSetActive(self.project.getProjectPath())
    
    def __hgQueueGuardsDeactivate(self):
        """
        Private slot used to deactivate all active guards.
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueueGuardsDeactivate(self.project.getProjectPath())
    
    def __hgQueueGuardsIdentifyActive(self):
        """
        Private slot used to list all active guards.
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueueGuardsIdentifyActive(self.project.getProjectPath())
    
    def __hgQueueCreateQueue(self):
        """
        Private slot used to create a new queue.
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueueCreateRenameQueue(self.project.getProjectPath(), True)
    
    def __hgQueueRenameQueue(self):
        """
        Private slot used to rename the active queue.
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueueCreateRenameQueue(self.project.getProjectPath(), False)
    
    def __hgQueueDeleteQueue(self):
        """
        Private slot used to delete the reference to a queue.
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueueDeletePurgeActivateQueue(self.project.getProjectPath(),
                                             Queues.QUEUE_DELETE)
    
    def __hgQueuePurgeQueue(self):
        """
        Private slot used to delete the reference to a queue and remove
        the patch directory.
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueueDeletePurgeActivateQueue(self.project.getProjectPath(),
                                             Queues.QUEUE_PURGE)
    
    def __hgQueueActivateQueue(self):
        """
        Private slot used to set the active queue.
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueueDeletePurgeActivateQueue(self.project.getProjectPath(),
                                             Queues.QUEUE_ACTIVATE)
    
    def __hgQueueListQueues(self):
        """
        Private slot used to list available queues.
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueueListQueues(self.project.getProjectPath())
