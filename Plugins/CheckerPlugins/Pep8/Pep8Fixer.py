# -*- coding: utf-8 -*-

# Copyright (c) 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a class to fix certain PEP 8 issues.
"""

import os
import re

from PyQt4.QtCore import QObject

from E5Gui import E5MessageBox

import Utilities

Pep8FixableIssues = ["E101", "W191", "E201", "E202", "E203", "E211", "E221",
                     "E222", "E225", "E231", "E241", "E251", "E261", "E262",
                     "W291", "W292", "W293", "E301", "E302", "E303", "E304",
                     "W391", "W603"]


class Pep8Fixer(QObject):
    """
    Class implementing a fixer for certain PEP 8 issues.
    """
    def __init__(self, project, filename, sourceLines, fixCodes, inPlace):
        """
        Constructor
        
        @param project  reference to the project object (Project)
        @param filename name of the file to be fixed (string)
        @param sourceLines list of source lines including eol marker
            (list of string)
        @param fixCodes list of codes to be fixed as a comma separated
            string (string)
        @param inPlace flag indicating to modify the file in place (boolean)
        """
        QObject.__init__(self)
        
        self.__project = project
        self.__filename = filename
        self.__origName = ""
        self.__source = sourceLines[:]  # save a copy
        self.__fixCodes = [c.strip() for c in fixCodes.split(",") if c.strip()]
        self.fixed = 0
        
        if not inPlace:
            self.__origName = self.__filename
            self.__filename = os.path.join(os.path.dirname(self.__filename),
                "fixed_" + os.path.basename(self.__filename))
        
        self.__fixes = {
            "E101": self.__fixTabs,
            "W191": self.__fixTabs,
            "E201": self.__fixWhitespaceAfter,
            "E202": self.__fixWhitespaceBefore,
            "E203": self.__fixWhitespaceBefore,
            "E211": self.__fixWhitespaceBefore,
            "E221": self.__fixWhitespaceAroundOperator,
            "E222": self.__fixWhitespaceAroundOperator,
            "E225": self.__fixMissingWhitespaceAroundOperator,
            "E231": self.__fixMissingWhitespaceAfter,
            "E241": self.__fixWhitespaceAroundOperator,
            "E251": self.__fixWhitespaceAroundEquals,
            "E261": self.__fixWhitespaceBeforeInline,
            "E262": self.__fixWhitespaceAfterInline,
            "W291": self.__fixWhitespace,
            "W292": self.__fixNewline,
            "W293": self.__fixWhitespace,
            "E301": self.__fixOneBlankLine,
            "E302": self.__fixTwoBlankLines,
            "E303": self.__fixTooManyBlankLines,
            "E304": self.__fixBlankLinesAfterDecorator,
            "W391": self.__fixTrailingBlankLines,
            "W603": self.__fixNotEqual,
        }
        self.__modified = False
        self.__stack = []   # these need to be fixed before the file is saved
                            # but after all inline fixes
    
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
                    """ Skipping it.</p><p>Reason: {1}</p>""")\
                    .format(self.__filename, str(err))
            )
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
           (code in self.__fixCodes or len(self.__fixCodes) == 0) and \
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
        for code, line, pos in reversed(self.__stack):
            self.__fixes[code](code, line, pos, apply=True)
    
    def __getEol(self):
        """
        Private method to get the applicable eol string.
        
        @return eol string (string)
        """
        if self.__origName:
            fn = self.__origName
        else:
            fn = self.__filename
        
        if self.__project.isOpen() and self.__project.isProjectFile(fn):
            eol = self.__project.getEolString()
        else:
            eol = Utilities.linesep()
        return eol
    
    def __fixTabs(self, code, line, pos):
        """
        Private method to fix obsolete tab usage.
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        self.__source[line - 1] = self.__source[line - 1].replace("\t", "    ")
        return (True, self.trUtf8("Tab converted to 4 spaces."))
    
    def __fixWhitespace(self, code, line, pos):
        """
        Private method to fix trailing whitespace.
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        self.__source[line - 1] = re.sub(r'[\t ]*$', "",
                                         self.__source[line - 1])
        return (True, self.trUtf8("Whitespace stripped from end of line."))
    
    def __fixNewline(self, code, line, pos):
        """
        Private method to fix a missing newline at the end of file.
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        self.__source[line - 1] += self.__getEol()
        return (True, self.trUtf8("newline added to end of file."))
    
    def __fixTrailingBlankLines(self, code, line, pos):
        """
        Private method to fix trailing blank lines.
        
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
    
    def __fixNotEqual(self, code, line, pos):
        """
        Private method to fix the not equal notation.
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        self.__source[line - 1] = self.__source[line - 1].replace("<>", "!=")
        return (True, self.trUtf8("'<>' replaced by '!='."))
    
    def __fixBlankLinesAfterDecorator(self, code, line, pos, apply=False):
        """
        Private method to fix superfluous blank lines after a function
        decorator.
        
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
    
    def __fixTooManyBlankLines(self, code, line, pos, apply=False):
        """
        Private method to fix superfluous blank lines.
        
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
    
    def __fixOneBlankLine(self, code, line, pos, apply=False):
        """
        Private method to fix the need for one blank line.
        
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
    
    def __fixTwoBlankLines(self, code, line, pos, apply=False):
        """
        Private method to fix the need for two blank lines.
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
    
    def __fixWhitespaceAfter(self, code, line, pos, apply=False):
        """
        Private method to fix superfluous whitespace after '([{'.
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        line = line - 1
        pos = pos - 1
        while self.__source[line][pos] in [" ", "\t"]:
            self.__source[line] = self.__source[line][:pos] + \
                                  self.__source[line][pos + 1:]
        return (True, self.trUtf8("Superfluous whitespace removed."))
    
    def __fixWhitespaceBefore(self, code, line, pos, apply=False):
        """
        Private method to fix superfluous whitespace before '}])',
        ',;:' and '(['.
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        line = line - 1
        pos = pos - 1
        while self.__source[line][pos] in [" ", "\t"]:
            self.__source[line] = self.__source[line][:pos] + \
                                  self.__source[line][pos + 1:]
            pos -= 1
        return (True, self.trUtf8("Superfluous whitespace removed."))
    
    def __fixMissingWhitespaceAfter(self, code, line, pos, apply=False):
        """
        Private method to fix missing whitespace after ',;:'.
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        line = line - 1
        self.__source[line] = self.__source[line][:pos] + \
                               " " + \
                               self.__source[line][pos:]
        return (True, self.trUtf8("Missing whitespace added."))
    
    def __fixWhitespaceAroundOperator(self, code, line, pos, apply=False):
        """
        Private method to fix extraneous whitespace around operator.
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        line = line - 1
        while self.__source[line][pos - 1] in [" ", "\t"]:
            self.__source[line] = self.__source[line][:pos - 1] + \
                                  self.__source[line][pos:]
            pos -= 1
        return (True, self.trUtf8("Extraneous whitespace removed."))
    
    def __fixMissingWhitespaceAroundOperator(self, code, line, pos,
                                                   apply=False):
        """
        Private method to fix missing whitespace after ',;:'.
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        line = line - 1
        pos = pos - 1
        self.__source[line] = self.__source[line][:pos] + \
                               " " + \
                               self.__source[line][pos:]
        return (True, self.trUtf8("Missing whitespace added."))
    
    def __fixWhitespaceAroundEquals(self, code, line, pos, apply=False):
        """
        Private method to fix extraneous whitespace around keyword and
        default parameter equals.
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        line = line - 1
        if self.__source[line][pos + 1] == " ":
            self.__source[line] = self.__source[line][:pos + 1] + \
                                   self.__source[line][pos + 2:]
        if self.__source[line][pos - 1] == " ":
            self.__source[line] = self.__source[line][:pos - 1] + \
                                   self.__source[line][pos:]
        return (True, self.trUtf8("Extraneous whitespace removed."))
    
    def __fixWhitespaceBeforeInline(self, code, line, pos, apply=False):
        """
        Private method to fix missing whitespace before inline comment.
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        line = line - 1
        pos = pos - 1
        if self.__source[line][pos] == " ":
            count = 1
        else:
            count = 2
        self.__source[line] = self.__source[line][:pos] + \
                               count * " " + \
                               self.__source[line][pos:]
        return (True, self.trUtf8("Missing whitespace added."))
    
    def __fixWhitespaceAfterInline(self, code, line, pos, apply=False):
        """
        Private method to fix whitespace after inline comment.
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return flag indicating an applied fix (boolean) and a message for
            the fix (string)
        """
        line = line - 1
        if self.__source[line][pos] == " ":
            pos += 1
            while self.__source[line][pos] == " ":
                self.__source[line] = self.__source[line][:pos] + \
                                      self.__source[line][pos + 1:]
        else:
            self.__source[line] = self.__source[line][:pos] + \
                                   " " + \
                                   self.__source[line][pos:]
        return (True, self.trUtf8(
            "Whitespace after inline comment sign corrected."))
