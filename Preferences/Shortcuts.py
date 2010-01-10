# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing functions dealing with keyboard shortcuts.
"""

import io

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from E4Gui.E4Application import e4App

from Preferences import Prefs, syncPreferences

from E4XML.XMLUtilities import make_parser
from E4XML.XMLErrorHandler import XMLErrorHandler, XMLFatalParseError
from E4XML.ShortcutsHandler import ShortcutsHandler
from E4XML.ShortcutsWriter import ShortcutsWriter
from E4XML.XMLEntityResolver import XMLEntityResolver

def __readShortcut(act, category, prefClass):
    """
    Private function to read a single keyboard shortcut from the settings.
    
    @param act reference to the action object (E4Action)
    @param category category the action belongs to (string)
    @param prefClass preferences class used as the storage area
    """
    if act.objectName():
        accel = prefClass.settings.value(
            "Shortcuts/{0}/{1}/Accel".format(category, act.objectName()))
        if accel is not None:
            act.setShortcut(QKeySequence(accel))
        accel = prefClass.settings.value(
            "Shortcuts/{0}/{1}/AltAccel".format(category, act.objectName()))
        if accel is not None:
            act.setAlternateShortcut(QKeySequence(accel))

def readShortcuts(prefClass = Prefs, helpViewer = None, pluginName = None):
    """
    Module function to read the keyboard shortcuts for the defined QActions.
    
    @keyparam prefClass preferences class used as the storage area
    @keyparam helpViewer reference to the help window object
    @keyparam pluginName name of the plugin for which to load shortcuts (string)
    """
    if helpViewer is None and pluginName is None:
        for act in e4App().getObject("Project").getActions():
            __readShortcut(act, "Project", prefClass)
        
        for act in e4App().getObject("UserInterface").getActions('ui'):
            __readShortcut(act, "General", prefClass)
        
        for act in e4App().getObject("UserInterface").getActions('wizards'):
            __readShortcut(act, "Wizards", prefClass)
        
        for act in e4App().getObject("DebugUI").getActions():
            __readShortcut(act, "Debug", prefClass)
        
        for act in e4App().getObject("ViewManager").getActions('edit'):
            __readShortcut(act, "Edit", prefClass)
        
        for act in e4App().getObject("ViewManager").getActions('file'):
            __readShortcut(act, "File", prefClass)
        
        for act in e4App().getObject("ViewManager").getActions('search'):
            __readShortcut(act, "Search", prefClass)
        
        for act in e4App().getObject("ViewManager").getActions('view'):
            __readShortcut(act, "View", prefClass)
        
        for act in e4App().getObject("ViewManager").getActions('macro'):
            __readShortcut(act, "Macro", prefClass)
        
        for act in e4App().getObject("ViewManager").getActions('bookmark'):
            __readShortcut(act, "Bookmarks", prefClass)
        
        for act in e4App().getObject("ViewManager").getActions('spelling'):
            __readShortcut(act, "Spelling", prefClass)
        
        actions = e4App().getObject("ViewManager").getActions('window')
        if actions:
            for act in actions:
                __readShortcut(act, "Window", prefClass)
        
        for category, ref in e4App().getPluginObjects():
            if hasattr(ref, "getActions"):
                actions = ref.getActions()
                for act in actions:
                    __readShortcut(act, category, prefClass)
    
    if helpViewer is not None:
        for act in helpViewer.getActions():
            __readShortcut(act, "HelpViewer", prefClass)
    
    if pluginName is not None:
        try:
            ref = e4App().getPluginObject(pluginName)
            if hasattr(ref, "getActions"):
                actions = ref.getActions()
                for act in actions:
                    __readShortcut(act, pluginName, prefClass)
        except KeyError:
            # silently ignore non available plugins
            pass
    
def __saveShortcut(act, category, prefClass):
    """
    Private function to write a single keyboard shortcut to the settings.
    
    @param act reference to the action object (E4Action)
    @param category category the action belongs to (string)
    @param prefClass preferences class used as the storage area
    """
    if act.objectName():
        prefClass.settings.setValue(
            "Shortcuts/{0}/{1}/Accel".format(category, act.objectName()), 
            act.shortcut())
        prefClass.settings.setValue(
            "Shortcuts/{0}/{1}/AltAccel".format(category, act.objectName()), 
            act.alternateShortcut())

def saveShortcuts(prefClass = Prefs):
    """
    Module function to write the keyboard shortcuts for the defined QActions.
    
    @param prefClass preferences class used as the storage area
    """
    # step 1: clear all previously saved shortcuts
    prefClass.settings.beginGroup("Shortcuts")
    prefClass.settings.remove("")
    prefClass.settings.endGroup()
    
    # step 2: save the various shortcuts
    for act in e4App().getObject("Project").getActions():
        __saveShortcut(act, "Project", prefClass)
    
    for act in e4App().getObject("UserInterface").getActions('ui'):
        __saveShortcut(act, "General", prefClass)
    
    for act in e4App().getObject("UserInterface").getActions('wizards'):
        __saveShortcut(act, "Wizards", prefClass)
    
    for act in e4App().getObject("DebugUI").getActions():
        __saveShortcut(act, "Debug", prefClass)
    
    for act in e4App().getObject("ViewManager").getActions('edit'):
        __saveShortcut(act, "Edit", prefClass)
    
    for act in e4App().getObject("ViewManager").getActions('file'):
        __saveShortcut(act, "File", prefClass)
    
    for act in e4App().getObject("ViewManager").getActions('search'):
        __saveShortcut(act, "Search", prefClass)
    
    for act in e4App().getObject("ViewManager").getActions('view'):
        __saveShortcut(act, "View", prefClass)
    
    for act in e4App().getObject("ViewManager").getActions('macro'):
        __saveShortcut(act, "Macro", prefClass)
    
    for act in e4App().getObject("ViewManager").getActions('bookmark'):
        __saveShortcut(act, "Bookmarks", prefClass)
    
    for act in e4App().getObject("ViewManager").getActions('spelling'):
        __saveShortcut(act, "Spelling", prefClass)
    
    actions = e4App().getObject("ViewManager").getActions('window')
    if actions:
        for act in actions:
            __saveShortcut(act, "Window", prefClass)
    
    for category, ref in e4App().getPluginObjects():
        if hasattr(ref, "getActions"):
            actions = ref.getActions()
            for act in actions:
                __saveShortcut(act, category, prefClass)
    
    for act in e4App().getObject("DummyHelpViewer").getActions():
        __saveShortcut(act, "HelpViewer", prefClass)

def exportShortcuts(fn):
    """
    Module function to export the keyboard shortcuts for the defined QActions.
    
    @param fn filename of the export file (string)
    @return flag indicating success
    """
    try:
        if fn.lower().endswith("e4kz"):
            try:
                import gzip
            except ImportError:
                QMessageBox.critical(None,
                    QApplication.translate("Shortcuts", "Export Keyboard Shortcuts"),
                    QApplication.translate("Shortcuts", 
                        """Compressed keyboard shortcut files"""
                        """ not supported. The compression library is missing."""))
                return 0
            f = gzip.open(fn, "w")
        else:
            f = open(fn, "w", encoding = "utf-8")
        
        ShortcutsWriter(f).writeXML()
        
        f.close()
        return True
    except IOError:
        return False

def importShortcuts(fn):
    """
    Module function to import the keyboard shortcuts for the defined E4Actions.
    
    @param fn filename of the import file (string)
    @return flag indicating success
    """
    try:
        if fn.lower().endswith("kz"):
            try:
                import gzip
            except ImportError:
                QMessageBox.critical(None,
                    QApplication.translate("Shortcuts", "Import Keyboard Shortcuts"),
                    QApplication.translate("Shortcuts", 
                        """Compressed keyboard shortcut files"""
                        """ not supported. The compression library is missing."""))
                return False
            f = gzip.open(fn, "r")
        else:
            f = open(fn, "r", encoding = "utf-8")
        try:
            line = f.readline()
            dtdLine = f.readline()
        finally:
            f.close()
    except IOError:
        QMessageBox.critical(None,
            QApplication.translate("Shortcuts", "Import Keyboard Shortcuts"),
            QApplication.translate("Shortcuts", 
                "<p>The keyboard shortcuts could not be read from file <b>{0}</b>.</p>")
                .format(fn))
        return False
    
    if fn.lower().endswith("kz"):
        # work around for a bug in xmlproc
        validating = False
    else:
        validating = dtdLine.startswith("<!DOCTYPE")
    parser = make_parser(validating)
    handler = ShortcutsHandler()
    er = XMLEntityResolver()
    eh = XMLErrorHandler()
    
    parser.setContentHandler(handler)
    parser.setEntityResolver(er)
    parser.setErrorHandler(eh)
    
    try:
        if fn.lower().endswith("kz"):
            try:
                import gzip
            except ImportError:
                QMessageBox.critical(None,
                    QApplication.translate("Shortcuts", "Import Keyboard Shortcuts"),
                    QApplication.translate("Shortcuts", 
                        """Compressed keyboard shortcut files"""
                        """ not supported. The compression library is missing."""))
                return False
            f = gzip.open(fn, "r")
        else:
            f = open(fn, "r", encoding = "utf-8")
        try:
            try:
                parser.parse(f)
            except UnicodeEncodeError:
                f.seek(0)
                buf = io.StringIO(f.read())
                parser.parse(buf)
        finally:
            f.close()
    except IOError:
        QMessageBox.critical(None,
            QApplication.translate("Shortcuts", "Import Keyboard Shortcuts"),
            QApplication.translate("Shortcuts", 
                "<p>The keyboard shortcuts could not be read from file <b>{0}</b>.</p>")
                .format(fn))
        return False
        
    except XMLFatalParseError:
        QMessageBox.critical(None,
            QApplication.translate("Shortcuts", "Import Keyboard Shortcuts"),
            QApplication.translate("Shortcuts", 
                "<p>The keyboard shortcuts file <b>{0}</b> has invalid contents.</p>")
                .format(fn))
        eh.showParseMessages()
        return False
        
    eh.showParseMessages()
    
    shortcuts = handler.getShortcuts()
    
    setActions(shortcuts)
    
    saveShortcuts()
    syncPreferences()
    
    return True

def __setAction(actions, sdict):
    """
    Private function to write a single keyboard shortcut to the settings.
    
    @param actions list of actions to set (list of E4Action)
    @param sdict dictionary containg accelerator information for one category
    """
    for act in actions:
        if act.objectName():
            try:
                accel, altAccel = sdict[act.objectName()]
                act.setShortcut(QKeySequence(accel))
                act.setAlternateShortcut(QKeySequence(altAccel))
            except KeyError:
                pass

def setActions(shortcuts):
    """
    Module function to set actions based on new format shortcuts file.
    
    @param shortcuts dictionary containing the accelerator information 
        read from a XML file
    """
    if "Project" in shortcuts:
        __setAction(e4App().getObject("Project").getActions(), 
            shortcuts["Project"])
    
    if "General" in shortcuts:
        __setAction(e4App().getObject("UserInterface").getActions('ui'), 
            shortcuts["General"])
    
    if "Wizards" in shortcuts:
        __setAction(e4App().getObject("UserInterface").getActions('wizards'), 
            shortcuts["Wizards"])
    
    if "Debug" in shortcuts:
        __setAction(e4App().getObject("DebugUI").getActions(), 
            shortcuts["Debug"])
    
    if "Edit" in shortcuts:
        __setAction(e4App().getObject("ViewManager").getActions('edit'), 
            shortcuts["Edit"])
    
    if "File" in shortcuts:
        __setAction(e4App().getObject("ViewManager").getActions('file'), 
            shortcuts["File"])
    
    if "Search" in shortcuts:
        __setAction(e4App().getObject("ViewManager").getActions('search'), 
            shortcuts["Search"])
    
    if "View" in shortcuts:
        __setAction(e4App().getObject("ViewManager").getActions('view'), 
            shortcuts["View"])
    
    if "Macro" in shortcuts:
        __setAction(e4App().getObject("ViewManager").getActions('macro'), 
            shortcuts["Macro"])
    
    if "Bookmarks" in shortcuts:
        __setAction(e4App().getObject("ViewManager").getActions('bookmark'), 
            shortcuts["Bookmarks"])
    
    if "Spelling" in shortcuts:
        __setAction(e4App().getObject("ViewManager").getActions('spelling'), 
            shortcuts["Spelling"])
    
    if "Window" in shortcuts:
        actions = e4App().getObject("ViewManager").getActions('window')
        if actions:
            __setAction(actions, shortcuts["Window"])
    
    for category, ref in e4App().getPluginObjects():
        if category in shortcuts and hasattr(ref, "getActions"):
            actions = ref.getActions()
            __setAction(actions, shortcuts[category])
    
    if "HelpViewer" in shortcuts:
        __setAction(e4App().getObject("DummyHelpViewer").getActions(), 
            shortcuts["HelpViewer"])
