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
    styleChecked = pyqtSignal(str, dict, int, list)
    #indentChecked = pyqtSignal(TBD)

    def __init__(self, backgroundService):
        """
        Contructor of InternalServices.
        
        @param backgroundService to connect to
        """
        super(InternalServices, self).__init__()
        self.backgroundService = backgroundService
        
        ericPath = getConfig('ericDir')
        # Syntax check
        path = os.path.join(ericPath, 'Plugins', 'CheckerPlugins',
                            'SyntaxChecker')
        self.backgroundService.serviceConnect(
            'syntax', path, 'SyntaxCheck',
            self.__translateSyntaxCheck,
            lambda fx, fn, ver, msg: self.syntaxChecked.emit(
                fn, True, fn, 0, 0, '', msg, []))
        
        # Style check
        path = os.path.join(ericPath, 'Plugins', 'CheckerPlugins',
                            'CodeStyleChecker')
        self.backgroundService.serviceConnect(
            'style', path, 'CodeStyleChecker',
            self.__translateStyleCheck,
            lambda fx, fn, ver, msg: self.styleChecked.emit(
                fn, {}, 0, [[0, 0, '---- ' + msg, False, False]]))
        
#        # Indent check
#        path = os.path.join(ericPath, 'Plugins', 'CheckerPlugins',
#                            'Tabnanny')
#        self.backgroundService.serviceConnect(
#            'indent', path, 'Tabnanny',
#            self.__translateIndentCheck)

    def syntaxCheck(self, filename, source="", checkFlakes=True,
                    ignoreStarImportWarnings=False, pyVer=None, editor=None):
        """
        Method to prepare to compile one Python source file to Python bytecode
        and to perform a pyflakes check in another task.
        
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

    def styleCheck(self, filename, source, args, pyVer=None, editor=None):
        """
        Method to prepare a style check on one Python source file in another
        task.
        
        @param filename source filename (string)
        @param source string containing the code to check (string)
        @param args arguments used by the codeStyleCheck function (list of
            excludeMessages (str), includeMessages (str), repeatMessages
            (bool), fixCodes (str), noFixCodes (str), fixIssues (bool),
            maxLineLength (int), hangClosing (bool), docType (str), errors
            (list of str), eol (str), encoding (str))
        @keyparam pyVer version of the interpreter to use or None for
            autodetect corresponding interpreter (int or None)
        @keyparam editor if the file is opened already (Editor object)
        """
        if pyVer is None:
            pyVer = determinePythonVersion(filename, source, editor)
        
        data = [source, args]
        self.backgroundService.enqueueRequest('style', filename, pyVer, data)
    
    def __translateStyleCheck(self, fn, codeStyleCheckerStats, results):
        """
        Privat slot called after perfoming a style check on one file.
        
        @param fn filename of the just checked file (str)
        @param codeStyleCheckerStats stats of style and name check (dict)
        @param results tuple for each found violation of style (tuple of
            lineno (int), position (int), text (str), fixed (bool),
            autofixing (bool), fixedMsg (str))
        """
        fixes = 0
        for result in results:
            msg = result[2].split('@@')
            if msg[0].startswith(('W', 'E')):
                msgType = 'pep8'
            elif msg[0].startswith('N'):
                msgType = 'NamingStyleChecker'
            else:
                msgType = 'DocStyleChecker'
            translMsg = msg[0][:5] + QApplication.translate(
                msgType, msg[0][5:]).format(*msg[1:])
        
            fixedMsg = result.pop()
            if fixedMsg:
                fixes += 1
                if '@@' in fixedMsg:
                    msg, param = fixedMsg.split('@@')
                    fixedMsg = QApplication.translate(
                        'CodeStyleFixer', msg).format(param)
                else:
                    fixedMsg = QApplication.translate(
                        'CodeStyleFixer', fixedMsg)
                
                translMsg += "\n" + QApplication.translate(
                    'CodeStyleCheckerDialog', "Fix: {0}").format(fixedMsg)
            result[2] = translMsg
        self.styleChecked.emit(fn, codeStyleCheckerStats, fixes, results)
