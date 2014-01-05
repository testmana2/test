# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#
# Original (c) 2005 Divmod, Inc.  See __init__.py file for details
#
# This module is based on pyflakes but was heavily hacked to
# work within Eric5 and Qt (translatable messages)

"""
Provide the class Message and its subclasses.
"""

# Tell 'lupdate' which strings to keep for translation.
QT_TRANSLATE_NOOP = lambda mod, txt: txt


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
        @param loc location of warning (object)
        """
        self.filename = filename
        self.lineno = loc.lineno
        self.col = getattr(loc, 'col_offset', 0)

    def __str__(self):
        """
        Special method return a string representation of the instance object.
        
        @return string representation of the object (string)
        """
        return '%s:%s: %s' % (self.filename, self.lineno,
                              self.message % self.message_args)
    
    def getMessageData(self):
        """
        Public method to get the individual message data elements.
        
        @return tuple containing file name, line number and message
            (string, integer, string)
        """
        return (self.filename, self.lineno, self.col, self.message,
                self.message_args)


class UnusedImport(Message):
    """
    Class defining the "Unused Import" message.
    """
    message = QT_TRANSLATE_NOOP(
        'py3Flakes',
        '{0!r} imported but unused.')

    def __init__(self, filename, loc, name):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location of warning (object)
        @param name name of the unused import (string)
        """
        Message.__init__(self, filename, loc)
        self.message_args = (name,)


class RedefinedWhileUnused(Message):
    """
    Class defining the "Redefined While Unused" message.
    """
    message = QT_TRANSLATE_NOOP(
        'py3Flakes',
        'Redefinition of unused {0!r} from line {1!r}.')

    def __init__(self, filename, loc, name, orig_loc):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location of warning (object)
        @param name name of the redefined object (string)
        @param orig_loc location of the original definition (object)
        """
        Message.__init__(self, filename, loc)
        self.message_args = (name, orig_loc.lineno)


class RedefinedInListComp(Message):
    """
    Class defining the list comprehension redefinition.
    """
    message = QT_TRANSLATE_NOOP(
        'py3Flakes',
        'List comprehension redefines {0!r} from line {1!r}.')

    def __init__(self, filename, loc, name, orig_loc):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location of warning (object)
        @param name name of the redefined object (string)
        @param orig_loc location of the original definition (object)
        """
        Message.__init__(self, filename, loc)
        self.message_args = (name, orig_loc.lineno)


class ImportShadowedByLoopVar(Message):
    """
    Class defining the "Import Shadowed By Loop Var" message.
    """
    message = QT_TRANSLATE_NOOP(
        'py3Flakes',
        'Import {0!r} from line {1!r} shadowed by loop variable.')

    def __init__(self, filename, loc, name, orig_loc):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location of warning (object)
        @param name name of the shadowed import (string)
        @param orig_loc location of the import (object)
        """
        Message.__init__(self, filename, loc)
        self.message_args = (name, orig_loc.lineno)


class ImportStarUsed(Message):
    """
    Class defining the "Import Star Used" message.
    """
    message = QT_TRANSLATE_NOOP(
        'py3Flakes',
        "'from {0} import *' used; unable to detect undefined names.")

    def __init__(self, filename, loc, modname):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location of warning (object)
        @param modname name of the module imported using star import (string)
        """
        Message.__init__(self, filename, loc)
        self.message_args = (modname,)


class UndefinedName(Message):
    """
    Class defining the "Undefined Name" message.
    """
    message = QT_TRANSLATE_NOOP('py3Flakes', 'Undefined name {0!r}.')

    def __init__(self, filename, loc, name):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location of warning (object)
        @param name undefined name (string)
        """
        Message.__init__(self, filename, loc)
        self.message_args = (name,)


class DoctestSyntaxError(Message):
    """
    Class defining the "Syntax error in doctest" message.
    """
    message = QT_TRANSLATE_NOOP('py3Flakes', 'Syntax error in doctest.')

    def __init__(self, filename, loc, position=None):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location of warning (object)
        @keyparam position of warning if existent (object)
        """
        Message.__init__(self, filename, loc)
        if position:
            (self.lineno, self.col) = position
        self.message_args = ()


class UndefinedExport(Message):
    """
    Class defining the "Undefined Export" message.
    """
    message = QT_TRANSLATE_NOOP(
        'py3Flakes',
        'Undefined name {0!r} in __all__.')

    def __init__(self, filename, loc, name):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location of warning (object)
        @param name undefined exported name (string)
        """
        Message.__init__(self, filename, loc)
        self.message_args = (name,)


class UndefinedLocal(Message):
    """
    Class defining the "Undefined Local Variable" message.
    """
    message = QT_TRANSLATE_NOOP(
        'py3Flakes',
        "Local variable {0!r} (defined in enclosing scope on line {1!r})"
        " referenced before assignment.")

    def __init__(self, filename, loc, name, orig_loc):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location of warning (object)
        @param name name of the prematurely referenced variable (string)
        @param orig_loc location of the variable definition (object)
        """
        Message.__init__(self, filename, loc)
        self.message_args = (name, orig_loc.lineno)


class DuplicateArgument(Message):
    """
    Class defining the "Duplicate Argument" message.
    """
    message = QT_TRANSLATE_NOOP(
        'py3Flakes',
        'Duplicate argument {0!r} in function definition.')

    def __init__(self, filename, loc, name):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location of warning (object)
        @param name name of the duplicate argument (string)
        """
        Message.__init__(self, filename, loc)
        self.message_args = (name,)


class Redefined(Message):
    """
    Class defining the "Redefined" message.
    """
    message = QT_TRANSLATE_NOOP(
        'py3Flakes',
        'Redefinition of {0!r} from line {1!r}.')

    def __init__(self, filename, loc, name, orig_loc):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location of warning (object)
        @param name name of the redefined function (string)
        @param orig_loc location of the original definition (object)
        """
        Message.__init__(self, filename, loc)
        self.message_args = (name, orig_loc.lineno)


class LateFutureImport(Message):
    """
    Class defining the "Late Future Import" message.
    """
    message = QT_TRANSLATE_NOOP(
        'py3Flakes',
        'Future import(s) {0!r} after other statements.')

    def __init__(self, filename, loc, names):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location of warning (object)
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
    message = QT_TRANSLATE_NOOP(
        'py3Flakes',
        'Local variable {0!r} is assigned to but never used.')

    def __init__(self, filename, loc, names):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location of warning (object)
        @param names names of the unused variable (string)
        """
        Message.__init__(self, filename, loc)
        self.message_args = (names,)
