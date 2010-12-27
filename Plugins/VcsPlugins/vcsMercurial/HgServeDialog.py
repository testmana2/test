# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog for the Mercurial server.
"""

import os

from PyQt4.QtCore import QProcess, Qt, QSize
from PyQt4.QtGui import QMainWindow, QAction, QToolBar, QPlainTextEdit, \
    QTextCursor, QBrush, QSpinBox, QComboBox

from E5Gui.E5Application import e5App
from E5Gui import E5MessageBox

import UI.PixmapCache

import Preferences

class HgServeDialog(QMainWindow):
    """
    Class implementing a dialog for the Mercurial server.
    """
    def __init__(self, vcs, path, parent = None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param path path of the repository to serve (string)
        @param parent reference to the parent widget (QWidget)
        """
        QMainWindow.__init__(self, parent)
        
        self.vcs = vcs
        self.__repoPath = path
        
        self.__styles = ["paper", "coal", "gitweb", "monoblue", "spartan", ]
        
        self.setWindowTitle(self.trUtf8("Mercurial Server"))
        
        self.__startAct = QAction(
            UI.PixmapCache.getIcon(
                os.path.join("VcsPlugins", "vcsMercurial", "icons", "startServer.png")), 
            self.trUtf8("Start Server"), self) 
        self.__startAct.triggered[()].connect(self.__startServer)
        self.__stopAct = QAction(
            UI.PixmapCache.getIcon(
                os.path.join("VcsPlugins", "vcsMercurial", "icons", "stopServer.png")), 
            self.trUtf8("Stop Server"), self) 
        self.__stopAct.triggered[()].connect(self.__stopServer)
        self.__browserAct = QAction(
            UI.PixmapCache.getIcon("home.png"), 
            self.trUtf8("Start Browser"), self) 
        self.__browserAct.triggered[()].connect(self.__startBrowser)
        
        self.__portSpin = QSpinBox(self)
        self.__portSpin.setMinimum(2048)
        self.__portSpin.setMaximum(65535)
        self.__portSpin.setToolTip(self.trUtf8("Enter the server port"))
        self.__portSpin.setValue(self.vcs.getPlugin().getPreferences("ServerPort"))
        
        self.__styleCombo = QComboBox(self)
        self.__styleCombo.addItems(self.__styles)
        self.__styleCombo.setToolTip(self.trUtf8("Select the style to use"))
        self.__styleCombo.setCurrentIndex(self.__styleCombo.findText(
            self.vcs.getPlugin().getPreferences("ServerStyle")))
        
        self.__serverToolbar = QToolBar(self.trUtf8("Server"), self)
        self.__serverToolbar.addAction(self.__startAct)
        self.__serverToolbar.addAction(self.__stopAct)
        self.__serverToolbar.addSeparator()
        self.__serverToolbar.addWidget(self.__portSpin)
        self.__serverToolbar.addWidget(self.__styleCombo)
        
        self.__browserToolbar = QToolBar(self.trUtf8("Browser"), self)
        self.__browserToolbar.addAction(self.__browserAct)
        
        self.addToolBar(Qt.TopToolBarArea, self.__serverToolbar)
        self.addToolBar(Qt.TopToolBarArea, self.__browserToolbar)
        
        self.__log = QPlainTextEdit(self)
        self.setCentralWidget(self.__log)
        
        # polish up the dialog
        self.__startAct.setEnabled(True)
        self.__stopAct.setEnabled(False)
        self.__browserAct.setEnabled(False)
        self.__portSpin.setEnabled(True)
        self.__styleCombo.setEnabled(True)
        self.resize(QSize(800, 600).expandedTo(self.minimumSizeHint()))
        
        self.process = QProcess()
        self.process.finished.connect(self.__procFinished)
        self.process.readyReadStandardOutput.connect(self.__readStdout)
        self.process.readyReadStandardError.connect(self.__readStderr)
        
        self.cNormalFormat = self.__log.currentCharFormat()
        self.cErrorFormat = self.__log.currentCharFormat()
        self.cErrorFormat.setForeground(QBrush(Preferences.getUI("LogStdErrColour")))
    
    def __startServer(self):
        """
        Private slot to start the Mercurial server.
        """
        port = self.__portSpin.value()
        style = self.__styleCombo.currentText()
        
        args = []
        args.append("serve")
        args.append("-v")
        args.append("--port")
        args.append(str(port))
        args.append("--style")
        args.append(style)
        
        self.process.setWorkingDirectory(self.__repoPath)
        
        self.process.start('hg', args)
        procStarted = self.process.waitForStarted()
        if procStarted:
            self.__startAct.setEnabled(False)
            self.__stopAct.setEnabled(True)
            self.__browserAct.setEnabled(True)
            self.__portSpin.setEnabled(False)
            self.__styleCombo.setEnabled(False)
            self.vcs.getPlugin().setPreferences("ServerPort", port)
            self.vcs.getPlugin().setPreferences("ServerStyle", style)
        else:
            E5MessageBox.critical(self,
                self.trUtf8('Process Generation Error'),
                self.trUtf8(
                    'The process {0} could not be started. '
                    'Ensure, that it is in the search path.'
                ).format('hg'))
    
    def __stopServer(self):
        """
        Private slot to stop the Mercurial server.
        """
        if self.process is not None and \
           self.process.state() != QProcess.NotRunning:
            self.process.terminate()
            self.process.waitForFinished(5000)
            if self.process.state() != QProcess.NotRunning:
                self.process.kill()
        
        self.__startAct.setEnabled(True)
        self.__stopAct.setEnabled(False)
        self.__browserAct.setEnabled(False)
        self.__portSpin.setEnabled(True)
        self.__styleCombo.setEnabled(True)
    
    def __startBrowser(self):
        """
        Private slot to start a browser for the served repository.
        """
        ui = e5App().getObject("UserInterface")
        ui.launchHelpViewer("http://localhost:{0}".format(self.__portSpin.value()))
    
    def closeEvent(self, e):
        """
        Private slot implementing a close event handler.
        
        @param e close event (QCloseEvent)
        """
        self.__stopServer()
    
    def __procFinished(self, exitCode, exitStatus):
        """
        Private slot connected to the finished signal.
        
        @param exitCode exit code of the process (integer)
        @param exitStatus exit status of the process (QProcess.ExitStatus)
        """
        self.__stopServer()
    
    def __readStdout(self):
        """
        Private slot to handle the readyReadStandardOutput signal. 
        
        It reads the output of the process and inserts it into the log.
        """
        if self.process is not None:
            s = str(self.process.readAllStandardOutput(), 
                     Preferences.getSystem("IOEncoding"), 
                     'replace')
            self.__appendText(s, False)
    
    def __readStderr(self):
        """
        Private slot to handle the readyReadStandardError signal.
        
        It reads the error output of the process and inserts it into the log.
        """
        if self.process is not None:
            s = str(self.process.readAllStandardError(), 
                     Preferences.getSystem("IOEncoding"), 
                     'replace')
            self.__appendText(s, True)
    
    def __appendText(self, txt, error = False):
        """
        Public method to append text to the end.
        
        @param txt text to insert (string)
        @param error flag indicating to insert error text (boolean)
        """
        tc = self.__log.textCursor()
        tc.movePosition(QTextCursor.End)
        self.__log.setTextCursor(tc)
        if error:
            self.__log.setCurrentCharFormat(self.cErrorFormat)
        else:
            self.__log.setCurrentCharFormat(self.cNormalFormat)
        self.__log.insertPlainText(txt)
        self.__log.ensureCursorVisible()
