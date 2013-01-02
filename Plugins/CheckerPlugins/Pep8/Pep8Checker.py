# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the PEP 8 checker.
"""

import os
import optparse

from PyQt4.QtCore import QProcess, QCoreApplication

from . import pep8

import Preferences
import Utilities

from eric5config import getConfig


class Pep8Checker(pep8.Checker):
    """
    Class implementing the PEP 8 checker.
    """
    def __init__(self, filename, lines, repeat=False,
                 select="", ignore=""):
        """
        Constructor
        
        @param filename name of the file to check (string)
        @param lines source of the file (list of strings)
        @keyparam repeat flag indicating to repeat message categories (boolean)
        @keyparam select list of message IDs to check for
            (comma separated string)
        @keyparam ignore list of message IDs to ignore
            (comma separated string)
        """
        pep8.options = optparse.Values()
        
        pep8.options.verbose = 0
        
        pep8.options.repeat = repeat
        if select:
            pep8.options.select = [s.strip() for s in select.split(',')
                                   if s.strip()]
        else:
            pep8.options.select = []
        if ignore:
            pep8.options.ignore = [i.strip() for i in ignore.split(',')
                                   if i.strip()]
        else:
            pep8.options.ignore = []
        pep8.options.physical_checks = pep8.find_checks('physical_line')
        pep8.options.logical_checks = pep8.find_checks('logical_line')
        pep8.options.counters = dict.fromkeys(pep8.BENCHMARK_KEYS, 0)
        pep8.options.messages = {}
        
        pep8.Checker.__init__(self, filename, lines)
        
        self.messages = []
        self.statistics = {}
    
    def __ignore_code(self, code):
        """
        Private method to check, if the message for the given code should
        be ignored.
        
        If codes are selected and the code has a selected prefix and does not
        have an ignored prefix, it is not ignored. If codes are selected and
        the code does not have a selected prefix, it is ignored. If no codes
        are selected, the code is ignored, if it has a prefix, that is
        contained in the ignored codes.
        
        @param code code to be checked (string)
        @return flag indicating, that the code should be ignored (boolean)
        """
        if pep8.options.select:
            if code.startswith(tuple(pep8.options.select)):
                if code.startswith(tuple(pep8.options.ignore)):
                    return True
                else:
                    return False
            else:
                return True
        else:
            if code.startswith(tuple(pep8.options.ignore)):
                return True
            else:
                return False
    
    def report_error_args(self, line_number, offset, code, check, *args):
        """
        Public method to collect the error messages.
        
        @param line_number line number of the issue (integer)
        @param offset position within line of the issue (integer)
        @param code message code (string)
        @param check reference to the checker function (function)
        @param args arguments for the message (list)
        """
        if self.__ignore_code(code):
            return
        
        text = pep8.getMessage(code, *args)
        if code in self.statistics:
            self.statistics[code] += 1
        else:
            self.statistics[code] = 1
        self.file_errors += 1
        if self.statistics[code] == 1 or pep8.options.repeat:
            self.messages.append(
                (self.filename, self.line_offset + line_number,
                 offset + 1, text)
            )


class Pep8Py2Checker(object):
    """
    Class implementing the PEP 8 checker interface for Python 2.
    """
    def __init__(self, filename, lines, repeat=False,
                 select="", ignore=""):
        """
        Constructor
        
        @param filename name of the file to check (string)
        @param lines source of the file (list of strings) (ignored)
        @keyparam repeat flag indicating to repeat message categories (boolean)
        @keyparam select list of message IDs to check for
            (comma separated string)
        @keyparam ignore list of message IDs to ignore
            (comma separated string)
        """
        self.messages = []
        self.statistics = {}
        
        interpreter = Preferences.getDebugger("PythonInterpreter")
        if interpreter == "" or not Utilities.isExecutable(interpreter):
            self.messages.append((filename, 1, 1,
                QCoreApplication.translate("Pep8Py2Checker",
                    "Python2 interpreter not configured.")))
            return
        
        checker = os.path.join(getConfig('ericDir'),
                               "UtilitiesPython2", "Pep8Checker.py")
        
        args = [checker]
        if repeat:
            args.append("-r")
        if select:
            args.append("-s")
            args.append(select)
        if ignore:
            args.append("-i")
            args.append(ignore)
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
                self.messages.append((filename, 1, 1, output[2]))
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
                
                text = pep8.getMessage(code, *args)
                self.messages.append((fname, lineno, position, text))
            while index < len(output):
                code, countStr = output[index].split(None, 1)
                self.statistics[code] = int(countStr)
                index += 1
        else:
            self.messages.append((filename, 1, 1,
                QCoreApplication.translate("Pep8Py2Checker",
                    "Python2 interpreter did not finish within 15s.")))
