# -*- coding: utf-8 -*-

# Copyright (c) 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the syntax check for Python 2.
"""

import sys
import re
import traceback
from codecs import BOM_UTF8, BOM_UTF16, BOM_UTF32

from py2flakes.checker import Checker
from py2flakes.messages import ImportStarUsed

coding_regexps = [
    (2, re.compile(r'''coding[:=]\s*([-\w_.]+)''')), 
    (1, re.compile(r'''<\?xml.*\bencoding\s*=\s*['"]([-\w_.]+)['"]\?>''')), 
]

def get_coding(text):
    """
    Function to get the coding of a text.
    
    @param text text to inspect (string)
    @return coding string
    """
    lines = text.splitlines()
    for coding in coding_regexps:
        coding_re = coding[1]
        head = lines[:coding[0]]
        for l in head:
            m = coding_re.search(l)
            if m:
                return m.group(1).lower()
    return None

def decode(text):
    """
    Function to decode a text.
    
    @param text text to decode (string)
    @return decoded text and encoding
    """
    try:
        if text.startswith(BOM_UTF8):
            # UTF-8 with BOM
            return unicode(text[len(BOM_UTF8):], 'utf-8'), 'utf-8-bom'
        elif text.startswith(BOM_UTF16):
            # UTF-16 with BOM
            return unicode(text[len(BOM_UTF16):], 'utf-16'), 'utf-16'
        elif text.startswith(BOM_UTF32):
            # UTF-32 with BOM
            return unicode(text[len(BOM_UTF32):], 'utf-32'), 'utf-32'
        coding = get_coding(text)
        if coding:
            return unicode(text, coding), coding
    except (UnicodeError, LookupError):
        pass
    
    # Assume UTF-8
    try:
        return unicode(text, 'utf-8'), 'utf-8-guessed'
    except (UnicodeError, LookupError):
        pass
    
    # Assume Latin-1 (behaviour before 3.7.1)
    return unicode(text, "latin-1"), 'latin-1-guessed'

def compile(file):
    """
    Function to compile one Python source file to Python bytecode.
    
    @param file source filename (string)
    @return A tuple indicating status (1 = an error was found), the
        filename, the linenumber, the code string, the error message
        and the full source code (boolean, string, string, string, 
        string, string). The values are only valid, if the status 
        equals 1.
    """
    import __builtin__
    try:
        f = open(file)
        codestring, encoding = decode(f.read())
        f.close()
    except IOError, msg:
        return (1, file, "1", "", "I/O Error: %s" % unicode(msg), "")

    if type(codestring) == type(u""):
        codestring = codestring.encode('utf-8')
    codestring = codestring.replace("\r\n","\n")
    codestring = codestring.replace("\r","\n")

    if codestring and codestring[-1] != '\n':
        codestring = codestring + '\n'
    
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
        lines = traceback.format_exception_only(SyntaxError, detail)
        match = re.match('\s*File "(.+)", line (\d+)', 
            lines[0].replace('<string>', '%s' % file))
        if match is not None:
            fn, line = match.group(1, 2)
            if lines[1].startswith('SyntaxError:'):
                code = ""
                error = re.match('SyntaxError: (.+)', lines[1]).group(1)
            else:
                code = re.match('(.+)', lines[1]).group(1)
                error = ""
                for seLine in lines[2:]:
                    if seLine.startswith('SyntaxError:'):
                        error = re.match('SyntaxError: (.+)', seLine).group(1)
        else:
            fn = detail.filename
            line = detail.lineno and detail.lineno or 1
            code = ""
            error = detail.msg
        return (1, fn, line, code, error, codestring)
    except ValueError, detail:
        try:
            fn = detail.filename
            line = detail.lineno
            error = detail.msg
        except AttributeError:
            fn = file
            line = 1
            error = unicode(detail)
        code = ""
        return (1, fn, line, code, error, codestring)
    except StandardError, detail:
        try:
            fn = detail.filename
            line = detail.lineno
            code = ""
            error = detail.msg
            return (1, fn, line, code, error, codestring)
        except:         # this catchall is intentional
            pass
    
    return (0, None, None, None, None, codestring)

def flakesCheck(fileName, codestring, ignoreStarImportWarnings):
    """
    Function to perform a pyflakes check.
    
    @param fileName name of the file (string)
    @param codestring source code to be checked (string)
    @param ignoreStarImportWarnings flag indicating to 
        ignore 'star import' warnings (boolean)
    @return list of strings containing the warnings
        (marker, file name, line number, message)
    """
    strings = []
    lines = codestring.splitlines()
    try:
        warnings = Checker(codestring, fileName)
        warnings.messages.sort(key = lambda a: a.lineno)
        for warning in warnings.messages:
            if ignoreStarImportWarnings and \
               isinstance(warning, ImportStarUsed):
                continue
            
            _fn, lineno, message = warning.getMessageData()
            if not lines[lineno - 1].strip()\
               .endswith("__IGNORE_WARNING__"):
                strings.extend(["FLAKES_WARNING", _fn, lineno, message])
    except SyntaxError as err:
        if err.text.strip():
            msg = err.text.strip()
        else:
            msg = err.msg
        strings.extend(["FLAKES_ERROR", fileName, err.lineno, msg])
    
    return strings

if __name__ == "__main__":
    if len(sys.argv) < 2 or \
       len(sys.argv) > 3 or \
       (len(sys.argv) == 3 and sys.argv[1] not in ["-fi", "-fs"]):
        print "ERROR"
        print ""
        print ""
        print ""
        print "No file name given."
    else:
        filename = sys.argv[-1]
        syntaxerror, fname, line, code, error, codestring = compile(filename)
        
        if syntaxerror:
            print "ERROR"
        else:
            print "NO_ERROR"
        print fname
        print line
        print code
        print error
        
        if not syntaxerror and sys.argv[1] in ["-fi", "-fs"]:
            # do pyflakes check
            warningLines = flakesCheck(filename, codestring, sys.argv[1] == "-fi")
            for warningLine in warningLines:
                print warningLine
    
    sys.exit(0)
    
#
# eflag: FileType = Python2
