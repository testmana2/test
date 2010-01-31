# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Ericdoc plugin.
"""

import os

from PyQt4.QtCore import QObject, SIGNAL
from PyQt4.QtGui import QDialog, QApplication

from E5Gui.E5Application import e5App

from E5Gui.E5Action import E5Action

from DocumentationPlugins.Ericdoc.EricdocConfigDialog import EricdocConfigDialog
from DocumentationPlugins.Ericdoc.EricdocExecDialog import EricdocExecDialog

import Utilities

# Start-Of-Header
name = "Ericdoc Plugin"
author = "Detlev Offenbach <detlev@die-offenbachs.de>"
autoactivate = True
deactivateable = True
version = "5.0.0"
className = "EricdocPlugin"
packageName = "__core__"
shortDescription = "Show the Ericdoc dialogs."
longDescription = """This plugin implements the Ericdoc dialogs.""" \
 """ Ericdoc is used to generate a source code documentation""" \
 """ for Python and Ruby projects."""
pyqtApi = 2
# End-Of-Header

error = ""

def exeDisplayData():
    """
    Public method to support the display of some executable info.
    
    @return dictionary containing the data to query the presence of
        the executable
    """
    exe = 'eric5-doc'
    if Utilities.isWindowsPlatform():
        exe += '.bat'
    
    data = {
        "programEntry"      : True, 
        "header"            : QApplication.translate("EricdocPlugin",
                                "Eric5 Documentation Generator"), 
        "exe"               : exe, 
        "versionCommand"    : '--version', 
        "versionStartsWith" : 'eric5-', 
        "versionPosition"   : -2, 
        "version"           : "", 
        "versionCleanup"    : None, 
    }
    
    return data

class EricdocPlugin(QObject):
    """
    Class implementing the Ericdoc plugin.
    """
    def __init__(self, ui):
        """
        Constructor
        
        @param ui reference to the user interface object (UI.UserInterface)
        """
        QObject.__init__(self, ui)
        self.__ui = ui
        self.__initialize()
        
    def __initialize(self):
        """
        Private slot to (re)initialize the plugin.
        """
        self.__projectAct = None

    def activate(self):
        """
        Public method to activate this plugin.
        
        @return tuple of None and activation status (boolean)
        """
        menu = e5App().getObject("Project").getMenu("Apidoc")
        if menu:
            self.__projectAct = \
                E5Action(self.trUtf8('Generate documentation (eric5-doc)'),
                    self.trUtf8('Generate &documentation (eric5-doc)'), 0, 0,
                    self, 'doc_eric5_doc')
            self.__projectAct.setStatusTip(\
                self.trUtf8('Generate API documentation using eric5-doc'))
            self.__projectAct.setWhatsThis(self.trUtf8(
                """<b>Generate documentation</b>"""
                """<p>Generate API documentation using eric5-doc.</p>"""
            ))
            self.connect(self.__projectAct, SIGNAL('triggered()'), self.__doEricdoc)
            e5App().getObject("Project").addE5Actions([self.__projectAct])
            menu.addAction(self.__projectAct)
        
        self.connect(e5App().getObject("Project"), SIGNAL("showMenu"), 
                     self.__projectShowMenu)
        
        return None, True

    def deactivate(self):
        """
        Public method to deactivate this plugin.
        """
        self.disconnect(e5App().getObject("Project"), SIGNAL("showMenu"), 
                        self.__projectShowMenu)
        
        menu = e5App().getObject("Project").getMenu("Apidoc")
        if menu:
            menu.removeAction(self.__projectAct)
            e5App().getObject("Project").removeE5Actions([self.__projectAct])
        self.__initialize()
    
    def __projectShowMenu(self, menuName, menu):
        """
        Private slot called, when the the project menu or a submenu is 
        about to be shown.
        
        @param menuName name of the menu to be shown (string)
        @param menu reference to the menu (QMenu)
        """
        if menuName == "Apidoc":
            if self.__projectAct is not None:
                self.__projectAct.setEnabled(\
                    e5App().getObject("Project").getProjectLanguage() in \
                        ["Python", "Python3", "Ruby"])
    
    def __doEricdoc(self):
        """
        Private slot to perform the eric5-doc api documentation generation.
        """
        project = e5App().getObject("Project")
        parms = project.getData('DOCUMENTATIONPARMS', "ERIC4DOC")
        dlg = EricdocConfigDialog(project.getProjectPath(), parms)
        if dlg.exec_() == QDialog.Accepted:
            args, parms = dlg.generateParameters()
            project.setData('DOCUMENTATIONPARMS', "ERIC4DOC", parms)
            
            # now do the call
            dia = EricdocExecDialog("Ericdoc")
            res = dia.start(args, project.ppath)
            if res:
                dia.exec_()
            
            outdir = parms['outputDirectory']
            if outdir == '':
                outdir = 'doc'      # that is eric5-docs default output dir
                
            # add it to the project data, if it isn't in already
            outdir = outdir.replace(project.ppath+os.sep, '')
            if outdir not in project.pdata['OTHERS']:
                project.pdata['OTHERS'].append(outdir)
                project.setDirty(True)
                project.othersAdded(outdir)
            
            if parms['qtHelpEnabled']:
                outdir = parms['qtHelpOutputDirectory']
                if outdir == '':
                    outdir = 'help'      # that is eric5-docs default QtHelp output dir
                    
                # add it to the project data, if it isn't in already
                outdir = outdir.replace(project.ppath+os.sep, '')
                if outdir not in project.pdata['OTHERS']:
                    project.pdata['OTHERS'].append(outdir)
                    project.setDirty(True)
                    project.othersAdded(outdir)
