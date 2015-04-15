# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2013 Tobias Rzepka <tobias.rzepka@gmail.com>
#

"""
Module implementing the open behavior of Python3 for use with Eric6.

The Eric6 used features are emulated only. The not emulated features
should throw a NotImplementedError exception.
"""

import __builtin__
import codecs


def open(file, mode='r', buffering=-1, encoding=None,
         errors=None, newline=None, closefd=True):
    """
    Replacement for the build in open function.
    
    @param file filename or file descriptor (string)
    @keyparam mode access mode (string)
    @keyparam buffering size of the read buffer (string)
    @keyparam encoding character encoding for reading/ writing (string)
    @keyparam errors behavior for the character encoding ('strict',
        'explicit', ...) (string)
    @keyparam newline controls how universal newlines works (string)
    @keyparam closefd close underlying file descriptor if given as file
        parameter (boolean)
    @return Returns the new file object
    """
    return File(file, mode, buffering, encoding, errors, newline, closefd)


class File(file):   # __IGNORE_WARNING__
    """
    Facade for the original file class.
    """
    def __init__(self, filein, mode='r', buffering=-1,
                 encoding=None, errors=None, newline=None, closefd=True):
        """
        Constructor
        
        It checks for unimplemented parameters.
        
        @param filein filename or file descriptor (string)
        @keyparam mode access mode (string)
        @keyparam buffering size of the read buffer (string)
        @keyparam encoding character encoding for reading/ writing (string)
        @keyparam errors behavior for the character encoding ('strict',
            'explicit', ...) (string)
        @keyparam newline controls how universal newlines works (string)
        @keyparam closefd close underlying file descriptor if given as file
            parameter (boolean)
        @exception NotImplementedError for not implemented method parameters
        """
        self.__encoding = encoding
        self.__newline = str(newline)
        self.__closefd = closefd
        if newline is not None:
            if 'r' in mode:
                raise NotImplementedError
            else:
                mode = mode.replace('t', 'b')
                if 'b' not in mode:
                    mode = mode + 'b'

        if closefd is False:
            raise NotImplementedError

        if errors is None:
            self.__errors = 'strict'
        else:
            self.__errors = errors

        file.__init__(self, filein,  mode,  buffering)    # __IGNORE_WARNING__

    def read(self, n=-1):
        """
        Public method to read n bytes or all if n=-1 from file.
        
        @keyparam n bytecount or all if n=-1 (int)
        @return decoded bytes read
        """
        txt = super(File, self).read(n)
        if self.__encoding is None:
            return txt
        else:
            return codecs.decode(txt, self.__encoding)

    def readline(self, limit=-1):
        """
        Public method to read one line from file.
        
        @keyparam limit maximum bytes to read or all if limit=-1 (int)
        @return decoded line read
        """
        txt = super(File, self).readline(limit)
        if self.__encoding is None:
            return txt
        else:
            return codecs.decode(txt, self.__encoding)

    def readlines(self, hint=-1):
        """
        Public method to read all lines from file.
        
        @keyparam hint maximum bytes to read or all if hint=-1 (int)
        @return decoded lines read
        """
        if self.__encoding is None:
            return super(File, self).readlines(hint)
        else:
            return [codecs.decode(txt, self.__encoding)
                    for txt in super(File, self).readlines(hint)]

    def write(self, txt):
        """
        Public method to write given data to file and encode if needed.
        
        @param txt data to write. (str, bytes)
        """
        if self.__encoding is not None:
            txt = codecs.encode(txt, self.__encoding, self.__errors)

        if self.__newline in ['\r\n', '\r']:
            txt = txt.replace('\n', self.__newline)

        super(File, self).write(txt)

    def next(self):
        """
        Public method used in an iterator.
        
        @return decoded data read
        """
        txt = super(File, self).next()
        if self.__encoding is None:
            return txt
        else:
            return codecs.decode(txt, self.__encoding)

# Inject into the __builtin__ dictionary
__builtin__.open = open

if __name__ == '__main__':
    fp = open('compatibility_fixes.py', encoding='latin1')
    print(fp.read())
    fp.close()

    with open('compatibility_fixes.py', encoding='UTF-8') as fp:
        rlines = fp.readlines()
        print(rlines[-1])
