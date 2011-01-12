# -*- coding: utf-8 -*-

# Copyright (c) 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Class implementing the PEP 8 checker for Python2.
"""

import sys
import optparse
import getopt

from Tools import readEncodedFile, normalizeCode

import pep8


class Pep8Checker(pep8.Checker):
    """
    Class implementing the PEP 8 checker for Python2.
    """
    def __init__(self, filename, lines, repeat=False,
                 select="", ignore=""):
        """
        Constructor
        
        @param filename name of the file to check (string)
        @param lines source of the file (list of strings)
        @keyparam repeat flag indicating to repeat message categories (boolean)
        @keyparam select list of message IDs to check for
            (comma separated string)
        @keyparam ignore list of message IDs to ignore
            (comma separated string)
        """
        pep8.options = optparse.Values()
        
        pep8.options.verbose = 0
        
        pep8.options.repeat = repeat
        if select:
            pep8.options.select = [s.strip() for s in select.split(',')
                                   if s.strip()]
        else:
            pep8.options.select = []
        if ignore:
            pep8.options.ignore = [i.strip() for i in ignore.split(',')
                                   if i.strip()]
        else:
            pep8.options.ignore = []
        pep8.options.physical_checks = pep8.find_checks('physical_line')
        pep8.options.logical_checks = pep8.find_checks('logical_line')
        pep8.options.counters = dict.fromkeys(pep8.BENCHMARK_KEYS, 0)
        pep8.options.messages = {}
        
        pep8.Checker.__init__(self, filename, lines)
        
        self.messages = []
    
    def __ignore_code(self, code):
        """
        Private method to check, if the message for the given code should
        be ignored.
        
        If codes are selected and the code has a selected prefix and does not
        have an ignored prefix, it is not ignored. If codes are selected and
        the code does not have a selected prefix, it is ignored. If no codes
        are selected, the code is ignored, if it has a prefix, that is
        contained in the ignored codes.
        
        @param code code to be checked (string)
        @return flag indicating, that the code should be ignored (boolean)
        """
        if pep8.options.select:
            if code.startswith(tuple(pep8.options.select)):
                if code.startswith(tuple(pep8.options.ignore)):
                    return True
                else:
                    return False
            else:
                return True
        else:
            if code.startswith(tuple(pep8.options.ignore)):
                return True
            else:
                return False
    
    def report_error_args(self, line_number, offset, code, check, *args):
        """
        Public method to collect the error messages.
        
        @param line_number line number of the issue (integer)
        @param offset position within line of the issue (integer)
        @param code message code (string)
        @param check reference to the checker function (function)
        @param args arguments for the message (list)
        """
        if self.__ignore_code(code):
            return
        
        if code in pep8.options.counters:
            pep8.options.counters[code] += 1
        else:
            pep8.options.counters[code] = 1
            pep8.options.messages[code] = code
        self.file_errors += 1
        if pep8.options.counters[code] == 1 or pep8.options.repeat:
            self.messages.append(
                (self.filename, self.line_offset + line_number,
                 offset + 1, code, args)
            )

if __name__ == "__main__":
    repeat = False
    select = ""
    ignore = ""
    filename = ""
    
    if "-f" not in sys.argv:
        print "ERROR"
        print ""
        print "No file name given."
    else:
        try:
            optlist, args = getopt.getopt(sys.argv[1:], "rf:i:s:")
        except getopt.GetoptError:
            print "ERROR"
            print ""
            print "Wrong arguments given"
            sys.exit(1)
        
        for opt, arg in optlist:
            if opt == "-r":
                repeat = True
            elif opt == "-f":
                filename = arg
            elif opt == "-i":
                ignore = arg
            elif opt == "-s":
                select = arg
        
        try:
            codestring = readEncodedFile(filename)[0]
            codestring = normalizeCode(codestring)
            codestring = codestring.splitlines(True)
        except IOError, msg:
            print "ERROR"
            print filename
            print "I/O Error: %s" % unicode(msg)
            sys.exit(1)
        
        checker = Pep8Checker(filename, codestring, repeat=repeat,
                              select=select, ignore=ignore)
        checker.check_all()
        if len(checker.messages) > 0:
            checker.messages.sort(key=lambda a: a[1])
            for message in checker.messages:
                fname, lineno, position, code, args = message
                print "PEP8"
                print fname
                print lineno
                print position
                print code
                print len(args)
                for a in args:
                    print a
        else:
            print "NO_PEP8"
            print filename

#
# eflag: FileType = Python2
