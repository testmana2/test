# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the code style checker.
"""

from __future__ import unicode_literals

try:
    str = unicode    # __IGNORE_WARNING__
except (NameError):
    pass

import os

from PyQt4.QtCore import QProcess, QCoreApplication

from . import pep8
from .NamingStyleChecker import NamingStyleChecker
from .DocStyleChecker import DocStyleChecker

import Preferences
import Utilities

from eric5config import getConfig


class CodeStyleCheckerPy2(object):
    """
    Class implementing the code style checker interface for Python 2.
    """
    def __init__(self, filename, lines, repeat=False,
                 select="", ignore="", max_line_length=79,
                 hang_closing=False, docType="pep257"):
        """
        Constructor
        
        @param filename name of the file to check (string)
        @param lines source of the file (list of strings) (ignored)
        @keyparam repeat flag indicating to repeat message categories (boolean)
        @keyparam select list of message IDs to check for
            (comma separated string)
        @keyparam ignore list of message IDs to ignore
            (comma separated string)
        @keyparam max_line_length maximum allowed line length (integer)
        @keyparam hang_closing flag indicating to allow hanging closing
            brackets (boolean)
        @keyparam docType type of the documentation strings
            (string, one of 'eric' or 'pep257')
        """
        assert docType in ("eric", "pep257")
        
        self.errors = []
        self.counters = {}
        
        interpreter = Preferences.getDebugger("PythonInterpreter")
        if interpreter == "" or not Utilities.isExecutable(interpreter):
            self.errors.append(
                (filename, 1, 1, QCoreApplication.translate(
                    "CodeStyleCheckerPy2",
                    "Python2 interpreter not configured.")))
            return
        
        checker = os.path.join(getConfig('ericDir'),
                               "UtilitiesPython2", "CodeStyleChecker.py")
        
        args = [checker]
        if repeat:
            args.append("-r")
        if select:
            args.append("-s")
            args.append(select)
        if ignore:
            args.append("-i")
            args.append(ignore)
        args.append("-m")
        args.append(str(max_line_length))
        if hang_closing:
            args.append("-h")
        args.append("-d")
        args.append(docType)
        args.append("-f")
        args.append(filename)
        
        proc = QProcess()
        proc.setProcessChannelMode(QProcess.MergedChannels)
        proc.start(interpreter, args)
        finished = proc.waitForFinished(15000)
        if finished:
            output = \
                str(proc.readAllStandardOutput(),
                    Preferences.getSystem("IOEncoding"),
                    'replace').splitlines()
            if output[0] == "ERROR":
                self.errors.append((filename, 1, 1, output[2]))
                return
            
            if output[0] == "NO_PEP8":
                return
            
            index = 0
            while index < len(output):
                if output[index] == "PEP8_STATISTICS":
                    index += 1
                    break
                
                fname = output[index + 1]
                lineno = int(output[index + 2])
                position = int(output[index + 3])
                code = output[index + 4]
                arglen = int(output[index + 5])
                args = []
                argindex = 0
                while argindex < arglen:
                    args.append(output[index + 6 + argindex])
                    argindex += 1
                index += 6 + arglen
                
                if code in NamingStyleChecker.Codes:
                    text = NamingStyleChecker.getMessage(code, *args)
                elif code in DocStyleChecker.Codes:
                    text = DocStyleChecker.getMessage(code, *args)
                else:
                    text = pep8.getMessage(code, *args)
                self.errors.append((fname, lineno, position, text))
            while index < len(output):
                code, countStr = output[index].split(None, 1)
                self.counters[code] = int(countStr)
                index += 1
        else:
            self.errors.append(
                (filename, 1, 1, QCoreApplication.translate(
                    "CodeStyleCheckerPy2",
                    "Python2 interpreter did not finish within 15s.")))
