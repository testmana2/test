# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#
# Original (c) 2005 Divmod, Inc.  See LICENSE file for details
#
# This module is based on pyflakes for Python2 but was heavily hacked to
# work with Python3 and Qt (translatable messages)

"""
Module implementing the messages for py3flakes.
"""

from PyQt4.QtCore import QCoreApplication


class Message(object):
    """
    Class defining the base for all specific message classes.
    """
    message = ''
    message_args = ()
    
    def __init__(self, filename, loc):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location (integer)
        """
        self.filename = filename
        self.lineno = loc.lineno
        self.col = getattr(loc, 'col_offset', 0)

    def __str__(self):
        """
        Special method return a string representation of the instance object.
        
        @return string representation of the object (string)
        """
        return '{0}:{1} {2}'.format(
            self.filename, self.lineno,
            self.message.format(*self.message_args))
    
    def getMessageData(self):
        """
        Public method to get the individual message data elements.
        
        @return tuple containing file name, line number and message
            (string, integer, string)
        """
        return (self.filename, self.lineno,
                self.message.format(*self.message_args))


class UnusedImport(Message):
    """
    Class defining the "Unused Import" message.
    """
    message = QCoreApplication.translate(
        'py3Flakes',
        '{0!r} imported but unused.')
    
    def __init__(self, filename, loc, name):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location (integer)
        @param name name of the unused import (string)
        """
        Message.__init__(self, filename, loc)
        self.message_args = (name,)


class RedefinedWhileUnused(Message):
    """
    Class defining the "Redefined While Unused" message.
    """
    message = QCoreApplication.translate(
        'py3Flakes',
        'Redefinition of unused {0!r} from line {1!r}.')
    
    def __init__(self, filename, loc, name, orig_loc):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location (integer)
        @param name name of the redefined object (string)
        @param orig_loc location of the original definition (integer)
        """
        Message.__init__(self, filename, loc)
        self.message_args = (name, orig_loc.lineno)


class RedefinedInListComp(Message):
    """
    Class defining the "Redefined by list comprehension" message.
    """
    message = QCoreApplication.translate(
        'py3Flakes',
        'list comprehension redefines {0!r} from line {1!r}')

    def __init__(self, filename, loc, name, orig_loc):
        Message.__init__(self, filename, loc)
        self.message_args = (name, orig_loc.lineno)


class ImportShadowedByLoopVar(Message):
    """
    Class defining the "Import Shadowed By Loop Var" message.
    """
    message = QCoreApplication.translate(
        'py3Flakes',
        'Import {0!r} from line {1!r} shadowed by loop variable.')
    
    def __init__(self, filename, loc, name, orig_loc):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location (integer)
        @param name name of the shadowed import (string)
        @param orig_loc location of the import (integer)
        """
        Message.__init__(self, filename, loc)
        self.message_args = (name, orig_loc.lineno)


class ImportStarUsed(Message):
    """
    Class defining the "Import Star Used" message.
    """
    message = QCoreApplication.translate(
        'py3Flakes',
        "'from {0} import *' used; unable to detect undefined names.")
    
    def __init__(self, filename, loc, modname):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location (integer)
        @param modname name of the module imported using star import (string)
        """
        Message.__init__(self, filename, loc)
        self.message_args = (modname,)


class UndefinedName(Message):
    """
    Class defining the "Undefined Name" message.
    """
    message = QCoreApplication.translate('py3Flakes', 'Undefined name {0!r}.')
    
    def __init__(self, filename, loc, name):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location (integer)
        @param name undefined name (string)
        """
        Message.__init__(self, filename, loc)
        self.message_args = (name,)


class DoctestSyntaxError(Message):
    """
    Class defining the "Doctest syntax error" message.
    """
    message = QCoreApplication.translate(
        'py3Flakes',
        'syntax error in doctest')

    def __init__(self, filename, loc, position=None):
        Message.__init__(self, filename, loc)
        if position:
            (self.lineno, self.col) = position
        self.message_args = ()


class UndefinedExport(Message):
    """
    Class defining the "Undefined Export" message.
    """
    message = QCoreApplication.translate(
        'py3Flakes', 'Undefined name {0!r} in __all__.')
    
    def __init__(self, filename, loc, name):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location (integer)
        @param name undefined exported name (string)
        """
        Message.__init__(self, filename, loc)
        self.message_args = (name,)


class UndefinedLocal(Message):
    """
    Class defining the "Undefined Local Variable" message.
    """
    message = QCoreApplication.translate(
        'py3Flakes',
        "Local variable {0!r} (defined in enclosing scope on line {1!r})"
        " referenced before assignment.")
    
    def __init__(self, filename, loc, name, orig_loc):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location (integer)
        @param name name of the prematurely referenced variable (string)
        @param orig_loc location of the variable definition (integer)
        """
        Message.__init__(self, filename, loc)
        self.message_args = (name, orig_loc.lineno)


class DuplicateArgument(Message):
    """
    Class defining the "Duplicate Argument" message.
    """
    message = QCoreApplication.translate(
        'py3Flakes',
        'Duplicate argument {0!r} in function definition.')
    
    def __init__(self, filename, loc, name):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location (integer)
        @param name name of the duplicate argument (string)
        """
        Message.__init__(self, filename, loc)
        self.message_args = (name,)


class RedefinedFunction(Message):
    """
    Class defining the "Redefined Function" message.
    """
    message = QCoreApplication.translate(
        'py3Flakes',
        'Redefinition of function {0!r} from line {1!r}.')
    
    def __init__(self, filename, loc, name, orig_loc):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location (integer)
        @param name name of the redefined function (string)
        @param orig_loc location of the original definition (integer)
        """
        Message.__init__(self, filename, loc)
        self.message_args = (name, orig_loc.lineno)


class LateFutureImport(Message):
    """
    Class defining the "Late Future Import" message.
    """
    message = QCoreApplication.translate(
        'py3Flakes',
        'Future import(s) {0!r} after other statements.')
    
    def __init__(self, filename, loc, names):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location (integer)
        @param names names of the imported futures (string)
        """
        Message.__init__(self, filename, loc)
        self.message_args = (names,)


class UnusedVariable(Message):
    """
    Class defining the "Unused Variable" message.
    
    Indicates that a variable has been explicitly assigned to but not actually
    used.
    """
    message = QCoreApplication.translate(
        'py3Flakes',
        'Local variable {0!r} is assigned to but never used.')
    
    def __init__(self, filename, loc, names):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location (integer)
        @param name name of the unused variable (string)
        """
        Message.__init__(self, filename, loc)
        self.message_args = (names,)


class ReturnWithArgsInsideGenerator(Message):
    """
    Indicates a return statement with arguments inside a generator.
    """
    message = QCoreApplication.translate(
        'py3Flakes',
        '\'return\' with argument inside generator')
