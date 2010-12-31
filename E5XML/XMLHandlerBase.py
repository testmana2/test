# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a base class for all of eric5s XML handlers.
"""

import pickle
import base64

from xml.sax.handler import ContentHandler

class XMLHandlerBase(ContentHandler):
    """
    Class implementing the base class for al of eric5s XML handlers.
    """
    def __init__(self):
        """
        Constructor
        """
        self.startDocumentSpecific = None
        
        self.elements = {
            'none'      : (self.defaultStartElement, self.endNone),
            'int'       : (self.defaultStartElement, self.endInt),
            'float'     : (self.defaultStartElement, self.endFloat),
            'complex'   : (self.defaultStartElement, self.endComplex),
            'bool'      : (self.defaultStartElement, self.endBool),
            'string'    : (self.defaultStartElement, self.endString),
            'bytes'     : (self.defaultStartElement, self.endBytes), 
            'bytearray' : (self.defaultStartElement, self.endBytearray), 
            'tuple'     : (self.startTuple, self.endTuple),
            'list'      : (self.startList, self.endList),
            'dict'      : (self.startDictionary, self.endDictionary),
            'set'       : (self.startSet, self.endSet), 
            'frozenset' : (self.startFrozenset, self.endFrozenset), 
            'pickle'    : (self.startPickle, self.endPickle),
            # for backward compatibility
            'long'      : (self.defaultStartElement, self.endInt),
            'unicode'   : (self.defaultStartElement, self.endString),
        }
        
        self.buffer = ""
        self.stack = []
        self._marker = '__MARKER__'
        
        self.NEWPARA = chr(0x2029)
        self.NEWLINE = chr(0x2028)
        
    def unescape(self, text, attribute = False):
        """
        Public method used to unescape certain characters.
        
        @param text the text to unescape (string)
        @param attribute flag indicating unescaping is done for an attribute
        """
        if attribute:
            return text.replace("&quot;",'"').replace("&gt;",">")\
                       .replace("&lt;","<").replace("&amp;","&")
        else:
            return text.replace("&gt;",">").replace("&lt;","<").replace("&amp;","&")
        
    def decodedNewLines(self, text):
        """
        Public method to decode newlines and paragraph breaks.
        
        @param text text to decode (string)
        """
        return text.replace(self.NEWPARA, "\n\n").replace(self.NEWLINE, "\n")
        
    def startDocument(self):
        """
        Handler called, when the document parsing is started.
        """
        self.buffer = ""
        if self.startDocumentSpecific is not None:
            self.startDocumentSpecific()
        
    def startElement(self, name, attrs):
        """
        Handler called, when a starting tag is found.
        
        @param name name of the tag (string)
        @param attrs list of tag attributes
        """
        try:
            self.elements[name][0](attrs)
        except KeyError:
            pass
        
    def endElement(self, name):
        """
        Handler called, when an ending tag is found.
        
        @param name name of the tag (string)
        """
        try:
            self.elements[name][1]()
        except KeyError:
            pass
        
    def characters(self, chars):
        """
        Handler called for ordinary text.
        
        @param chars the scanned text (string)
        """
        self.buffer += chars
        
    def defaultStartElement(self, attrs):
        """
        Handler method for common start tags.
        
        @param attrs list of tag attributes
        """
        self.buffer = ""
        
    def defaultEndElement(self):
        """
        Handler method for the common end tags.
        """
        pass
        
    def _prepareBasics(self):
        """
        Protected method to prepare the parsing of XML for basic python types.
        """
        self.stack = []

    ############################################################################
    ## The various handler methods for basic types
    ############################################################################

    def endNone(self):
        """
        Handler method for the "none" end tag.
        """
        self.stack.append(None)
        
    def endInt(self):
        """
        Handler method for the "int" end tag.
        """
        self.stack.append(int(self.buffer.strip()))
        
    def endBool(self):
        """
        Handler method for the "bool" end tag.
        """
        if self.buffer.strip() == "True":
            self.stack.append(True)
        else:
            self.stack.append(False)
        
    def endFloat(self):
        """
        Handler method for the "float" end tag.
        """
        self.stack.append(float(self.buffer.strip()))
        
    def endComplex(self):
        """
        Handler method for the "complex" end tag.
        """
        real, imag = self.buffer.strip().split()
        self.stack.append(float(real) + float(imag)*1j)
        
    def endString(self):
        """
        Handler method for the "string" end tag.
        """
        s = str(self.unescape(self.buffer))
        self.stack.append(s)
        
    def endBytes(self):
        """
        Handler method for the "bytes" end tag.
        """
        by = bytes([int(b) for b in self.buffer.strip().split(",")])
        self.stack.append(by)
        
    def endBytearray(self):
        """
        Handler method for the "bytearray" end tag.
        """
        by = bytearray([int(b) for b in self.buffer.strip().split(",")])
        self.stack.append(by)
        
    def startList(self, attrs):
        """
        Handler method for the "list" start tag.
        
        @param attrs list of tag attributes
        """
        self.stack.append(self._marker)
        
    def endList(self):
        """
        Handler method for the "list" end tag.
        """
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i] is self._marker:
                break
        assert i != -1
        l = self.stack[i + 1:len(self.stack)]
        self.stack[i:] = [l]
        
    def startTuple(self, attrs):
        """
        Handler method for the "tuple" start tag.
        
        @param attrs list of tag attributes
        """
        self.stack.append(self._marker)
        
    def endTuple(self):
        """
        Handler method for the "tuple" end tag.
        """
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i] is self._marker:
                break
        assert i != -1
        t = tuple(self.stack[i + 1:len(self.stack)])
        self.stack[i:] = [t]
        
    def startDictionary(self, attrs):
        """
        Handler method for the "dictionary" start tag.
        
        @param attrs list of tag attributes
        """
        self.stack.append(self._marker)
        
    def endDictionary(self):
        """
        Handler method for the "dictionary" end tag.
        """
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i] is self._marker:
                break
        assert i != -1
        d = {}
        for j in range(i + 1, len(self.stack), 2):
            d[self.stack[j]] = self.stack[j + 1]
        self.stack[i:] = [d]
        
    def startSet(self, attrs):
        """
        Handler method for the "set" start tag.
        
        @param attrs list of tag attributes
        """
        self.stack.append(self._marker)
        
    def endSet(self):
        """
        Handler method for the "set" end tag.
        """
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i] is self._marker:
                break
        assert i != -1
        s = set(self.stack[i + 1:len(self.stack)])
        self.stack[i:] = [s]
        
    def startFrozenset(self, attrs):
        """
        Handler method for the "frozenset" start tag.
        
        @param attrs list of tag attributes
        """
        self.stack.append(self._marker)
        
    def endFrozenset(self):
        """
        Handler method for the "frozenset" end tag.
        """
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i] is self._marker:
                break
        assert i != -1
        f = frozenset(self.stack[i + 1:len(self.stack)])
        self.stack[i:] = [f]
        
    def startPickle(self, attrs):
        """
        Handler method for the "pickle" start tag.
        
        @param attrs list of tag attributes
        """
        self.pickleEnc = attrs.get("encoding", "base64")
        
    def endPickle(self):
        """
        Handler method for the "pickle" end tag.
        """
        pic = base64.b64decode(self.buffer.encode("ASCII"))
        self.stack.append(pickle.loads(pic))
