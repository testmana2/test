# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a Qt free version of a background client for the various
checkers and other python interpreter dependent functions.
"""

from __future__ import unicode_literals
try:
    bytes = unicode  #__IGNORE_WARNING__
except NameError:
    pass

import json
import os
import socket
import struct
import sys
from zlib import adler32

if __name__ == '__main__':
    # Add Eric basepath to sys.path to be able to import modules which are
    # laying not only below Utilities
    path = os.path.dirname(sys.argv[0])
    path = os.path.dirname(path)
    sys.path.append(path)

from Plugins.CheckerPlugins.SyntaxChecker import SyntaxCheck


class BackgroundClient(object):
    """
    Class implementing the main part of the background client.
    """
    def __init__(self, host, port):
        """
        Constructor of the BackgroundClient class.
        
        @param host ip address the background service is listening
        @param port port of the background service
        """
        self.connection = socket.create_connection((host, port))
        ver = b'2' if sys.version_info[0] == 2 else b'3'
        self.connection.sendall(ver)
        self.connection.settimeout(0.25)

    def __send(self, fx, fn, data):
        """
        Private method to send a job response back to the BackgroundService.
        
        @param fx remote function name to execute (str)
        @param fn filename for identification (str)
        @param data return value(s) (any basic datatype)
        """
        packedData = json.dumps([fx, fn, data])
        if sys.version_info[0] == 3:
            packedData = bytes(packedData, 'utf-8')
        header = struct.pack(
            b'!II', len(packedData), adler32(packedData) & 0xffffffff)
        self.connection.sendall(header)
        self.connection.sendall(packedData)

    def run(self):
        """
        Implement the main loop of the client.
        """
        while True:
            try:
                header = self.connection.recv(8)  # __IGNORE_EXCEPTION__
            except socket.timeout:
                continue
            except socket.error:
                # Leave main loop if connection was closed.
                break
            # Leave main loop if connection was closed.
            if not header:
                break
            
            length, datahash = struct.unpack(b'!II', header)
            
            packedData = b''
            while len(packedData) < length:
                packedData += self.connection.recv(length - len(packedData))
            
            assert adler32(packedData) & 0xffffffff == datahash, \
                'Hashes not equal'
            if sys.version_info[0] == 3:
                packedData = packedData.decode('utf-8')
            fx, fn, data = json.loads(packedData)
            if fx == 'syntax':
                ret = SyntaxCheck.syntaxAndPyflakesCheck(fn, *data)
            elif fx == 'style':
                print(data)
            elif fx == 'indent':
                pass
            else:
                continue
            
            self.__send(fx, fn, ret)
            
        self.connection.close()
        sys.exit()

    def __unhandled_exception(self, exctype, excval, exctb):
        """
        Private method called to report an uncaught exception.
        
        @param exctype the type of the exception
        @param excval data about the exception
        @param exctb traceback for the exception
        """
        # TODO: Wrap arguments so they can be serialized by JSON
        self.__send(
            'exception', '?', [str(exctype), str(excval), str(exctb)])

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Host and port parameters are missing. Abort.')
        sys.exit(1)
    
    host, port = sys.argv[1:]
    backgroundClient = BackgroundClient(host, int(port))
    # set the system exception handling function to ensure, that
    # we report on all unhandled exceptions
    sys.excepthook = backgroundClient._BackgroundClient__unhandled_exception
    # Start the main loop
    backgroundClient.run()
