# -*- coding: utf-8 -*-

# Copyright (c) 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a checker for PEP-257 documentation string conventions.
"""

#
# The routines of the checker class are modeled after the ones found in
# pep257.py (version 0.2.4).
#

try:
    # Python 2
    from StringIO import StringIO       # __IGNORE_EXCEPTION__
except ImportError:
    # Python 3
    from io import StringIO             # __IGNORE_WARNING__
import tokenize
import ast
import sys


class Pep257Context(object):
    """
    Class implementing the source context.
    """
    def __init__(self, source, startLine, contextType):
        """
        Constructor
        
        @param source source code of the context (list of string or string)
        @param startLine line number the context starts in the source (integer)
        @param contextType type of the context object (string)
        """
        if isinstance(source, str):
            self.__source = source.splitlines(True)
        else:
            self.__source = source[:]
        self.__start = startLine
        self.__indent = ""
        self.__type = contextType
        
        # ensure first line is left justified
        if self.__source:
            self.__indent = self.__source[0].replace(
                self.__source[0].lstrip(), "")
            self.__source[0] = self.__source[0].lstrip()
    
    def source(self):
        """
        Public method to get the source.
        
        @return source (list of string)
        """
        return self.__source
    
    def ssource(self):
        """
        Public method to get the joined source lines.
        
        @return source (string)
        """
        return "".join(self.__source)
    
    def start(self):
        """
        Public method to get the start line number.
        
        @return start line number (integer)
        """
        return self.__start
    
    def end(self):
        """
        Public method to get the end line number.
        
        @return end line number (integer)
        """
        return self.__start + len(self.__source) - 1
    
    def indent(self):
        """
        Public method to get the indentation of the first line.
        
        @return indentation string (string)
        """
        return self.__indent
    
    def contextType(self):
        """
        Public method to get the context type.
        
        @return context type (string)
        """
        return self.__type


class Pep257Checker(object):
    """
    Class implementing a checker for PEP-257 documentation string conventions.
    """
    Codes = [
        "D101", "D102", "D103", "D104", "D105",
        "D111", "D112", "D113",
        "D121", "D122",
        "D131", "D132", "D133", "D134",
        "D141", "D142", "D143", "D144", "D145",
        
        "D203", "D205",
        "D221",
        "D231", "D234", "D235", "D236", "D237", "D238",
        "D242", "D243", "D244", "D245", "D246", "D247",
    ]
    
    def __init__(self, source, filename, select, ignore, expected, repeat,
                 maxLineLength=79, docType="pep257"):
        """
        Constructor
        
        @param source source code to be checked (list of string)
        @param filename name of the source file (string)
        @param select list of selected codes (list of string)
        @param ignore list of codes to be ignored (list of string)
        @param expected list of expected codes (list of string)
        @param repeat flag indicating to report each occurrence of a code
            (boolean)
        @keyparam maxLineLength allowed line length (integer)
        @keyparam docType type of the documentation strings
            (string, one of 'eric' or 'pep257')
        """
        assert docType in ("eric", "pep257")
        
        self.__select = tuple(select)
        self.__ignore = tuple(ignore)
        self.__expected = expected[:]
        self.__repeat = repeat
        self.__maxLineLength = maxLineLength
        self.__docType = docType
        self.__filename = filename
        self.__source = source[:]
        self.__isScript = self.__source[0].startswith('#!')
        
        # statistics counters
        self.counters = {}
        
        # collection of detected errors
        self.errors = []
        
        self.__lineNumber = 0
        
        # caches
        self.__functionsCache = None
        self.__classesCache = None
        self.__methodsCache = None
        
        self.__keywords = [
            'moduleDocstring', 'functionDocstring',
            'classDocstring', 'methodDocstring',
            'defDocstring', 'docstring'
        ]
        if self.__docType == "pep257":
            checkersWithCodes = {
                "moduleDocstring": [
                    (self.__checkModulesDocstrings, ("D101",)),
                ],
                "functionDocstring": [
                ],
                "classDocstring": [
                    (self.__checkClassDocstring, ("D104", "D105")),
                    (self.__checkBlankBeforeAndAfterClass, ("D142", "D143")),
                ],
                "methodDocstring": [
                ],
                "defDocstring": [
                    (self.__checkFunctionDocstring, ("D102", "D103")),
                    (self.__checkImperativeMood, ("D132",)),
                    (self.__checkNoSignature, ("D133",)),
                    (self.__checkReturnType, ("D134",)),
                    (self.__checkNoBlankLineBefore, ("D141",)),
                ],
                "docstring": [
                    (self.__checkTripleDoubleQuotes, ("D111",)),
                    (self.__checkBackslashes, ("D112",)),
                    (self.__checkUnicode, ("D113",)),
                    (self.__checkOneLiner, ("D121",)),
                    (self.__checkIndent, ("D122",)),
                    (self.__checkEndsWithPeriod, ("D131",)),
                    (self.__checkBlankAfterSummary, ("D144",)),
                    (self.__checkBlankAfterLastParagraph, ("D145",)),
                ],
            }
        elif self.__docType == "eric":
            checkersWithCodes = {
                "moduleDocstring": [
                    (self.__checkModulesDocstrings, ("D101",)),
                ],
                "functionDocstring": [
                ],
                "classDocstring": [
                    (self.__checkClassDocstring, ("D104", "D205")),
                    (self.__checkEricNoBlankBeforeAndAfterClassOrFunction,
                     ("D242", "D243")),
                ],
                "methodDocstring": [
                ],
                "defDocstring": [
                    (self.__checkFunctionDocstring, ("D102", "D203")),
                    (self.__checkImperativeMood, ("D132",)),
                    (self.__checkNoSignature, ("D133",)),
                    (self.__checkEricReturn, ("D234",)),
                    (self.__checkEricFunctionArguments,
                     ("D235", "D236", "D237", "D238")),
                    (self.__checkEricNoBlankBeforeAndAfterClassOrFunction,
                     ("D244", "D245")),
                ],
                "docstring": [
                    (self.__checkTripleDoubleQuotes, ("D111",)),
                    (self.__checkBackslashes, ("D112",)),
                    (self.__checkUnicode, ("D113",)),
                    (self.__checkEricOneLiner, ("D221",)),
                    (self.__checkIndent, ("D122",)),
                    (self.__checkEricEndsWithPeriod, ("D231",)),
                    (self.__checkEricBlankAfterSummary, ("D246",)),
                    (self.__checkEricNBlankAfterLastParagraph, ("D247",)),
                ],
            }
        
        self.__checkers = {}
        for key, checkers in checkersWithCodes.items():
            for checker, codes in checkers:
                if any(not (code and self.__ignoreCode(code))
                        for code in codes):
                    if key not in self.__checkers:
                        self.__checkers[key] = []
                    self.__checkers[key].append(checker)
    
    def __ignoreCode(self, code):
        """
        Private method to check if the error code should be ignored.

        @param code message code to check for (string)
        @return flag indicating to ignore the given code (boolean)
        """
        return (code.startswith(self.__ignore) and
                not code.startswith(self.__select))
    
    def __error(self, lineNumber, offset, code, *args):
        """
        Private method to record an issue.
        
        @param lineNumber line number of the issue (integer)
        @param offset position within line of the issue (integer)
        @param code message code (string)
        @param args arguments for the message (list)
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
                (self.__filename, lineNumber + 1, offset, code, args))
    
    def __resetReadline(self):
        """
        Private method to reset the internal readline function.
        """
        self.__lineNumber = 0
    
    def __readline(self):
        """
        Private method to get the next line from the source.
        
        @return next line of source (string)
        """
        self.__lineNumber += 1
        if self.__lineNumber > len(self.__source):
            return ''
        return self.__source[self.__lineNumber - 1]
    
    def run(self):
        """
        Public method to check the given source for violations of doc string
        conventions according to PEP-257.
        """
        if not self.__source or not self.__filename:
            # don't do anything, if essential data is missing
            return
        
        for keyword in self.__keywords:
            if keyword in self.__checkers:
                for check in self.__checkers[keyword]:
                    for context in self.__parseContexts(keyword):
                        docstring = self.__parseDocstring(context, keyword)
                        check(docstring, context)
    
    def __getSummaryLine(self, docstringContext):
        """
        Private method to extract the summary line.
        
        @param docstringContext docstring context (Pep257Context)
        @return summary line (string) and the line it was found on (integer)
        """
        lines = docstringContext.source()
        
        line = (lines[0]
                .replace('r"""', "", 1)
                .replace('u"""', "", 1)
                .replace('"""', "")
                .replace("r'''", "", 1)
                .replace("u'''", "", 1)
                .replace("'''", "")
                .strip())
        
        if len(lines) == 1 or len(line) > 0:
            return line, 0
        return lines[1].strip().replace('"""', "").replace("'''", ""), 1
    
    def __getSummaryLines(self, docstringContext):
        """
        Private method to extract the summary lines.
        
        @param docstringContext docstring context (Pep257Context)
        @return summary lines (list of string) and the line it was found on
            (integer)
        """
        summaries = []
        lines = docstringContext.source()
        
        line0 = (lines[0]
                .replace('r"""', "", 1)
                .replace('u"""', "", 1)
                .replace('"""', "")
                .replace("r'''", "", 1)
                .replace("u'''", "", 1)
                .replace("'''", "")
                .strip())
        if len(lines) > 1:
            line1 = lines[1].strip().replace('"""', "").replace("'''", "")
        else:
            line1 = ""
        if len(lines) > 2:
            line2 = lines[2].strip().replace('"""', "").replace("'''", "")
        else:
            line2 = ""
        if line0:
            lineno = 0
            summaries.append(line0)
            if not line0.endswith(".") and line1:
                # two line summary
                summaries.append(line1)
        elif line1:
            lineno = 1
            summaries.append(line1)
            if not line1.endswith(".") and line2:
                # two line summary
                summaries.append(line2)
        else:
            lineno = 2
            summaries.append(line2)
        return summaries, lineno
    
    if sys.version_info[0] < 3:
        def __getArgNames(self, node):
            """
            Private method to get the argument names of a function node.
            
            @param node AST node to extract arguments names from
            @return tuple of two list of argument names, one for arguments
                and one for keyword arguments (tuple of list of string)
            """
            def unpackArgs(args):
                """
                Local helper function to unpack function argument names.
                
                @param args list of AST node arguments
                @return list of argument names (list of string)
                """
                ret = []
                for arg in args:
                    if isinstance(arg, ast.Tuple):
                        ret.extend(unpackArgs(arg.elts))
                    else:
                        ret.append(arg.id)
                return ret
            
            arguments = unpackArgs(node.args.args)
            if node.args.vararg is not None:
                arguments.append(node.args.vararg)
            kwarguments = []
            if node.args.kwarg is not None:
                kwarguments.append(node.args.kwarg)
            return arguments, kwarguments
    else:
        def __getArgNames(self, node):          # __IGNORE_WARNING__
            """
            Private method to get the argument names of a function node.
            
            @param node AST node to extract arguments names from
            @return tuple of two list of argument names, one for arguments
                and one for keyword arguments (tuple of list of string)
            """
            arguments = []
            arguments.extend([arg.arg for arg in node.args.args])
            if node.args.vararg is not None:
                arguments.append(node.args.vararg)
            
            kwarguments = []
            kwarguments.extend([arg.arg for arg in node.args.kwonlyargs])
            if node.args.kwarg is not None:
                kwarguments.append(node.args.kwarg)
            return arguments, kwarguments
    
    ##################################################################
    ## Parsing functionality below
    ##################################################################
    
    def __parseModuleDocstring(self, source):
        """
        Private method to extract a docstring given a module source.
        
        @param source source to parse (list of string)
        @return context of extracted docstring (Pep257Context)
        """
        for kind, value, (line, char), _, _ in tokenize.generate_tokens(
                StringIO("".join(source)).readline):
            if kind in [tokenize.COMMENT, tokenize.NEWLINE, tokenize.NL]:
                continue
            elif kind == tokenize.STRING:  # first STRING should be docstring
                return Pep257Context(value, line - 1, "docstring")
            else:
                return None

    def __parseDocstring(self, context, what=''):
        """
        Private method to extract a docstring given `def` or `class` source.
        
        @param context context data to get the docstring from (Pep257Context)
        @return context of extracted docstring (Pep257Context)
        """
        moduleDocstring = self.__parseModuleDocstring(context.source())
        if what.startswith('module') or context.contextType() == "module":
            return moduleDocstring
        if moduleDocstring:
            return moduleDocstring
        
        tokenGenerator = tokenize.generate_tokens(
            StringIO(context.ssource()).readline)
        try:
            kind = None
            while kind != tokenize.INDENT:
                kind, _, _, _, _ = next(tokenGenerator)
            kind, value, (line, char), _, _ = next(tokenGenerator)
            if kind == tokenize.STRING:  # STRING after INDENT is a docstring
                return Pep257Context(
                    value, context.start() + line - 1, "docstring")
        except StopIteration:
            pass
        
        return None
    
    def __parseTopLevel(self, keyword):
        """
        Private method to extract top-level functions or classes.
        
        @param keyword keyword signaling what to extract (string)
        @return extracted function or class contexts (list of Pep257Context)
        """
        self.__resetReadline()
        tokenGenerator = tokenize.generate_tokens(self.__readline)
        kind, value, char = None, None, None
        contexts = []
        try:
            while True:
                start, end = None, None
                while not (kind == tokenize.NAME and
                           value == keyword and
                           char == 0):
                    kind, value, (line, char), _, _ = next(tokenGenerator)
                start = line - 1, char
                while not (kind == tokenize.DEDENT and
                           value == '' and
                           char == 0):
                    kind, value, (line, char), _, _ = next(tokenGenerator)
                end = line - 1, char
                contexts.append(Pep257Context(
                    self.__source[start[0]:end[0]], start[0], keyword))
        except StopIteration:
            return contexts
    
    def __parseFunctions(self):
        """
        Private method to extract top-level functions.
        
        @return extracted function contexts (list of Pep257Context)
        """
        if not self.__functionsCache:
            self.__functionsCache = self.__parseTopLevel('def')
        return self.__functionsCache
    
    def __parseClasses(self):
        """
        Private method to extract top-level classes.
        
        @return extracted class contexts (list of Pep257Context)
        """
        if not self.__classesCache:
            self.__classesCache = self.__parseTopLevel('class')
        return self.__classesCache
    
    def __skipIndentedBlock(self, tokenGenerator):
        """
        Private method to skip over an indented block of source code.
        
        @param tokenGenerator token generator
        @return last token of the indented block
        """
        kind, value, start, end, raw = next(tokenGenerator)
        while kind != tokenize.INDENT:
            kind, value, start, end, raw = next(tokenGenerator)
        indent = 1
        for kind, value, start, end, raw in tokenGenerator:
            if kind == tokenize.INDENT:
                indent += 1
            elif kind == tokenize.DEDENT:
                indent -= 1
            if indent == 0:
                return kind, value, start, end, raw
    
    def __parseMethods(self):
        """
        Private method to extract methods of all classes.
        
        @return extracted method contexts (list of Pep257Context)
        """
        if not self.__methodsCache:
            contexts = []
            for classContext in self.__parseClasses():
                tokenGenerator = tokenize.generate_tokens(
                    StringIO(classContext.ssource()).readline)
                kind, value, char = None, None, None
                try:
                    while True:
                        start, end = None, None
                        while not (kind == tokenize.NAME and value == 'def'):
                            kind, value, (line, char), _, _ = \
                                next(tokenGenerator)
                        start = line - 1, char
                        kind, value, (line, char), _, _ = \
                            self.__skipIndentedBlock(tokenGenerator)
                        end = line - 1, char
                        startLine = classContext.start() + start[0]
                        endLine = classContext.start() + end[0]
                        contexts.append(
                            Pep257Context(self.__source[startLine:endLine],
                                          startLine, "def"))
                except StopIteration:
                    pass
            self.__methodsCache = contexts
        
        return self.__methodsCache

    def __parseContexts(self, kind):
        """
        Private method to extract a context from the source.
        
        @param kind kind of context to extract (string)
        @return requested contexts (list of Pep257Context)
        """
        if kind == 'moduleDocstring':
            return [Pep257Context(self.__source, 0, "module")]
        if kind == 'functionDocstring':
            return self.__parseFunctions()
        if kind == 'classDocstring':
            return self.__parseClasses()
        if kind == 'methodDocstring':
            return self.__parseMethods()
        if kind == 'defDocstring':
            return self.__parseFunctions() + self.__parseMethods()
        if kind == 'docstring':
            return ([Pep257Context(self.__source, 0, "module")] +
                    self.__parseFunctions() +
                    self.__parseClasses() +
                    self.__parseMethods())
        return []       # fall back
    
    ##################################################################
    ## Checking functionality below (PEP-257)
    ##################################################################

    def __checkModulesDocstrings(self, docstringContext, context):
        """
        Private method to check, if the module has a docstring.
        
        @param docstringContext docstring context (Pep257Context)
        @param context context of the docstring (Pep257Context)
        """
        if docstringContext is None:
            self.__error(context.start(), 0, "D101")
            return
        
        docstring = docstringContext.ssource()
        if (not docstring or not docstring.strip() or
                not docstring.strip('\'"')):
            self.__error(context.start(), 0, "D101")
    
    def __checkFunctionDocstring(self, docstringContext, context):
        """
        Private method to check, that all public functions and methods
        have a docstring.
        
        @param docstringContext docstring context (Pep257Context)
        @param context context of the docstring (Pep257Context)
        """
        if self.__isScript:
            # assume nothing is exported
            return
        
        functionName = context.source()[0].lstrip().split()[1].split("(")[0]
        if functionName.startswith('_') and not functionName.endswith('__'):
            if self.__docType == "eric":
                code = "D203"
            else:
                code = "D103"
        else:
            code = "D102"
        
        if docstringContext is None:
            self.__error(context.start(), 0, code)
            return
        
        docstring = docstringContext.ssource()
        if (not docstring or not docstring.strip() or
                not docstring.strip('\'"')):
            self.__error(context.start(), 0, code)
    
    def __checkClassDocstring(self, docstringContext, context):
        """
        Private method to check, that all public functions and methods
        have a docstring.
        
        @param docstringContext docstring context (Pep257Context)
        @param context context of the docstring (Pep257Context)
        """
        if self.__isScript:
            # assume nothing is exported
            return
        
        className = context.source()[0].lstrip().split()[1].split("(")[0]
        if className.startswith('_'):
            if self.__docType == "eric":
                code = "D205"
            else:
                code = "D105"
        else:
            code = "D104"
        
        if docstringContext is None:
            self.__error(context.start(), 0, code)
            return
        
        docstring = docstringContext.ssource()
        if (not docstring or not docstring.strip() or
                not docstring.strip('\'"')):
            self.__error(context.start(), 0, code)
    
    def __checkTripleDoubleQuotes(self, docstringContext, context):
        """
        Private method to check, that all docstrings are surrounded
        by triple double quotes.
        
        @param docstringContext docstring context (Pep257Context)
        @param context context of the docstring (Pep257Context)
        """
        if docstringContext is None:
            return
        
        docstring = docstringContext.ssource().strip()
        if not docstring.startswith(('"""', 'r"""', 'u"""')):
            self.__error(docstringContext.start(), 0, "D111")
    
    def __checkBackslashes(self, docstringContext, context):
        """
        Private method to check, that all docstrings containing
        backslashes are surrounded by raw triple double quotes.
        
        @param docstringContext docstring context (Pep257Context)
        @param context context of the docstring (Pep257Context)
        """
        if docstringContext is None:
            return
        
        docstring = docstringContext.ssource().strip()
        if "\\" in docstring and not docstring.startswith('r"""'):
            self.__error(docstringContext.start(), 0, "D112")
    
    def __checkUnicode(self, docstringContext, context):
        """
        Private method to check, that all docstrings containing unicode
        characters are surrounded by unicode triple double quotes.
        
        @param docstringContext docstring context (Pep257Context)
        @param context context of the docstring (Pep257Context)
        """
        if docstringContext is None:
            return
        
        docstring = docstringContext.ssource().strip()
        if not docstring.startswith('u"""') and \
                any(ord(char) > 127 for char in docstring):
            self.__error(docstringContext.start(), 0, "D113")
    
    def __checkOneLiner(self, docstringContext, context):
        """
        Private method to check, that one-liner docstrings fit on
        one line with quotes.
        
        @param docstringContext docstring context (Pep257Context)
        @param context context of the docstring (Pep257Context)
        """
        if docstringContext is None:
            return
        
        lines = docstringContext.source()
        if len(lines) > 1:
            nonEmptyLines = [l for l in lines if l.strip().strip('\'"')]
            if len(nonEmptyLines) == 1:
                modLen = len(context.indent() + '"""' +
                             nonEmptyLines[0].strip() + '"""')
                if context.contextType() != "module":
                    modLen += 4
                if not nonEmptyLines[0].strip().endswith("."):
                    # account for a trailing dot
                    modLen += 1
                if modLen <= self.__maxLineLength:
                    self.__error(docstringContext.start(), 0, "D121")
    
    def __checkIndent(self, docstringContext, context):
        """
        Private method to check, that docstrings are properly indented.
        
        @param docstringContext docstring context (Pep257Context)
        @param context context of the docstring (Pep257Context)
        """
        if docstringContext is None:
            return
        
        lines = docstringContext.source()
        if len(lines) == 1:
            return
        
        nonEmptyLines = [l.rstrip() for l in lines[1:] if l.strip()]
        if not nonEmptyLines:
            return
        
        indent = min([len(l) - len(l.strip()) for l in nonEmptyLines])
        if context.contextType() == "module":
            expectedIndent = 0
        else:
            expectedIndent = len(context.indent()) + 4
        if indent != expectedIndent:
            self.__error(docstringContext.start(), 0, "D122")
    
    def __checkEndsWithPeriod(self, docstringContext, context):
        """
        Private method to check, that docstring summaries end with a period.
        
        @param docstringContext docstring context (Pep257Context)
        @param context context of the docstring (Pep257Context)
        """
        if docstringContext is None:
            return
        
        summary, lineNumber = self.__getSummaryLine(docstringContext)
        if not summary.endswith("."):
            self.__error(docstringContext.start() + lineNumber, 0, "D131")
    
    def __checkImperativeMood(self, docstringContext, context):
        """
        Private method to check, that docstring summaries are in
        imperative mood.
        
        @param docstringContext docstring context (Pep257Context)
        @param context context of the docstring (Pep257Context)
        """
        if docstringContext is None:
            return
        
        summary, lineNumber = self.__getSummaryLine(docstringContext)
        firstWord = summary.strip().split()[0]
        if firstWord.endswith("s") and not firstWord.endswith("ss"):
            self.__error(docstringContext.start() + lineNumber, 0, "D132")
    
    def __checkNoSignature(self, docstringContext, context):
        """
        Private method to check, that docstring summaries don't repeat
        the function's signature.
        
        @param docstringContext docstring context (Pep257Context)
        @param context context of the docstring (Pep257Context)
        """
        if docstringContext is None:
            return
        
        functionName = context.source()[0].lstrip().split()[1].split("(")[0]
        summary, lineNumber = self.__getSummaryLine(docstringContext)
        if functionName + "(" in summary.replace(" ", ""):
            self.__error(docstringContext.start() + lineNumber, 0, "D133")
    
    def __checkReturnType(self, docstringContext, context):
        """
        Private method to check, that docstrings mention the return value type.
        
        @param docstringContext docstring context (Pep257Context)
        @param context context of the docstring (Pep257Context)
        """
        if docstringContext is None or self.__isScript:
            return
        
        if "return" not in docstringContext.ssource().lower():
            tokens = list(
                tokenize.generate_tokens(StringIO(context.ssource()).readline))
            return_ = [tokens[i + 1][0] for i,  token in enumerate(tokens)
                       if token[1] == "return"]
            if (set(return_) -
                    set([tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE]) !=
                    set([])):
                self.__error(docstringContext.end(), 0, "D134")
    
    def __checkNoBlankLineBefore(self, docstringContext, context):
        """
        Private method to check, that function/method docstrings are not
        preceded by a blank line.
        
        @param docstringContext docstring context (Pep257Context)
        @param context context of the docstring (Pep257Context)
        """
        if docstringContext is None:
            return
        
        contextLines = context.source()
        cti = 0
        while cti < len(contextLines) and \
                not contextLines[cti].strip().startswith(
                ('"""', 'r"""', 'u"""', "'''", "r'''", "u'''")):
            cti += 1
        if cti == len(contextLines):
            return
        
        if not contextLines[cti - 1].strip():
            self.__error(docstringContext.start(), 0, "D141")
    
    def __checkBlankBeforeAndAfterClass(self, docstringContext, context):
        """
        Private method to check, that class docstrings have one
        blank line around them.
        
        @param docstringContext docstring context (Pep257Context)
        @param context context of the docstring (Pep257Context)
        """
        if docstringContext is None:
            return
        
        contextLines = context.source()
        cti = 0
        while cti < len(contextLines) and \
            not contextLines[cti].strip().startswith(
                ('"""', 'r"""', 'u"""', "'''", "r'''", "u'''")):
            cti += 1
        if cti == len(contextLines):
            return
        
        start = cti
        if contextLines[cti].strip() in (
                '"""', 'r"""', 'u"""', "'''", "r'''", "u'''"):
            # it is a multi line docstring
            cti += 1
        
        while cti < len(contextLines) and \
                not contextLines[cti].strip().endswith(('"""', "'''")):
            cti += 1
        end = cti
        if cti == len(contextLines):
            return
        
        if contextLines[start - 1].strip():
            self.__error(docstringContext.start(), 0, "D142")
        if contextLines[end + 1].strip():
            self.__error(docstringContext.end(), 0, "D143")
    
    def __checkBlankAfterSummary(self, docstringContext, context):
        """
        Private method to check, that docstring summaries are followed
        by a blank line.
        
        @param docstringContext docstring context (Pep257Context)
        @param context context of the docstring (Pep257Context)
        """
        if docstringContext is None:
            return
        
        docstrings = docstringContext.source()
        if len(docstrings) <= 3:
            # correct/invalid one-liner
            return
        
        summary, lineNumber = self.__getSummaryLine(docstringContext)
        if len(docstrings) > 2:
            if docstrings[lineNumber + 1].strip():
                self.__error(docstringContext.start() + lineNumber, 0, "D144")
    
    def __checkBlankAfterLastParagraph(self, docstringContext, context):
        """
        Private method to check, that the last paragraph of docstrings is
        followed by a blank line.
        
        @param docstringContext docstring context (Pep257Context)
        @param context context of the docstring (Pep257Context)
        """
        if docstringContext is None:
            return
        
        docstrings = docstringContext.source()
        if len(docstrings) <= 3:
            # correct/invalid one-liner
            return
        
        if docstrings[-2].strip():
            self.__error(docstringContext.end(), 0, "D145")
    
    ##################################################################
    ## Checking functionality below (eric specific ones)
    ##################################################################

    def __checkEricOneLiner(self, docstringContext, context):
        """
        Private method to check, that one-liner docstrings are on
        three lines (quotes, docstring, quotes).
        
        @param docstringContext docstring context (Pep257Context)
        @param context context of the docstring (Pep257Context)
        """
        if docstringContext is None:
            return
        
        lines = docstringContext.source()
        if len(lines) != 3:
            nonEmptyLines = [l for l in lines if l.strip().strip('\'"')]
            if len(nonEmptyLines) == 1:
                self.__error(docstringContext.start(), 0, "D221")
    
    def __checkEricEndsWithPeriod(self, docstringContext, context):
        """
        Private method to check, that docstring summaries end with a period.
        
        @param docstringContext docstring context (Pep257Context)
        @param context context of the docstring (Pep257Context)
        """
        if docstringContext is None:
            return
        
        summaryLines, lineNumber = self.__getSummaryLines(docstringContext)
        summary = " ".join([s.strip() for s in summaryLines if s])
        if not summary.endswith(".") and \
                not summary.split(None, 1)[0].lower() == "constructor":
            self.__error(
                docstringContext.start() + lineNumber + len(summaryLines) - 1,
                0, "D231")
    
    def __checkEricReturn(self, docstringContext, context):
        """
        Private method to check, that docstrings contain an @return line.
        
        @param docstringContext docstring context (Pep257Context)
        @param context context of the docstring (Pep257Context)
        """
        if docstringContext is None or self.__isScript:
            return
        
        if "@return" not in docstringContext.ssource():
            tokens = list(
                tokenize.generate_tokens(StringIO(context.ssource()).readline))
            return_ = [tokens[i + 1][0] for i,  token in enumerate(tokens)
                       if token[1] == "return"]
            if (set(return_) -
                    set([tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE]) !=
                    set([])):
                self.__error(docstringContext.end(), 0, "D234")
    
    def __checkEricFunctionArguments(self, docstringContext, context):
        """
        Private method to check, that docstrings contain an @param line
        for each argument.
        
        @param docstringContext docstring context (Pep257Context)
        @param context context of the docstring (Pep257Context)
        """
        if docstringContext is None or self.__isScript:
            return
        
        try:
            tree = ast.parse(context.ssource())
        except (SyntaxError, TypeError):
            return
        if (isinstance(tree, ast.Module) and len(tree.body) == 1 and
                isinstance(tree.body[0], ast.FunctionDef)):
            functionDef = tree.body[0]
            argNames, kwNames = self.__getArgNames(functionDef)
            if "self" in argNames:
                argNames.remove("self")
            if "cls" in argNames:
                argNames.remove("cls")
            
            docstring = docstringContext.ssource()
            if (docstring.count("@param") + docstring.count("@keyparam") < 
                    len(argNames + kwNames)):
                self.__error(docstringContext.end(), 0, "D235")
            elif (docstring.count("@param") + docstring.count("@keyparam") > 
                    len(argNames + kwNames)):
                self.__error(docstringContext.end(), 0, "D236")
            else:
                # extract @param and @keyparam from docstring
                args = []
                kwargs = []
                for line in docstringContext.source():
                    if line.strip().startswith(("@param", "@keyparam")):
                        at, name, _ = line.strip().split(None, 2)
                        if at == "@keyparam":
                            kwargs.append(name)
                        args.append(name)
                
                # do the checks
                for name in kwNames:
                    if name not in kwargs:
                        self.__error(docstringContext.end(), 0, "D237")
                        return
                if argNames + kwNames != args:
                    self.__error(docstringContext.end(), 0, "D238")
    
    def __checkEricBlankAfterSummary(self, docstringContext, context):
        """
        Private method to check, that docstring summaries are followed
        by a blank line.
        
        @param docstringContext docstring context (Pep257Context)
        @param context context of the docstring (Pep257Context)
        """
        if docstringContext is None:
            return
        
        docstrings = docstringContext.source()
        if len(docstrings) <= 3:
            # correct/invalid one-liner
            return
        
        summaryLines, lineNumber = self.__getSummaryLines(docstringContext)
        if len(docstrings) > lineNumber + len(summaryLines) - 1:
            if docstrings[lineNumber + len(summaryLines)].strip():
                self.__error(docstringContext.start() + lineNumber, 0, "D246")
    
    def __checkEricNoBlankBeforeAndAfterClassOrFunction(
            self, docstringContext, context):
        """
        Private method to check, that class and function/method docstrings
        have no blank line around them.
        
        @param docstringContext docstring context (Pep257Context)
        @param context context of the docstring (Pep257Context)
        """
        if docstringContext is None:
            return
        
        contextLines = context.source()
        isClassContext = contextLines[0].lstrip().startswith("class ")
        cti = 0
        while cti < len(contextLines) and \
            not contextLines[cti].strip().startswith(
                ('"""', 'r"""', 'u"""', "'''", "r'''", "u'''")):
            cti += 1
        if cti == len(contextLines):
            return
        
        start = cti
        if contextLines[cti].strip() in (
                '"""', 'r"""', 'u"""', "'''", "r'''", "u'''"):
            # it is a multi line docstring
            cti += 1
        
        while cti < len(contextLines) and \
                not contextLines[cti].strip().endswith(('"""', "'''")):
            cti += 1
        end = cti
        if cti == len(contextLines):
            return
        
        if isClassContext:
            if not contextLines[start - 1].strip():
                self.__error(docstringContext.start(), 0, "D242")
            if not contextLines[end + 1].strip():
                self.__error(docstringContext.end(), 0, "D243")
        else:
            if not contextLines[start - 1].strip():
                self.__error(docstringContext.start(), 0, "D244")
            if not contextLines[end + 1].strip():
                self.__error(docstringContext.end(), 0, "D245")
    
    def __checkEricNBlankAfterLastParagraph(self, docstringContext, context):
        """
        Private method to check, that the last paragraph of docstrings is
        not followed by a blank line.
        
        @param docstringContext docstring context (Pep257Context)
        @param context context of the docstring (Pep257Context)
        """
        if docstringContext is None:
            return
        
        docstrings = docstringContext.source()
        if len(docstrings) <= 3:
            # correct/invalid one-liner
            return
        
        if not docstrings[-2].strip():
            self.__error(docstringContext.end(), 0, "D247")

#
# eflag: FileType = Python2
