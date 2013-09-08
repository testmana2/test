# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the syntax check for Python 2/3.
"""

import sys
if sys.version_info[0] >= 3:
    if __name__ == '__main__':
        from py3flakes.checker import Checker
        from py3flakes.messages import ImportStarUsed
    else:
        from .py3flakes.checker import Checker      #__IGNORE_WARNING__
        from .py3flakes.messages import ImportStarUsed      #__IGNORE_WARNING__
else:
    str = unicode      #__IGNORE_WARNING__
    if __name__ == '__main__':
        from py2flakes.checker import Checker      #__IGNORE_WARNING__
        from py2flakes.messages import ImportStarUsed      #__IGNORE_WARNING__
    else:
        from .py2flakes.checker import Checker      #__IGNORE_WARNING__
        from .py2flakes.messages import ImportStarUsed      #__IGNORE_WARNING__

import re
import traceback
from codecs import BOM_UTF8, BOM_UTF16, BOM_UTF32

try:
    import Preferences
except (ImportError):
    pass

codingBytes_regexps = [
    (2, re.compile(br'''coding[:=]\s*([-\w_.]+)''')),
    (1, re.compile(br'''<\?xml.*\bencoding\s*=\s*['"]([-\w_.]+)['"]\?>''')),
]


def get_codingBytes(text):
    """
    Function to get the coding of a bytes text.
    
    @param text bytes text to inspect (bytes)
    @return coding string
    """
    lines = text.splitlines()
    for coding in codingBytes_regexps:
        coding_re = coding[1]
        head = lines[:coding[0]]
        for l in head:
            m = coding_re.search(l)
            if m:
                return str(m.group(1), "ascii").lower()
    return None


def decode(text):
    """
    Function to decode some byte text into a string.
    
    @param text byte text to decode (bytes)
    @return tuple of decoded text and encoding (string, string)
    """
    try:
        if text.startswith(BOM_UTF8):
            # UTF-8 with BOM
            return str(text[len(BOM_UTF8):], 'utf-8'), 'utf-8-bom'
        elif text.startswith(BOM_UTF16):
            # UTF-16 with BOM
            return str(text[len(BOM_UTF16):], 'utf-16'), 'utf-16'
        elif text.startswith(BOM_UTF32):
            # UTF-32 with BOM
            return str(text[len(BOM_UTF32):], 'utf-32'), 'utf-32'
        coding = get_codingBytes(text)
        if coding:
            return str(text, coding), coding
    except (UnicodeError, LookupError):
        pass
    
    # Assume UTF-8
    try:
        return str(text, 'utf-8'), 'utf-8-guessed'
    except (UnicodeError, LookupError):
        pass
    
    try:
        guess = None
        if Preferences.getEditor("AdvancedEncodingDetection"):
            # Try the universal character encoding detector
            try:
                import ThirdParty.CharDet.chardet
                guess = ThirdParty.CharDet.chardet.detect(text)
                if guess and guess['confidence'] > 0.95 and guess['encoding'] is not None:
                    codec = guess['encoding'].lower()
                    return str(text, codec), '{0}-guessed'.format(codec)
            except (UnicodeError, LookupError, ImportError):
                pass
    except (NameError):
        pass
    
    # Try default encoding
    try:
        codec = Preferences.getEditor("DefaultEncoding")
        return str(text, codec), '{0}-default'.format(codec)
    except (UnicodeError, LookupError, NameError):
        pass
    
    try:
        if Preferences.getEditor("AdvancedEncodingDetection"):
            # Use the guessed one even if confifence level is low
            if guess and guess['encoding'] is not None:
                try:
                    codec = guess['encoding'].lower()
                    return str(text, codec), '{0}-guessed'.format(codec)
                except (UnicodeError, LookupError):
                    pass
    except (NameError):
        pass
    
    # Assume UTF-8 loosing information
    return str(text, "utf-8", "ignore"), 'utf-8-ignore'


def readEncodedFile(filename):
    """
    Function to read a file and decode it's contents into proper text.
    
    @param filename name of the file to read (string)
    @return tuple of decoded text and encoding (string, string)
    """
    try:
        filename = filename.encode(sys.getfilesystemencoding())
    except (UnicodeDecodeError):
        pass
    f = open(filename, "rb")
    text = f.read()
    f.close()
    return decode(text)


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
        except:
            pass
    
    return codestring


def extractLineFlags(line, startComment="#", endComment=""):
    """
    Function to extract flags starting and ending with '__' from a line comment.
    
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


def compile_and_check(file_, codestring="", checkFlakes=True, ignoreStarImportWarnings=False):
    """
    Function to compile one Python source file to Python bytecode
    and to perform a pyflakes check.
    
    @param file_ source filename (string)
    @param codestring string containing the code to compile (string)
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
            file_enc = file_.encode(sys.getfilesystemencoding())
        else:
            file_enc = file_
        
        if not codestring:
            try:
                codestring = readEncodedFile(file_)[0]
            except (UnicodeDecodeError, IOError):
                return (False, None, None, None, None, None, [])
        
        codestring = normalizeCode(codestring)
        
        if file_.endswith('.ptl'):
            try:
                import quixote.ptl_compile
            except ImportError:
                return (False, None, None, None, None, None, [])
            template = quixote.ptl_compile.Template(codestring, file_enc)
            template.compile()
        
        # ast.PyCF_ONLY_AST = 1024, speed optimisation
        module = builtins.compile(codestring, file_enc, 'exec',  1024)
    except SyntaxError as detail:
        index = 0
        code = ""
        error = ""
        lines = traceback.format_exception_only(SyntaxError, detail)
        match = re.match('\s*File "(.+)", line (\d+)',
            lines[0].replace('<string>', '{0}'.format(file_)))
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
        index = 0
        code = ""
        try:
            fn = detail.filename
            line = detail.lineno
            error = detail.msg
        except AttributeError:
            fn = file_
            line = 1
            error = str(detail)
        return (True, fn, line, index, code, error, [])
    except Exception as detail:
        try:
            fn = detail.filename
            line = detail.lineno
            index = 0
            code = ""
            error = detail.msg
            return (True, fn, line, index, code, error, [])
        except:         # this catchall is intentional
            pass
    
    # pyflakes
    if not checkFlakes:
        return (False, "", -1, -1, "", "", [])
    
    strings = []
    lines = codestring.splitlines()
    try:
        warnings = Checker(module, file_)
        warnings.messages.sort(key=lambda a: a.lineno)
        for warning in warnings.messages:
            if ignoreStarImportWarnings and \
                isinstance(warning, ImportStarUsed):
                    continue
            
            _fn, lineno, message, msg_args = warning.getMessageData()
            if "__IGNORE_WARNING__" not in extractLineFlags(lines[lineno - 1].strip()):
                strings.append(["FLAKES_WARNING", _fn, lineno, message, msg_args])
    except SyntaxError as err:
        if err.text.strip():
            msg = err.text.strip()
        else:
            msg = err.msg
        strings.append(["FLAKES_ERROR", file_, err.lineno, msg, ()])
    
    return (False, "", -1, -1, "", "", strings)


if __name__ == "__main__":
    if len(sys.argv) < 2 or \
       len(sys.argv) > 3 or \
       (len(sys.argv) == 3 and sys.argv[1] not in ["-fi", "-fs"]):
        print("ERROR")
        print("")
        print("")
        print("")
        print("")
        print("No file name given.")
    else:
        filename = sys.argv[-1]
        checkFlakes = len(sys.argv) == 3
        ignoreStarImportWarnings = sys.argv[1] == "-fi"     # Setting is ignored if checkFlakes is False
        
        try:
            codestring = readEncodedFile(filename)[0]
            
            syntaxerror, fname, line, index, code, error, warnings = \
                compile_and_check(filename, codestring, checkFlakes, ignoreStarImportWarnings)
        except IOError as msg:
            # fake a syntax error
            syntaxerror, fname, line, index, code, error, warnings = \
                True, filename, 1, 0, "", "I/O Error: %s" % str(msg), []
        
        if syntaxerror:
            print("ERROR")
        else:
            print("NO_ERROR")
        print(fname)
        print(line)
        print(index)
        print(code)
        print(error)
        
        if not syntaxerror:
            for warningLine in warnings:
                msg_args = warningLine.pop()
                for warning in warningLine:
                    print(warning)
                msg_args = [str(x) for x in msg_args]
                print('#'.join(msg_args))
    
    sys.exit(0)
