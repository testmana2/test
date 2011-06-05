# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a TestResult derivative for the eric5 debugger.
"""

import select
import traceback
from unittest import TestResult


from DebugProtocol import ResponseUTTestFailed, ResponseUTTestErrored, \
    ResponseUTStartTest, ResponseUTStopTest


class DCTestResult(TestResult):
    """
    A TestResult derivative to work with eric5's debug client.
    
    For more details see unittest.py of the standard python distribution.
    """
    def __init__(self, parent):
        """
        Constructor
        
        @param parent The parent widget.
        """
        TestResult.__init__(self)
        self.parent = parent
        
    def addFailure(self, test, err):
        """
        Method called if a test failed.
        
        @param test Reference to the test object
        @param err The error traceback
        """
        TestResult.addFailure(self, test, err)
        tracebackLines = traceback.format_exception(*(err + (10,)))
        self.parent.write('{0}{1}\n'.format(ResponseUTTestFailed,
            str((str(test), tracebackLines))))
        
    def addError(self, test, err):
        """
        Method called if a test errored.
        
        @param test Reference to the test object
        @param err The error traceback
        """
        TestResult.addError(self, test, err)
        tracebackLines = traceback.format_exception(*(err + (10,)))
        self.parent.write('{0}{1}\n'.format(ResponseUTTestErrored,
            str((str(test), tracebackLines))))
        
    def startTest(self, test):
        """
        Method called at the start of a test.
        
        @param test Reference to the test object
        """
        TestResult.startTest(self, test)
        self.parent.write('{0}{1}\n'.format(ResponseUTStartTest,
            str((str(test), test.shortDescription()))))

    def stopTest(self, test):
        """
        Method called at the end of a test.
        
        @param test Reference to the test object
        """
        TestResult.stopTest(self, test)
        self.parent.write('{0}\n'.format(ResponseUTStopTest))
        
        # ensure that pending input is processed
        rrdy, wrdy, xrdy = select.select([self.parent.readstream], [], [], 0.01)

        if self.parent.readstream in rrdy:
            self.parent.readReady(self.parent.readstream.fileno())
