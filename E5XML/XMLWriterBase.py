# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a base class for all of eric5s XML writers.
"""

import pickle
import base64

class XMLWriterBase(object):
    """
    Class implementing a base class for all of eric5s XML writers.
    """
    def __init__(self, file):
        """
        Constructor
        
        @param file open file (like) object for writing
        """
        self.pf = file
        
        self.basics = {
            type(None) : self._write_none,
            int        : self._write_int,
            float      : self._write_float,
            complex    : self._write_complex,
            bool       : self._write_bool,
            str        : self._write_string,
            bytes      : self._write_bytes, 
            bytearray  : self._write_bytearray, 
            tuple      : self._write_tuple,
            list       : self._write_list,
            dict       : self._write_dictionary,
            set        : self._write_set, 
            frozenset  : self._write_frozenset, 
        }
        
        self.NEWPARA = chr(0x2029)
        self.NEWLINE = chr(0x2028)
        
    def _write(self, s, newline = True):
        """
        Protected method used to do the real write operation.
        
        @param s string to be written to the XML file
        @param newline flag indicating a linebreak
        """
        self.pf.write("%s%s" % (s, 
            newline and "\n" or ""))
        
    def writeXML(self):
        """
        Public method to write the XML to the file.
        """
        # write the XML header
        self._write('<?xml version="1.0" encoding="UTF-8"?>')
    
    def escape(self, data, attribute=False):
        """
        Function to escape &, <, and > in a string of data.
        
        @param data data to be escaped (string)
        @param attribute flag indicating escaping is done for an attribute
        @return the escaped data (string)
        """
    
        # must do ampersand first
        data = data.replace("&", "&amp;")
        data = data.replace(">", "&gt;")
        data = data.replace("<", "&lt;")
        if attribute:
            data = data.replace('"', "&quot;")
        return data
    
    def encodedNewLines(self, text):
        """
        Public method to encode newlines and paragraph breaks.
        
        @param text text to encode (string)
        """
        return text.replace("\n\n", self.NEWPARA).replace("\n", self.NEWLINE)
    
    def _writeBasics(self, pyobject, indent = 0):
        """
        Protected method to dump an object of a basic Python type.
        
        @param pyobject object to be dumped
        @param indent indentation level for prettier output (integer)
        """
        writeMethod = self.basics.get(type(pyobject)) or self._write_unimplemented
        writeMethod(pyobject, indent)

    ############################################################################
    ## The various writer methods for basic types
    ############################################################################

    def _write_none(self, value, indent):
        """
        Protected method to dump a NoneType object.
        
        @param value value to be dumped (None) (ignored)
        @param indent indentation level for prettier output (integer)
        """
        self._write('%s<none />' % ("  " * indent))
        
    def _write_int(self, value, indent):
        """
        Protected method to dump an int object.
        
        @param value value to be dumped (integer)
        @param indent indentation level for prettier output (integer)
        """
        self._write('%s<int>%s</int>' % ("  " * indent, value))
        
    def _write_bool(self, value, indent):
        """
        Protected method to dump a bool object.
        
        @param value value to be dumped (boolean)
        @param indent indentation level for prettier output (integer)
        """
        self._write('%s<bool>%s</bool>' % ("  " * indent, value))
        
    def _write_float(self, value, indent):
        """
        Protected method to dump a float object.
        
        @param value value to be dumped (float)
        @param indent indentation level for prettier output (integer)
        """
        self._write('%s<float>%s</float>' % ("  " * indent, value))
        
    def _write_complex(self, value, indent):
        """
        Protected method to dump a complex object.
        
        @param value value to be dumped (complex)
        @param indent indentation level for prettier output (integer)
        """
        self._write('%s<complex>%s %s</complex>' % \
            ("  " * indent, value.real, value.imag))
        
    def _write_string(self, value, indent):
        """
        Protected method to dump a str object.
        
        @param value value to be dumped (string)
        @param indent indentation level for prettier output (integer)
        """
        self._write('%s<string>%s</string>' % ("  " * indent, self.escape(value)))
        
    def _write_bytes(self, value, indent):
        """
        Protected method to dump a bytes object.
        
        @param value value to be dumped (bytes)
        @param indent indentation level for prettier output (integer)
        """
        self._write('%s<bytes>%s</bytes>' % (
            " " * indent, ",".join(["%d" % b for b in value])))
        
    def _write_bytearray(self, value, indent):
        """
        Protected method to dump a bytearray object.
        
        @param value value to be dumped (bytearray)
        @param indent indentation level for prettier output (integer)
        """
        self._write('%s<bytearray>%s</bytearray>' % (
            " " * indent, ",".join(["%d" % b for b in value])))
        
    def _write_tuple(self, value, indent):
        """
        Protected method to dump a tuple object.
        
        @param value value to be dumped (tuple)
        @param indent indentation level for prettier output (integer)
        """
        self._write('%s<tuple>' % ("  " * indent))
        nindent = indent + 1
        for elem in value:
            self._writeBasics(elem, nindent)
        self._write('%s</tuple>' % ("  " * indent))
        
    def _write_list(self, value, indent):
        """
        Protected method to dump a list object.
        
        @param value value to be dumped (list)
        @param indent indentation level for prettier output (integer)
        """
        self._write('%s<list>' % ("  " * indent))
        nindent = indent + 1
        for elem in value:
            self._writeBasics(elem, nindent)
        self._write('%s</list>' % ("  " * indent))
        
    def _write_dictionary(self, value, indent):
        """
        Protected method to dump a dict object.
        
        @param value value to be dumped (dictionary)
        @param indent indentation level for prettier output (integer)
        """
        self._write('%s<dict>' % ("  " * indent))
        nindent1 = indent + 1
        nindent2 = indent + 2
        keys = sorted(list(value.keys()))
        for key in keys:
            self._write('%s<key>' % ("  " * nindent1))
            self._writeBasics(key, nindent2)
            self._write('%s</key>' % ("  " * nindent1))
            self._write('%s<value>' % ("  " * nindent1))
            self._writeBasics(value[key], nindent2)
            self._write('%s</value>' % ("  " * nindent1))
        self._write('%s</dict>' % ("  " * indent))
        
    def _write_set(self, value, indent):
        """
        Protected method to dump a set object.
        
        @param value value to be dumped (set)
        @param indent indentation level for prettier output (integer)
        """
        self._write('%s<set>' % ("  " * indent))
        nindent = indent + 1
        for elem in value:
            self._writeBasics(elem, nindent)
        self._write('%s</set>' % ("  " * indent))
        
    def _write_frozenset(self, value, indent):
        """
        Protected method to dump a frozenset object.
        
        @param value value to be dumped (frozenset)
        @param indent indentation level for prettier output (integer)
        """
        self._write('%s<frozenset>' % ("  " * indent))
        nindent = indent + 1
        for elem in value:
            self._writeBasics(elem, nindent)
        self._write('%s</frozenset>' % ("  " * indent))
        
    def _write_unimplemented(self, value, indent):
        """
        Protected method to dump a type, that has no special method.
        
        @param value value to be dumped (any pickleable object)
        @param indent indentation level for prettier output (integer)
        """
        self._write('%s<pickle method="pickle" encoding="base64">%s</pickle>' % \
            ("  " * indent, str(base64.b64encode(pickle.dumps(value)), "ASCII")))
