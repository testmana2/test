# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the writer class for writing an XML templates file.
"""

import time

from .XMLStreamWriterBase import XMLStreamWriterBase
from .Config import templatesFileFormatVersion

class TemplatesWriter(XMLStreamWriterBase):
    """
    Class implementing the writer class for writing an XML templates file.
    """
    def __init__(self, device, templatesViewer):
        """
        Constructor
        
        @param device reference to the I/O device to write to (QIODevice)
        @param templatesViewer reference to the templates viewer object (TemplateViewer)
        """
        XMLStreamWriterBase.__init__(self, device)
        
        self.templatesViewer = templatesViewer
        
    def writeXML(self):
        """
        Public method to write the XML to the file.
        """
        XMLStreamWriterBase.writeXML(self)
        
        self.writeDTD('<!DOCTYPE Templates SYSTEM "Templates-{0}.dtd">'.format(
            templatesFileFormatVersion))
        
        # add some generation comments
        self.writeComment(" eric5 templates file ")
        self.writeComment(" Saved: {0} ".format(time.strftime('%Y-%m-%d, %H:%M:%S')))
##        self._write("<!-- eric5 templates file -->")
##        self._write("<!-- Saved: {0} -->".format(time.strftime('%Y-%m-%d, %H:%M:%S')))
        
        # add the main tag
        self.writeStartElement("Templates")
        self.writeAttribute("version", templatesFileFormatVersion)
##        self._write('<Templates version="{0}">'.format(templatesFileFormatVersion))
        
        # do the template groups
        groups = self.templatesViewer.getAllGroups()
        for group in groups:
            self.writeStartElement("TemplateGroup")
            self.writeAttribute("name", group.getName())
            self.writeAttribute("language", group.getLanguage())
##            self._write('  <TemplateGroup name="{0}" language="{1}">'.format(
##                        group.getName(), group.getLanguage()))
            # do the templates
            templates = group.getAllEntries()
            for template in templates:
                self.writeStartElement("Template")
                self.writeAttribute("name", template.getName())
                self.writeTextElement("TemplateDescription", template.getDescription())
                self.writeTextElement("TemplateText", template.getTemplateText())
                self.writeEndElement()
            self.writeEndElement()
        
        self.writeEndElement()
        self.writeEndDocument()
##                self._write('    <Template name="{0}">'.format(
##                    self.escape(template.getName(), True)))
##                self._write('      <TemplateDescription>{0}</TemplateDescription>'.format(
##                    self.escape("{0}".format(template.getDescription()))))
##                self._write('      <TemplateText>{0}</TemplateText>'.format(
##                    self.escape("{0}".format(template.getTemplateText()))))
##                self._write('    </Template>')
##            self._write('  </TemplateGroup>')
##        
##        self._write('</Templates>', newline = False)
