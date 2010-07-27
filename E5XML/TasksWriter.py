# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the writer class for writing an XML tasks file.
"""

import time

from E5Gui.E5Application import e5App

from .XMLWriterBase import XMLWriterBase
from .Config import tasksFileFormatVersion

import Preferences
import Utilities

class TasksWriter(XMLWriterBase):
    """
    Class implementing the writer class for writing an XML tasks file.
    """
    def __init__(self, file, forProject = False, projectName=""):
        """
        Constructor
        
        @param file open file (like) object for writing
        @param forProject flag indicating project related mode (boolean)
        @param projectName name of the project (string)
        """
        XMLWriterBase.__init__(self, file)
        
        self.name = projectName
        self.forProject = forProject
        
    def writeXML(self):
        """
        Public method to write the XML to the file.
        """
        XMLWriterBase.writeXML(self)
        
        self._write('<!DOCTYPE Tasks SYSTEM "Tasks-{0}.dtd">'.format(
            tasksFileFormatVersion))
        
        # add some generation comments
        if self.forProject:
            self._write("<!-- eric5 tasks file for project {0} -->".format(self.name))
            if Preferences.getProject("XMLTimestamp"):
                self._write("<!-- Saved: {0} -->".format(
                    time.strftime('%Y-%m-%d, %H:%M:%S')))
        else:
            self._write("<!-- eric5 tasks file -->")
            self._write("<!-- Saved: {0} -->".format(time.strftime('%Y-%m-%d, %H:%M:%S')))
        
        # add the main tag
        self._write('<Tasks version="{0}">'.format(tasksFileFormatVersion))
        
        # do the tasks
        if self.forProject:
            tasks = e5App().getObject("TaskViewer").getProjectTasks()
        else:
            tasks = e5App().getObject("TaskViewer").getGlobalTasks()
        for task in tasks:
            self._write('  <Task priority="{0:d}" completed="{1}" bugfix="{2}">'\
                .format(task.priority, task.completed, task.isBugfixTask))
            self._write('    <Summary>{0}</Summary>'.format(
                self.escape("{0}".format(task.description.strip()))))
            self._write('    <Description>{0}</Description>'.format(
                self.escape(self.encodedNewLines(task.longtext.strip()))))
            self._write('    <Created>{0}</Created>'.format(
                time.strftime("%Y-%m-%d, %H:%M:%S", time.localtime(task.created))))
            if task.filename:
                self._write('    <Resource>')
                self._write('      <Filename>{0}</Filename>'.format(
                    Utilities.fromNativeSeparators(task.filename)))
                self._write('      <Linenumber>{0:d}</Linenumber>'.format(task.lineno))
                self._write('    </Resource>')
            self._write('  </Task>')
        
        self._write('</Tasks>', newline = False)
