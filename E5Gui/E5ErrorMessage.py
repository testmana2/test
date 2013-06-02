# -*- coding: utf-8 -*-

# Copyright (c) 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a specialized error message dialog.
"""

from PyQt4.QtCore import qInstallMsgHandler, QCoreApplication, QtDebugMsg, \
    QtWarningMsg, QtCriticalMsg, QtFatalMsg, QThread, QMetaObject, Qt, Q_ARG
from PyQt4.QtGui import QErrorMessage, qApp

import Utilities


__msgHandlerDialog = None
__origMsgHandler = None


class E5ErrorMessage(QErrorMessage):
    """
    Class implementing a specialized error message dialog.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        
        # TODO: make this list configurable by the user
        self.__filters = [
            "QFont::",
            "QCocoaMenu::removeMenuItem",
            "QCocoaMenu::insertNative",
            ",type id:"
        ]
    
    def __filterMessage(self, message):
        """
        Private method to filter messages.
        
        @param message message to be checked (string)
        @return flag indicating that the message should be filtered out (boolean)
        """
        for filter in self.__filters:
            if filter in message:
                return True
        
        return False
    
    def showMessage(self, message, msgType=""):
        """
        Public method to show a message.
        
        @param message error message to be shown (string)
        @param msgType type of the error message (string)
        """
        if not self.__filterMessage(message):
            if msgType:
                super().showMessage(message, msgType)
            else:
                super().showMessage(message)


def messageHandler(msgType, message):
    """
    Module function handling messages.
    
    @param msgType type of the message (integer, QtMsgType)
    @param message message to be shown (bytes)
    """
    if __msgHandlerDialog:
        try:
            if msgType == QtDebugMsg:
                messageType = QCoreApplication.translate(
                    "E5ErrorMessage", "Debug Message:")
            elif msgType == QtWarningMsg:
                messageType = QCoreApplication.translate(
                    "E5ErrorMessage", "Warning:")
            elif msgType == QtCriticalMsg:
                messageType = QCoreApplication.translate(
                    "E5ErrorMessage", "Critical:")
            elif msgType == QtFatalMsg:
                messageType = QCoreApplication.translate(
                    "E5ErrorMessage", "Fatal Error:")
            if isinstance(message, bytes):
                message = message.decode()
            msg = "<p><b>{0}</b></p><p>{1}</p>".format(
                messageType, Utilities.html_uencode(message))
            if QThread.currentThread() == qApp.thread():
                __msgHandlerDialog.showMessage(msg)
            else:
                QMetaObject.invokeMethod(
                    __msgHandlerDialog,
                    "showMessage",
                    Qt.QueuedConnection,
                    Q_ARG(str, msg))
            return
        except RuntimeError:
            pass
    elif __origMsgHandler:
        __origMsgHandler(msgType, message)
        return
    
    if msgType == QtDebugMsg:
        messageType = QCoreApplication.translate("E5ErrorMessage", "Debug Message")
    elif msgType == QtWarningMsg:
        messageType = QCoreApplication.translate("E5ErrorMessage", "Warning")
    elif msgType == QtCriticalMsg:
        messageType = QCoreApplication.translate("E5ErrorMessage", "Critical")
    elif msgType == QtFatalMsg:
        messageType = QCoreApplication.translate("E5ErrorMessage", "Fatal Error")
    if isinstance(message, bytes):
        message = message.decode()
    print("{0}: {1}".format(messageType, message))


def qtHandler():
    """
    Module function to install an E5ErrorMessage dialog as the global
    message handler.
    """
    global __msgHandlerDialog, __origMsgHandler
    
    if __msgHandlerDialog is None:
        # Install an E5ErrorMessage dialog as the global message handler.
        __msgHandlerDialog = E5ErrorMessage()
        __origMsgHandler = qInstallMsgHandler(messageHandler)
    
    return __msgHandlerDialog
