# -*- coding: utf-8 -*-

# Copyright (c) 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing an interface to the Mercurial command server.
"""

import struct
import io

from PyQt4.QtCore import QProcess, QProcessEnvironment, QObject, QByteArray, \
    QCoreApplication

import Preferences


class HgClient(QObject):
    """
    Class implementing the Mercurial command server interface.
    """
    InputFormat = ">I"
    OutputFormat = ">cI"
    OutputFormatSize = struct.calcsize(OutputFormat)
    ReturnFormat = ">i"
    
    def __init__(self, repoPath, encoding, parent=None):
        """
        Constructor
        
        @param repoPath root directory of the repository (string)
        @param encoding encoding to be used by the command server (string)
        @param parent reference to the parent object (QObject)
        """
        super().__init__(parent)
        
        self.__server = None
        self.__started = False
        self.__version = None
        self.__encoding = Preferences.getSystem("IOEncoding")
        self.__cancel = False
        self.__commandRunning = False
        self.__repoPath = repoPath
        
        # generate command line and environment
        self.__serverArgs = []
        self.__serverArgs.append("serve")
        self.__serverArgs.append("--cmdserver")
        self.__serverArgs.append("pipe")
        self.__serverArgs.append("--config")
        self.__serverArgs.append("ui.interactive=True")
        if repoPath:
            self.__serverArgs.append("--repository")
            self.__serverArgs.append(repoPath)
        
        if encoding:
            self.__encoding = encoding
    
    def startServer(self):
        """
        Public method to start the command server.
        
        @return tuple of flag indicating a successful start (boolean) and
            an error message (string) in case of failure
        """
        self.__server = QProcess()
        self.__server.setWorkingDirectory(self.__repoPath)
        
        # connect signals
        self.__server.finished.connect(self.__serverFinished)
        
        # set the encoding for the server
        if self.__encoding:
            env = QProcessEnvironment.systemEnvironment()
            env.insert("HGENCODING", self.__encoding)
            self.__server.setProcessEnvironment(env)
        
        self.__server.start('hg', self.__serverArgs)
        serverStarted = self.__server.waitForStarted()
        if not serverStarted:
            return False, self.trUtf8(
                    'The process {0} could not be started. '
                    'Ensure, that it is in the search path.'
                ).format('hg')
        
        self.__server.setReadChannel(QProcess.StandardOutput)
        ok, error = self.__readHello()
        self.__started = ok
        return ok, error
    
    def stopServer(self):
        """
        Public method to stop the command server.
        """
        self.__server.closeWriteChannel()
        res = self.__server.waitForFinished(5000)
        if not res:
            self.__server.terminate()
            res = self.__server.waitForFinished(3000)
            if not res:
                self.__server.kill()
                self.__server.waitForFinished(3000)
        
        self.__started = False
        self.__server.finished.disconnect(self.__serverFinished)
        self.__server = None
    
    def restartServer(self):
        """
        Public method to restart the command server.
        
        @return tuple of flag indicating a successful start (boolean) and
            an error message (string) in case of failure
        """
        self.stopServer()
        return self.startServer()
    
    def __readHello(self):
        """
        Private method to read the hello message sent by the command server.
        
        @return tuple of flag indicating success (boolean) and an error message
            in case of failure (string)
        """
        ch, msg = self.__readChannel()
        if not ch:
            return False, self.trUtf8("Did not receive the 'hello' message.")
        elif ch != "o":
            return False, self.trUtf8("Received data on unexpected channel.")
        
        msg = msg.split("\n")
        
        if not msg[0].startswith("capabilities: "):
            return False, self.trUtf8("Bad 'hello' message, expected 'capabilities: '"
                                      " but got '{0}'.").format(msg[0])
        self.__capabilities = msg[0][len('capabilities: '):]
        if not self.__capabilities:
            return False, self.trUtf8("'capabilities' message did not contain"
                                      " any capability.")
        
        self.__capabilities = set(self.__capabilities.split())
        if "runcommand" not in self.__capabilities:
            return False, "'capabilities' did not contain 'runcommand'."
        
        if not msg[1].startswith("encoding: "):
            return False, self.trUtf8("Bad 'hello' message, expected 'encoding: '"
                                      " but got '{0}'.").format(msg[1])
        encoding = msg[1][len('encoding: '):]
        if not encoding:
            return False, self.trUtf8("'encoding' message did not contain"
                                      " any encoding.")
        self.__encoding = encoding
        
        return True, ""
    
    def __serverFinished(self, exitCode, exitStatus):
        """
        Private slot connected to the finished signal.
        
        @param exitCode exit code of the process (integer)
        @param exitStatus exit status of the process (QProcess.ExitStatus)
        """
        self.__started = False
    
    def __readChannel(self):
        """
        Private method to read data from the command server.
        
        @return tuple of channel designator and channel data
            (string, integer or string or bytes)
        """
        if self.__server.bytesAvailable() > 0 or \
           self.__server.waitForReadyRead(10000):
            data = bytes(self.__server.read(HgClient.OutputFormatSize))
            if not data:
                return "", ""
            
            channel, length = struct.unpack(HgClient.OutputFormat, data)
            channel = channel.decode(self.__encoding)
            if channel in "IL":
                return channel, length
            else:
                data = self.__server.read(length)
                if channel == "r":
                    return (channel, data)
                else:
                    return (channel, str(data, self.__encoding, "replace"))
        else:
            return "", ""
    
    def __writeDataBlock(self, data):
        """
        Private slot to write some data to the command server.
        
        @param data data to be sent (string)
        """
        if not isinstance(data, bytes):
            data = data.encode(self.__encoding)
        self.__server.write(QByteArray(struct.pack(HgClient.InputFormat, len(data))))
        self.__server.write(QByteArray(data))
        self.__server.waitForBytesWritten()
    
    def __runcommand(self, args, inputChannels, outputChannels):
        """
        Private method to run a command in the server (low level).
        
        @param args list of arguments for the command (list of string)
        @param inputChannels dictionary of input channels. The dictionary must
            have the keys 'I' and 'L' and each entry must be a function receiving
            the number of bytes to write.
        @param outputChannels dictionary of output channels. The dictionary must
            have the keys 'o' and 'e' and each entry must be a function receiving
            the data.
        @return result code of the command, -1 if the command server wasn't started or
            -10, if the command was canceled (integer)
        """
        if not self.__started:
            return -1
        
        self.__server.write(QByteArray(b'runcommand\n'))
        self.__writeDataBlock('\0'.join(args))
        
        while True:
            QCoreApplication.processEvents()
            
            if self.__cancel:
                return -10
            
            if self.__server.bytesAvailable() == 0:
                continue
            channel, data = self.__readChannel()
            
            # input channels
            if channel in inputChannels:
                self.__writeDataBlock(inputChannels[channel](data))
            
            # output channels
            elif channel in outputChannels:
                outputChannels[channel](data)
            
            # result channel, command is finished
            elif channel == "r":
                return struct.unpack(HgClient.ReturnFormat, data)[0]
            
            # unexpected but required channel
            elif channel.isupper():
                raise RuntimeError(
                    "Unexpected but required channel '{0}'.".format(channel))
            
            # optional channels
            else:
                pass
    
    def runcommand(self, args, prompt=None, input=None, output=None, error=None):
        """
        Public method to execute a command via the command server.
        
        @param args list of arguments for the command (list of string)
        @keyparam prompt function to reply to prompts by the server. It
            receives the max number of bytes to return and the contents
            of the output channel received so far.
        @keyparam input function to reply to bulk data requests by the server.
            It receives the max number of bytes to return.
        @keyparam output function receiving the data from the server (string).
            If a prompt function is given, this parameter will be ignored.
        @keyparam error function receiving error messages from the server (string)
        @return output and errors of the command server (string). In case output
            and/or error functions were given, the respective return value will
            be an empty string.
        """
        self.__commandRunning = True
        outputChannels = {}
        outputBuffer = None
        errorBuffer = None
        
        if prompt is not None or output is None:
            outputBuffer = io.StringIO()
            outputChannels["o"] = outputBuffer.write
        else:
            outputChannels["o"] = output
        if error:
            outputChannels["e"] = error
        else:
            errorBuffer = io.StringIO()
            outputChannels["e"] = errorBuffer.write
        
        inputChannels = {}
        if prompt is not None:
            def func(size):
                reply = prompt(size, outputBuffer.getvalue())
                return reply
            inputChannels["L"] = func
        if input is not None:
            inputChannels["I"] = input
        
        self.__cancel = False
        self.__runcommand(args, inputChannels, outputChannels)
        if outputBuffer:
            out = outputBuffer.getvalue()
        else:
            out = ""
        if errorBuffer:
            err = errorBuffer.getvalue()
        else:
            err = ""
        
        self.__commandRunning = False
        
        return out, err
    
    def cancel(self):
        """
        Public method to cancel the running command.
        """
        self.__cancel = True
        self.restartServer()
    
    def wasCanceled(self):
        """
        Public method to check, if the last command was canceled.
        """
        return self.__cancel
    
    def isExecuting(self):
        """
        Public method to check, if the server is executing a command.
        
        @return flag indicating the execution of a command (boolean)
        """
