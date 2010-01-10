# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Package implementing various functions/classes needed everywhere within eric5. 
"""

import os
import sys
import re
import fnmatch
import glob
import random
import base64

import warnings
warnings.filterwarnings("error", category=SyntaxWarning)

from codecs import BOM_UTF8, BOM_UTF16, BOM_UTF32

from PyQt4.QtCore import QRegExp, QDir, QProcess, Qt, \
    qVersion, PYQT_VERSION_STR, QCoreApplication
from PyQt4.Qsci import QSCINTILLA_VERSION_STR, QsciScintilla

from Globals import isWindowsPlatform   # import this method into the Utilities namespace

from E4Gui.E4Application import e4App

from UI.Info import Program, Version

from eric5config import getConfig
import Preferences

configDir = None

codingBytes_regexps = [
    (2, re.compile(br'''coding[:=]\s*([-\w_.]+)''')), 
    (1, re.compile(br'''<\?xml.*\bencoding\s*=\s*['"]([-\w_.]+)['"]\?>''')), 
]
coding_regexps = [
    (2, re.compile(r'''coding[:=]\s*([-\w_.]+)''')), 
    (1, re.compile(r'''<\?xml.*\bencoding\s*=\s*['"]([-\w_.]+)['"]\?>''')), 
]

supportedCodecs = ['utf-8', 
          'iso8859-1', 'iso8859-15', 'iso8859-2', 'iso8859-3', 
          'iso8859-4', 'iso8859-5', 'iso8859-6', 'iso8859-7', 
          'iso8859-8', 'iso8859-9', 'iso8859-10', 'iso8859-11', 
          'iso8859-13', 'iso8859-14', 'iso8859-16', 'latin-1', 
          'koi8-r', 'koi8-u', 
          'utf-16', 'utf-32', 
          'cp037', 'cp424', 'cp437', 'cp500', 'cp737', 'cp775', 
          'cp850', 'cp852', 'cp855', 'cp856', 'cp857', 'cp860', 
          'cp861', 'cp862', 'cp863', 'cp864', 'cp865', 'cp866', 
          'cp869', 'cp874', 'cp875', 'cp932', 'cp949', 'cp950', 
          'cp1006', 'cp1026', 'cp1140', 'cp1250', 'cp1251', 
          'cp1252', 'cp1253', 'cp1254', 'cp1255', 'cp1256', 
          'cp1257', 'cp1258', 
          'gb2312', 'gb18030', 
          'ascii']

class CodingError(Exception):
    """
    Class implementing an exception, which is raised, if a given coding is incorrect.
    """
    def __init__(self, coding):
        """
        Constructor
        """
        self.errorMessage = QApplication.translate("CodingError", 
            "The coding '{0}' is wrong for the given text.").format(coding)
        
    def __repr__(self):
        """
        Private method returning a representation of the exception.
        
        @return string representing the error message
        """
        return str(self.errorMessage)
        
    def __str__(self):
        """
        Private method returning a string representation of the exception.
        
        @return string representing the error message
        """
        return str(self.errorMessage)
    
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

def readEncodedFile(filename):
    """
    Function to read a file and decode it's contents into proper text.
    
    @param filename name of the file to read (string)
    @return tuple of decoded text and encoding (string, string)
    """
    f = open(filename, "rb")
    text = f.read()
    f.close()
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
    
    guess = None
    if Preferences.getEditor("AdvancedEncodingDetection"):
        # Try the universal character encoding detector
        try:
            import ThirdParty.CharDet.chardet
            guess = ThirdParty.CharDet.chardet.detect(text)
            if guess and guess['confidence'] > 0.95 and guess['encoding'] is not None:
                codec = guess['encoding'].lower()
                return str(text, codec), '%s-guessed' % codec
        except (UnicodeError, LookupError):
            pass
        except ImportError:
            pass
    
    # Try default encoding
    try:
        codec = Preferences.getEditor("DefaultEncoding")
        return str(text, codec), '%s-default' % codec
    except (UnicodeError, LookupError):
        pass
    
    # Assume UTF-8
    try:
        return str(text, 'utf-8'), 'utf-8-guessed'
    except (UnicodeError, LookupError):
        pass
    
    if Preferences.getEditor("AdvancedEncodingDetection"):
        # Use the guessed one even if confifence level is low
        if guess and guess['encoding'] is not None:
            try:
                codec = guess['encoding'].lower()
                return str(text, codec), '%s-guessed' % codec
            except (UnicodeError, LookupError):
                pass
    
    # Assume UTF-8 loosing information
    return str(text, "utf-8", "ignore"), 'utf-8-ignore'

def writeEncodedFile(filename, text, orig_coding):
    """
    Function to write a file with properly encoded text.
    
    @param filename name of the file to read (string)
    @param text text to be written (string)
    @param orig_coding type of the original encoding (string)
    @return encoding used for writing the file (string)
    """
    encoding = None
    if orig_coding == 'utf-8-bom':
        etext, encoding = BOM_UTF8 + text.encode("utf-8"), 'utf-8-bom'
    else:
        # Try declared coding spec
        coding = get_coding(text)
        if coding:
            try:
                etext, encoding = text.encode(coding), coding
            except (UnicodeError, LookupError):
                # Error: Declared encoding is incorrect
                raise CodingError(coding)
        else:
            if orig_coding and orig_coding.endswith(
                ('-selected', '-default', '-guessed', '-ignore')):
                coding = orig_coding\
                    .replace("-selected", "")\
                    .replace("-default", "")\
                    .replace("-guessed", "")\
                    .replace("-ignore", "")
                try:
                    etext, encoding = text.encode(coding), coding
                except (UnicodeError, LookupError):
                    pass
            
            if encoding is None:
                # Try configured default
                try:
                    codec = Preferences.getEditor("DefaultEncoding")
                    etext, encoding = text.encode(codec), codec
                except (UnicodeError, LookupError):
                    pass
                
                if encoding is None:
                    # Try saving as ASCII
                    try:
                        etext, encoding = text.encode('ascii'), 'ascii'
                    except UnicodeError:
                        pass
                    
                    if encoding is None:
                        # Save as UTF-8 without BOM
                        etext, encoding = text.encode('utf-8'), 'utf-8'
    
    f = open(filename, "wb")
    f.write(etext)
    f.close()
    
    return encoding
    
_escape = re.compile(eval(r'"[&<>\"\u0080-\uffff]"'))

_escape_map = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
}

def escape_entities(m, map=_escape_map):
    """
    Function to encode html entities.
    
    @param m the match object
    @param map the map of entities to encode
    @return the converted text (string)
    """
    char = m.group()
    text = map.get(char)
    if text is None:
        text = "&#%d;" % ord(char)
    return text
    
def html_encode(text, pattern=_escape):
    """
    Function to correctly encode a text for html.
    
    @param text text to be encoded (string)
    @param pattern search pattern for text to be encoded (string)
    @return the encoded text (string)
    """
    if not text:
        return ""
    text = pattern.sub(escape_entities, text)
    return text

_uescape = re.compile(r'[\u0080-\uffff]')

def escape_uentities(m):
    """
    Function to encode html entities.
    
    @param m the match object
    @return the converted text (string)
    """
    char = m.group()
    text = "&#%d;" % ord(char)
    return text
    
def html_uencode(text, pattern=_uescape):
    """
    Function to correctly encode a unicode text for html.
    
    @param text text to be encoded (string)
    @param pattern search pattern for text to be encoded (string)
    @return the encoded text (string)
    """
    if not text:
        return ""
    text = pattern.sub(escape_uentities, text)
    return text

def convertLineEnds(text, eol):
    """
    Function to convert the end of line characters.
    
    @param text text to be converted (string)
    @param eol new eol setting (string)
    @return text with converted eols (string)
    """
    if eol == '\r\n':
        regexp = re.compile(r"""(\r(?!\n)|(?<!\r)\n)""")
        return regexp.sub(lambda m, eol = '\r\n': eol, text)
    elif eol == '\n':
        regexp = re.compile(r"""(\r\n|\r)""")
        return regexp.sub(lambda m, eol = '\n': eol, text)
    elif eol == '\r':
        regexp = re.compile(r"""(\r\n|\n)""")
        return regexp.sub(lambda m, eol = '\r': eol, text)
    else:
        return text

def linesep():
    """
    Function to return the lineseparator used by the editor.
    
    @return line separator used by the editor (string)
    """
    eolMode = Preferences.getEditor("EOLMode")
    if eolMode == QsciScintilla.EolUnix:
        return "\n"
    elif eolMode == QsciScintilla.EolMac:
        return "\r"
    else:
        return "\r\n"

def toNativeSeparators(path):
    """
    Function returning a path, that is using native separator characters.
    
    @param path path to be converted (string)
    @return path with converted separator characters (string)
    """
    return QDir.toNativeSeparators(path)
    
def fromNativeSeparators(path):
    """
    Function returning a path, that is using "/" separator characters.
    
    @param path path to be converted (string)
    @return path with converted separator characters (string)
    """
    return QDir.fromNativeSeparators(path)
    
def normcasepath(path):
    """
    Function returning a path, that is normalized with respect to its case and references.
    
    @param path file path (string)
    @return case normalized path (string)
    """
    return os.path.normcase(os.path.normpath(path))
    
def normabspath(path):
    """
    Function returning a normalized, absolute path.
    
    @param path file path (string)
    @return absolute, normalized path (string)
    """
    return os.path.abspath(path)
    
def normcaseabspath(path):
    """
    Function returning an absolute path, that is normalized with respect to its case 
    and references.
    
    @param path file path (string)
    @return absolute, normalized path (string)
    """
    return os.path.normcase(os.path.abspath(path))
    
def normjoinpath(a, *p):
    """
    Function returning a normalized path of the joined parts passed into it.
    
    @param a first path to be joined (string)
    @param p variable number of path parts to be joind (string)
    @return normalized path (string)
    """
    return os.path.normpath(os.path.join(a, *p))
    
def normabsjoinpath(a, *p):
    """
    Function returning a normalized, absolute path of the joined parts passed into it.
    
    @param a first path to be joined (string)
    @param p variable number of path parts to be joind (string)
    @return absolute, normalized path (string)
    """
    return os.path.abspath(os.path.join(a, *p))
    
def relpath(path, start = os.path.curdir):
    """
    Return a relative version of a path.
    
    @param path path to make relative (string)
    @param start path to make relative from (string)
    """
    if not path:
        raise ValueError("no path specified")

    start_list = os.path.abspath(start).split(os.path.sep)
    path_list = os.path.abspath(path).split(os.path.sep)

    # Work out how much of the filepath is shared by start and path.
    i = len(os.path.commonprefix([start_list, path_list]))

    rel_list = [os.path.pardir] * (len(start_list) - i) + path_list[i:]
    if not rel_list:
        return os.path.curdir
    return os.path.join(*rel_list)

def isinpath(file):
    """
    Function to check for an executable file.
    
    @param file filename of the executable to check (string)
    @return flag to indicate, if the executable file is accessible
        via the searchpath defined by the PATH environment variable.
    """
    if os.path.isabs(file):
        return os.access(file, os.X_OK)
    
    path = getEnvironmentEntry('PATH')
    
    # environment variable not defined
    if path is None:
        return False
    
    dirs = path.split(os.pathsep)
    for dir in dirs:
        if os.access(os.path.join(dir, file), os.X_OK):
            return True
    
    return False
    
def getExecutablePath(file):
    """
    Function to build the full path of an executable file from the environment.
    
    @param file filename of the executable to check (string)
    @return full executable name, if the executable file is accessible
        via the searchpath defined by the PATH environment variable, or an
        empty string otherwise.
    """
    if os.path.isabs(file):
        if os.access(file, os.X_OK):
            return file
        else:
            return ""
        
    path = os.getenv('PATH')
    
    # environment variable not defined
    if path is None:
        return ""
        
    dirs = path.split(os.pathsep)
    for dir in dirs:
        exe = os.path.join(dir, file)
        if os.access(exe, os.X_OK):
            return exe
            
    return ""
    
def isExecutable(exe):
    """
    Function to check, if a file is executable.
    
    @param exe filename of the executable to check (string)
    @return flag indicating executable status (boolean)
    """
    return os.access(exe, os.X_OK)
    
def samepath(f1, f2):
    """
    Function to compare two paths.
    
    @param f1 first path for the compare (string)
    @param f2 second path for the compare (string)
    @return flag indicating whether the two paths represent the
        same path on disk.
    """
    if f1 is None or f2 is None:
        return False
    
    if normcaseabspath(os.path.realpath(f1)) == normcaseabspath(os.path.realpath(f2)):
        return True
    
    return False
    
try:
    EXTSEP = os.extsep
except AttributeError:
    EXTSEP = "."

def splitPath(name):
    """
    Function to split a pathname into a directory part and a file part.
    
    @param name path name (string)
    @return a tuple of 2 strings (dirname, filename).
    """
    if os.path.isdir(name):
        dn = os.path.abspath(name)
        fn = "."
    else:
        dn, fn = os.path.split(name)
    return (dn, fn)

def joinext(prefix, ext):
    """
    Function to join a file extension to a path.
    
    The leading "." of ext is replaced by a platform specific extension
    separator if necessary.
    
    @param prefix the basepart of the filename (string)
    @param ext the extension part (string)
    @return the complete filename (string)
    """
    if ext[0] != ".":
        ext = ".%s" % ext # require leading separator, to match os.path.splitext
    return prefix + EXTSEP + ext[1:]

def compactPath(path, width, measure = len):
    """
    Function to return a compacted path fitting inside the given width.
    
    @param path path to be compacted (string)
    @param width width for the compacted path (integer)
    @param measure reference to a function used to measure the length of the string
    @return compacted path (string)
    """
    if measure(path) <= width:
        return path
    
    ellipsis = '...'
    
    head, tail = os.path.split(path)
    while head:
        path = os.path.join("%s%s" % (head, ellipsis), tail)
        if measure(path) <= width:
            return path
        head = head[:-1]
    path = os.path.join(ellipsis, tail)
    if measure(path) <= width:
        return path
    while tail:
        path = "%s%s" % (ellipsis, tail)
        if measure(path) <= width:
            return path
        tail = tail[1:]
    return ""
    
def direntries(path, filesonly=False, pattern=None, followsymlinks=True, checkStop=None):
    """
    Function returning a list of all files and directories.
    
    @param path root of the tree to check
    @param filesonly flag indicating that only files are wanted
    @param pattern a filename pattern to check against
    @param followsymlinks flag indicating whether symbolic links
            should be followed
    @param checkStop function to be called to check for a stop
    @return list of all files and directories in the tree rooted
        at path. The names are expanded to start with path. 
    """
    if filesonly:
        files = []
    else:
        files = [path]
    try:
        entries = os.listdir(path)
        for entry in entries:
            if checkStop and checkStop():
                break
            
            if entry in ['CVS', '.svn', '_svn', '.hg', '.ropeproject']:
                continue
            
            fentry = os.path.join(path, entry)
            if pattern and \
            not os.path.isdir(fentry) and \
            not fnmatch.fnmatch(entry, pattern):
                # entry doesn't fit the given pattern
                continue
                
            if os.path.isdir(fentry):
                if os.path.islink(fentry) and not followsymlinks:
                    continue
                files += direntries(fentry, filesonly, pattern, followsymlinks, checkStop)
            else:
                files.append(fentry)
    except OSError:
        pass
    except UnicodeDecodeError:
        pass
    return files

def getDirs(path, excludeDirs):
    """
    Function returning a list of all directories below path.
    
    @param path root of the tree to check
    @param excludeDirs basename of directories to ignore
    @return list of all directories found
    """
    try:
        names = os.listdir(path)
    except EnvironmentError:
        return

    dirs = []
    for name in names:
        if os.path.isdir(os.path.join(path, name)) and \
          not os.path.islink(os.path.join(path, name)):
            exclude = 0
            for e in excludeDirs:
                if name.split(os.sep,1)[0] == e:
                    exclude = 1
                    break
            if not exclude:
                dirs.append(os.path.join(path, name))

    for name in dirs[:]:
        if not os.path.islink(name):
            dirs = dirs + getDirs(name, excludeDirs)

    return dirs

def getTestFileName(fn):
    """
    Function to build the filename of a unittest file.
    
    The filename for the unittest file is built by prepending
    the string "test" to the filename passed into this function.
    
    @param fn filename basis to be used for the unittest filename (string)
    @return filename of the corresponding unittest file (string)
    """
    dn, fn = os.path.split(fn)
    return os.path.join(dn, "test%s" % fn)

def parseOptionString(s):
    """
    Function used to convert an option string into a list of options.
    
    @param s option string (string or string)
    @return list of options (list of strings)
    """
    rx = QRegExp(r"""\s([^\s]+|"[^"]+"|'[^']+')""")
    s = re.sub(r"%[A-Z%]", _percentReplacementFunc, s)
    return parseString(s, rx)
    
def parseEnvironmentString(s):
    """
    Function used to convert an environment string into a list of environment settings.
    
    @param s environment string (string)
    @return list of environment settings (list of strings)
    """
    rx = QRegExp(r"""\s(\w+\+?=[^\s]+|\w+="[^"]+"|\w+='[^']+')""")
    return parseString(s, rx)

def parseString(s, rx):
    """
    Function used to convert a string into a list.
    
    @param s string to be parsed (string)
    @param rx regex defining the parse pattern (QRegExp)
    @return list of parsed data (list of strings)
    """
    olist = []
    if not s.startswith(' '):
        # prepare the  string to fit our pattern
        s = ' ' + s
        
    pos = rx.indexIn(s)
    while pos != -1:
        cs = rx.cap(1)
        if cs.startswith('"') or cs.startswith("'"):
            cs = cs[1:-1]
        olist.append(cs)
        pos += rx.matchedLength()
        pos = rx.indexIn(s, pos)
        
    return olist

def _percentReplacementFunc(matchobj):
    """
    Protected function called for replacing % codes.
    
    @param matchobj matchobject for the code
    @return replacement string
    """
    return getPercentReplacement(matchobj.group(0))
    
def getPercentReplacement(code):
    """
    Function to get the replacement for code.
    
    @param code code indicator (string)
    @return replacement string (string)
    """
    if code in ["C", "%C"]:
        # column of the cursor of the current editor
        aw = e4App().getObject("ViewManager").activeWindow()
        if aw is None:
            column = -1
        else:
            column = aw.getCursorPosition()[1]
        return "%d" % column
    elif code in ["D", "%D"]:
        # directory of active editor
        aw = e4App().getObject("ViewManager").activeWindow()
        if aw is None:
            dn = "not_available"
        else:
            fn = aw.getFileName()
            if fn is None:
                dn = "not_available"
            else:
                dn = os.path.dirname(fn)
        return dn
    elif code in ["F", "%F"]:
        # filename (complete) of active editor
        aw = e4App().getObject("ViewManager").activeWindow()
        if aw is None:
            fn = "not_available"
        else:
            fn = aw.getFileName()
            if fn is None:
                fn = "not_available"
        return fn
    elif code in ["H", "%H"]:
        # home directory
        return getHomeDir()
    elif code in ["L", "%L"]:
        # line of the cursor of the current editor
        aw = e4App().getObject("ViewManager").activeWindow()
        if aw is None:
            line = 0
        else:
            line = aw.getCursorPosition()[0] + 1
        return "%d" % line
    elif code in ["P", "%P"]:
        # project path
        projectPath = e4App().getObject("Project").getProjectPath()
        if not projectPath:
            projectPath = "not_available"
        return projectPath
    elif code in ["S", "%S"]:
        # selected text of the current editor
        aw = e4App().getObject("ViewManager").activeWindow()
        if aw is None:
            text = "not_available"
        else:
            text = aw.selectedText()
        return text
    elif code in ["U", "%U"]:
        # username
        un = getUserName()
        if un is None:
            return code
        else:
            return un
    elif code in ["%", "%%"]:
        # the percent sign
        return "%"
    else:
        # unknown code, just return it
        return code
    
def getPercentReplacementHelp():
    """
    Function to get the help text for the supported %-codes.
    
    @returns help text (string)
    """
    return QCoreApplication.translate("Utilities", 
        """<p>You may use %-codes as placeholders in the string."""
        """ Supported codes are:"""
        """<table>"""
        """<tr><td>%C</td><td>column of the cursor of the current editor</td></tr>"""
        """<tr><td>%D</td><td>directory of the current editor</td></tr>"""
        """<tr><td>%F</td><td>filename of the current editor</td></tr>"""
        """<tr><td>%H</td><td>home directory of the current user</td></tr>"""
        """<tr><td>%L</td><td>line of the cursor of the current editor</td></tr>"""
        """<tr><td>%P</td><td>path of the current project</td></tr>"""
        """<tr><td>%S</td><td>selected text of the current editor</td></tr>"""
        """<tr><td>%U</td><td>username of the current user</td></tr>"""
        """<tr><td>%%</td><td>the percent sign</td></tr>"""
        """</table>"""
        """</p>""")

def getUserName():
    """
    Function to get the user name.
    
    @return user name (string)
    """
    if isWindowsPlatform():
        return win32_GetUserName()
    else:
        return posix_GetUserName()

def getHomeDir():
    """
    Function to get a users home directory
    
    @return home directory (string)
    """
    return QDir.homePath()
    
def getPythonModulesDirectory():
    """
    Function to determine the path to Python's modules directory.
    
    @return path to the Python modules directory (string)
    """
    import distutils.sysconfig
    return distutils.sysconfig.get_python_lib(True)
    
def getPythonLibPath():
    """
    Function to determine the path to Python's library.
    
    @return path to the Python library (string)
    """
    pyFullVers = sys.version.split()[0]

    vl = re.findall("[0-9.]*", pyFullVers)[0].split(".")
    major = vl[0]
    minor = vl[1]

    pyVers = major + "." + minor
    pyVersNr = int(major) * 10 + int(minor)

    if isWindowsPlatform():
        libDir = sys.prefix + "\\Lib"
    else:
        try:
            syslib = sys.lib
        except AttributeError:
            syslib = "lib"
        libDir = sys.prefix + "/" + syslib + "/python" + pyVers
        
    return libDir
    
def getPythonVersion():
    """
    Function to get the Python version (major, minor) as an integer value.
    
    @return An integer representing major and minor version number (integer)
    """
    return sys.hexversion >> 16
    
def compile(file, codestring = ""):
    """
    Function to compile one Python source file to Python bytecode.
    
    @param file source filename (string)
    @param codestring string containing the code to compile (string)
    @return A tuple indicating status (True = an error was found), the
        filename, the linenumber, the code string and the error message
        (boolean, string, string, string, string). The values are only
        valid, if the status equals 1.
    """
    import builtins
    if not codestring:
        try:
            codestring = Utilities.readEncodedFile(file)[0]
        except (UnicodeDecodeError, IOError):
            return (False, None, None, None, None)

    codestring = codestring.replace("\r\n","\n")
    codestring = codestring.replace("\r","\n")

    if codestring and codestring[-1] != '\n':
        codestring = codestring + '\n'
    
    try:
        if file.endswith('.ptl'):
            try:
                import quixote.ptl_compile
            except ImportError:
                return (False, None, None, None, None)
            template = quixote.ptl_compile.Template(codestring, file)
            template.compile()
            codeobject = template.code
        else:
            codeobject = builtins.compile(codestring, file, 'exec')
    except SyntaxError as detail:
        import traceback, re
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
        return (True, fn, line, code, error)
    except ValueError as detail:
        try:
            fn = detail.filename
            line = detail.lineno
            error = detail.msg
        except AttributeError:
            fn = ""
            line = 1
            error = str(detail)
        code = ""
        return (True, fn, line, code, error)
    except Exception as detail:
        try:
            fn = detail.filename
            line = detail.lineno
            code = ""
            error = detail.msg
            return (True, fn, line, code, error)
        except:         # this catchall is intentional
            pass
    
    return (False, None, None, None, None)

def getConfigDir():
    """
    Module function to get the name of the directory storing the config data.
    
    @return directory name of the config dir (string)
    """
    if configDir is not None and os.path.exists(configDir):
        hp = configDir
    else:
        if isWindowsPlatform():
            cdn = "_eric5"
        else:
            cdn = ".eric5"
            
        hp = QDir.homePath()
        dn = QDir(hp)
        dn.mkdir(cdn)
        hp += "/" + cdn
    return toNativeSeparators(hp)

def setConfigDir(d):
    """
    Module function to set the name of the directory storing the config data.
    
    @param d name of an existing directory (string)
    """
    global configDir
    configDir = os.path.expanduser(d)

################################################################################
# functions for environment handling
################################################################################

def getEnvironmentEntry(key, default = None):
    """
    Module function to get an environment entry.
    
    @param key key of the requested environment entry (string)
    @param default value to be returned, if the environment doesn't contain
        the requested entry (string)
    @return the requested entry or the default value, if the entry wasn't 
        found (string or None)
    """
    filter = QRegExp("^%s[ \t]*=" % key)
    if isWindowsPlatform():
        filter.setCaseSensitivity(Qt.CaseInsensitive)
    
    entries = [e for e in QProcess.systemEnvironment() if filter.indexIn(e) != -1]
    if not entries:
        return default
    
    # if there are multiple entries, just consider the first one
    ename, val = entries[0].split("=", 1)
    return val.strip()

def hasEnvironmentEntry(key):
    """
    Module function to check, if the environment contains an entry.
    
    @param key key of the requested environment entry (string)
    @return flag indicating the presence of the requested entry (boolean)
    """
    filter = QRegExp("^%s[ \t]*=" % key)
    if isWindowsPlatform():
        filter.setCaseSensitivity(Qt.CaseInsensitive)
    
    entries = [e for e in QProcess.systemEnvironment() if filter.indexIn(e) != -1]
    return len(entries) > 0

################################################################################
# Qt utility functions below
################################################################################

def generateQtToolName(toolname):
    """
    Module function to generate the executable name for a Qt tool like designer.
    
    @param toolname base name of the tool (string)
    @return the Qt tool name without extension (string)
    """
    return "%s%s%s" % (Preferences.getQt("QtToolsPrefix4"), 
                       toolname, 
                       Preferences.getQt("QtToolsPostfix4")
                      )

def prepareQtMacBundle(toolname, version, args):
    """
    Module function for starting Qt tools that are Mac OS X bundles.

    @param toolname  plain name of the tool (e.g. "designer") (string)
    @param version indication for the requested version (Qt 4) (integer)
    @param args    name of input file for tool, if any (list of strings)
    @return command-name and args for QProcess (tuple)
    """
    if version == 4:
        qtDir = Preferences.getQt("Qt4Dir")
    else:
        return ("", [])
    
    fullBundle = os.path.join(qtDir, 'bin',
        generateQtToolName(toolname)) + ".app"

    newArgs = []
    newArgs.append("-a")
    newArgs.append(fullBundle)
    newArgs += args

    return ("open", newArgs)

################################################################################
# Other utility functions below
################################################################################

def generateVersionInfo(linesep = '\n'):
    """
    Module function to generate a string with various version infos.
    
    @param linesep string to be used to separate lines (string)
    @return string with version infos (string)
    """
    try:
        import sipconfig
        sip_version_str = sipconfig.Configuration().sip_version_str
    except ImportError:
        sip_version_str = "sip version not available"
    
    info =  "Version Numbers:%s  Python %s%s" % \
        (linesep, sys.version.split()[0], linesep)
    info += "  Qt %s%s  PyQt4 %s%s" % \
        (qVersion(), linesep, PYQT_VERSION_STR, linesep)
    info += "  sip %s%s  QScintilla %s%s" % \
        (sip_version_str, linesep, QSCINTILLA_VERSION_STR, linesep)
    info += "  %s %s%s" % \
        (Program, Version, linesep * 2)
    info += "Platform: %s%s%s%s" % \
        (sys.platform, linesep, sys.version, linesep)
    
    return info

def generatePluginsVersionInfo(linesep = '\n'):
    """
    Module function to generate a string with plugins version infos.
    
    @param linesep string to be used to separate lines (string)
    @return string with plugins version infos (string)
    """
    infoStr = ""
    app = e4App()
    if app is not None:
        try:
            pm = app.getObject("PluginManager")
            versions = {}
            for info in pm.getPluginInfos():
                versions[info[0]] = info[2]
            
            infoStr = "Plugins Version Numbers:%s" % linesep
            for pluginName in sorted(versions.keys()):
                infoStr += "  %s %s%s" % (pluginName, versions[pluginName], linesep)
        except KeyError:
            pass
    
    return infoStr

def generateDistroInfo(linesep = '\n'):
    """
    Module function to generate a string with distribution infos.
    
    @param linesep string to be used to separate lines (string)
    @return string with plugins version infos (string)
    """
    infoStr = ""
    if sys.platform.startswith("linux"):
        releaseList = glob.glob("/etc/*-release")
        if releaseList:
            infoStr = "Distribution Info:%s" % linesep
            infoParas = []
            for rfile in releaseList:
                try:
                    f = open(rfile, "r")
                    lines = f.read().splitlines()
                    f.close
                except IOError:
                    continue
                
                lines.insert(0, rfile)
                infoParas.append('  ' + (linesep + '  ').join(lines))
            infoStr += (linesep + linesep).join(infoParas)
    
    return infoStr

################################################################################
# password handling functions below
################################################################################

def pwEncode(pw):
    """
    Module function to encode a password.
    
    @param pw password to encode (string)
    @return encoded password (string)
    """
    pop = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,;:-_!$?*+#"
    marker = "CE4"
    rpw = "".join(random.sample(pop, 32)) + pw + "".join(random.sample(pop, 32))
    return marker + base64.b64encode(rpw.encode()).decode()

def pwDecode(epw):
    """
    Module function to decode a password.
    
    @param pw encoded password to decode (string)
    @return decoded password (string)
    """
    if not epw.startswith("CE4"):
        return epw  # it was not encoded using pwEncode
    
    return base64.b64decode(epw[3:].encode())[32:-32].decode()

################################################################################
# posix compatibility functions below
################################################################################

def posix_GetUserName():
    """
    Function to get the user name under Posix systems.
    
    @return user name (string)
    """
    try:
        import pwd
        return pwd.getpwuid(os.getuid())[0]
    except ImportError:
        try:
            u = getEnvironmentEntry('USER')
        except KeyError:
            u = getEnvironmentEntry('user', None)
        return u

################################################################################
# win32 compatibility functions below
################################################################################

def win32_Kill(pid):
    """
    Function to provide an os.kill equivalent for Win32.
    
    @param pid process id
    """
    import win32api
    handle = win32api.OpenProcess(1, 0, pid)
    return (0 != win32api.TerminateProcess(handle, 0))

def win32_GetUserName():
    """
    Function to get the user name under Win32.
    
    @return user name (string)
    """
    try:
        import win32api
        return win32api.GetUserName()
    except ImportError:
        try:
            u = getEnvironmentEntry('USERNAME')
        except KeyError:
            u = getEnvironmentEntry('username', None)
        return u
