# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#
# Original (c) 2005-2008 Divmod, Inc.
#
# This module is based on pyflakes for Python2 but was heavily hacked to
# work with Python3

import builtins
import os.path
import ast

from . import messages

class Binding(object):
    """
    Represents the binding of a value to a name.

    The checker uses this to keep track of which names have been bound and
    which names have not. See Assignment for a special type of binding that
    is checked with stricter rules.
    """
    def __init__(self, name, source):
        self.name = name
        self.source = source
        self.used = False

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<{0} object {1!r} from line {2!r} at 0x{3:x}>'.format(
            self.__class__.__name__,
            self.name,
            self.source.lineno,
            id(self))

class UnBinding(Binding):
    '''
    Created by the 'del' operator.
    '''

class Importation(Binding):
    """
    A binding created by an import statement.
    """
    def __init__(self, name, source):
        self.fullName = name
        name = name.split('.')[0]
        super(Importation, self).__init__(name, source)

class Argument(Binding):
    """
    Represents binding a name as an argument.
    """

class Assignment(Binding):
    """
    Represents binding a name with an explicit assignment.

    The checker will raise warnings for any Assignment that isn't used. Also,
    the checker does not consider assignments in tuple/list unpacking to be
    Assignments, rather it treats them as simple Bindings.
    """

class FunctionDefinition(Binding):
    """
    Represents a function definition.
    """
    pass

class ExportBinding(Binding):
    """
    A binding created by an __all__ assignment.  If the names in the list
    can be determined statically, they will be treated as names for export and
    additional checking applied to them.

    The only __all__ assignment that can be recognized is one which takes
    the value of a literal list containing literal strings.  For example::

        __all__ = ["foo", "bar"]

    Names which are imported and not otherwise used but appear in the value of
    __all__ will not have an unused import warning reported for them.
    """
    def names(self):
        """
        Return a list of the names referenced by this binding.
        """
        names = []
        if isinstance(self.source, ast.List):
            for node in self.source.elts:
                if isinstance(node, (ast.Str, ast.Bytes)):
                    names.append(node.s)
                elif isinstance(node, ast.Num):
                    names.append(node.n)
        return names

class Scope(dict):
    """
    Class defining the scope base class.
    """
    importStarred = False       # set to True when import * is found

    def __repr__(self):
        return '<{0} at 0x{1:x} {2}>'.format(
            self.__class__.__name__, id(self), dict.__repr__(self))

    def __init__(self):
        super(Scope, self).__init__()

class ClassScope(Scope):
    """
    Class representing a name scope for a class.
    """
    pass

class FunctionScope(Scope):
    """
    Class representing a name scope for a function.
    """
    def __init__(self):
        super(FunctionScope, self).__init__()
        self.globals = {}

class ModuleScope(Scope):
    """
    Class representing a name scope for a module.
    """
    pass

# Globally defined names which are not attributes of the builtins module.
_MAGIC_GLOBALS = ['__file__', '__builtins__']

class Checker(object):
    """
    Class to check the cleanliness and sanity of Python code.
    """
    nodeDepth = 0
    traceTree = False

    def __init__(self, module, filename = '(none)'):
        """
        Constructor
        
        @param module parsed module tree or module source code
        @param filename name of the module file (string)
        """
        self._deferredFunctions = []
        self._deferredAssignments = []
        self.dead_scopes = []
        self.messages = []
        self.filename = filename
        self.scopeStack = [ModuleScope()]
        self.futuresAllowed = True
        
        if isinstance(module, str):
            module = ast.parse(module, filename, "exec")
        self.handleBody(module)
        self._runDeferred(self._deferredFunctions)
        # Set _deferredFunctions to None so that deferFunction will fail
        # noisily if called after we've run through the deferred functions.
        self._deferredFunctions = None
        self._runDeferred(self._deferredAssignments)
        # Set _deferredAssignments to None so that deferAssignment will fail
        # noisly if called after we've run through the deferred assignments.
        self._deferredAssignments = None
        del self.scopeStack[1:]
        self.popScope()
        self.check_dead_scopes()

    def deferFunction(self, callable):
        '''
        Schedule a function handler to be called just before completion.

        This is used for handling function bodies, which must be deferred
        because code later in the file might modify the global scope. When
        `callable` is called, the scope at the time this is called will be
        restored, however it will contain any new bindings added to it.
        '''
        self._deferredFunctions.append((callable, self.scopeStack[:]))

    def deferAssignment(self, callable):
        """
        Schedule an assignment handler to be called just after deferred
        function handlers.
        """
        self._deferredAssignments.append((callable, self.scopeStack[:]))

    def _runDeferred(self, deferred):
        """
        Run the callables in deferred using their associated scope stack.
        """
        for handler, scope in deferred:
            self.scopeStack = scope
            handler()

    def scope(self):
        return self.scopeStack[-1]
    scope = property(scope)

    def popScope(self):
        self.dead_scopes.append(self.scopeStack.pop())

    def check_dead_scopes(self):
        """
        Look at scopes which have been fully examined and report names in them
        which were imported but unused.
        """
        for scope in self.dead_scopes:
            export = isinstance(scope.get('__all__'), ExportBinding)
            if export:
                all = scope['__all__'].names()
                if os.path.split(self.filename)[1] != '__init__.py':
                    # Look for possible mistakes in the export list
                    undefined = set(all) - set(scope)
                    for name in undefined:
                        self.report(
                            messages.UndefinedExport,
                            scope['__all__'].source.lineno,
                            name)
            else:
                all = []

            # Look for imported names that aren't used.
            for importation in scope.values():
                if isinstance(importation, Importation):
                    if not importation.used and importation.name not in all:
                        self.report(
                            messages.UnusedImport,
                            importation.source.lineno,
                            importation.name)

    def pushFunctionScope(self):
        self.scopeStack.append(FunctionScope())

    def pushClassScope(self):
        self.scopeStack.append(ClassScope())

    def report(self, messageClass, *args, **kwargs):
        self.messages.append(messageClass(self.filename, *args, **kwargs))

    def handleBody(self, tree):
        for node in tree.body:
            self.handleNode(node, tree)

    def handleNode(self, node, parent):
        if node:
            node.parent = parent
            if self.traceTree:
                print('  ' * self.nodeDepth + node.__class__.__name__)
            self.nodeDepth += 1
            nodeType = node.__class__.__name__.upper()
            try:
                handler = getattr(self, nodeType)
                handler(node)
            finally:
                self.nodeDepth -= 1
            if self.traceTree:
                print('  ' * self.nodeDepth + 'end ' + node.__class__.__name__)

    def ignore(self, node):
        pass
    
    # ast nodes to be ignored
    PASS = CONTINUE = BREAK = ELLIPSIS = NUM = STR = BYTES = \
    ATTRIBUTES = AND = OR = ADD = SUB = MULT = DIV = \
    MOD = POW = LSHIFT = RSHIFT = BITOR = BITXOR = BITAND = FLOORDIV = \
    INVERT = NOT = UADD = USUB = INVERT = NOT = UADD = USUB = ignore

    def addBinding(self, lineno, value, reportRedef = True):
        '''Called when a binding is altered.

        @param lineno line of the statement responsible for the change (integer)
        @param value the optional new value, a Binding instance, associated
            with the binding; if None, the binding is deleted if it exists
        @param reportRedef flag indicating if rebinding while unused will be
            reported (boolean)
        '''
        if (isinstance(self.scope.get(value.name), FunctionDefinition)
                    and isinstance(value, FunctionDefinition)):
            self.report(messages.RedefinedFunction,
                        lineno, value.name, self.scope[value.name].source.lineno)

        if not isinstance(self.scope, ClassScope):
            for scope in self.scopeStack[::-1]:
                existing = scope.get(value.name)
                if (isinstance(existing, Importation)
                        and not existing.used
                        and (not isinstance(value, Importation) or value.fullName == existing.fullName)
                        and reportRedef):

                    self.report(messages.RedefinedWhileUnused,
                                lineno, value.name, scope[value.name].source.lineno)

        if isinstance(value, UnBinding):
            try:
                del self.scope[value.name]
            except KeyError:
                self.report(messages.UndefinedName, lineno, value.name)
        else:
            self.scope[value.name] = value
    
    ############################################################
    ## individual handler methods below
    ############################################################
    
    def LIST(self, node):
        for elt in node.elts:
            self.handleNode(elt, node)
    
    SET = TUPLE = LIST
    
    def DICT(self, node):
        for key in node.keys:
            self.handleNode(key, node)
        for val in node.values:
            self.handleNode(val, node)
    
    def WITH(self, node):
        """
        Handle with by checking the target of the statement (which can be an
        identifier, a list or tuple of targets, an attribute, etc) for
        undefined names and defining any it adds to the scope and by continuing
        to process the suite within the statement.
        """
        # Check the "foo" part of a "with foo as bar" statement.  Do this no
        # matter what, since there's always a "foo" part.
        self.handleNode(node.context_expr, node)

        arg = None
        if node.optional_vars is not None:
            arg = Argument(node.optional_vars.id, node)
            self.addBinding(node.lineno, arg, reportRedef=False)
        self.handleBody(node)
        if arg:
            del self.scope[arg.name]

    def GLOBAL(self, node):
        """
        Keep track of globals declarations.
        """
        if isinstance(self.scope, FunctionScope):
            self.scope.globals.update(dict.fromkeys(node.names))
    
    NONLOCAL = GLOBAL

    def LISTCOMP(self, node):
        for generator in node.generators:
            self.handleNode(generator, node)
        self.handleNode(node.elt, node)
    
    SETCOMP = GENERATOREXP = LISTCOMP
    
    def DICTCOMP(self, node):
        for generator in node.generators:
            self.handleNode(generator, node)
        self.handleNode(node.key, node)
        self.handleNode(node.value, node)
    
    def COMPREHENSION(self, node):
        node.target.parent = node
        self.handleAssignName(node.target)
        self.handleNode(node.iter, node)
        for elt in node.ifs:
            self.handleNode(elt, node)
    
    def FOR(self, node):
        """
        Process bindings for loop variables.
        """
        vars = []
        def collectLoopVars(n):
            if isinstance(n, ast.Name):
                vars.append(n.id)

        collectLoopVars(node.target)
        for varn in vars:
            if (isinstance(self.scope.get(varn), Importation)
                    # unused ones will get an unused import warning
                    and self.scope[varn].used):
                self.report(messages.ImportShadowedByLoopVar,
                            node.lineno, varn, self.scope[varn].source.lineno)
        
        node.target.parent = node
        self.handleAssignName(node.target)
        self.handleNode(node.iter, node)
        self.handleBody(node)

    def NAME(self, node):
        """
        Locate the name in locals / function / globals scopes.
        """
        # try local scope
        importStarred = self.scope.importStarred
        try:
            self.scope[node.id].used = (self.scope, node.lineno)
        except KeyError:
            pass
        else:
            return

        # try enclosing function scopes
        for scope in self.scopeStack[-2:0:-1]:
            importStarred = importStarred or scope.importStarred
            if not isinstance(scope, FunctionScope):
                continue
            try:
                scope[node.id].used = (self.scope, node.lineno)
            except KeyError:
                pass
            else:
                return

        # try global scope
        importStarred = importStarred or self.scopeStack[0].importStarred
        try:
            self.scopeStack[0][node.id].used = (self.scope, node.lineno)
        except KeyError:
            if ((not hasattr(builtins, node.id))
                    and node.id not in _MAGIC_GLOBALS
                    and not importStarred):
                if (os.path.basename(self.filename) == '__init__.py' and
                    node.id == '__path__'):
                    # the special name __path__ is valid only in packages
                    pass
                else:
                    self.report(messages.UndefinedName, node.lineno, node.id)

    def FUNCTIONDEF(self, node):
        if getattr(node, "decorator_list", None) is not None:
            for decorator in node.decorator_list:
                self.handleNode(decorator, node)
        self.addBinding(node.lineno, FunctionDefinition(node.name, node))
        self.LAMBDA(node)

    def LAMBDA(self, node):
        for default in node.args.defaults + node.args.kw_defaults:
            self.handleNode(default, node)

        def runFunction():
            args = []

            def addArgs(arglist):
                for arg in arglist:
                    if isinstance(arg.arg, tuple):
                        addArgs(arg.arg)
                    else:
                        if arg.arg in args:
                            self.report(messages.DuplicateArgument, node.lineno, arg.arg)
                        args.append(arg.arg)
            
            def checkUnusedAssignments():
                """
                Check to see if any assignments have not been used.
                """
                for name, binding in self.scope.items():
                    if (not binding.used and not name in self.scope.globals
                        and isinstance(binding, Assignment)):
                        self.report(messages.UnusedVariable,
                                    binding.source.lineno, name)

            self.pushFunctionScope()
            addArgs(node.args.args)
            addArgs(node.args.kwonlyargs)
            for name in args:
                self.addBinding(node.lineno, Argument(name, node), reportRedef=False)
            if node.args.vararg:
                self.addBinding(node.lineno, Argument(node.args.vararg, node), 
                                reportRedef=False)
            if node.args.kwarg:
                self.addBinding(node.lineno, Argument(node.args.kwarg, node), 
                                reportRedef=False)
            if isinstance(node.body, list):
                self.handleBody(node)
            else:
                self.handleNode(node.body, node)
            self.deferAssignment(checkUnusedAssignments)
            self.popScope()

        self.deferFunction(runFunction)

    def CLASSDEF(self, node):
        """
        Check names used in a class definition, including its decorators, base
        classes, and the body of its definition.  Additionally, add its name to
        the current scope.
        """
        if getattr(node, "decorator_list", None) is not None:
            for decorator in node.decorator_list:
                self.handleNode(decorator, node)
        for baseNode in node.bases:
            self.handleNode(baseNode, node)
        self.addBinding(node.lineno, Binding(node.name, node))
        self.pushClassScope()
        self.handleBody(node)
        self.popScope()

    def handleAssignName(self, node):
        # special handling for ast.Subscript and ast.Starred
        if isinstance(node, (ast.Subscript, ast.Starred)):
            node.value.parent = node
            self.handleAssignName(node.value)
            if isinstance(node, ast.Subscript):
                if isinstance(node.slice, ast.Slice):
                    self.handleNode(node.slice.lower, node)
                    self.handleNode(node.slice.upper, node)
                else:
                    self.handleNode(node.slice.value, node)
            return
        
        # if the name hasn't already been defined in the current scope
        if isinstance(node, (ast.Tuple, ast.List)):
            for elt in node.elts:
                elt.parent = node
                self.handleAssignName(elt)
            return
        
        if isinstance(node, ast.Attribute):
            self.handleNode(node.value, node)
            return
        
        if isinstance(self.scope, FunctionScope) and node.id not in self.scope:
            # for each function or module scope above us
            for scope in self.scopeStack[:-1]:
                if not isinstance(scope, (FunctionScope, ModuleScope)):
                    continue
                # if the name was defined in that scope, and the name has
                # been accessed already in the current scope, and hasn't
                # been declared global
                if (node.id in scope
                        and scope[node.id].used
                        and scope[node.id].used[0] is self.scope
                        and node.id not in self.scope.globals):
                    # then it's probably a mistake
                    self.report(messages.UndefinedLocal,
                                scope[node.id].used[1],
                                node.id,
                                scope[node.id].source.lineno)
                    break

        if isinstance(node.parent,
                      (ast.For, ast.ListComp, ast.GeneratorExp,
                       ast.Tuple, ast.List)):
            binding = Binding(node.id, node)
        elif (node.id == '__all__' and
              isinstance(self.scope, ModuleScope) and
              isinstance(node.parent, ast.Assign)):
            binding = ExportBinding(node.id, node.parent.value)
        else:
            binding = Assignment(node.id, node)
        if node.id in self.scope:
            binding.used = self.scope[node.id].used
        self.addBinding(node.lineno, binding)

    def ASSIGN(self, node):
        self.handleNode(node.value, node)
        for subnode in node.targets[::-1]:
            subnode.parent = node
            if isinstance(subnode, ast.Attribute):
                self.handleNode(subnode.value, subnode)
            else:
                self.handleAssignName(subnode)
    
    def AUGASSIGN(self, node):
        self.handleNode(node.value, node)
        self.handleNode(node.target, node)
    
    def IMPORT(self, node):
        for alias in node.names:
            name = alias.asname or alias.name
            importation = Importation(name, node)
            self.addBinding(node.lineno, importation)

    def IMPORTFROM(self, node):
        if node.module == '__future__':
            if not self.futuresAllowed:
                self.report(messages.LateFutureImport, node.lineno, 
                            [n.name for n in node.names])
        else:
            self.futuresAllowed = False

        for alias in node.names:
            if alias.name == '*':
                self.scope.importStarred = True
                self.report(messages.ImportStarUsed, node.lineno, node.module)
                continue
            name = alias.asname or alias.name
            importation = Importation(name, node)
            if node.module == '__future__':
                importation.used = (self.scope, node.lineno)
            self.addBinding(node.lineno, importation)
    
    def CALL(self, node):
        self.handleNode(node.func, node)
        for arg in node.args:
            self.handleNode(arg, node)
        for kw in node.keywords:
            self.handleNode(kw, node)
        node.starargs and self.handleNode(node.starargs, node)
        node.kwargs and self.handleNode(node.kwargs, node)
    
    def KEYWORD(self, node):
        self.handleNode(node.value, node)
    
    def BOOLOP(self, node):
        for val in node.values:
            self.handleNode(val, node)
    
    def BINOP(self, node):
        self.handleNode(node.left, node)
        self.handleNode(node.right, node)
    
    def UNARYOP(self, node):
        self.handleNode(node.operand, node)
    
    def RETURN(self, node):
        node.value and self.handleNode(node.value, node)
    
    def DELETE(self, node):
        for tgt in node.targets:
            self.handleNode(tgt, node)
    
    def EXPR(self, node):
        self.handleNode(node.value, node)
    
    def ATTRIBUTE(self, node):
        self.handleNode(node.value, node)
    
    def IF(self, node):
        self.handleNode(node.test, node)
        self.handleBody(node)
        for stmt in node.orelse:
            self.handleNode(stmt, node)
    
    WHILE = IF
    
    def RAISE(self, node):
        node.exc and self.handleNode(node.exc, node)
        node.cause and self.handleNode(node.cause, node)
    
    def TRYEXCEPT(self, node):
        self.handleBody(node)
        for handler in node.handlers:
            self.handleNode(handler, node)
        for stmt in node.orelse:
            self.handleNode(stmt, node)
    
    def TRYFINALLY(self, node):
        self.handleBody(node)
        for stmt in node.finalbody:
            self.handleNode(stmt, node)
    
    def EXCEPTHANDLER(self, node):
        node.type and self.handleNode(node.type, node)
        if node.name:
            node.id = node.name
            self.handleAssignName(node)
        self.handleBody(node)
    
    def ASSERT(self, node):
        self.handleNode(node.test, node)
        node.msg and self.handleNode(node.msg, node)
    
    def COMPARE(self, node):
        self.handleNode(node.left, node)
        for comparator in node.comparators:
            self.handleNode(comparator, node)
    
    def YIELD(self, node):
        node.value and self.handleNode(node.value, node)
    
    def SUBSCRIPT(self, node):
        self.handleNode(node.value, node)
        self.handleNode(node.slice, node)
    
    def SLICE(self, node):
        node.lower and self.handleNode(node.lower, node)
        node.upper and self.handleNode(node.upper, node)
        node.step and self.handleNode(node.step, node)
    
    def EXTSLICE(self, node):
        for slice in node.dims:
            self.handleNode(slice, node)
    
    def INDEX(self, node):
        self.handleNode(node.value, node)
    
    def IFEXP(self, node):
        self.handleNode(node.test, node)
        self.handleNode(node.body, node)
        self.handleNode(node.orelse, node)
    
    def STARRED(self, node):
        self.handleNode(node.value, node)
