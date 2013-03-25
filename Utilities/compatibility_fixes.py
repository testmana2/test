# -*- coding: utf-8 -*-

# Copyright (c) 2013 Tobias Rzepka <tobias.rzepka@gmail.com>
#

"""
Module implementing the open behavior of Python3 for use with Eric5.
The from Eric5 used features are emulated only. The not emulated features
should throw a NotImplementedError exception.
"""

from __future__ import unicode_literals    # __IGNORE_WARNING__

import __builtin__
import codecs


def open(file, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True):
    return File(file, mode, buffering,  encoding, errors, newline, closefd)


class File(file):
    def __init__(self, filein, mode='r', buffering=-1,  encoding=None, errors=None, newline=None, closefd=True):
        self.__encoding = encoding
        self.__newline = newline
        self.__closefd = closefd
        if newline is not None:
            if 'r' in mode:
                raise NotImplementedError
            else:
                mode = mode.replace('t', 'b')

        if closefd == False:
            raise NotImplementedError

        if errors is None:
            self.__errors = 'strict'
        else:
            self.__errors = errors
        
        file.__init__(self, filein,  mode,  buffering)

    def read(self,  n=-1):
        txt = super(File, self).read(n)
        if self.__encoding is None:
            return txt
        else:
            return codecs.decode(txt,  self.__encoding)
    
    def readline(self,  limit=-1):
        txt = super(File, self).readline(limit)
        if self.__encoding is None:
            return txt
        else:
            return codecs.decode(txt,  self.__encoding)

    def readlines(self,  hint=-1):
        if self.__encoding is None:
            return super(File, self).readlines(hint)
        else:
            return [codecs.decode(txt,  self.__encoding) for txt in super(File, self).readlines(hint)]

    def write(self,  txt):
        if self.__encoding is not None:
            txt = codecs.encode(txt, self.__encoding, self.__errors)
        
        if self.__newline in ['\r\n', '\r']:
            txt = txt.replace('\n', self.__newline)
        
        super(File, self).write(txt)
    
    def next(self):
        txt = super(File, self).next()
        if self.__encoding is None:
            return txt
        else:
            return codecs.decode(txt,  self.__encoding)

            
__builtin__.open = open

if __name__ == '__main__':
    fp = open('compatibility_fixes.py', encoding='latin1')
    print(fp.read())
    fp.close()
    
    with open('compatibility_fixes.py', encoding='UTF-8') as fp:
        rlines = fp.readlines()
        print(rlines[-1])
