# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#
# pylint: disable=C0103

"""
Module implementing the syntax check for Python 2/3.
"""
from __future__ import unicode_literals

import re
import sys
import traceback

try:
    from pyflakes.checker import Checker
    from pyflakes.messages import ImportStarUsed
except ImportError:
    pass


def initService():
    """
    Initialize the service and return the entry point.
    
    @return the entry point for the background client (function)
    """
    return syntaxAndPyflakesCheck


def normalizeCode(codestring):
    """
    Function to normalize the given code.
    
    @param codestring code to be normalized (string)
    @return normalized code (string)
    """
    codestring = codestring.replace("\r\n", "\n").replace("\r", "\n")

    if codestring and codestring[-1] != '\n':
        codestring = codestring + '\n'

    # Check type for py2: if not str it's unicode
    if sys.version_info[0] == 2:
        try:
            codestring = codestring.encode('utf-8')
        except UnicodeError:
            pass
    
    return codestring


def extractLineFlags(line, startComment="#", endComment=""):
    """
    Function to extract flags starting and ending with '__' from a line
    comment.
    
    @param line line to extract flags from (string)
    @keyparam startComment string identifying the start of the comment (string)
    @keyparam endComment string identifying the end of a comment (string)
    @return list containing the extracted flags (list of strings)
    """
    flags = []
    
    pos = line.rfind(startComment)
    if pos >= 0:
        comment = line[pos + len(startComment):].strip()
        if endComment:
            comment = comment.replace("endComment", "")
        flags = [f.strip() for f in comment.split()
                 if (f.startswith("__") and f.endswith("__"))]
    return flags


def syntaxAndPyflakesCheck(filename, codestring="", checkFlakes=True,
                           ignoreStarImportWarnings=False):
    """
    Function to compile one Python source file to Python bytecode
    and to perform a pyflakes check.
    
    @param filename source filename (string)
    @keyparam codestring string containing the code to compile (string)
    @keyparam checkFlakes flag indicating to do a pyflakes check (boolean)
    @keyparam ignoreStarImportWarnings flag indicating to
        ignore 'star import' warnings (boolean)
    @return A tuple indicating status (True = an error was found), the
        file name, the line number, the index number, the code string
        and the error message (boolean, string, string, string, string,
        string). If checkFlakes is True, a list of strings containing the
        warnings (marker, file name, line number, message)
        The values are only valid, if the status is True.
    """
    try:
        import builtins
    except ImportError:
        import __builtin__ as builtins        #__IGNORE_WARNING__
    
    try:
        if sys.version_info[0] == 2:
            file_enc = filename.encode(sys.getfilesystemencoding())
        else:
            file_enc = filename
        
        # It also encoded the code back to avoid 'Encoding declaration in
        # unicode string' exception on Python2
        codestring = normalizeCode(codestring)
        
        if filename.endswith('.ptl'):
            try:
                import quixote.ptl_compile
            except ImportError:
                return (True, filename, 0, 0, '',
                        'Quixote plugin not found.', [])
            template = quixote.ptl_compile.Template(codestring, file_enc)
            template.compile()
        
        # ast.PyCF_ONLY_AST = 1024, speed optimisation
        module = builtins.compile(codestring, file_enc, 'exec',  1024)
    except SyntaxError as detail:
        index = 0
        code = ""
        error = ""
        lines = traceback.format_exception_only(SyntaxError, detail)
        if sys.version_info[0] == 2:
            lines = [x.decode(sys.getfilesystemencoding()) for x in lines]
        match = re.match('\s*File "(.+)", line (\d+)',
                         lines[0].replace('<string>', '{0}'.format(filename)))
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
            line = detail.lineno or 1
            error = detail.msg
        return (True, fn, int(line), index, code, error, [])
    except ValueError as detail:
        try:
            fn = detail.filename
            line = detail.lineno
            error = detail.msg
        except AttributeError:
            fn = filename
            line = 1
            error = str(detail)
        return (True, fn, line, 0, "", error, [])
    except Exception as detail:
        try:
            fn = detail.filename
            line = detail.lineno
            error = detail.msg
            return (True, fn, line, 0, "", error, [])
        except:         # this catchall is intentional
            pass
    
    # pyflakes
    if not checkFlakes:
        return (False, "", -1, -1, "", "", [])
    
    strings = []
    lines = codestring.splitlines()
    try:
        warnings = Checker(module, filename)
        warnings.messages.sort(key=lambda a: a.lineno)
        for warning in warnings.messages:
            if ignoreStarImportWarnings and \
                    isinstance(warning, ImportStarUsed):
                continue
            
            _fn, lineno, col, message, msg_args = warning.getMessageData()
            if "__IGNORE_WARNING__" not in extractLineFlags(
                    lines[lineno - 1].strip()):
                strings.append([
                    "FLAKES_WARNING", _fn, lineno, col, message, msg_args])
    except SyntaxError as err:
        if err.text.strip():
            msg = err.text.strip()
        else:
            msg = err.msg
        strings.append(["FLAKES_ERROR", filename, err.lineno, 0, msg, ()])
    
    return (False, "", -1, -1, "", "", strings)
