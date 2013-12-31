# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a background service for the various checkers and other
python interpreter dependent functions.
"""

from __future__ import unicode_literals

import json
import os
import struct
import sys
import threading
from zlib import adler32

from PyQt4.QtCore import QProcess, pyqtSignal
from PyQt4.QtGui import QApplication
from PyQt4.QtNetwork import QTcpServer, QHostAddress

from E5Gui.E5Application import e5App

import Preferences
import Utilities
from Utilities.BackgroundClient import BackgroundClient

from eric5config import getConfig


class BackgroundService(QTcpServer):
    """
    Class implementing the main part of the background service.
    """
    syntaxChecked = pyqtSignal(str, bool, str, int, int, str, str, list)
    #styleChecked = pyqtSignal(TBD)
    #indentChecked = pyqtSignal(TBD)
    
    def __init__(self):
        """
        Constructor of the BackgroundService class.
        """
        self.processes = [None, None]
        self.connections = [None, None]

        super(BackgroundService, self).__init__()

        networkInterface = Preferences.getDebugger("NetworkInterface")
        if networkInterface == "all" or '.' in networkInterface:
            self.hostAddress = '127.0.0.1'
        else:
            self.hostAddress = '::1'
        self.listen(QHostAddress(self.hostAddress))

        self.newConnection.connect(self.on_newConnection)
        port = self.serverPort()
        ## NOTE: Need the port if started external in debugger:
        print('BackgroundService listening on: %i' % port)
        for pyIdx, pyName in enumerate(['Python', 'Python3']):
            interpreter = Preferences.getDebugger(
                pyName + "Interpreter")
            
            if Utilities.samefilepath(interpreter, sys.executable):
                process = self.__startInternalClient(port)
            else:
                process = self.__startExternalClient(interpreter, port)
            self.processes[pyIdx] = process

    def on_newConnection(self):
        """
        Slot for new incomming connections from the clients.
        """
        connection = self.nextPendingConnection()
        if not connection.waitForReadyRead(1000):
            return
        ch = 0 if connection.read(1) == b'2' else 1
        self.connections[ch] = connection
        connection.readyRead.connect(
            lambda x=ch: self.__receive(x))

    def shutdown(self):
        """
        Cleanup the connections and processes when Eric is shuting down.
        """
        for connection in self.connections:
            if connection:
                connection.close()
        
        for process in self.processes:
            if isinstance(process, QProcess):
                process.close()
                process = None
            elif isinstance(process, threading.Thread):
                process.join(0.1)
                process = None

    def __startExternalClient(self, interpreter, port):
        """
        Private method to start the background client as external process.
        
        @param interpreter path and name of the executable to start (string)
        @param port socket port to which the interpreter should connect (int)
        @return the process object (QProcess) or None
        """
        if interpreter == "" or not Utilities.isinpath(interpreter):
            return None
        
        backgroundClient = os.path.join(
            getConfig('ericDir'),
            "Utilities", "BackgroundClient.py")
        proc = QProcess()
        args = [backgroundClient, self.hostAddress, str(port)]
        proc.start(interpreter, args)
        if not proc.waitForStarted(10000):
            proc = None
        return proc

    def __startInternalClient(self, port):
        """
        Private method to start the background client as internal thread.
        
        @param port socket port to which the interpreter should connect (int)
        @return the thread object (Thread) or None
        """
        self.backgroundClient = BackgroundClient(
            self.hostAddress, port)
        thread = threading.Thread(target=self.backgroundClient.run)
        thread.start()
        return thread

    # TODO: Implement a queued processing of incomming events. Dublicate file
    # checks should update an older request to avoid overrun or starving of
    # the check.
    def __send(self, fx, fn, data, isPy3):
        """
        Private method to send a job request to one of the clients.
        
        @param fx remote function name to execute (str)
        @param fn filename for identification (str)
        @param data function argument(s) (any basic datatype)
        @param isPy3 flag for the required interpreter (boolean)
        """
        packedData = json.dumps([fx, fn, data])
        if sys.version_info[0] == 3:
            packedData = bytes(packedData, 'utf-8')
        connection = self.connections[int(isPy3)]
        if connection is None:
            self.__postResult(
                fx, fn, [
                    True, fn, 0, 0, '',
                    'No connection to Python{0} interpreter. '
                    'Check your debugger settings.'.format(int(isPy3) + 2)])
        else:
            header = struct.pack(
                b'!II', len(packedData), adler32(packedData) & 0xffffffff)
            connection.write(header)
            connection.write(packedData)

    def __receive(self, channel):
        """
        Private method to receive the response from the clients.
        
        @param channel of the incomming connection (int: 0 or 1)
        """
        connection = self.connections[channel]
        header = connection.read(8)
        length, datahash = struct.unpack(b'!II', header)
        
        packedData = b''
        while len(packedData) < length:
            connection.waitForReadyRead(50)
            packedData += connection.read(length - len(packedData))

        assert adler32(packedData) & 0xffffffff == datahash, 'Hashes not equal'
        if sys.version_info[0] == 3:
            packedData = packedData.decode('utf-8')
        # "check" if is's a tuple of 3 values
        try:
            fx, fn, data = json.loads(packedData)
            self.__postResult(fx, fn, data)
        except:
            pass

    def __postResult(self, fx, fn, data):
        """
        Private method to emit the correspondig signal for the returned
        function.
        
        @param fx remote function name to execute (str)
        @param fn filename for identification (str)
        @param data function argument(s) (any basic datatype)
        """
        if fx == 'syntax':
            self.syntaxChecked.emit(fn, *data)
        elif fx == 'style':
            pass
        elif fx == 'indent':
            pass
        elif fx == 'exception':
            # Call sys.excepthook(type, value, traceback) to emulate the
            # exception which was caught on the client
            sys.excepthook(*data)
        
        #QApplication.translate(packedData)
        
    # ggf. nach Utilities verschieben
    def determinePythonVersion(self, filename, source):
        """
        Determine the python version of a given file.
        
        @param filename name of the file with extension (str)
        @param source of the file (str)
        @return flag if file is Python2 or Python3 (boolean)
        """
        flags = Utilities.extractFlags(source)
        ext = os.path.splitext(filename)[1]
        project = e5App().getObject('Project')
        if "FileType" in flags:
            isPy3 = flags["FileType"] not in ["Python", "Python2"]
        elif (Preferences.getProject("DeterminePyFromProject") and
              project.isOpen() and
              project.isProjectFile(filename)):
                    isPy3 = project.getProjectLanguage() == "Python3"
        else:
            isPy3 = ext in Preferences.getPython("PythonExtensions")
        return isPy3

    def syntaxCheck(self, filename, source="", checkFlakes=True,
                    ignoreStarImportWarnings=False, isPy3=None):
        """
        Function to compile one Python source file to Python bytecode
        and to perform a pyflakes check.
        
        @param filename source filename (string)
        @keyparam source string containing the code to check (string)
        @keyparam checkFlakes flag indicating to do a pyflakes check (boolean)
        @keyparam ignoreStarImportWarnings flag indicating to
            ignore 'star import' warnings (boolean)
        @keyparam isPy3 flag sets the interpreter to use or None for autodetect
            corresponding interpreter (boolean or None)
        """
        if isPy3 is None:
            isPy3 = self.determinePythonVersion(filename, source)
        
        data = [source, checkFlakes, ignoreStarImportWarnings]
        self.__send('syntax', filename, data, isPy3)
