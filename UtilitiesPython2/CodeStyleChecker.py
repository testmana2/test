# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Class implementing the PEP 8 checker for Python2.
"""

import sys
import getopt

from Tools import readEncodedFile, normalizeCode

import pep8
from NamingStyleCheckerPy2 import NamingStyleChecker

# register the name checker
pep8.register_check(NamingStyleChecker, NamingStyleChecker.Codes)

from DocStyleCheckerPy2 import DocStyleChecker


class CodeStyleReport(pep8.BaseReport):
    """
    Class implementing a special report to be used with our dialog.
    """
    def __init__(self, options):
        """
        Constructor
        
        @param options options for the report (optparse.Values)
        """
        super(CodeStyleReport, self).__init__(options)
        
        self.__repeat = options.repeat
        self.errors = []
    
    def error_args(self, line_number, offset, code, check, *args):
        """
        Public method to collect the error messages.
        
        @param line_number line number of the issue (integer)
        @param offset position within line of the issue (integer)
        @param code message code (string)
        @param check reference to the checker function (function)
        @param args arguments for the message (list)
        @return error code (string)
        """
        code = super(CodeStyleReport, self).error_args(
            line_number, offset, code, check, *args)
        if code and (self.counters[code] == 1 or self.__repeat):
            self.errors.append(
                (self.filename, line_number, offset, code, args)
            )
        return code


if __name__ == "__main__":
    repeat = False
    select = ""
    ignore = ""
    filename = ""
    max_line_length = 79
    hang_closing = False
    docType = "pep257"
    
    if "-f" not in sys.argv:
        print "ERROR"
        print ""
        print "No file name given."
    else:
        try:
            optlist, args = getopt.getopt(sys.argv[1:], "d:f:hi:m:rs:")
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
            elif opt == "-m":
                try:
                    max_line_length = int(arg)
                except ValueError:
                    # ignore silently
                    pass
            elif opt == "-h":
                hang_closing = True
            elif opt == "-d":
                if arg in ("pep257", "eric"):
                    docType = arg
        
        try:
            source = readEncodedFile(filename)[0]
            source = normalizeCode(source)
            source = source.splitlines(True)
        except IOError, msg:
            print "ERROR"
            print filename
            print "I/O Error: %s" % unicode(msg)
            sys.exit(1)
        
        if select:
            select = [s.strip() for s in select.split(',')
                      if s.strip()]
        else:
            select = []
        if ignore:
            ignore = [i.strip() for i in ignore.split(',')
                      if i.strip()]
        else:
            ignore = []
        
        # check coding style
        styleGuide = pep8.StyleGuide(
            reporter=CodeStyleReport,
            repeat=repeat,
            select=select,
            ignore=ignore,
            max_line_length=max_line_length,
            hang_closing=hang_closing,
        )
        report = styleGuide.check_files([filename])
        
        # check documentation style
        docStyleChecker = DocStyleChecker(
            source, filename, select, ignore, [], repeat,
            maxLineLength=max_line_length, docType=docType)
        docStyleChecker.run()
        
        errors = report.errors + docStyleChecker.errors
        
        if len(errors) > 0:
            errors.sort(key=lambda a: a[1])
            for error in errors:
                fname, lineno, position, code, args = error
                print "PEP8"
                print fname
                print lineno
                print position
                print code
                print len(args)
                for a in args:
                    print a
            print "PEP8_STATISTICS"
            for key in report.counters:
                if key.startswith(("E", "N", "W")):
                    print key, report.counters[key]
            for key in docStyleChecker.counters:
                if key.startswith("D"):
                    print key, docStyleChecker.counters[key]
        else:
            print "NO_PEP8"
            print filename

#
# eflag: FileType = Python2