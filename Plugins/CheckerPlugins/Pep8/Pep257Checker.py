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

from PyQt4.QtCore import QT_TRANSLATE_NOOP, QCoreApplication


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
        "D141"
    ]
    
    Messages = {
        "D101": QT_TRANSLATE_NOOP(
            "Pep257Checker", "module is missing a docstring"),
        "D102": QT_TRANSLATE_NOOP(
            "Pep257Checker", "public function/method is missing a docstring"),
        "D103": QT_TRANSLATE_NOOP(
            "Pep257Checker",
            "private function/method may be missing a docstring"),
        "D104": QT_TRANSLATE_NOOP(
            "Pep257Checker", "public class is missing a docstring"),
        "D105": QT_TRANSLATE_NOOP(
            "Pep257Checker", "private class may be missing a docstring"),
        "D111": QT_TRANSLATE_NOOP(
            "Pep257Checker", 'docstring not surrounded by """'),
        "D112": QT_TRANSLATE_NOOP(
            "Pep257Checker", 'docstring containing \\ not surrounded by r"""'),
        "D113": QT_TRANSLATE_NOOP(
            "Pep257Checker",
            'docstring containing unicode character not surrounded by u"""'),
        "D121": QT_TRANSLATE_NOOP(
            "Pep257Checker", "one-liner docstring on multiple lines"),
        "D122": QT_TRANSLATE_NOOP(
            "Pep257Checker", "docstring has wrong indentation"),
        "D131": QT_TRANSLATE_NOOP(
            "Pep257Checker", "docstring summary does not end with a period"),
        "D132": QT_TRANSLATE_NOOP(
            "Pep257Checker",
            "docstring summary is not in imperative mood"
            " (Does instead of Do)"),
        "D133": QT_TRANSLATE_NOOP(
            "Pep257Checker",
            "docstring summary looks like a function's/method's signature"),
        "D134": QT_TRANSLATE_NOOP(
            "Pep257Checker",
            "docstring does not mention the return value type"),
        "D141": QT_TRANSLATE_NOOP(
            "Pep257Checker", "docstring is separated by a blank line"),
    }
    
    def __init__(self, source, filename, select, ignore, expected, repeat):
        """
        Constructor (according to 'extended' pep8.py API)
        
        @param source source code to be checked (list of string)
        @param filename name of the source file (string)
        @param select list of selected codes (list of string)
        @param ignore list of codes to be ignored (list of string)
        @param expected list of expected codes (list of string)
        @param repeat flag indicating to report each occurrence of a code
            (boolean)
        """
        self.__select = tuple(select)
        self.__ignore = tuple(ignore)
        self.__expected = expected[:]
        self.__repeat = repeat
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
        self.__checkersWithCodes = {
            "moduleDocstring": [
                (self.__checkModulesDocstrings, ("D101",)),
            ],
            "functionDocstring": [
            ],
            "classDocstring": [
                (self.__checkClassDocstring, ("D104", "D105")),
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
            ],
        }
        
        self.__checkers = {}
        for key, checkers in self.__checkersWithCodes.items():
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
            if code in Pep257Checker.Codes:
                text = self.__getMessage(code, *args)
            # record the issue with one based line number
            self.errors.append((self.__filename, lineNumber + 1, offset, text))
    
    def __getMessage(self, code, *args):
        """
        Private method to get a translated and formatted message for a
        given code.
        
        @param code message code (string)
        @param args arguments for a formatted message (list)
        @return translated and formatted message (string)
        """
        if code in Pep257Checker.Messages:
            return code + " " + QCoreApplication.translate(
                "Pep257Checker", Pep257Checker.Messages[code]).format(*args)
        else:
            return code + " " + QCoreApplication.translate(
                "Pep257Checker", "no message for this code defined")
    
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
                .strip())
        
        if len(lines) == 1 or len(line) > 0:
            return line, 0
        return lines[1].strip(), 1
        
        first_line = lines[0].strip()
        if len(lines) == 1 or len(first_line) > 0:
            return first_line, 0
        return lines[1].strip(), 1
    
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
        if what.startswith('module'):
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
    ## Checking functionality below
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
        if docstringContext is None or self.__isScript:
            return
        
        contextLines = context.source()
        cti = 0
        while not contextLines[cti].strip().startswith(
                ('"""', 'r"""', 'u"""')):
            cti += 1
        if not contextLines[cti - 1].strip():
            self.__error(docstringContext.start(), 0, "D141")
    
    # D142: check_blank_before_after_class
##def check_blank_before_after_class(class_docstring, context, is_script):
##    """Class docstring should have 1 blank line around them.
##
##    Insert a blank line before and after all docstrings (one-line or
##    multi-line) that document a class -- generally speaking, the class's
##    methods are separated from each other by a single blank line, and the
##    docstring needs to be offset from the first method by a blank line;
##    for symmetry, put a blank line between the class header and the
##    docstring.
##
##    """
##    if not class_docstring:
##        return
##    before, after = context.split(class_docstring)[:2]
##    before_blanks = [not line.strip() for line in before.split('\n')]
##    after_blanks = [not line.strip() for line in after.split('\n')]
##    if before_blanks[-3:] != [False, True, True]:
##        return True
##    if not all(after_blanks) and after_blanks[:3] != [True, True, False]:
##        return True
    
    # D143: check_blank_after_summary
##def check_blank_after_summary(docstring, context, is_script):
##    """Blank line missing after one-line summary.
##
##    Multi-line docstrings consist of a summary line just like a one-line
##    docstring, followed by a blank line, followed by a more elaborate
##    description. The summary line may be used by automatic indexing tools;
##    it is important that it fits on one line and is separated from the
##    rest of the docstring by a blank line.
##
##    """
##    if not docstring:
##        return
##    lines = eval(docstring).split('\n')
##    if len(lines) > 1:
##        (summary_line, line_number) = get_summary_line_info(docstring)
##        if len(lines) <= (line_number+1) or lines[line_number+1].strip() != '':
##            return True
    
    # D144: check_blank_after_last_paragraph
##def check_blank_after_last_paragraph(docstring, context, is_script):
##    """Multiline docstring should end with 1 blank line.
##
##    The BDFL recommends inserting a blank line between the last
##    paragraph in a multi-line docstring and its closing quotes,
##    placing the closing quotes on a line by themselves.
##
##    """
##    if (not docstring) or len(eval(docstring).split('\n')) == 1:
##        return
##    blanks = [not line.strip() for line in eval(docstring).split('\n')]
##    if blanks[-3:] != [False, True, True]:
##        return True
