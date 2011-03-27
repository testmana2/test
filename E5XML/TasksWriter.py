# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the writer class for writing an XML tasks file.
"""

import time

from E5Gui.E5Application import e5App

from .XMLStreamWriterBase import XMLStreamWriterBase
from .Config import tasksFileFormatVersion, tasksFileFormatVersionAlternative

import Preferences
import Utilities

class TasksWriter(XMLStreamWriterBase):
    """
    Class implementing the writer class for writing an XML tasks file.
    """
    def __init__(self, device, forProject = False, projectName = ""):
        """
        Constructor
        
        @param device reference to the I/O device to write to (QIODevice)
        @param forProject flag indicating project related mode (boolean)
        @param projectName name of the project (string)
        """
        XMLStreamWriterBase.__init__(self, device)
        
        self.name = projectName
        self.forProject = forProject
        
    def writeXML(self):
        """
        Public method to write the XML to the file.
        """
        viewer = e5App().getObject("TaskViewer")
        
        XMLStreamWriterBase.writeXML(self)
        
        formatVersion = tasksFileFormatVersion
        if self.forProject and viewer.projectTasksScanFilter is not None:
            formatVersion = tasksFileFormatVersionAlternative
        self.writeDTD('<!DOCTYPE Tasks SYSTEM "Tasks-{0}.dtd">'.format(
            formatVersion))
        
        # add some generation comments
        if self.forProject:
            self.writeComment(" eric5 tasks file for project {0} ".format(self.name))
            if Preferences.getProject("XMLTimestamp"):
                self.writeComment(" Saved: {0} ".format(
                    time.strftime('%Y-%m-%d, %H:%M:%S')))
        else:
            self.writeComment(" eric5 tasks file ")
            self.writeComment(" Saved: {0} ".format(time.strftime('%Y-%m-%d, %H:%M:%S')))
        
        # add the main tag
        self.writeStartElement("Tasks")
        self.writeAttribute("version", tasksFileFormatVersion)
        
        # write the project scan filter
        if self.forProject and viewer.projectTasksScanFilter is not None:
            self.writeTextElement("ProjectScanFilter",
                e5App().getObject("TaskViewer").projectTasksScanFilter.strip())
        
        # do the tasks
        if self.forProject:
            tasks = viewer.getProjectTasks()
        else:
            tasks = viewer.getGlobalTasks()
        for task in tasks:
            self.writeStartElement("Task")
            self.writeAttribute("priority", str(task.priority))
            self.writeAttribute("completed", str(task.completed))
            self.writeAttribute("bugfix", str(task.isBugfixTask))
            self.writeTextElement("Summary", task.description.strip())
            self.writeTextElement("Description", task.longtext.strip())
            self.writeTextElement("Created", 
                time.strftime("%Y-%m-%d, %H:%M:%S", time.localtime(task.created)))
            if task.filename:
                self.writeStartElement("Resource")
                self.writeTextElement("Filename", 
                    Utilities.fromNativeSeparators(task.filename))
                self.writeTextElement("Linenumber", str(task.lineno))
                self.writeEndElement()
            self.writeEndElement()
        
        self.writeEndElement()
        self.writeEndDocument()
