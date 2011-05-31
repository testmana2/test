# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog starting a process and showing its output.
"""

import os

from PyQt4.QtCore import QProcess, QTimer, pyqtSlot, Qt, QCoreApplication
from PyQt4.QtGui import QDialog, QDialogButtonBox, QLineEdit

from E5Gui import E5MessageBox

from .Ui_HgDialog import Ui_HgDialog

import Preferences


class HgDialog(QDialog, Ui_HgDialog):
    """
    Class implementing a dialog starting a process and showing its output.
    
    It starts a QProcess and displays a dialog that
    shows the output of the process. The dialog is modal,
    which causes a synchronized execution of the process.
    """
    def __init__(self, text, parent=None):
        """
        Constructor
        
        @param text text to be shown by the label (string)
        @param parent parent widget (QWidget)
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.proc = None
        self.username = ''
        self.password = ''
        
        self.outputGroup.setTitle(text)
    
    def __finish(self):
        """
        Private slot called when the process finished or the user pressed the button.
        """
        if self.proc is not None and \
           self.proc.state() != QProcess.NotRunning:
            self.proc.terminate()
            QTimer.singleShot(2000, self.proc.kill)
            self.proc.waitForFinished(3000)
        
        self.inputGroup.setEnabled(False)
        self.inputGroup.hide()
        
        self.proc = None
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        self.buttonBox.button(QDialogButtonBox.Close).setFocus(Qt.OtherFocusReason)
        
        if Preferences.getVCS("AutoClose") and \
           self.normal and \
           self.errors.toPlainText() == "":
            self.accept()
    
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.buttonBox.button(QDialogButtonBox.Close):
            self.close()
        elif button == self.buttonBox.button(QDialogButtonBox.Cancel):
            self.__finish()
    
    def __procFinished(self, exitCode, exitStatus):
        """
        Private slot connected to the finished signal.
        
        @param exitCode exit code of the process (integer)
        @param exitStatus exit status of the process (QProcess.ExitStatus)
        """
        self.normal = (exitStatus == QProcess.NormalExit) and (exitCode == 0)
        self.__finish()
    
    def startProcess(self, args, workingDir=None, showArgs=True):
        """
        Public slot used to start the process.
        
        @param args list of arguments for the process (list of strings)
        @keyparam workingDir working directory for the process (string)
        @keyparam showArgs flag indicating to show the arguments (boolean)
        @return flag indicating a successful start of the process
        """
        self.errorGroup.hide()
        self.normal = False
        self.intercept = False
        
        self.__hasAddOrDelete = False
        if args[0] in ["fetch", "qpush", "qpop", "qgoto", "rebase", "transplant",
                       "update"] or \
           (args[0] == "pull" and \
            ("--update" in args[1:] or "--rebase" in args[1:])):
            self.__updateCommand = True
        else:
            self.__updateCommand = False
        
        self.proc = QProcess()
        
        if showArgs:
            self.resultbox.append(' '.join(args))
            self.resultbox.append('')
        
        self.proc.finished.connect(self.__procFinished)
        self.proc.readyReadStandardOutput.connect(self.__readStdout)
        self.proc.readyReadStandardError.connect(self.__readStderr)
        
        if workingDir:
            self.proc.setWorkingDirectory(workingDir)
        self.proc.start('hg', args)
        procStarted = self.proc.waitForStarted()
        if not procStarted:
            self.buttonBox.setFocus()
            self.inputGroup.setEnabled(False)
            E5MessageBox.critical(self,
                self.trUtf8('Process Generation Error'),
                self.trUtf8(
                    'The process {0} could not be started. '
                    'Ensure, that it is in the search path.'
                ).format('hg'))
        else:
            self.inputGroup.setEnabled(True)
            self.inputGroup.show()
        return procStarted
    
    def normalExit(self):
        """
        Public method to check for a normal process termination.
        
        @return flag indicating normal process termination (boolean)
        """
        return self.normal
    
    def normalExitWithoutErrors(self):
        """
        Public method to check for a normal process termination without
        error messages.
        
        @return flag indicating normal process termination (boolean)
        """
        return self.normal and self.errors.toPlainText() == ""
    
    def __readStdout(self):
        """
        Private slot to handle the readyReadStandardOutput signal.
        
        It reads the output of the process, formats it and inserts it into
        the contents pane.
        """
        if self.proc is not None:
            s = str(self.proc.readAllStandardOutput(),
                    Preferences.getSystem("IOEncoding"),
                    'replace')
            self.resultbox.insertPlainText(s)
            self.resultbox.ensureCursorVisible()
            
            # check for a changed project file
            if self.__updateCommand:
                for line in s.splitlines():
                    if '.e4p' in line:
                        self.__hasAddOrDelete = True
                        break
        
        QCoreApplication.processEvents()
    
    def __readStderr(self):
        """
        Private slot to handle the readyReadStandardError signal.
        
        It reads the error output of the process and inserts it into the
        error pane.
        """
        if self.proc is not None:
            self.errorGroup.show()
            s = str(self.proc.readAllStandardError(),
                    Preferences.getSystem("IOEncoding"),
                    'replace')
            self.errors.insertPlainText(s)
            self.errors.ensureCursorVisible()
        
        QCoreApplication.processEvents()
    
    def on_passwordCheckBox_toggled(self, isOn):
        """
        Private slot to handle the password checkbox toggled.
        
        @param isOn flag indicating the status of the check box (boolean)
        """
        if isOn:
            self.input.setEchoMode(QLineEdit.Password)
        else:
            self.input.setEchoMode(QLineEdit.Normal)
    
    @pyqtSlot()
    def on_sendButton_clicked(self):
        """
        Private slot to send the input to the subversion process.
        """
        input = self.input.text()
        input += os.linesep
        
        if self.passwordCheckBox.isChecked():
            self.errors.insertPlainText(os.linesep)
            self.errors.ensureCursorVisible()
        else:
            self.errors.insertPlainText(input)
            self.errors.ensureCursorVisible()
        
        self.proc.write(input)
        
        self.passwordCheckBox.setChecked(False)
        self.input.clear()
    
    def on_input_returnPressed(self):
        """
        Private slot to handle the press of the return key in the input field.
        """
        self.intercept = True
        self.on_sendButton_clicked()
    
    def keyPressEvent(self, evt):
        """
        Protected slot to handle a key press event.
        
        @param evt the key press event (QKeyEvent)
        """
        if self.intercept:
            self.intercept = False
            evt.accept()
            return
        QDialog.keyPressEvent(self, evt)
    
    def hasAddOrDelete(self):
        """
        Public method to check, if the last action contained an add or delete.
        
        @return flag indicating the presence of an add or delete (boolean)
        """
        return self.__hasAddOrDelete
