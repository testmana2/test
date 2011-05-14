# -*- coding: utf-8 -*-

# Copyright (c) 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the queues extension project helper.
"""

from PyQt4.QtCore import QObject
from PyQt4.QtGui import QMenu

from E5Gui.E5Action import E5Action


class QueuesProjectHelper(QObject):
    """
    Class implementing the queues extension project helper.
    """
    def __init__(self):
        """
        Constructor
        """
        QObject.__init__(self)
        
        self.actions = []
        
        self.initActions()
    
    def setObjects(self, vcsObject, projectObject):
        """
        Public method to set references to the vcs and project objects.
        
        @param vcsObject reference to the vcs object
        @param projectObject reference to the project object
        """
        self.vcs = vcsObject
        self.project = projectObject
    
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
        
        self.hgQueueListAct = E5Action(self.trUtf8('List Patches'),
                self.trUtf8('List Patches...'),
                0, 0, self, 'mercurial_queues_list')
        self.hgQueueListAct.setStatusTip(self.trUtf8(
            'List applied and unapplied patches'
        ))
        self.hgQueueListAct.setWhatsThis(self.trUtf8(
            """<b>List Patches</b>"""
            """<p>This list all applied and unapplied patches.</p>"""
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
            """<p>This finishes the applied patches) by moving them out of"""
            """ mq control into regular repository history.</p>"""
        ))
        self.hgQueueFinishAct.triggered[()].connect(self.__hgQueueFinishAppliedPatches)
        self.actions.append(self.hgQueueFinishAct)
        
        self.__initPushPopActions()
        self.__initPushPopForceActions()
    
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
            """<p>This pushes patches onto the stack  of applied patches until"""
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
    
    def initMenu(self, mainMenu):
        """
        Public method to generate the VCS menu.
        
        @param mainMenu reference to the main menu (QMenu)
        @return populated menu (QMenu)
        """
        menu = QMenu(self.trUtf8("Queues"), mainMenu)
        
        pushPopMenu = QMenu(self.trUtf8("Push/Pop"), menu)
        pushPopMenu.addAction(self.hgQueuePushAct)
        pushPopMenu.addAction(self.hgQueuePushUntilAct)
        pushPopMenu.addAction(self.hgQueuePushAllAct)
        pushPopMenu.addAction(self.hgQueuePopAct)
        pushPopMenu.addAction(self.hgQueuePopUntilAct)
        pushPopMenu.addAction(self.hgQueuePopAllAct)
        
        pushPopForceMenu = QMenu(self.trUtf8("Push/Pop (force)"), menu)
        pushPopForceMenu.addAction(self.hgQueuePushForceAct)
        pushPopForceMenu.addAction(self.hgQueuePushUntilForceAct)
        pushPopForceMenu.addAction(self.hgQueuePushAllForceAct)
        pushPopForceMenu.addAction(self.hgQueuePopForceAct)
        pushPopForceMenu.addAction(self.hgQueuePopUntilForceAct)
        pushPopForceMenu.addAction(self.hgQueuePopAllForceAct)
        
        menu.addAction(self.hgQueueNewAct)
        menu.addAction(self.hgQueueRefreshAct)
        menu.addAction(self.hgQueueFinishAct)
        menu.addSeparator()
        menu.addAction(self.hgQueueDiffAct)
        menu.addSeparator()
        menu.addAction(self.hgQueueListAct)
        menu.addSeparator()
        menu.addMenu(pushPopMenu)
        menu.addMenu(pushPopForceMenu)
        
        return menu
    
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
    
    def __hgQueueShowPatch(self):
        """
        Private slot used to show the contents of the current patch. 
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueueShowPatch(self.project.getProjectPath())
    
    def __hgQueuePushPatch(self):
        """
        Private slot used to push the next patch onto the stack. 
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueuePushPopPatches(self.project.getProjectPath(), 
                pop=False, all=False, named=False)
    
    def __hgQueuePushPatchForced(self):
        """
        Private slot used to push the next patch onto the stack on top
        of local changes. 
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueuePushPopPatches(self.project.getProjectPath(), 
                pop=False, all=False, named=False, force=True)
    
    def __hgQueuePushAllPatches(self):
        """
        Private slot used to push all patches onto the stack. 
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueuePushPopPatches(self.project.getProjectPath(), 
                pop=False, all=True, named=False)
    
    def __hgQueuePushAllPatchesForced(self):
        """
        Private slot used to push all patches onto the stack on top
        of local changes. 
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueuePushPopPatches(self.project.getProjectPath(), 
                pop=False, all=True, named=False, force=True)
    
    def __hgQueuePushPatches(self):
        """
        Private slot used to push patches onto the stack until a named
        one is at the top. 
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueuePushPopPatches(self.project.getProjectPath(), 
                pop=False, all=False, named=True)
    
    def __hgQueuePushPatchesForced(self):
        """
        Private slot used to push patches onto the stack until a named
        one is at the top on top of local changes. 
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueuePushPopPatches(self.project.getProjectPath(), 
                pop=False, all=False, named=True, force=True)
    
    def __hgQueuePopPatch(self):
        """
        Private slot used to pop the current patch off the stack. 
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueuePushPopPatches(self.project.getProjectPath(), 
                pop=True, all=False, named=False)
    
    def __hgQueuePopPatchForced(self):
        """
        Private slot used to pop the current patch off the stack forgetting
        any local changes to patched files. 
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueuePushPopPatches(self.project.getProjectPath(), 
                pop=True, all=False, named=False)
    
    def __hgQueuePopAllPatches(self):
        """
        Private slot used to pop all patches off the stack. 
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueuePushPopPatches(self.project.getProjectPath(), 
                pop=True, all=True, named=False)
    
    def __hgQueuePopAllPatchesForced(self):
        """
        Private slot used to pop all patches off the stack forgetting
        any local changes to patched files. 
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueuePushPopPatches(self.project.getProjectPath(), 
                pop=True, all=True, named=False, force=True)
    
    def __hgQueuePopPatches(self):
        """
        Private slot used to pop patches off the stack until a named
        one is at the top. 
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueuePushPopPatches(self.project.getProjectPath(), 
                pop=True, all=False, named=True)
    
    def __hgQueuePopPatchesForced(self):
        """
        Private slot used to pop patches off the stack until a named
        one is at the top forgetting any local changes to patched files. 
        """
        self.vcs.getExtensionObject("mq")\
            .hgQueuePushPopPatches(self.project.getProjectPath(), 
                pop=True, all=False, named=True)
    
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
