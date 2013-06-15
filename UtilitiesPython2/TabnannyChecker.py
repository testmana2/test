#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the indentation check for Python 2.
"""

import sys

import Tabnanny

from Tools import readEncodedFile, normalizeCode

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "ERROR"
        print ""
        print ""
        print "No file name given."
    else:
        filename = sys.argv[-1]
        try:
            codestring = readEncodedFile(filename)[0]
            codestring = normalizeCode(codestring)
            
            nok, fname, line, error = Tabnanny.check(filename, codestring)
        except IOError, msg:
            # fake an indentation error
            nok, fname, line, error = \
                True, filename, "1", "I/O Error: %s" % unicode(msg)
        
        if nok:
            print "ERROR"
        else:
            print "NO_ERROR"
        print fname
        print line
        print error
    
    sys.exit(0)

#
# eflag: FileType = Python2
