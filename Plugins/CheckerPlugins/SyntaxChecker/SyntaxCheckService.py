# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#
# pylint: disable=C0103

"""
Module implementing an interface to add different languages to do a syntax
check.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import QObject, pyqtSignal

from E5Gui.E5Application import e5App
from Utilities import determinePythonVersion


class SyntaxCheckService(QObject):
    """
    Implement the syntax check service.
    
    Plugins can add other languages to the syntax check by calling addLanguage
    and support of an extra checker module on the client side which has to
    connect directly to the background service.
    """
    syntaxChecked = pyqtSignal(str, bool, int, int, str, str, list)

    def __init__(self):
        """
        Contructor of SyntaxCheckService.
        
        @param backgroundService to connect to (BackgroundService class)
        """
        super(SyntaxCheckService, self).__init__()
        self.backgroundService = e5App().getObject("BackgroundService")
        self.__supportedLanguages = {}

    def __determineLanguage(self, filename, source):
        """
        Private methode to determine the language of the file.
        
        @return language of the file or None if not found (str or None)
        """
        pyVer = determinePythonVersion(filename, source)
        if pyVer:
            return 'Python{0}'.format(pyVer)
        
        for lang, (getArgs, getExt) in self.__supportedLanguages.items():
            if filename.endswith(getExt()):
                return lang
        
        return None

    def addLanguage(
            self, lang, path, module, getArgs, getExt, callback, onError):
        """
        Register the new language to the supported languages.
        
        @param lang new language to check syntax (str)
        @param path full path to the module (str)
        @param module name to import (str)
        @param getArgs function to collect the required arguments to call the
            syntax checker on client side (function)
        @param getExt function that returns the supported file extensions of
            the syntax checker (function)
        @param callback function on service response (function)
        @param onError callback function if client or service isn't available
            (function)
        """
        self.__supportedLanguages[lang] = getArgs, getExt
        # Connect to the background service
        self.backgroundService.serviceConnect(
            'syntax', lang, path, module, callback, onError)

    def getLanguages(self):
        """
        Return the supported language names.
        
        @return list of languanges supported (list of str)
        """
        return list(self.__supportedLanguages.keys())

    def removeLanguage(self, lang):
        """
        Remove the language from syntax check.
        
        @param lang language to remove (str)
        """
        self.__supportedLanguages.pop(lang, None)
        self.backgroundService.serviceDisconnect('syntax', lang)

    def getExtensions(self):
        """
        Return all supported file extensions for the syntax checker dialog.
        
        @return set of all supported file extensions (set of str)
        """
        extensions = set()
        for getArgs, getExt in self.__supportedLanguages.values():
            for ext in getExt():
                extensions.add(ext)
        return extensions

    def syntaxCheck(self, lang, filename, source=""):
        """
        Method to prepare to compile one Python source file to Python bytecode
        and to perform a pyflakes check in another task.
        
        @param lang language of the file or None to determine by internal
            algorithm (str or None)
        @param filename source filename (string)
        @keyparam source string containing the code to check (string)
        """
        if not lang:
            lang = self.__determineLanguage(filename, source)
        if lang not in self.getLanguages():
            return
        data = [source]
        # Call the getArgs function to get the required arguments
        args = self.__supportedLanguages[lang][0]()
        data.extend(args)
        self.backgroundService.enqueueRequest('syntax', lang, filename, data)
