# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the editor assembly widget containing the navigation combos and
the editor widget.
"""

from PyQt4.QtCore import QTimer
from PyQt4.QtGui import QWidget, QGridLayout, QComboBox

from .Editor import Editor

from Utilities.ModuleParser import Module, Function, getTypeFromTypeName

import UI.PixmapCache


class EditorAssembly(QWidget):
    """
    Class implementing the editor assembly widget containing the navigation combos and
    the editor widget.
    """
    def __init__(self, dbs, fn=None, vm=None, filetype="", editor=None, tv=None):
        """
        Constructor
        
        @param dbs reference to the debug server object
        @param fn name of the file to be opened (string). If it is None,
                a new (empty) editor is opened
        @param vm reference to the view manager object (ViewManager.ViewManager)
        @param filetype type of the source file (string)
        @param editor reference to an Editor object, if this is a cloned view
        @param tv reference to the task viewer object
        """
        super().__init__()
        
        self.__layout = QGridLayout(self)
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.setSpacing(1)
        
        self.__globalsCombo = QComboBox()
        self.__membersCombo = QComboBox()
        self.__editor = Editor(dbs, fn, vm, filetype, editor, tv)
        
        self.__layout.addWidget(self.__globalsCombo, 0, 0)
        self.__layout.addWidget(self.__membersCombo, 0, 1)
        self.__layout.addWidget(self.__editor, 1, 0, 1, -1)
        
        self.__module = None
        
        self.__globalsCombo.activated[int].connect(self.__globalsActivated)
        self.__membersCombo.activated[int].connect(self.__membersActivated)
        
        self.__parseTimer = QTimer(self)
        self.__parseTimer.setSingleShot(True)
        self.__parseTimer.setInterval(5 * 1000)
        self.__parseTimer.timeout.connect(self.__parseEditor)
        self.__editor.textChanged.connect(self.__resetParseTimer)
        
        self.__selectedGlobal = ""
        self.__selectedMember = ""
        
        QTimer.singleShot(0, self.__parseEditor)
    
    def shutdownTimer(self):
        """
        Public method to stop and disconnect the timer.
        """
        self.__parseTimer.stop()
        self.__parseTimer.timeout.disconnect(self.__parseEditor)
        self.__editor.textChanged.disconnect(self.__resetParseTimer)
    
    def getEditor(self):
        """
        Public method to get the reference to the editor widget.
        
        @return reference to the editor widget (Editor)
        """
        return self.__editor
    
    def __globalsActivated(self, index, moveCursor=True):
        """
        Private method to jump to the line of the selected global entry and to populate
        the members combo box.
        
        @param index index of the selected entry (integer)
        @keyparam moveCursor flag indicating to move the editor cursor (boolean)
        """
        # step 1: go to the line of the selected entry
        lineno = self.__globalsCombo.itemData(index)
        if lineno is not None:
            if moveCursor:
                txt = self.__editor.text(lineno - 1).rstrip()
                pos = len(txt.replace(txt.strip(), ""))
                self.__editor.gotoLine(lineno, pos if pos == 0 else pos + 1)
                self.__editor.setFocus()
            
            # step 2: populate the members combo, if the entry is a class
            self.__membersCombo.clear()
            entryName = self.__globalsCombo.itemText(index)
            if self.__module:
                if entryName in self.__module.classes:
                    entry = self.__module.classes[entryName]
                elif entryName in self.__module.modules:
                    entry = self.__module.modules[entryName]
                    # step 2.0: add module classes
                    items = []
                    for cl in entry.classes.values():
                        if cl.isPrivate():
                            icon = UI.PixmapCache.getIcon("class_private.png")
                        elif cl.isProtected():
                            icon = UI.PixmapCache.getIcon("class_protected.png")
                        else:
                            icon = UI.PixmapCache.getIcon("class.png")
                        items.append((cl.name, icon, cl.lineno))
                    for itm in sorted(items):
                        self.__membersCombo.addItem(itm[1], itm[0], itm[2])
                else:
                    return
                
                # step 2.1: add class methods
                items = []
                for meth in entry.methods.values():
                    if meth.modifier == Function.Static:
                        icon = UI.PixmapCache.getIcon("method_static.png")
                    elif meth.modifier == Function.Class:
                        icon = UI.PixmapCache.getIcon("method_class.png")
                    elif meth.isPrivate():
                        icon = UI.PixmapCache.getIcon("method_private.png")
                    elif meth.isProtected():
                        icon = UI.PixmapCache.getIcon("method_protected.png")
                    else:
                        icon = UI.PixmapCache.getIcon("method.png")
                    items.append((meth.name, icon, meth.lineno))
                for itm in sorted(items):
                    self.__membersCombo.addItem(itm[1], itm[0], itm[2])
                
                # step 2.2: add class instance attributes
                items = []
                for attr in entry.attributes.values():
                    if attr.isPrivate():
                        icon = UI.PixmapCache.getIcon("attribute_private.png")
                    elif attr.isProtected():
                        icon = UI.PixmapCache.getIcon("attribute_protected.png")
                    else:
                        icon = UI.PixmapCache.getIcon("attribute.png")
                    items.append((attr.name, icon, attr.lineno))
                for itm in sorted(items):
                    self.__membersCombo.addItem(itm[1], itm[0], itm[2])
                
                # step 2.3: add class attributes
                items = []
                icon = UI.PixmapCache.getIcon("attribute_class.png")
                for glob in entry.globals.values():
                    items.append((glob.name, icon, glob.lineno))
                for itm in sorted(items):
                    self.__membersCombo.addItem(itm[1], itm[0], itm[2])
    
    def __membersActivated(self, index, moveCursor=True):
        """
        Private method to jump to the line of the selected members entry.
        
        @param index index of the selected entry (integer)
        @keyparam moveCursor flag indicating to move the editor cursor (boolean)
        """
        lineno = self.__membersCombo.itemData(index)
        if lineno is not None and moveCursor:
            txt = self.__editor.text(lineno - 1).rstrip()
            pos = len(txt.replace(txt.strip(), ""))
            self.__editor.gotoLine(lineno, pos if pos == 0 else pos + 1)
            self.__editor.setFocus()
    
    def __resetParseTimer(self):
        """
        Private slot to reset the parse timer.
        """
        self.__parseTimer.stop()
        self.__parseTimer.start()
    
    def __parseEditor(self):
        """
        Private method to parse the editor source and repopulate the globals combo.
        """
        self.__module = None
        sourceType = getTypeFromTypeName(self.__editor.determineFileType())
        if sourceType != -1:
            src = self.__editor.text()
            if src:
                fn = self.__editor.getFileName()
                if fn is None:
                    fn = ""
                self.__module = Module("", fn, sourceType)
                self.__module.scan(src)
                
                # remember the current selections
                self.__selectedGlobal = self.__globalsCombo.currentText()
                self.__selectedMember = self.__membersCombo.currentText()
                
                self.__globalsCombo.clear()
                self.__membersCombo.clear()
                
                self.__globalsCombo.addItem("")
                
                # step 1: add modules
                items = []
                for module in self.__module.modules.values():
                    items.append((module.name, UI.PixmapCache.getIcon("module.png"),
                                  module.lineno))
                for itm in sorted(items):
                    self.__globalsCombo.addItem(itm[1], itm[0], itm[2])
                
                # step 2: add classes
                items = []
                for cl in self.__module.classes.values():
                    if cl.isPrivate():
                        icon = UI.PixmapCache.getIcon("class_private.png")
                    elif cl.isProtected():
                        icon = UI.PixmapCache.getIcon("class_protected.png")
                    else:
                        icon = UI.PixmapCache.getIcon("class.png")
                    items.append((cl.name, icon, cl.lineno))
                for itm in sorted(items):
                    self.__globalsCombo.addItem(itm[1], itm[0], itm[2])
                
                # step 3: add functions
                items = []
                for func in self.__module.functions.values():
                    if func.isPrivate():
                        icon = UI.PixmapCache.getIcon("method_private.png")
                    elif func.isProtected():
                        icon = UI.PixmapCache.getIcon("method_protected.png")
                    else:
                        icon = UI.PixmapCache.getIcon("method.png")
                    items.append((func.name, icon, func.lineno))
                for itm in sorted(items):
                    self.__globalsCombo.addItem(itm[1], itm[0], itm[2])
                
                # step 4: add attributes
                items = []
                for glob in self.__module.globals.values():
                    if glob.isPrivate():
                        icon = UI.PixmapCache.getIcon("attribute_private.png")
                    elif glob.isProtected():
                        icon = UI.PixmapCache.getIcon("attribute_protected.png")
                    else:
                        icon = UI.PixmapCache.getIcon("attribute.png")
                    items.append((glob.name, icon, glob.lineno))
                for itm in sorted(items):
                    self.__globalsCombo.addItem(itm[1], itm[0], itm[2])
                
                # reset the currently selected entries without moving the text cursor
                index = self.__globalsCombo.findText(self.__selectedGlobal)
                if index != -1:
                    self.__globalsCombo.setCurrentIndex(index)
                    self.__globalsActivated(index, moveCursor=False)
                index = self.__membersCombo.findText(self.__selectedMember)
                if index != -1:
                    self.__membersCombo.setCurrentIndex(index)
                    self.__membersActivated(index, moveCursor=False)