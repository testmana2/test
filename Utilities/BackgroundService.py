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
from zlib import adler32

from PyQt4.QtCore import QProcess, pyqtSignal
from PyQt4.QtGui import QApplication
from PyQt4.QtNetwork import QTcpServer, QHostAddress

import Preferences
import Utilities

from eric5config import getConfig


class BackgroundService(QTcpServer):
    """
    Class implementing the main part of the background service.
    """
    serviceNotAvailable = pyqtSignal(str, str, str, str)
    
    def __init__(self):
        """
        Constructor of the BackgroundService class.
        """
        self.processes = []
        self.connections = {}
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
        ## Note: Need the port if started external in debugger:
        print('BackgroundService listening on: %i' % port)
        for pyName in ['Python', 'Python3']:
            interpreter = Preferences.getDebugger(
                pyName + "Interpreter")
            process = self.__startExternalClient(interpreter, port)
            if process:
                self.processes.append(process)

    def __startExternalClient(self, interpreter, port):
        """
        Private method to start the background client as external process.
        
        @param interpreter path and name of the executable to start (string)
        @param port socket port to which the interpreter should connect (int)
        @return the process object (QProcess or None)
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
    
    def __processQueue(self):
        """
        Private method to take the next service request and send it to the
        client.
        """
        if self.__queue and self.isWorking is None:
            fx, lang, fn, data = self.__queue.pop(0)
            self.isWorking = lang
            self.__send(fx, lang, fn, data)
    
    def __send(self, fx, lang, fn, data):
        """
        Private method to send a job request to one of the clients.
        
        @param fx remote function name to execute (str)
        @param lang language to connect to (str)
        @param fn filename for identification (str)
        @param data function argument(s) (any basic datatype)
        """
        connection = self.connections.get(lang)
        if connection is None:
            if fx != 'INIT':
                self.serviceNotAvailable.emit(
                    fx, lang, fn, self.tr(
                        '{0} not configured.').format(lang))
            # Reset flag and continue processing queue
            self.isWorking = None
            self.__processQueue()
        else:
            packedData = json.dumps([fx, fn, data])
            if sys.version_info[0] == 3:
                packedData = bytes(packedData, 'utf-8')
            header = struct.pack(
                b'!II', len(packedData), adler32(packedData) & 0xffffffff)
            connection.write(header)
            connection.write(packedData)

    def __receive(self, lang):
        """
        Private method to receive the response from the clients.
        
        @param lang language of the incomming connection (str)
        """
        connection = self.connections[lang]
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
        
        if fx == 'INIT':
            pass
        elif fx == 'EXCEPTION':
            # Call sys.excepthook(type, value, traceback) to emulate the
            # exception which was caught on the client
            sys.excepthook(*data)
            QApplication.processEvents()
        elif data == 'Unknown service.':
            callback = self.services.get((fx, lang))
            if callback:
                callback[3](fx, lang, fn, data)
        else:
            callback = self.services.get((fx, lang))
            if callback:
                callback[2](fn, *data)
        
        self.isWorking = None
        self.__processQueue()

    def enqueueRequest(self, fx, lang, fn, data):
        """
        Implement a queued processing of incomming events.
        
        Dublicate service requests updates an older request to avoid overrun or
        starving of the services.
        @param fx function name of the service (str)
        @param lang language to connect to (str)
        @param fn filename for identification (str)
        @param data function argument(s) (any basic datatype(s))
        """
        args = [fx, lang, fn, data]
        if fx == 'INIT':
            self.__queue.insert(0, args)
        else:
            for pendingArg in self.__queue:
                # Check if it's the same service request (fx, lang, fn equal)
                if pendingArg[:3] == args[:3]:
                    # Update the data
                    pendingArg[3] = args[3]
                    break
            else:
                self.__queue.append(args)
        self.__processQueue()
    
    def serviceConnect(
            self, fx, lang, modulepath, module, callback,
            onErrorCallback=None):
        """
        Announce a new service to the background service/ client.
        
        @param fx function name of the service (str)
        @param lang language of the new service (str)
        @param modulepath full path to the module (str)
        @param module name to import (str)
        @param callback function on service response (function)
        @param onErrorCallback function if client isn't available (function)
        """
        self.services[(fx, lang)] = \
            modulepath, module, callback, onErrorCallback
        self.enqueueRequest('INIT', lang, fx, [modulepath, module])
        if onErrorCallback:
            self.serviceNotAvailable.connect(onErrorCallback)
    
    def serviceDisconnect(self, fx, lang):
        """
        Remove the service from the service list.
        
        @param fx function name of the service (function)
        @param lang language of the service (str)
        """
        serviceArgs = self.services.pop((fx, lang), None)
        if serviceArgs and serviceArgs[3]:
            self.serviceNotAvailable.disconnect(serviceArgs[3])

    def on_newConnection(self):
        """
        Slot for new incomming connections from the clients.
        """
        connection = self.nextPendingConnection()
        if not connection.waitForReadyRead(1000):
            return
        lang = connection.read(64)
        if sys.version_info[0] == 3:
            lang = lang.decode('utf-8')
        # Avoid hanging of eric on shutdown
        if self.connections.get(lang):
            self.connections[lang].close()
        if self.isWorking == lang:
            self.isWorking = None
        self.connections[lang] = connection
        connection.readyRead.connect(
            lambda x=lang: self.__receive(x))
        connection.disconnected.connect(
            lambda x=lang: self.on_disconnectSocket(x))
            
        for (fx, lng), args in self.services.items():
            if lng == lang:
                # Register service with modulepath and module
                self.enqueueRequest('INIT', lng, fx, args[:2])

    def on_disconnectSocket(self, lang):
        """
        Slot when connection to a client is lost.
        
        @param lang client language which connection is lost (str)
        """
        self.connections.pop(lang)
        # Maybe the task is killed while ideling
        if self.isWorking == lang:
            self.isWorking = None
        # Remove pending jobs and send warning to the waiting caller
        # Make a copy of the list because it's modified in the loop
        for args in self.__queue[:]:
            fx, lng, fn, data = args
            if lng == lang:
                # Call onErrorCallback with error message
                self.__queue.remove(args)
                self.services[(fx, lng)][3](fx, fn, lng, self.tr(
                    'Error in Erics background service stopped service.'))
        
    def shutdown(self):
        """
        Cleanup the connections and processes when Eric is shuting down.
        """
        # Make copy of dictionary values because the list is changed by
        # on_disconnectSocket
        for connection in list(self.connections.values()):
            if connection:
                connection.close()
        
        for process in self.processes:
            process.close()
            process = None
