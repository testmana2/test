# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#
# pylint: disable=C0103

"""
Module implementing a Qt free version of a background client for the various
checkers and other python interpreter dependent functions.
"""

from __future__ import unicode_literals

import os

from PyQt4.QtCore import QObject, pyqtSignal
from PyQt4.QtGui import QApplication

from eric5config import getConfig
from Utilities import determinePythonVersion


class InternalServices(QObject):
    """
    Implement the standard services (syntax with flakes and the style check).
    """
    syntaxChecked = pyqtSignal(str, bool, str, int, int, str, str, list)
    #styleChecked = pyqtSignal(TBD)
    #indentChecked = pyqtSignal(TBD)

    def __init__(self, backgroundService):
        """
        Contructor of InternalServices.
        
        @param backgroundService to connect to
        """
        super(InternalServices, self).__init__()
        self.backgroundService = backgroundService
        
        path = os.path.join(
            getConfig('ericDir'), 'Plugins', 'CheckerPlugins', 'SyntaxChecker')
        self.backgroundService.serviceConnect(
            'syntax', path, 'SyntaxCheck',
            self.__translateSyntaxCheck,
            lambda fx, fn, ver, msg: self.syntaxChecked.emit(
                fn, True, fn, 0, 0, '', msg, []))

    def syntaxCheck(self, filename, source="", checkFlakes=True,
                    ignoreStarImportWarnings=False, pyVer=None, editor=None):
        """
        Function to compile one Python source file to Python bytecode
        and to perform a pyflakes check.
        
        @param filename source filename (string)
        @keyparam source string containing the code to check (string)
        @keyparam checkFlakes flag indicating to do a pyflakes check (boolean)
        @keyparam ignoreStarImportWarnings flag indicating to
            ignore 'star import' warnings (boolean)
        @keyparam pyVer version of the interpreter to use or None for
            autodetect corresponding interpreter (int or None)
        @keyparam editor if the file is opened already (Editor object)
        """
        if pyVer is None:
            pyVer = determinePythonVersion(filename, source, editor)
        
        data = [source, checkFlakes, ignoreStarImportWarnings]
        self.backgroundService.enqueueRequest('syntax', filename, pyVer, data)

    def __translateSyntaxCheck(
            self, fn, nok, fname, line, index, code, error, warnings):
        """
        Slot to translate the resulting messages.
        
        If checkFlakes is True, warnings contains a list of strings containing
        the warnings (marker, file name, line number, message)
        The values are only valid, if nok is False.
        
        @param fn filename of the checked file (str)
        @param nok flag if an error in the source was found (boolean)
        @param fname filename of the checked file (str)  # TODO: remove dubl.
        @param line number where the error occured (int)
        @param index the column where the error occured (int)
        @param code the part of the code where the error occured (str)
        @param error the name of the error (str)
        @param warnings a list of strings containing the warnings
            (marker, file name, line number, col, message, list(msg_args))
        """
        for warning in warnings:
            # Translate messages
            msg_args = warning.pop()
            translated = QApplication.translate(
                'py3Flakes', warning[4]).format(*msg_args)
            # Avoid leading "u" at Python2 unicode strings
            if translated.startswith("u'"):
                translated = translated[1:]
            warning[4] = translated.replace(" u'", " '")
        
        self.syntaxChecked.emit(
            fn, nok, fname, line, index, code, error, warnings)
