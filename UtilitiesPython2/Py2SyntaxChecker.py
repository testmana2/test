#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the syntax check for Python 2.
"""

import sys
import re
import traceback
import warnings
import json

from Tools import readEncodedFile, normalizeCode, extractLineFlags


def compile(file, codestring):
    """
    Function to compile one Python source file to Python bytecode.
    
    @param file source filename (string)
    @param codestring source code (string)
    @return A tuple indicating status (True = an error was found), the
        file name, the line number, the index number, the code string
        and the error message (boolean, string, string, string, string,
        string). The values are only valid, if the status equals 1.
    """
    import __builtin__
    
    try:
        if type(file) == type(u""):
            file = file.encode('utf-8')
        
        if file.endswith('.ptl'):
            try:
                import quixote.ptl_compile
            except ImportError:
                return (0, None, None, None, None)
            template = quixote.ptl_compile.Template(codestring, file)
            template.compile()
        else:
            __builtin__.compile(codestring, file, 'exec')
    except SyntaxError, detail:
        index = "0"
        code = ""
        error = ""
        lines = traceback.format_exception_only(SyntaxError, detail)
        match = re.match(
            '\s*File "(.+)", line (\d+)',
            lines[0].replace('<string>', '%s' % file))
        if match is not None:
            fn, line = match.group(1, 2)
            if lines[1].startswith('SyntaxError:'):
                error = re.match('SyntaxError: (.+)', lines[1]).group(1)
            else:
                code = re.match('(.+)', lines[1]).group(1)
                for seLine in lines[2:]:
                    if seLine.startswith('SyntaxError:'):
                        error = re.match('SyntaxError: (.+)', seLine).group(1)
                    elif seLine.rstrip().endswith('^'):
                        index = len(seLine.rstrip()) - 4
        else:
            fn = detail.filename
            line = detail.lineno and detail.lineno or 1
            error = detail.msg
        return (1, fn, line, index, code, error)
    except ValueError, detail:
        index = "0"
        code = ""
        try:
            fn = detail.filename
            line = detail.lineno
            error = detail.msg
        except AttributeError:
            fn = file
            line = 1
            error = unicode(detail)
        return (1, fn, line, index, code, error)
    except StandardError, detail:
        try:
            fn = detail.filename
            line = detail.lineno
            index = "0"
            code = ""
            error = detail.msg
            return (1, fn, line, index, code, error)
        except:         # this catchall is intentional
            pass
    
    return (0, None, None, None, None, None)


def flakesCheck(fileName, codestring, ignoreStarImportWarnings):
    """
    Function to perform a pyflakes check.
    
    @param fileName name of the file (string)
    @param codestring source code to be checked (string)
    @param ignoreStarImportWarnings flag indicating to
        ignore 'star import' warnings (boolean)
    @return list of lists containing the warnings
        (marker, file name, line number, message)
    """
    from py2flakes.checker import Checker
    from py2flakes.messages import ImportStarUsed
    
    flakesWarnings = []
    lines = codestring.splitlines()
    try:
        warnings_ = Checker(codestring, fileName)
        warnings_.messages.sort(key=lambda a: a.lineno)
        for warning in warnings_.messages:
            if ignoreStarImportWarnings and \
               isinstance(warning, ImportStarUsed):
                continue
            
            _fn, lineno, message = warning.getMessageData()
            if "__IGNORE_WARNING__" not in \
                    extractLineFlags(lines[lineno - 1].strip()):
                flakesWarnings.append(["FLAKES_WARNING", _fn, lineno, message])
    except SyntaxError as err:
        if err.text.strip():
            msg = err.text.strip()
        else:
            msg = err.msg
        flakesWarnings.append(["FLAKES_ERROR", fileName, err.lineno, msg])
    
    return flakesWarnings

if __name__ == "__main__":
    info = []
    if len(sys.argv) < 2 or \
       len(sys.argv) > 3 or \
       (len(sys.argv) == 3 and sys.argv[1] not in ["-fi", "-fs"]):
        info.append(["ERROR", "", "", "", "", "No file name given."])
    else:
        warnings.simplefilter("error")
        filename = sys.argv[-1]
        try:
            codestring = readEncodedFile(filename)[0]
            codestring = normalizeCode(codestring)
            
            syntaxerror, fname, line, index, code, error = \
                compile(filename, codestring)
        except IOError, msg:
            # fake a syntax error
            syntaxerror, fname, line, index, code, error = \
                1, filename, "1", "0", "", "I/O Error: %s" % unicode(msg)
        
        if syntaxerror:
            info.append(["ERROR", fname, line, index, code, error])
        else:
            info.append(["NO_ERROR"])
        
        if not syntaxerror and sys.argv[1] in ["-fi", "-fs"]:
            # do pyflakes check
            flakesWarnings = flakesCheck(
                filename, codestring, sys.argv[1] == "-fi")
            info.extend(flakesWarnings)
    
    print json.dumps(info)
    
    sys.exit(0)
    
#
# eflag: FileType = Python2
