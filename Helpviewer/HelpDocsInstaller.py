# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a thread class populating and updating the QtHelp
documentation database.
"""

from PyQt4.QtCore import pyqtSignal, QThread, Qt, QMutex, QDateTime, QDir, \
    QLibraryInfo, QFileInfo
from PyQt4.QtHelp import QHelpEngineCore

from eric5config import getConfig


class HelpDocsInstaller(QThread):
    """
    Class implementing the worker thread populating and updating the QtHelp
    documentation database.
    
    @signal errorMessage(str) emitted, if an error occurred during
        the installation of the documentation
    @signal docsInstalled(bool) emitted after the installation has finished
    """
    errorMessage = pyqtSignal(str)
    docsInstalled = pyqtSignal(bool)
    
    def __init__(self, collection):
        """
        Constructor
        
        @param collection full pathname of the collection file (string)
        """
        super().__init__()
        
        self.__abort = False
        self.__collection = collection
        self.__mutex = QMutex()
    
    def stop(self):
        """
        Public slot to stop the installation procedure.
        """
        if not self.isRunning():
            return
        
        self.__mutex.lock()
        self.__abort = True
        self.__mutex.unlock()
        self.wait()
    
    def installDocs(self):
        """
        Public method to start the installation procedure.
        """
        self.start(QThread.LowPriority)
    
    def run(self):
        """
        Protected method executed by the thread.
        """
        engine = QHelpEngineCore(self.__collection)
        engine.setupData()
        changes = False
        
        qt4Docs = ["designer", "linguist", "qt"]
        qt5Docs = ["activeqt", "qtconcurrent", "qtcore", "qtdbus", "qtdesigner", "qtdoc",
            "qtgraphicaleffects", "qtgui", "qthelp", "qtimageformats", "qtlinguist",
            "qtmultimedia", "qtnetwork", "qtopengl", "qtprintsupport", "qtqml", "qtquick",
            "qtscript", "qtsql", "qtsvg", "qttestlib", "qtuitools", "qtwebkit",
            "qtwebkitexamples", "qtwidgets", "qtxml", "qtxmlpatterns"]
        for qtDocs, version in [(qt4Docs, 4), (qt5Docs, 5)]:
            for doc in qtDocs:
                changes |= self.__installQtDoc(doc, version, engine)
                self.__mutex.lock()
                if self.__abort:
                    engine = None
                    self.__mutex.unlock()
                    return
                self.__mutex.unlock()
        
        changes |= self.__installEric5Doc(engine)
        engine = None
        del engine
        self.docsInstalled.emit(changes)
    
    def __installQtDoc(self, name, version, engine):
        """
        Private method to install/update a Qt help document.
        
        @param name name of the Qt help document (string)
        @param version Qt version of the help documens (integer)
        @param engine reference to the help engine (QHelpEngineCore)
        @return flag indicating success (boolean)
        """
        versionKey = "qt_version_{0}@@{1}".format(version, name)
        info = engine.customValue(versionKey, "")
        lst = info.split('|')
        
        dt = QDateTime()
        if len(lst) and lst[0]:
            dt = QDateTime.fromString(lst[0], Qt.ISODate)
        
        qchFile = ""
        if len(lst) == 2:
            qchFile = lst[1]
        
        if version == 4:
            docsPath = QDir(QLibraryInfo.location(QLibraryInfo.DocumentationPath) + \
                       QDir.separator() + "qch")
        elif version == 5:
            docsPath = QDir(QLibraryInfo.location(QLibraryInfo.DocumentationPath))
        else:
            # unsupported Qt version
            return False
        
        files = docsPath.entryList(["*.qch"])
        if not files:
            engine.setCustomValue(versionKey,
                QDateTime().toString(Qt.ISODate) + '|')
            return False
        
        for f in files:
            if f.startswith(name):
                fi = QFileInfo(docsPath.absolutePath() + QDir.separator() + f)
                namespace = QHelpEngineCore.namespaceName(fi.absoluteFilePath())
                if not namespace:
                    continue
                
                if dt.isValid() and \
                   namespace in engine.registeredDocumentations() and \
                   fi.lastModified().toString(Qt.ISODate) == dt.toString(Qt.ISODate) and \
                   qchFile == fi.absoluteFilePath():
                    return False
                
                if namespace in engine.registeredDocumentations():
                    engine.unregisterDocumentation(namespace)
                
                if not engine.registerDocumentation(fi.absoluteFilePath()):
                    self.errorMessage.emit(
                        self.trUtf8("""<p>The file <b>{0}</b> could not be registered."""
                                    """<br/>Reason: {1}</p>""")\
                            .format(fi.absoluteFilePath, engine.error())
                    )
                    return False
                
                engine.setCustomValue(versionKey,
                    fi.lastModified().toString(Qt.ISODate) + '|' + \
                    fi.absoluteFilePath())
                return True
        
        return False
    
    def __installEric5Doc(self, engine):
        """
        Private method to install/update the eric5 help documentation.
        
        @param engine reference to the help engine (QHelpEngineCore)
        @return flag indicating success (boolean)
        """
        versionKey = "eric5_ide"
        info = engine.customValue(versionKey, "")
        lst = info.split('|')
        
        dt = QDateTime()
        if len(lst) and lst[0]:
            dt = QDateTime.fromString(lst[0], Qt.ISODate)
        
        qchFile = ""
        if len(lst) == 2:
            qchFile = lst[1]
        
        docsPath = QDir(getConfig("ericDocDir") + QDir.separator() + "Help")
        
        files = docsPath.entryList(["*.qch"])
        if not files:
            engine.setCustomValue(versionKey,
                QDateTime().toString(Qt.ISODate) + '|')
            return False
        
        for f in files:
            if f == "source.qch":
                fi = QFileInfo(docsPath.absolutePath() + QDir.separator() + f)
                if dt.isValid() and \
                   fi.lastModified().toString(Qt.ISODate) == dt.toString(Qt.ISODate) and \
                   qchFile == fi.absoluteFilePath():
                    return False
                
                namespace = QHelpEngineCore.namespaceName(fi.absoluteFilePath())
                if not namespace:
                    continue
                
                if namespace in engine.registeredDocumentations():
                    engine.unregisterDocumentation(namespace)
                
                if not engine.registerDocumentation(fi.absoluteFilePath()):
                    self.errorMessage.emit(
                        self.trUtf8("""<p>The file <b>{0}</b> could not be registered."""
                                    """<br/>Reason: {1}</p>""")\
                            .format(fi.absoluteFilePath, engine.error())
                    )
                    return False
                
                engine.setCustomValue(versionKey,
                    fi.lastModified().toString(Qt.ISODate) + '|' + \
                    fi.absoluteFilePath())
                return True
        
        return False
