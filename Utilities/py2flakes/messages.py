# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#
# Original (c) 2005 Divmod, Inc.  See LICENSE file for details
#
# This module is based on pyflakes for Python2 but was heavily hacked to
# work within Eric5 and Qt (translatable messages)

"""
Module implementing the messages for py2flakes.
"""


def QT_TRANSLATE_NOOP(mod, txt):
    """
    Function to tell 'lupdate' which strings to keep for translation.
    
    @param mod module name
    @param txt translatable string
    @return the untranslated! string
    """
    return txt


class Message(object):
    """
    Class defining the base for all specific message classes.
    """
    message = ''
    message_args = ()
    
    def __init__(self, filename, lineno):
        """
        Constructor
        
        @param filename name of the file (string)
        @param lineno line number (integer)
        """
        self.filename = filename
        self.lineno = lineno
    
    def __str__(self):
        """
        Special method return a string representation of the instance object.
        
        @return string representation of the object (string)
        """
        return '%s:%s: %s' % (
            self.filename, self.lineno, self.message % self.message_args)
    
    def getMessageData(self):
        """
        Public method to get the individual message data elements.
        
        @return tuple containing file name, line number and message
            (string, integer, string)
        """
        return (self.filename, self.lineno, self.message, self.message_args)


class UnusedImport(Message):
    """
    Class defining the "Unused Import" message.
    """
    message = QT_TRANSLATE_NOOP(
        'py3Flakes',
        '{0!r} imported but unused.')
    
    def __init__(self, filename, lineno, name):
        """
        Constructor
        
        @param filename name of the file (string)
        @param lineno line number (integer)
        @param name name of the unused import (string)
        """
        Message.__init__(self, filename, lineno)
        self.message_args = (name,)


class RedefinedWhileUnused(Message):
    """
    Class defining the "Redefined While Unused" message.
    """
    message = QT_TRANSLATE_NOOP(
        'py3Flakes',
        'Redefinition of unused {0!r} from line {1!r}.')

    def __init__(self, filename, lineno, name, orig_lineno):
        """
        Constructor
        
        @param filename name of the file (string)
        @param lineno line number (integer)
        @param name name of the redefined object (string)
        @param orig_lineno line number of the original definition (integer)
        """
        Message.__init__(self, filename, lineno)
        self.message_args = (name, orig_lineno)


class RedefinedInListComp(Message):
    """
    Class defining the list comprehension redefinition.
    """
    message = QT_TRANSLATE_NOOP(
        'py3Flakes',
        'List comprehension redefines {0!r} from line {1!r}.')

    def __init__(self, filename, lineno, name, orig_lineno):
        """
        Constructor
        
        @param filename name of the file (string)
        @param lineno line number (integer)
        @param name name of the redefined object (string)
        @param orig_lineno line number of the original definition (integer)
        """
        Message.__init__(self, filename, lineno)
        self.message_args = (name, orig_lineno)


class ImportShadowedByLoopVar(Message):
    """
    Class defining the "Import Shadowed By Loop Var" message.
    """
    message = QT_TRANSLATE_NOOP(
        'py3Flakes',
        'Import {0!r} from line {1!r} shadowed by loop variable.')
    
    def __init__(self, filename, lineno, name, orig_lineno):
        """
        Constructor
        
        @param filename name of the file (string)
        @param lineno line number (integer)
        @param name name of the shadowed import (string)
        @param orig_lineno line number of the import (integer)
        """
        Message.__init__(self, filename, lineno)
        self.message_args = (name, orig_lineno)


class ImportStarUsed(Message):
    """
    Class defining the "Import Star Used" message.
    """
    message = QT_TRANSLATE_NOOP(
        'py3Flakes',
        "'from {0} import *' used; unable to detect undefined names.")
    
    def __init__(self, filename, lineno, modname):
        """
        Constructor
        
        @param filename name of the file (string)
        @param lineno line number (integer)
        @param modname name of the module imported using star import (string)
        """
        Message.__init__(self, filename, lineno)
        self.message_args = (modname,)


class UndefinedName(Message):
    """
    Class defining the "Undefined Name" message.
    """
    message = QT_TRANSLATE_NOOP('py3Flakes', 'Undefined name {0!r}.')
    
    def __init__(self, filename, lineno, name):
        """
        Constructor
        
        @param filename name of the file (string)
        @param lineno line number (integer)
        @param name undefined name (string)
        """
        Message.__init__(self, filename, lineno)
        self.message_args = (name,)


class UndefinedExport(Message):
    """
    Class defining the "Undefined Export" message.
    """
    message = QT_TRANSLATE_NOOP(
        'py3Flakes',
        'Undefined name {0!r} in __all__.')
    
    def __init__(self, filename, lineno, name):
        """
        Constructor
        
        @param filename name of the file (string)
        @param lineno line number (integer)
        @param name undefined exported name (string)
        """
        Message.__init__(self, filename, lineno)
        self.message_args = (name,)


class UndefinedLocal(Message):
    """
    Class defining the "Undefined Local Variable" message.
    """
    message = QT_TRANSLATE_NOOP(
        'py3Flakes',
        "Local variable {0!r} (defined in enclosing scope on line {1!r})"
        " referenced before assignment.")
    
    def __init__(self, filename, lineno, name, orig_lineno):
        """
        Constructor
        
        @param filename name of the file (string)
        @param lineno line number (integer)
        @param name name of the prematurely referenced variable (string)
        @param orig_lineno line number of the variable definition (integer)
        """
        Message.__init__(self, filename, lineno)
        self.message_args = (name, orig_lineno)


class DuplicateArgument(Message):
    """
    Class defining the "Duplicate Argument" message.
    """
    message = QT_TRANSLATE_NOOP(
        'py3Flakes',
        'Duplicate argument {0!r} in function definition.')
    
    def __init__(self, filename, lineno, name):
        """
        Constructor
        
        @param filename name of the file (string)
        @param lineno line number (integer)
        @param name name of the duplicate argument (string)
        """
        Message.__init__(self, filename, lineno)
        self.message_args = (name,)


class Redefined(Message):
    """
    Class defining the "Redefined" message.
    """
    message = QT_TRANSLATE_NOOP(
        'py3Flakes',
        'Redefinition of {0!r} from line {1!r}.')
    
    def __init__(self, filename, lineno, name, orig_lineno):
        """
        Constructor
        
        @param filename name of the file (string)
        @param lineno line number (integer)
        @param name name of the redefined function (string)
        @param orig_lineno line number of the original definition (integer)
        """
        Message.__init__(self, filename, lineno)
        self.message_args = (name, orig_lineno)


class LateFutureImport(Message):
    """
    Class defining the "Late Future Import" message.
    """
    message = QT_TRANSLATE_NOOP(
        'py3Flakes',
        'Future import(s) {0!r} after other statements.')
    
    def __init__(self, filename, lineno, names):
        """
        Constructor
        
        @param filename name of the file (string)
        @param lineno line number (integer)
        @param names names of the imported futures (string)
        """
        Message.__init__(self, filename, lineno)
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
    
    def __init__(self, filename, lineno, names):
        """
        Constructor
        
        @param filename name of the file (string)
        @param lineno line number (integer)
        @param names names of the unused variable (string)
        """
        Message.__init__(self, filename, lineno)
        self.message_args = (names,)
    
#
# eflag: FileType = Python2
