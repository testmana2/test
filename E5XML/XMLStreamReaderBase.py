# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a base class for all of eric5s XML stream writers.
"""

import pickle
import base64

from PyQt4.QtCore import QXmlStreamReader, QCoreApplication

class XMLStreamReaderBase(QXmlStreamReader):
    """
    Class implementing a base class for all of eric5s XML stream readers.
    """
    def __init__(self, device):
        """
        Constructor
        
        @param device reference to the I/O device to read from (QIODevice)
        """
        QXmlStreamReader.__init__(self, device)
        
        self.NEWPARA = chr(0x2029)
        self.NEWLINE = chr(0x2028)
    
    def decodedNewLines(self, text):
        """
        Public method to decode newlines and paragraph breaks.
        
        @param text text to decode (string)
        """
        return text.replace(self.NEWPARA, "\n\n").replace(self.NEWLINE, "\n")
    
    def _skipUnknownElement(self):
        """
        Protected method to skip over all unknown elements.
        """
        if not self.isStartElement():
            return
        
        while not self.atEnd():
            self.readNext()
            if self.isEndElement():
                break
            
            if self.isStartElement():
                self._skipUnknownElement()
    
    def _readBasics(self):
        """
        Protected method to read an object of a basic Python type.
        
        @return Python object read
        """
        while not self.atEnd():
            self.readNext()
            if self.isStartElement():
                try:
                    if self.name() == "none":
                        val = None
                    elif self.name() == "int":
                        val = int(self.readElementText())
                    elif self.name() == "bool":
                        b = self.readElementText()
                        if b == "True":
                            val = True
                        else:
                            val = False
                    elif self.name() == "float":
                        val = float(self.readElementText())
                    elif self.name() == "complex":
                        real, imag = self.readElementText().split()
                        val = float(real) + float(imag)*1j
                    elif self.name() == "string":
                        val = self.readElementText()
                    elif self.name() == "bytes":
                        by = bytes(
                            [int(b) for b in self.readElementText().split(",")])
                        val = by
                    elif self.name() == "bytearray":
                        by = bytearray(
                            [int(b) for b in self.readElementText().split(",")])
                        val = by
                    elif self.name() == "tuple":
                        val = self.__readTuple()
                        return val
                    else:
                        self._skipUnknownElement()
                except ValueError as err:
                    self.raiseError(str(err))
            
            if self.isEndElement():
                if self.name() in ["tuple"]:
                    return None
                else:
                    return val
    
    def __readTuple(self):
        """
        Private method to read a Python tuple.
        
        @return Python tuple
        """
        l = []
        while not self.atEnd():
            val = self._readBasics()
            if self.isEndElement() and self.name() == "tuple" and val is None:
                return tuple(l)
            else:
                l.append(val)
