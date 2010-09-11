# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a class for reading an XML tasks file.
"""

import time

from E5Gui.E5Application import e5App

from .Config import tasksFileFormatVersion
from .XMLStreamReaderBase import XMLStreamReaderBase

import Utilities

class TasksReader(XMLStreamReaderBase):
    """
    Class for reading an XML tasks file.
    """
    supportedVersions = ["4.2"]
    
    def __init__(self, device, forProject = False, viewer = None):
        """
        Constructor
        
        @param device reference to the I/O device to read from (QIODevice)
        @param forProject flag indicating project related mode (boolean)
        @param viewer reference to the task viewer (TaskViewer)
        """
        XMLStreamReaderBase.__init__(self, device)
        
        self.viewer = viewer
        
        self.forProject = forProject
        if viewer:
            self.viewer = viewer
        else:
            self.viewer = e5App().getObject("TaskViewer")
        
        self.version = ""
    
    def readXML(self):
        """
        Public method to read and parse the XML document.
        """
        while not self.atEnd():
            self.readNext()
            if self.isStartElement():
                if self.name() == "Tasks":
                    self.version = self.attribute("version", tasksFileFormatVersion)
                    if self.version not in self.supportedVersions:
                        self.raiseUnsupportedFormatVersion(self.version)
                elif self.name() == "Task":
                    self.__readTask()
                else:
                    self.raiseUnexpectedStartTag(self.name())
        
        self.showErrorMessage()
    
    def __readTask(self):
        """
        Private method to read the task info.
        """
        task = {"summary"     : "",
                "priority"    : 1,
                "completed"   : False,
                "created"     : 0,
                "filename"    : "",
                "linenumber"  : 0,
                "bugfix"      : False,
                "description" : "",
               }
        task["priority"] = int(self.attribute("priority", "1"))
        
        val = self.attribute("completed", "False")
        if val in ["True", "False"]:
            val = (val == "True")
        else:
            val = bool(int(val))
        task["completed"] = val
        
        val = self.attribute("bugfix", "False")
        if val in ["True", "False"]:
            val = (val == "True")
        else:
            val = bool(int(val))
        task["bugfix"] = val
        
        while not self.atEnd():
            self.readNext()
            if self.isEndElement() and self.name() == "Task":
                self.viewer.addTask(task["summary"], priority = task["priority"],
                    filename = task["filename"], lineno = task["linenumber"], 
                    completed = task["completed"], _time = task["created"], 
                    isProjectTask = self.forProject, isBugfixTask = task["bugfix"], 
                    longtext = task["description"])
                break
            
            if self.isStartElement():
                if self.name() == "Summary":
                    task["summary"] = self.readElementText()
                elif self.name() == "Description":
                    task["description"] = self.readElementText()
                elif self.name() == "Created":
                    task["created"] = time.mktime(
                        time.strptime(self.readElementText(), "%Y-%m-%d, %H:%M:%S"))
                elif self.name() == "Resource":
                    continue    # handle but ignore this tag
                elif self.name() == "Filename":
                    task["filename"] = \
                        Utilities.toNativeSeparators(self.readElementText())
                elif self.name() == "Linenumber":
                    try:
                        task["linenumber"] = int(self.readElementText())
                    except ValueError:
                        pass
                else:
                    self.raiseUnexpectedStartTag(self.name())
