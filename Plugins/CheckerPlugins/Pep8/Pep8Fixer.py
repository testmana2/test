# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a class to fix certain PEP 8 issues.
"""

import os
import re
import tokenize
import io

from PyQt4.QtCore import QObject

from E5Gui import E5MessageBox

from . import pep8

import Utilities

Pep8FixableIssues = ["E101", "E111", "E121", "E122", "E123", "E124",
                     "E125", "E126", "E127", "E128", "E133", "W191",
                     "E201", "E202", "E203", "E211", "E221", "E222",
                     "E223", "E224", "E225", "E226", "E227", "E228",
                     "E231", "E241", "E242", "E251", "E261", "E262",
                     "E271", "E272", "E273", "E274", "W291", "W292",
                     "W293", "E301", "E302", "E303", "E304", "W391",
                     "E401", "E502", "W603", "E701", "E702", "E703",
                     "E711", "E712"
                    ]


class Pep8Fixer(QObject):
    """
    Class implementing a fixer for certain PEP 8 issues.
    """
    def __init__(self, project, filename, sourceLines, fixCodes, noFixCodes,
                 maxLineLength, inPlace):
        """
        Constructor
        
        @param project  reference to the project object (Project)
        @param filename name of the file to be fixed (string)
        @param sourceLines list of source lines including eol marker
            (list of string)
        @param fixCodes list of codes to be fixed as a comma separated
            string (string)
        @param noFixCodes list of codes not to be fixed as a comma
            separated string (string)
        @param maxLineLength maximum allowed line length (integer)
        @param inPlace flag indicating to modify the file in place (boolean)
        """
        super().__init__()
        
        self.__project = project
        self.__filename = filename
        self.__origName = ""
        self.__source = sourceLines[:]  # save a copy
        self.__fixCodes = [c.strip() for c in fixCodes.split(",") if c.strip()]
        self.__noFixCodes = [c.strip() for c in noFixCodes.split(",") if c.strip()]
        self.__maxLineLength = maxLineLength
        self.fixed = 0
        
        self.__reindenter = None
        self.__eol = ""
        self.__indentWord = self.__getIndentWord()
        
        if not inPlace:
            self.__origName = self.__filename
            self.__filename = os.path.join(os.path.dirname(self.__filename),
                "fixed_" + os.path.basename(self.__filename))
        
        self.__fixes = {
            "E101": self.__fixE101,
            "E111": self.__fixE101,
            "E121": self.__fixE121,
            "E122": self.__fixE122,
            "E123": self.__fixE123,
            "E124": self.__fixE121,
            "E125": self.__fixE125,
            "E126": self.__fixE126,
            "E127": self.__fixE127,
            "E128": self.__fixE127,
            "E133": self.__fixE126,
            "W191": self.__fixE101,
            "E201": self.__fixE201,
            "E202": self.__fixE201,
            "E203": self.__fixE201,
            "E211": self.__fixE201,
            "E221": self.__fixE221,
            "E222": self.__fixE221,
            "E223": self.__fixE221,
            "E224": self.__fixE221,
            "E225": self.__fixE221,
            "E226": self.__fixE221,
            "E227": self.__fixE221,
            "E228": self.__fixE221,
            "E231": self.__fixE231,
            "E241": self.__fixE221,
            "E242": self.__fixE221,
            "E251": self.__fixE251,
            "E261": self.__fixE261,
            "E262": self.__fixE261,
            "E271": self.__fixE221,
            "E272": self.__fixE221,
            "E273": self.__fixE221,
            "E274": self.__fixE221,
            "W291": self.__fixW291,
            "W292": self.__fixW292,
            "W293": self.__fixW291,
            "E301": self.__fixE301,
            "E302": self.__fixE302,
            "E303": self.__fixE303,
            "E304": self.__fixE304,
            "W391": self.__fixW391,
            "E401": self.__fixE401,
            "E502": self.__fixE502,
            "W603": self.__fixW603,
            "E701": self.__fixE701,
            "E702": self.__fixE702,
            "E703": self.__fixE702,
            "E711": self.__fixE711,
            "E712": self.__fixE711,
        }
        self.__modified = False
        self.__stackLogical = []    # these need to be fixed before the file
                                    # is saved but after all other inline
                                    # fixes. These work with logical lines.
        self.__stack = []           # these need to be fixed before the file
                                    # is saved but after all inline fixes
    
    def saveFile(self, encoding):
        """
        Public method to save the modified file.
        
        @param encoding encoding of the source file (string)
        @return flag indicating success (boolean)
        """
        if not self.__modified:
            # no need to write
            return True
        
        # apply deferred fixes
        self.__finalize()
        
        txt = "".join(self.__source)
        try:
            Utilities.writeEncodedFile(self.__filename, txt, encoding)
        except (IOError, Utilities.CodingError, UnicodeError) as err:
            E5MessageBox.critical(self,
                self.trUtf8("Fix PEP 8 issues"),
                self.trUtf8(
                    """<p>Could not save the file <b>{0}</b>."""
                    """ Skipping it.</p><p>Reason: {1}</p>""")
                    .format(self.__filename, str(err))
            )
            return False
        
        return True
    
    def __codeMatch(self, code):
        """
        Private method to check, if the code should be fixed.
        
        @param code to check (string)
        @return flag indicating it should be fixed (boolean)
        """
        def mutualStartswith(a, b):
            """
            Local helper method to compare the beginnings of two strings
            against each other.
            
            @return flag indicating that one string starts with the other
                (boolean)
            """
            return b.startswith(a) or a.startswith(b)
        
        if self.__noFixCodes:
            for noFixCode in [c.strip() for c in self.__noFixCodes]:
                if mutualStartswith(code.lower(), noFixCode.lower()):
                    return False

        if self.__fixCodes:
            for fixCode in [c.strip() for c in self.__fixCodes]:
                if mutualStartswith(code.lower(), fixCode.lower()):
                    return True
            return False

        return True
    
    def fixIssue(self, line, pos, message):
        """
        Public method to fix the fixable issues.
        
        @param line line number of issue (integer)
        @param pos character position of issue (integer)
        @param message message text (string)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        code = message.split(None, 1)[0].strip()
        
        if line <= len(self.__source) and \
           self.__codeMatch(code) and \
           code in self.__fixes:
            res = self.__fixes[code](code, line, pos)
            if res[0]:
                self.__modified = True
                self.fixed += 1
        else:
            res = (False, "")
        
        return res
    
    def __finalize(self):
        """
        Private method to apply all deferred fixes.
        """
        # step 1: do fixes operating on logical lines first
        for code, line, pos in self.__stackLogical:
            self.__fixes[code](code, line, pos, apply=True)
        
        # step 2: do fixes that change the number of lines
        for code, line, pos in reversed(self.__stack):
            self.__fixes[code](code, line, pos, apply=True)
    
    def __getEol(self):
        """
        Private method to get the applicable eol string.
        
        @return eol string (string)
        """
        if not self.__eol:
            if self.__origName:
                fn = self.__origName
            else:
                fn = self.__filename
            
            if self.__project.isOpen() and self.__project.isProjectFile(fn):
                self.__eol = self.__project.getEolString()
            else:
                self.__eol = Utilities.linesep()
        return self.__eol
    
    def __findLogical(self):
        """
        Private method to extract the index of all the starts and ends of lines.
        
        @return tuple containing two lists of integer with start and end tuples
            of lines
        """
        logical_start = []
        logical_end = []
        last_newline = True
        sio = io.StringIO("".join(self.__source))
        parens = 0
        for t in tokenize.generate_tokens(sio.readline):
            if t[0] in [tokenize.COMMENT, tokenize.DEDENT,
                        tokenize.INDENT, tokenize.NL,
                        tokenize.ENDMARKER]:
                continue
            if not parens and t[0] in [tokenize.NEWLINE, tokenize.SEMI]:
                last_newline = True
                logical_end.append((t[3][0] - 1, t[2][1]))
                continue
            if last_newline and not parens:
                logical_start.append((t[2][0] - 1, t[2][1]))
                last_newline = False
            if t[0] == tokenize.OP:
                if t[1] in '([{':
                    parens += 1
                elif t[1] in '}])':
                    parens -= 1
        return logical_start, logical_end
    
    def __getLogical(self, line, pos):
        """
        Private method to get the logical line corresponding to the given
        position.
        
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return tuple of a tuple of two integers giving the start of the
            logical line, another tuple of two integers giving the end
            of the logical line and a list of strings with the original
            source lines
        """
        try:
            (logical_start, logical_end) = self.__findLogical()
        except (SyntaxError, tokenize.TokenError):
            return None

        line = line - 1
        ls = None
        le = None
        for i in range(0, len(logical_start)):
            x = logical_end[i]
            if x[0] > line or (x[0] == line and x[1] > pos):
                le = x
                ls = logical_start[i]
                break
        if ls is None:
            return None
        
        original = self.__source[ls[0]:le[0] + 1]
        return ls, le, original
    
    def __getIndentWord(self):
        """
        Private method to determine the indentation type.
        
        @return string to be used for an indentation (string)
        """
        sio = io.StringIO("".join(self.__source))
        indentWord = "    "     # default in case of failure
        try:
            for token in tokenize.generate_tokens(sio.readline):
                if token[0] == tokenize.INDENT:
                    indentWord = token[1]
                    break
        except (SyntaxError, tokenize.TokenError):
            pass
        return indentWord
    
    def __getIndent(self, line):
        """
        Private method to get the indentation string.
        
        @param line line to determine the indentation string from (string)
        @return indentation string (string)
        """
        return line.replace(line.lstrip(), "")
    
    def __fixReindent(self, line, pos, logical):
        """
        Private method to fix a badly indented line.

        This is done by adding or removing from its initial indent only.
        
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return flag indicating a change was done (boolean)
        """
        assert logical
        ls, _, original = logical

        rewrapper = Pep8IndentationWrapper(original)
        valid_indents = rewrapper.pep8Expected()
        if not rewrapper.rel_indent:
            return False
        
        if line > ls[0]:
            # got a valid continuation line number
            row = line - ls[0] - 1
            # always pick the first option for this
            valid = valid_indents[row]
            got = rewrapper.rel_indent[row]
        else:
            return False
        
        line1 = ls[0] + row
        # always pick the expected indent, for now.
        indent_to = valid[0]

        if got != indent_to:
            orig_line = self.__source[line1]
            new_line = ' ' * (indent_to) + orig_line.lstrip()
            if new_line == orig_line:
                return False
            else:
                self.__source[line1] = new_line
                return True
        else:
            return False
    
    def __fixWhitespace(self, line, offset, replacement):
        """
        Private method to correct whitespace at the given offset.
        
        @param line line to be corrected (string)
        @param offset offset within line (integer)
        @param replacement replacement string (string)
        @return corrected line
        """
        left = line[:offset].rstrip(" \t")
        right = line[offset:].lstrip(" \t")
        if right.startswith("#"):
            return line
        else:
            return left + replacement + right
    
    def __fixE101(self, code, line, pos):
        """
        Private method to fix obsolete tab usage and indentation errors
        (E101, E111, W191).
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        if self.__reindenter is None:
            self.__reindenter = Pep8Reindenter(self.__source)
            self.__reindenter.run()
        fixedLine = self.__reindenter.fixedLine(line - 1)
        if fixedLine is not None:
            self.__source[line - 1] = fixedLine
            if code in ["E101", "W191"]:
                msg = self.trUtf8("Tab converted to 4 spaces.")
            else:
                msg = self.trUtf8("Indentation adjusted to be a multiple of four.")
            return (True, msg)
        else:
            return (False, self.trUtf8("Fix for {0} failed.").format(code))
    
    def __fixE121(self, code, line, pos, apply=False):
        """
        Private method to fix the indentation of continuation lines and
        closing brackets (E121,E124).
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        if apply:
            logical = self.__getLogical(line, pos)
            if logical:
                # Fix by adjusting initial indent level.
                self.__fixReindent(line, pos, logical)
        else:
            self.__stackLogical.append((code, line, pos))
        if code == "E121":
            msg = self.trUtf8("Indentation of continuation line corrected.")
        elif code == "E124":
            msg = self.trUtf8("Indentation of closing bracket corrected.")
        return (True, msg)
    
    def __fixE122(self, code, line, pos, apply=False):
        """
        Private method to fix a missing indentation of continuation lines (E122).
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        if apply:
            logical = self.__getLogical(line, pos)
            if logical:
                # Fix by adding an initial indent.
                modified = self.__fixReindent(line, pos, logical)
                if not modified:
                    # fall back to simple method
                    line = line - 1
                    text = self.__source[line]
                    indentation = self.__getIndent(text)
                    self.__source[line] = indentation + \
                        self.__indentWord + text.lstrip()
        else:
            self.__stackLogical.append((code, line, pos))
        return (True, self.trUtf8("Missing indentation of continuation line corrected."))
    
    def __fixE123(self, code, line, pos, apply=False):
        """
        Private method to fix the indentation of a closing bracket lines (E123).
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        if apply:
            logical = self.__getLogical(line, pos)
            if logical:
                # Fix by deleting whitespace to the correct level.
                logicalLines = logical[2]
                row = line - 1
                text = self.__source[row]
                newText = self.__getIndent(logicalLines[0]) + text.lstrip()
                if newText == text:
                    # fall back to slower method
                    self.__fixReindent(line, pos, logical)
                else:
                    self.__source[row] = newText
        else:
            self.__stackLogical.append((code, line, pos))
        return (True, self.trUtf8("Closing bracket aligned to opening bracket."))
    
    def __fixE125(self, code, line, pos, apply=False):
        """
        Private method to fix the indentation of continuation lines not
        distinguishable from next logical line (E125).
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        if apply:
            logical = self.__getLogical(line, pos)
            if logical:
                # Fix by adjusting initial indent level.
                modified = self.__fixReindent(line, pos, logical)
                if not modified:
                    row = line - 1
                    text = self.__source[row]
                    self.__source[row] = self.__getIndent(text) + \
                        self.__indentWord + text.lstrip()
        else:
            self.__stackLogical.append((code, line, pos))
        return (True, self.trUtf8("Indentation level changed."))
    
    def __fixE126(self, code, line, pos, apply=False):
        """
        Private method to fix over-indented/under-indented hanging
        indentation (E126, E133).
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        if apply:
            logical = self.__getLogical(line, pos)
            if logical:
                # Fix by deleting whitespace to the left.
                logicalLines = logical[2]
                row = line - 1
                text = self.__source[row]
                newText = self.__getIndent(logicalLines[0]) + \
                    self.__indentWord + text.lstrip()
                if newText == text:
                    # fall back to slower method
                    self.__fixReindent(line, pos, logical)
                else:
                    self.__source[row] = newText
        else:
            self.__stackLogical.append((code, line, pos))
        return (True, self.trUtf8("Indentation level of hanging indentation changed."))
    
    def __fixE127(self, code, line, pos, apply=False):
        """
        Private method to fix over/under indented lines (E127, E128).
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        if apply:
            logical = self.__getLogical(line, pos)
            if logical:
                # Fix by inserting/deleting whitespace to the correct level.
                logicalLines = logical[2]
                row = line - 1
                text = self.__source[row]
                newText = text
                
                if logicalLines[0].rstrip().endswith('\\'):
                    newText = self.__getIndent(logicalLines[0]) + \
                        self.__indentWord + text.lstrip()
                else:
                    startIndex = None
                    for symbol in '([{':
                        if symbol in logicalLines[0]:
                            foundIndex = logicalLines[0].find(symbol) + 1
                            if startIndex is None:
                                startIndex = foundIndex
                            else:
                                startIndex = min(startIndex, foundIndex)

                    if startIndex is not None:
                        newText = startIndex * ' ' + text.lstrip()
                    
                if newText == text:
                    # fall back to slower method
                    self.__fixReindent(line, pos, logical)
                else:
                    self.__source[row] = newText
        else:
            self.__stackLogical.append((code, line, pos))
        return (True, self.trUtf8("Visual indentation corrected."))
    
    def __fixE201(self, code, line, pos):
        """
        Private method to fix extraneous whitespace (E201, E202,
        E203, E211).
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        line = line - 1
        text = self.__source[line]
        
        if '"""' in text or "'''" in text or text.rstrip().endswith('\\'):
            return (False, self.trUtf8("Extraneous whitespace cannot be removed."))
        
        newText = self.__fixWhitespace(text, pos, '')
        if newText == text:
            return (False, "")
        
        self.__source[line] = newText
        return (True, self.trUtf8("Extraneous whitespace removed."))
    
    def __fixE221(self, code, line, pos):
        """
        Private method to fix extraneous whitespace around operator or
        keyword (E221, E222, E223, E224, E225, E226, E227, E228, E241,
        E242, E271, E272, E273, E274).
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        line = line - 1
        text = self.__source[line]
        
        if '"""' in text or "'''" in text or text.rstrip().endswith('\\'):
            return (False, self.trUtf8("Extraneous whitespace cannot be removed."))
        
        newText = self.__fixWhitespace(text, pos, ' ')
        if newText == text:
            return (False, "")
        
        self.__source[line] = newText
        if code in ["E225", "E226", "E227", "E228"]:
            return (True, self.trUtf8("Missing whitespace added."))
        else:
            return (True, self.trUtf8("Extraneous whitespace removed."))
    
    def __fixE231(self, code, line, pos):
        """
        Private method to fix missing whitespace after ',;:'.
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        line = line - 1
        pos = pos + 1
        self.__source[line] = self.__source[line][:pos] + \
                               " " + \
                               self.__source[line][pos:]
        return (True, self.trUtf8("Missing whitespace added."))
    
    def __fixE251(self, code, line, pos):
        """
        Private method to fix extraneous whitespace around keyword and
        default parameter equals (E251).
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        line = line - 1
        text = self.__source[line]
        
        # This is necessary since pep8 sometimes reports columns that goes
        # past the end of the physical line. This happens in cases like,
        # foo(bar\n=None)
        col = min(pos, len(text) - 1)
        if text[col].strip():
            newText = text
        else:
            newText = text[:col].rstrip() + text[col:].lstrip()
        
        # There could be an escaped newline
        #
        #     def foo(a=\
        #             1)
        if newText.endswith(('=\\\n', '=\\\r\n', '=\\\r')):
            self.__source[line] = newText.rstrip("\n\r \t\\")
            self.__source[line + 1] = self.__source[line + 1].lstrip()
        else:
            self.__source[line] = newText
        return (True, self.trUtf8("Extraneous whitespace removed."))
    
    def __fixE261(self, code, line, pos):
        """
        Private method to fix whitespace before or after inline comment
        (E261, E262).
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        line = line - 1
        text = self.__source[line]
        left = text[:pos].rstrip(' \t#')
        right = text[pos:].lstrip(' \t#')
        newText = left + ("  # " + right if right.strip() else right)
        self.__source[line] = newText
        return (True, self.trUtf8("Whitespace around comment sign corrected."))
    
    def __fixE301(self, code, line, pos, apply=False):
        """
        Private method to fix the need for one blank line (E301).
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        if apply:
            self.__source.insert(line - 1, self.__getEol())
        else:
            self.__stack.append((code, line, pos))
        return (True, self.trUtf8("One blank line inserted."))
    
    def __fixE302(self, code, line, pos, apply=False):
        """
        Private method to fix the need for two blank lines (E302).
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        # count blank lines
        index = line - 1
        blanks = 0
        while index:
            if self.__source[index - 1].strip() == "":
                blanks += 1
                index -= 1
            else:
                break
        delta = blanks - 2
        
        if apply:
            line -= 1
            if delta < 0:
                # insert blank lines (one or two)
                while delta < 0:
                    self.__source.insert(line, self.__getEol())
                    delta += 1
            elif delta > 0:
                # delete superfluous blank lines
                while delta > 0:
                    del self.__source[line - 1]
                    line -= 1
                    delta -= 1
        else:
            self.__stack.append((code, line, pos))
        
        if delta < 0:
            msg = self.trUtf8("%n blank line(s) inserted.", "", -delta)
        elif delta > 0:
            msg = self.trUtf8("%n superfluous lines removed", "", delta)
        else:
            msg = ""
        return (True, msg)
    
    def __fixE303(self, code, line, pos, apply=False):
        """
        Private method to fix superfluous blank lines (E303).
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        if apply:
            index = line - 3
            while index:
                if self.__source[index].strip() == "":
                    del self.__source[index]
                    index -= 1
                else:
                    break
        else:
            self.__stack.append((code, line, pos))
        return (True, self.trUtf8("Superfluous blank lines removed."))
    
    def __fixE304(self, code, line, pos, apply=False):
        """
        Private method to fix superfluous blank lines after a function
        decorator (E304).
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        if apply:
            index = line - 2
            while index:
                if self.__source[index].strip() == "":
                    del self.__source[index]
                    index -= 1
                else:
                    break
        else:
            self.__stack.append((code, line, pos))
        return (True, self.trUtf8(
            "Superfluous blank lines after function decorator removed."))
    
    def __fixE401(self, code, line, pos, apply=False):
        """
        Private method to fix multiple imports on one line (E401).
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        if apply:
            line = line - 1
            text = self.__source[line]
            if not text.lstrip().startswith("import"):
                return (False, "")
            
            # pep8 (1.3.1) reports false positive if there is an import
            # statement followed by a semicolon and some unrelated
            # statement with commas in it.
            if ';' in text:
                return (False, "")
            
            newText = text[:pos].rstrip("\t ,") + self.__getEol() + \
                self.__getIndent(text) + "import " + text[pos:].lstrip("\t ,")
            self.__source[line] = newText
        else:
            self.__stack.append((code, line, pos))
        return (True, self.trUtf8("Imports were put on separate lines."))
    
    def __fixE502(self, code, line, pos):
        """
        Private method to fix redundant backslash within brackets (E502).
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        self.__source[line - 1] = self.__source[line - 1].rstrip("\n\r \t\\") + \
            self.__getEol()
        return (True, self.trUtf8("Redundant backslash in brackets removed."))
    
    def __fixE701(self, code, line, pos, apply=False):
        """
        Private method to fix colon-separated compund statements (E701).
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        if apply:
            line = line - 1
            text = self.__source[line]
            pos = pos + 1
            
            newText = text[:pos] + self.__getEol() + self.__getIndent(text) + \
                self.__indentWord + text[pos:].lstrip("\n\r \t\\") + \
                self.__getEol()
            self.__source[line] = newText
        else:
            self.__stack.append((code, line, pos))
        return (True, self.trUtf8("Compound statement corrected."))
    
    def __fixE702(self, code, line, pos, apply=False):
        """
        Private method to fix semicolon-separated compound statements
        (E702, E703).
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        if apply:
            line = line - 1
            text = self.__source[line]
            
            if text.rstrip().endswith("\\"):
                # normalize '1; \\\n2' into '1; 2'
                self.__source[line] = text.rstrip("\n\r \t\\")
                self.__source[line + 1] = self.__source[line + 1].lstrip()
            elif text.rstrip().endswith(";"):
                self.__source[line] = text.rstrip("\n\r \t;") + self.__getEol()
            else:
                first = text[:pos].rstrip("\n\r \t;") + self.__getEol()
                second = text[pos:].lstrip("\n\r \t;")
                self.__source[line] = first + self.__getIndent(text) + second
        else:
            self.__stack.append((code, line, pos))
        return (True, self.trUtf8("Compound statement corrected."))
    
    def __fixE711(self, code, line, pos):
        """
        Private method to fix comparison with None (E711, E712).
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        line = line - 1
        text = self.__source[line]
        
        rightPos = pos + 2
        if rightPos >= len(text):
            return (False, "")
        
        left = text[:pos].rstrip()
        center = text[pos:rightPos]
        right = text[rightPos:].lstrip()
        
        if not right.startswith(("None", "True", "False")):
            return (False, "")
        
        if center.strip() == "==":
            center = "is"
        elif center.strip() == "!=":
            center = "is not"
        else:
            return (False, "")
        
        self.__source[line] = " ".join([left, center, right])
        return (True, self.trUtf8("Comparison to None/True/False corrected."))
    
    def __fixW291(self, code, line, pos):
        """
        Private method to fix trailing whitespace (W291, W293).
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        self.__source[line - 1] = re.sub(r'[\t ]+(\r?)$', r"\1",
                                         self.__source[line - 1])
        return (True, self.trUtf8("Whitespace stripped from end of line."))
    
    def __fixW292(self, code, line, pos):
        """
        Private method to fix a missing newline at the end of file (W292).
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        self.__source[line - 1] += self.__getEol()
        return (True, self.trUtf8("newline added to end of file."))
    
    def __fixW391(self, code, line, pos):
        """
        Private method to fix trailing blank lines (W391).
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        index = line - 1
        while index:
            if self.__source[index].strip() == "":
                del self.__source[index]
                index -= 1
            else:
                break
        return (True, self.trUtf8(
            "Superfluous trailing blank lines removed from end of file."))
    
    def __fixW603(self, code, line, pos):
        """
        Private method to fix the not equal notation (W603).
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        self.__source[line - 1] = self.__source[line - 1].replace("<>", "!=")
        return (True, self.trUtf8("'<>' replaced by '!='."))


class Pep8Reindenter(object):
    """
    Class to reindent badly-indented code to uniformly use four-space indentation.

    Released to the public domain, by Tim Peters, 03 October 2000.
    """
    def __init__(self, sourceLines):
        """
        Constructor
        
        @param sourceLines list of source lines including eol marker
            (list of string)
        """
        # Raw file lines.
        self.raw = sourceLines
        self.after = []

        # File lines, rstripped & tab-expanded.  Dummy at start is so
        # that we can use tokenize's 1-based line numbering easily.
        # Note that a line is all-blank iff it's "\n".
        self.lines = [line.rstrip().expandtabs() + "\n"
                      for line in self.raw]
        self.lines.insert(0, None)
        self.index = 1  # index into self.lines of next line

        # List of (lineno, indentlevel) pairs, one for each stmt and
        # comment line.  indentlevel is -1 for comment lines, as a
        # signal that tokenize doesn't know what to do about them;
        # indeed, they're our headache!
        self.stats = []
    
    def run(self):
        """
        Public method to run the re-indenter.
        """
        try:
            stats = self.__genStats(tokenize.generate_tokens(self.getline))
        except (SyntaxError, tokenize.TokenError):
            return False
        
        # Remove trailing empty lines.
        lines = self.lines
        while lines and lines[-1] == "\n":
            lines.pop()
        # Sentinel.
        stats.append((len(lines), 0))
        # Map count of leading spaces to # we want.
        have2want = {}
        # Program after transformation.
        after = self.after = []
        # Copy over initial empty lines -- there's nothing to do until
        # we see a line with *something* on it.
        i = stats[0][0]
        after.extend(lines[1:i])
        for i in range(len(stats) - 1):
            thisstmt, thislevel = stats[i]
            nextstmt = stats[i + 1][0]
            have = self.__getlspace(lines[thisstmt])
            want = thislevel * 4
            if want < 0:
                # A comment line.
                if have:
                    # An indented comment line.  If we saw the same
                    # indentation before, reuse what it most recently
                    # mapped to.
                    want = have2want.get(have, -1)
                    if want < 0:
                        # Then it probably belongs to the next real stmt.
                        for j in range(i + 1, len(stats) - 1):
                            jline, jlevel = stats[j]
                            if jlevel >= 0:
                                if have == self.__getlspace(lines[jline]):
                                    want = jlevel * 4
                                break
                    if want < 0:           # Maybe it's a hanging
                                           # comment like this one,
                        # in which case we should shift it like its base
                        # line got shifted.
                        for j in range(i - 1, -1, -1):
                            jline, jlevel = stats[j]
                            if jlevel >= 0:
                                want = have + self.__getlspace(after[jline - 1]) - \
                                       self.__getlspace(lines[jline])
                                break
                    if want < 0:
                        # Still no luck -- leave it alone.
                        want = have
                else:
                    want = 0
            assert want >= 0
            have2want[have] = want
            diff = want - have
            if diff == 0 or have == 0:
                after.extend(lines[thisstmt:nextstmt])
            else:
                for line in lines[thisstmt:nextstmt]:
                    if diff > 0:
                        if line == "\n":
                            after.append(line)
                        else:
                            after.append(" " * diff + line)
                    else:
                        remove = min(self.__getlspace(line), -diff)
                        after.append(line[remove:])
        return self.raw != self.after
    
    def fixedLine(self, line):
        """
        Public method to get a fixed line.
        
        @param line number of the line to retrieve (integer)
        @return fixed line (string)
        """
        if line < len(self.after):
            return self.after[line]
    
    def getline(self):
        """
        Public method to get a line of text for tokenize.
        
        @return line of text (string)
        """
        if self.index >= len(self.lines):
            line = ""
        else:
            line = self.lines[self.index]
            self.index += 1
        return line

    def __genStats(self, tokens):
        """
        Private method to generate the re-indent statistics.
        
        @param tokens tokens generator (tokenize._tokenize)
        """
        find_stmt = True  # next token begins a fresh stmt?
        level = 0  # current indent level
        stats = []

        for t in tokens:
            token_type = t[0]
            sline = t[2][0]
            line = t[4]

            if token_type == tokenize.NEWLINE:
                # A program statement, or ENDMARKER, will eventually follow,
                # after some (possibly empty) run of tokens of the form
                #     (NL | COMMENT)* (INDENT | DEDENT+)?
                self.find_stmt = True

            elif token_type == tokenize.INDENT:
                find_stmt = True
                level += 1

            elif token_type == tokenize.DEDENT:
                find_stmt = True
                level -= 1

            elif token_type == tokenize.COMMENT:
                if find_stmt:
                    stats.append((sline, -1))
                    # but we're still looking for a new stmt, so leave
                    # find_stmt alone

            elif token_type == tokenize.NL:
                pass

            elif find_stmt:
                # This is the first "real token" following a NEWLINE, so it
                # must be the first token of the next program statement, or an
                # ENDMARKER.
                find_stmt = False
                if line:   # not endmarker
                    stats.append((sline, level))
        
        return stats
    
    def __getlspace(self, line):
        """
        Private method to count number of leading blanks.
        
        @param line line to check (string)
        @return number of leading blanks (integer)
        """
        i = 0
        n = len(line)
        while i < n and line[i] == " ":
            i += 1
        return i


class Pep8IndentationWrapper(object):
    """
    Class used by fixers dealing with indentation.

    Each instance operates on a single logical line.
    """
    
    SKIP_TOKENS = frozenset([
        tokenize.COMMENT, tokenize.NL, tokenize.INDENT,
        tokenize.DEDENT, tokenize.NEWLINE, tokenize.ENDMARKER
    ])

    def __init__(self, physical_lines):
        """
        Constructor
        
        @param physical_lines list of physical lines to operate on
            (list of strings)
        """
        self.lines = physical_lines
        self.tokens = []
        self.rel_indent = None
        sio = io.StringIO(''.join(physical_lines))
        for t in tokenize.generate_tokens(sio.readline):
            if not len(self.tokens) and t[0] in self.SKIP_TOKENS:
                continue
            if t[0] != tokenize.ENDMARKER:
                self.tokens.append(t)

        self.logical_line = self.__buildTokensLogical(self.tokens)

    def __buildTokensLogical(self, tokens):
        """
        Private method to build a logical line from a list of tokens.
        
        @param tokens list of tokens as generated by tokenize.generate_tokens
        @return logical line (string)
        """
        # from pep8.py with minor modifications
        logical = []
        previous = None
        for t in tokens:
            token_type, text = t[0:2]
            if token_type in self.SKIP_TOKENS:
                continue
            if previous:
                end_line, end = previous[3]
                start_line, start = t[2]
                if end_line != start_line:  # different row
                    prev_text = self.lines[end_line - 1][end - 1]
                    if prev_text == ',' or (prev_text not in '{[('
                                            and text not in '}])'):
                        logical.append(' ')
                elif end != start:  # different column
                    fill = self.lines[end_line - 1][end:start]
                    logical.append(fill)
            logical.append(text)
            previous = t
        logical_line = ''.join(logical)
        assert logical_line.lstrip() == logical_line
        assert logical_line.rstrip() == logical_line
        return logical_line

    def pep8Expected(self):
        """
        Public method to replicate logic in pep8.py, to know what level to
        indent things to.

        @return list of lists, where each list represents valid indent levels for
        the line in question, relative from the initial indent. However, the
        first entry is the indent level which was expected.
        """
        # What follows is an adjusted version of
        # pep8.py:continuation_line_indentation. All of the comments have been
        # stripped and the 'yield' statements replaced with 'pass'.
        if not self.tokens:
            return

        first_row = self.tokens[0][2][0]
        nrows = 1 + self.tokens[-1][2][0] - first_row

        # here are the return values
        valid_indents = [list()] * nrows
        indent_level = self.tokens[0][2][1]
        valid_indents[0].append(indent_level)

        if nrows == 1:
            # bug, really.
            return valid_indents

        indent_next = self.logical_line.endswith(':')

        row = depth = 0
        parens = [0] * nrows
        self.rel_indent = rel_indent = [0] * nrows
        indent = [indent_level]
        indent_chances = {}
        last_indent = (0, 0)
        last_token_multiline = None

        for token_type, text, start, end, line in self.tokens:
            newline = row < start[0] - first_row
            if newline:
                row = start[0] - first_row
                newline = (not last_token_multiline and
                           token_type not in (tokenize.NL, tokenize.NEWLINE))

            if newline:
                # This is where the differences start. Instead of looking at
                # the line and determining whether the observed indent matches
                # our expectations, we decide which type of indentation is in
                # use at the given indent level, and return the offset. This
                # algorithm is susceptible to "carried errors", but should
                # through repeated runs eventually solve indentation for
                # multiline expressions.

                if depth:
                    for open_row in range(row - 1, -1, -1):
                        if parens[open_row]:
                            break
                else:
                    open_row = 0

                # That's all we get to work with. This code attempts to
                # "reverse" the below logic, and place into the valid indents
                # list
                vi = []
                add_second_chances = False
                if token_type == tokenize.OP and text in ']})':
                    # this line starts with a closing bracket, so it needs to
                    # be closed at the same indent as the opening one.
                    if indent[depth]:
                        # hanging indent
                        vi.append(indent[depth])
                    else:
                        # visual indent
                        vi.append(indent_level + rel_indent[open_row])
                elif depth and indent[depth]:
                    # visual indent was previously confirmed.
                    vi.append(indent[depth])
                    add_second_chances = True
                elif depth and True in indent_chances.values():
                    # visual indent happened before, so stick to
                    # visual indent this time.
                    if depth > 1 and indent[depth - 1]:
                        vi.append(indent[depth - 1])
                    else:
                        # stupid fallback
                        vi.append(indent_level + 4)
                    add_second_chances = True
                elif not depth:
                    vi.append(indent_level + 4)
                else:
                    # must be in hanging indent
                    hang = rel_indent[open_row] + 4
                    vi.append(indent_level + hang)

                # about the best we can do without look-ahead
                if (indent_next and vi[0] == indent_level + 4 and
                        nrows == row + 1):
                    vi[0] += 4

                if add_second_chances:
                    # visual indenters like to line things up.
                    min_indent = vi[0]
                    for col, what in indent_chances.items():
                        if col > min_indent and (
                            what is True or
                            (what == str and token_type == tokenize.STRING) or
                            (what == text and token_type == tokenize.OP)
                        ):
                            vi.append(col)
                    vi = sorted(vi)

                valid_indents[row] = vi

                # Returning to original continuation_line_indentation() from
                # pep8.
                visual_indent = indent_chances.get(start[1])
                last_indent = start
                rel_indent[row] = pep8.expand_indent(line) - indent_level
                hang = rel_indent[row] - rel_indent[open_row]

                if token_type == tokenize.OP and text in ']})':
                    pass
                elif visual_indent is True:
                    if not indent[depth]:
                        indent[depth] = start[1]

            # line altered: comments shouldn't define a visual indent
            if parens[row] and not indent[depth] and token_type not in (
                tokenize.NL, tokenize.COMMENT
            ):
                indent[depth] = start[1]
                indent_chances[start[1]] = True
            elif token_type == tokenize.STRING or text in (
                'u', 'ur', 'b', 'br'
            ):
                indent_chances[start[1]] = str

            if token_type == tokenize.OP:
                if text in '([{':
                    depth += 1
                    indent.append(0)
                    parens[row] += 1
                elif text in ')]}' and depth > 0:
                    prev_indent = indent.pop() or last_indent[1]
                    for d in range(depth):
                        if indent[d] > prev_indent:
                            indent[d] = 0
                    for ind in list(indent_chances):
                        if ind >= prev_indent:
                            del indent_chances[ind]
                    depth -= 1
                    if depth and indent[depth]:  # modified
                        indent_chances[indent[depth]] = True
                    for idx in range(row, -1, -1):
                        if parens[idx]:
                            parens[idx] -= 1
                            break
                assert len(indent) == depth + 1
                if start[1] not in indent_chances:
                    indent_chances[start[1]] = text

            last_token_multiline = (start[0] != end[0])

        return valid_indents
