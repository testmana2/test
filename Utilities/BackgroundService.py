# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#
# pylint: disable=C0103

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
from PyQt4.QtNetwork import QTcpServer, QHostAddress

import Preferences
import Utilities
from Utilities.BackgroundClient import BackgroundClient

from eric5config import getConfig


class BackgroundService(QTcpServer):
    """
    Class implementing the main part of the background service.
    """
    serviceNotAvailable = pyqtSignal(str, str, int, str)
    
    def __init__(self):
        """
        Constructor of the BackgroundService class.
        """
        self.processes = [None, None]
        self.connections = [None, None]
        self.isWorking = None
        self.__queue = []
        self.services = {}

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
        if sys.platform == 'win32':
            pyCompare = Utilities.samefilepath
        else:
            pyCompare = Utilities.samepath
        
        for pyIdx, pyName in enumerate(['Python', 'Python3']):
            interpreter = Preferences.getDebugger(
                pyName + "Interpreter")
            
            if pyCompare(interpreter, sys.executable):
                process = self.__startInternalClient(port)
            else:
                process = self.__startExternalClient(interpreter, port)
            self.processes[pyIdx] = process

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
        backgroundClient = BackgroundClient(
            self.hostAddress, port)
        thread = threading.Thread(target=backgroundClient.run)
        thread.start()
        return thread
    
    def __processQueue(self):
        """
        Private method to take the next service request and send it to the
        client.
        """
        if self.__queue and self.isWorking is None:
            fx, fn, pyVer, data = self.__queue.pop(0)
            self.isWorking = pyVer
            self.__send(fx, fn, pyVer, data)
    
    def __send(self, fx, fn, pyVer, data):
        """
        Private method to send a job request to one of the clients.
        
        @param fx remote function name to execute (str)
        @param fn filename for identification (str)
        @param pyVer version for the required interpreter (int)
        @param data function argument(s) (any basic datatype)
        """
        packedData = json.dumps([fx, fn, data])
        if sys.version_info[0] == 3:
            packedData = bytes(packedData, 'utf-8')
        connection = self.connections[pyVer - 2]
        if connection is None:
            if fx != 'INIT':
                self.serviceNotAvailable.emit(
                    fx, fn, pyVer, self.trUtf8(
                        'Python{0} interpreter not configured.').format(pyVer))
            # Reset flag and continue processing queue
            self.isWorking = None
            self.__processQueue()
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
        fx, fn, data = json.loads(packedData)
        self.__postResult(fx, fn, data)
        
    def __postResult(self, fx, fn, data):
        """
        Private method to emit the correspondig signal for the returned
        function.
        
        @param fx remote function name to execute (str)
        @param fn filename for identification (str)
        @param data function argument(s) (any basic datatype)
        """
        if fx == 'INIT':
            pass
        elif fx == 'exception':
            # Call sys.excepthook(type, value, traceback) to emulate the
            # exception which was caught on the client
            #sys.excepthook(*data)
            print(data)
        else:
            callback = self.services.get(fx)
            if callback:
                callback[2](fn, *data)
        
        self.isWorking = None
        self.__processQueue()

    def enqueueRequest(self, fx, fn, pyVer, data):
        """
        Implement a queued processing of incomming events.
        
        Dublicate file checks update an older request to avoid overrun or
        starving of the check.
        @param fx function name of the service (str)
        @param fn filename for identification (str)
        @param pyVer version for the required interpreter (int)
        @param data function argument(s) (any basic datatype)
        """
        args = [fx, fn, pyVer, data]
        if fx == 'INIT':
            self.__queue.insert(0, args)
        else:
            for pendingArg in self.__queue:
                if pendingArg[:3] == args[:3]:
                    pendingArg[3] = args[3]
                    break
            else:
                self.__queue.append(args)
        self.__processQueue()
    
    def serviceConnect(
            self, fx, modulepath, module, callback, onErrorCallback=None):
        """
        Announce a new service to the background service/ client.
        
        @param fx function name of the service (str)
        @param modulepath full path to the module (str)
        @param module name to import (str)
        @param callback function on service response (function)
        @param onErrorCallback function if client isn't available (function)
        """
        self.services[fx] = modulepath, module, callback, onErrorCallback
        self.enqueueRequest('INIT', fx, 0, [modulepath, module])
        self.enqueueRequest('INIT', fx, 1, [modulepath, module])
        if onErrorCallback:
            self.serviceNotAvailable.connect(onErrorCallback)
    
    def serviceDisconnect(self, fx):
        """
        Remove the service from the service list.
        
        @param fx function name of the service
        """
        self.services.pop(fx, None)

    def on_newConnection(self):
        """
        Slot for new incomming connections from the clients.
        """
        connection = self.nextPendingConnection()
        if not connection.waitForReadyRead(1000):
            return
        ch = 0 if connection.read(1) == b'2' else 1
        # Avoid hanging of eric on shutdown
        if self.connections[ch]:
            self.connections[ch].close()
        if self.isWorking == ch + 2:
            self.isWorking = None
        self.connections[ch] = connection
        connection.readyRead.connect(
            lambda x=ch: self.__receive(x))
        
        for fx, args in self.services.items():
            self.enqueueRequest('INIT', fx, ch, args[:2])

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
