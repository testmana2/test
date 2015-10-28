# -*- coding: utf-8 -*-

# Copyright (c) 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a checker for miscellaneous checks.
"""

from __future__ import unicode_literals

import sys
import ast
import re


class MiscellaneousChecker(object):
    """
    Class implementing a checker for miscellaneous checks.
    """
    Codes = [
        "M101", "M102",
        "M111", "M112",
        "M121",
        "M131",
        "M701", "M702",
        "M801",
        "M811",
        
        "M901",
    ]

    def __init__(self, source, filename, select, ignore, expected, repeat,
                 args):
        """
        Constructor
        
        @param source source code to be checked
        @type list of str
        @param filename name of the source file
        @type str
        @param select list of selected codes
        @type list of str
        @param ignore list of codes to be ignored
        @type list of str
        @param expected list of expected codes
        @type list of str
        @param repeat flag indicating to report each occurrence of a code
        @type bool
        @param args dictionary of arguments for the miscellaneous checks
        @type dict
        """
        self.__select = tuple(select)
        self.__ignore = ('',) if select else tuple(ignore)
        self.__expected = expected[:]
        self.__repeat = repeat
        self.__filename = filename
        self.__source = source[:]
        self.__args = args
        
        self.__blindExceptRegex = re.compile(
            r'(except:)')                               # __IGNORE_WARNING__
        self.__pep3101FormatRegex = re.compile(
            r'^(?:[^\'"]*[\'"][^\'"]*[\'"])*\s*%|^\s*%')

        # statistics counters
        self.counters = {}
        
        # collection of detected errors
        self.errors = []
        
        checkersWithCodes = [
            # TODO: fill this
            (self.__checkCoding, ("M101", "M102")),
            (self.__checkCopyright, ("M111", "M112")),
            (self.__checkBlindExcept, ("M121",)),
            (self.__checkPep3101, ("M131",)),
            (self.__checkPrintStatements, ("M801",)),
            (self.__checkTuple, ("M811", )),
            (self.__checkFuture, ("M701", "M702")),
        ]
        
        self.__defaultArgs = {
            "CodingChecker": 'latin-1, utf-8',
            "CopyrightChecker": {
                "MinFilesize": 0,
                "Author": "",
            },
        }
        
        self.__checkers = []
        for checker, codes in checkersWithCodes:
            if any(not (code and self.__ignoreCode(code))
                    for code in codes):
                self.__checkers.append(checker)
    
    def __ignoreCode(self, code):
        """
        Private method to check if the message code should be ignored.

        @param code message code to check for
        @type str
        @return flag indicating to ignore the given code
        @rtype bool
        """
        return (code.startswith(self.__ignore) and
                not code.startswith(self.__select))
    
    def __error(self, lineNumber, offset, code, *args):
        """
        Private method to record an issue.
        
        @param lineNumber line number of the issue
        @type int
        @param offset position within line of the issue
        @type int
        @param code message code
        @type str
        @param args arguments for the message
        @type list
        """
        if self.__ignoreCode(code):
            return
        
        if code in self.counters:
            self.counters[code] += 1
        else:
            self.counters[code] = 1
        
        # Don't care about expected codes
        if code in self.__expected:
            return
        
        if code and (self.counters[code] == 1 or self.__repeat):
            # record the issue with one based line number
            self.errors.append(
                (self.__filename, lineNumber + 1, offset, (code, args)))
    
    def __reportInvalidSyntax(self):
        """
        Private method to report a syntax error.
        """
        exc_type, exc = sys.exc_info()[:2]
        if len(exc.args) > 1:
            offset = exc.args[1]
            if len(offset) > 2:
                offset = offset[1:3]
        else:
            offset = (1, 0)
        self.__error(offset[0] - 1, offset[1] or 0,
                     'M901', exc_type.__name__, exc.args[0])
    
    def run(self):
        """
        Public method to check the given source against miscellaneous
        conditions.
        """
        if not self.__filename:
            # don't do anything, if essential data is missing
            return
        
        if not self.__checkers:
            # don't do anything, if no codes were selected
            return
        
        source = "".join(self.__source)
        # Check type for py2: if not str it's unicode
        if sys.version_info[0] == 2:
            try:
                source = source.encode('utf-8')
            except UnicodeError:
                pass
        try:
            self.__tree = compile(source, self.__filename, 'exec',
                                  ast.PyCF_ONLY_AST)
        except (SyntaxError, TypeError):
            self.__reportInvalidSyntax()
            return
        
        for check in self.__checkers:
            check()
    
    def __checkCoding(self):
        """
        Private method to check the presence of a coding line and valid
        encodings.
        """
        if len(self.__source) == 0:
            return
        
        encodings = [e.lower().strip()
                     for e in self.__args.get(
                     "CodingChecker", self.__defaultArgs["CodingChecker"])
                     .split(",")]
        for lineno, line in enumerate(self.__source[:2]):
            matched = re.search('coding[:=]\s*([-\w.]+)', line, re.IGNORECASE)
            if matched:
                if encodings and matched.group(1).lower() not in encodings:
                    self.__error(lineno, 0, "M102", matched.group(1))
                break
        else:
            self.__error(0, 0, "M101")
    
    def __checkCopyright(self):
        """
        Private method to check the presence of a copyright statement.
        """
        source = "".join(self.__source)
        copyrightArgs = self.__args.get(
            "CopyrightChecker", self.__defaultArgs["CopyrightChecker"])
        copyrightMinFileSize = copyrightArgs.get(
            "MinFilesize",
            self.__defaultArgs["CopyrightChecker"]["MinFilesize"])
        copyrightAuthor = copyrightArgs.get(
            "Author",
            self.__defaultArgs["CopyrightChecker"]["Author"])
        copyrightRegexStr = \
            r"Copyright\s+(\(C\)\s+)?(\d{{4}}\s+-\s+)?\d{{4}}\s+{author}"
        
        tocheck = max(1024, copyrightMinFileSize)
        topOfSource = source[:tocheck]
        if len(topOfSource) < copyrightMinFileSize:
            return

        copyrightRe = re.compile(copyrightRegexStr.format(author=r".*"),
                                 re.IGNORECASE)
        if not copyrightRe.search(topOfSource):
            self.__error(0, 0, "M111")
            return
        
        if copyrightAuthor:
            copyrightAuthorRe = re.compile(
                copyrightRegexStr.format(author=copyrightAuthor),
                re.IGNORECASE)
            if not copyrightAuthorRe.search(topOfSource):
                self.__error(0, 0, "M112")
    
    def __checkBlindExcept(self):
        """
        Private method to check for blind except statements.
        """
        for lineno, line in enumerate(self.__source):
            match = self.__blindExceptRegex.search(line)
            if match:
                self.__error(lineno, match.start(), "M121")
    
    def __checkPep3101(self):
        """
        Private method to check for old style string formatting.
        """
        for lineno, line in enumerate(self.__source):
            match = self.__pep3101FormatRegex.search(line)
            if match:
                lineLen = len(line)
                pos = line.find('%')
                formatPos = pos
                formatter = '%'
                if line[pos + 1] == "(":
                    pos = line.find(")", pos)
                c = line[pos]
                while c not in "diouxXeEfFgGcrs":
                    pos += 1
                    if pos >= lineLen:
                        break
                    c = line[pos]
                if c in "diouxXeEfFgGcrs":
                    formatter += c
                self.__error(lineno, formatPos, "M131", formatter)
    
    def __checkPrintStatements(self):
        """
        Private method to check for print statements.
        """
        for node in ast.walk(self.__tree):
            if (isinstance(node, ast.Call) and
                getattr(node.func, 'id', None) == 'print') or \
               (hasattr(ast, 'Print') and isinstance(node, ast.Print)):
                self.__error(node.lineno - 1, node.col_offset, "M801")
    
    def __checkTuple(self):
        """
        Private method to check for one element tuples.
        """
        for node in ast.walk(self.__tree):
            if isinstance(node, ast.Tuple) and \
                    len(node.elts) == 1:
                self.__error(node.lineno - 1, node.col_offset, "M811")
    
    def __checkFuture(self):
        """
        Private method to check the __future__ imports.
        """
        expectedImports = set(
            [i.strip()
             for i in self.__args.get("FutureChecker", "").split(",")
             if bool(i.strip())])
        if len(expectedImports) == 0:
            # nothing to check for; disabling the check
            return
        
        imports = set()
        node = None
        
        for node in ast.walk(self.__tree):
            if (isinstance(node, ast.ImportFrom) and
                    node.module == '__future__'):
                imports |= set(name.name for name in node.names)
            elif isinstance(node, ast.Expr):
                if not isinstance(node.value, ast.Str):
                    break
            elif not isinstance(node, ast.Module):
                break

        if isinstance(node, ast.Module):
            return

        if not (imports >= expectedImports):
            if imports:
                self.__error(node.lineno - 1, node.col_offset, "M701",
                             ", ".join(expectedImports), ", ".join(imports))
            else:
                self.__error(node.lineno - 1, node.col_offset, "M702",
                             ", ".join(expectedImports))
