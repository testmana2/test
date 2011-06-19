# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the UI to the pyunit package.
"""

import unittest
import sys
import traceback
import time
import re
import os

from PyQt4.QtCore import pyqtSignal, QEvent, Qt, pyqtSlot
from PyQt4.QtGui import QWidget, QColor, QDialog, QApplication, QDialogButtonBox, \
    QMainWindow

from E5Gui.E5Application import e5App
from E5Gui.E5Completers import E5FileCompleter
from E5Gui import E5MessageBox, E5FileDialog

from .Ui_UnittestDialog import Ui_UnittestDialog
from .Ui_UnittestStacktraceDialog import Ui_UnittestStacktraceDialog

from DebugClients.Python3.coverage import coverage

import UI.PixmapCache

import Utilities


class UnittestDialog(QWidget, Ui_UnittestDialog):
    """
    Class implementing the UI to the pyunit package.
    
    @signal unittestFile(str, int, int) emitted to show the source of a unittest file
    """
    unittestFile = pyqtSignal(str, int, int)
    
    def __init__(self, prog=None, dbs=None, ui=None, parent=None, name=None):
        """
        Constructor
        
        @param prog filename of the program to open
        @param dbs reference to the debug server object. It is an indication
                whether we were called from within the eric5 IDE
        @param ui reference to the UI object
        @param parent parent widget of this dialog (QWidget)
        @param name name of this dialog (string)
        """
        super().__init__(parent)
        if name:
            self.setObjectName(name)
        self.setupUi(self)
        
        self.startButton = self.buttonBox.addButton(
            self.trUtf8("Start"), QDialogButtonBox.ActionRole)
        self.startButton.setToolTip(self.trUtf8("Start the selected testsuite"))
        self.startButton.setWhatsThis(self.trUtf8(
            """<b>Start Test</b>"""
            """<p>This button starts the selected testsuite.</p>"""))
        self.stopButton = self.buttonBox.addButton(
            self.trUtf8("Stop"), QDialogButtonBox.ActionRole)
        self.stopButton.setToolTip(self.trUtf8("Stop the running unittest"))
        self.stopButton.setWhatsThis(self.trUtf8(
            """<b>Stop Test</b>"""
            """<p>This button stops a running unittest.</p>"""))
        self.stopButton.setEnabled(False)
        self.startButton.setDefault(True)
        
        self.dbs = dbs
        
        self.setWindowFlags(
            self.windowFlags() | Qt.WindowFlags(Qt.WindowContextHelpButtonHint))
        self.setWindowIcon(UI.PixmapCache.getIcon("eric.png"))
        self.setWindowTitle(self.trUtf8("Unittest"))
        if dbs:
            self.ui = ui
        else:
            self.localCheckBox.hide()
        self.__setProgressColor("green")
        self.progressLed.setDarkFactor(150)
        self.progressLed.off()
        
        self.testSuiteCompleter = E5FileCompleter(self.testsuiteComboBox)
        
        self.fileHistory = []
        self.testNameHistory = []
        self.running = False
        self.savedModulelist = None
        self.savedSysPath = sys.path
        if prog:
            self.insertProg(prog)
        
        self.rx1 = self.trUtf8("^Failure: ")
        self.rx2 = self.trUtf8("^Error: ")
        
        # now connect the debug server signals if called from the eric5 IDE
        if self.dbs:
            self.dbs.utPrepared.connect(self.__UTPrepared)
            self.dbs.utFinished.connect(self.__setStoppedMode)
            self.dbs.utStartTest.connect(self.testStarted)
            self.dbs.utStopTest.connect(self.testFinished)
            self.dbs.utTestFailed.connect(self.testFailed)
            self.dbs.utTestErrored.connect(self.testErrored)
        
    def __setProgressColor(self, color):
        """
        Private methode to set the color of the progress color label.
        
        @param color colour to be shown (string)
        """
        self.progressLed.setColor(QColor(color))
        
    def insertProg(self, prog):
        """
        Public slot to insert the filename prog into the testsuiteComboBox object.
        
        @param prog filename to be inserted (string)
        """
        # prepend the selected file to the testsuite combobox
        if prog is None:
            prog = ""
        if prog in self.fileHistory:
            self.fileHistory.remove(prog)
        self.fileHistory.insert(0, prog)
        self.testsuiteComboBox.clear()
        self.testsuiteComboBox.addItems(self.fileHistory)
        
    def insertTestName(self, testName):
        """
        Public slot to insert a test name into the testComboBox object.
        
        @param testName name of the test to be inserted (string)
        """
        # prepend the selected file to the testsuite combobox
        if testName is None:
            testName = ""
        if testName in self.testNameHistory:
            self.testNameHistory.remove(testName)
        self.testNameHistory.insert(0, testName)
        self.testComboBox.clear()
        self.testComboBox.addItems(self.testNameHistory)
        
    @pyqtSlot()
    def on_fileDialogButton_clicked(self):
        """
        Private slot to open a file dialog.
        """
        if self.dbs:
            py2Extensions = \
                ' '.join(["*{0}".format(ext)
                          for ext in self.dbs.getExtensions('Python2')])
            py3Extensions = \
                ' '.join(["*{0}".format(ext)
                          for ext in self.dbs.getExtensions('Python3')])
            filter = self.trUtf8(
                "Python3 Files ({1});;Python2 Files ({0});;All Files (*)")\
                .format(py2Extensions, py3Extensions)
        else:
            filter = self.trUtf8("Python Files (*.py);;All Files (*)")
        prog = E5FileDialog.getOpenFileName(
            self,
            "",
            self.testsuiteComboBox.currentText(),
            filter)
        
        if not prog:
            return
        
        self.insertProg(Utilities.toNativeSeparators(prog))
        
    @pyqtSlot(str)
    def on_testsuiteComboBox_editTextChanged(self, txt):
        """
        Private slot to handle changes of the test file name.
        
        @param txt name of the test file (string)
        """
        if self.dbs:
            exts = self.dbs.getExtensions("Python3")
            if txt.endswith(exts):
                self.coverageCheckBox.setChecked(False)
                self.coverageCheckBox.setEnabled(False)
                self.localCheckBox.setChecked(False)
                self.localCheckBox.setEnabled(False)
                return
        
        self.coverageCheckBox.setEnabled(True)
        self.localCheckBox.setEnabled(True)
        
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.startButton:
            self.on_startButton_clicked()
        elif button == self.stopButton:
            self.on_stopButton_clicked()
        
    @pyqtSlot()
    def on_startButton_clicked(self):
        """
        Public slot to start the test.
        """
        if self.running:
            return
        
        prog = self.testsuiteComboBox.currentText()
        if not prog:
            E5MessageBox.critical(self,
                    self.trUtf8("Unittest"),
                    self.trUtf8("You must enter a test suite file."))
            return
        
        # prepend the selected file to the testsuite combobox
        self.insertProg(prog)
        self.sbLabel.setText(self.trUtf8("Preparing Testsuite"))
        QApplication.processEvents()
        
        testFunctionName = self.testComboBox.currentText()
        if testFunctionName:
            self.insertTestName(testFunctionName)
        else:
            testFunctionName = "suite"
        
        # build the module name from the filename without extension
        self.testName = os.path.splitext(os.path.basename(prog))[0]
        
        if self.dbs and not self.localCheckBox.isChecked():
            # we are cooperating with the eric5 IDE
            project = e5App().getObject("Project")
            if project.isOpen() and project.isProjectSource(prog):
                mainScript = project.getMainScript(True)
            else:
                mainScript = os.path.abspath(prog)
            self.dbs.remoteUTPrepare(prog, self.testName, testFunctionName,
                self.coverageCheckBox.isChecked(), mainScript,
                self.coverageEraseCheckBox.isChecked())
        else:
            # we are running as an application or in local mode
            sys.path = [os.path.dirname(os.path.abspath(prog))] + self.savedSysPath
            
            # clean up list of imported modules to force a reimport upon running the test
            if self.savedModulelist:
                for modname in list(sys.modules.keys()):
                    if modname not in self.savedModulelist:
                        # delete it
                        del(sys.modules[modname])
            self.savedModulelist = sys.modules.copy()
            
            # now try to generate the testsuite
            try:
                module = __import__(self.testName)
                try:
                    test = unittest.defaultTestLoader.loadTestsFromName(
                        testFunctionName, module)
                except AttributeError:
                    test = unittest.defaultTestLoader.loadTestsFromModule(module)
            except:
                exc_type, exc_value, exc_tb = sys.exc_info()
                E5MessageBox.critical(self,
                        self.trUtf8("Unittest"),
                        self.trUtf8("<p>Unable to run test <b>{0}</b>.<br>{1}<br>{2}</p>")
                            .format(self.testName, str(exc_type), str(exc_value)))
                return
                
            # now set up the coverage stuff
            if self.coverageCheckBox.isChecked():
                if self.dbs:
                    # we are cooperating with the eric5 IDE
                    project = e5App().getObject("Project")
                    if project.isOpen() and project.isProjectSource(prog):
                        mainScript = project.getMainScript(True)
                    else:
                        mainScript = os.path.abspath(prog)
                else:
                    mainScript = os.path.abspath(prog)
                cover = coverage(
                    data_file="{0}.coverage".format(os.path.splitext(mainScript)[0]))
                cover.use_cache(True)
                if self.coverageEraseCheckBox.isChecked():
                    cover.erase()
            else:
                cover = None
            
            self.testResult = QtTestResult(self)
            self.totalTests = test.countTestCases()
            self.__setRunningMode()
            if cover:
                cover.start()
            test.run(self.testResult)
            if cover:
                cover.stop()
                cover.save()
            self.__setStoppedMode()
            sys.path = self.savedSysPath
        
    def __UTPrepared(self, nrTests, exc_type, exc_value):
        """
        Private slot to handle the utPrepared signal.
        
        If the unittest suite was loaded successfully, we ask the
        client to run the test suite.
        
        @param nrTests number of tests contained in the test suite (integer)
        @param exc_type type of exception occured during preparation (string)
        @param exc_value value of exception occured during preparation (string)
        """
        if nrTests == 0:
            E5MessageBox.critical(self,
                    self.trUtf8("Unittest"),
                    self.trUtf8("<p>Unable to run test <b>{0}</b>.<br>{1}<br>{2}</p>")
                        .format(self.testName, exc_type, exc_value))
            return
            
        self.totalTests = nrTests
        self.__setRunningMode()
        self.dbs.remoteUTRun()
        
    @pyqtSlot()
    def on_stopButton_clicked(self):
        """
        Private slot to stop the test.
        """
        if self.dbs and not self.localCheckBox.isChecked():
            self.dbs.remoteUTStop()
        elif self.testResult:
            self.testResult.stop()
            
    def on_errorsListWidget_currentTextChanged(self, text):
        """
        Private slot to handle the highlighted signal.
        
        @param txt current text (string)
        """
        if text:
            text = re.sub(self.rx1, "", text)
            text = re.sub(self.rx2, "", text)
            itm = self.testsListWidget.findItems(text, Qt.MatchFlags(Qt.MatchExactly))[0]
            self.testsListWidget.setCurrentItem(itm)
            self.testsListWidget.scrollToItem(itm)
        
    def __setRunningMode(self):
        """
        Private method to set the GUI in running mode.
        """
        self.running = True
        
        # reset counters and error infos
        self.runCount = 0
        self.failCount = 0
        self.errorCount = 0
        self.remainingCount = self.totalTests
        self.errorInfo = []

        # reset the GUI
        self.progressCounterRunCount.setText(str(self.runCount))
        self.progressCounterFailureCount.setText(str(self.failCount))
        self.progressCounterErrorCount.setText(str(self.errorCount))
        self.progressCounterRemCount.setText(str(self.remainingCount))
        self.errorsListWidget.clear()
        self.testsListWidget.clear()
        self.progressProgressBar.setRange(0, self.totalTests)
        self.__setProgressColor("green")
        self.progressProgressBar.reset()
        self.stopButton.setEnabled(True)
        self.startButton.setEnabled(False)
        self.stopButton.setDefault(True)
        self.sbLabel.setText(self.trUtf8("Running"))
        self.progressLed.on()
        QApplication.processEvents()
        
        self.startTime = time.time()
        
    def __setStoppedMode(self):
        """
        Private method to set the GUI in stopped mode.
        """
        self.stopTime = time.time()
        self.timeTaken = float(self.stopTime - self.startTime)
        self.running = False
        
        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.startButton.setDefault(True)
        if self.runCount == 1:
            self.sbLabel.setText(self.trUtf8("Ran {0} test in {1:.3f}s")
                .format(self.runCount, self.timeTaken))
        else:
            self.sbLabel.setText(self.trUtf8("Ran {0} tests in {1:.3f}s")
                .format(self.runCount, self.timeTaken))
        self.progressLed.off()

    def testFailed(self, test, exc):
        """
        Public method called if a test fails.
        
        @param test name of the failed test (string)
        @param exc string representation of the exception (list of strings)
        """
        self.failCount += 1
        self.progressCounterFailureCount.setText(str(self.failCount))
        self.errorsListWidget.insertItem(0, self.trUtf8("Failure: {0}").format(test))
        self.errorInfo.insert(0, (test, exc))
        
    def testErrored(self, test, exc):
        """
        Public method called if a test errors.
        
        @param test name of the failed test (string)
        @param exc string representation of the exception (list of strings)
        """
        self.errorCount += 1
        self.progressCounterErrorCount.setText(str(self.errorCount))
        self.errorsListWidget.insertItem(0, self.trUtf8("Error: {0}").format(test))
        self.errorInfo.insert(0, (test, exc))
        
    def testStarted(self, test, doc):
        """
        Public method called if a test is about to be run.
        
        @param test name of the started test (string)
        @param doc documentation of the started test (string)
        """
        if doc:
            self.testsListWidget.insertItem(0, "    {0}".format(doc))
        self.testsListWidget.insertItem(0, test)
        if self.dbs is None or self.localCheckBox.isChecked():
            QApplication.processEvents()
        
    def testFinished(self):
        """
        Public method called if a test has finished.
        
        <b>Note</b>: It is also called if it has already failed or errored.
        """
        # update the counters
        self.remainingCount -= 1
        self.runCount += 1
        self.progressCounterRunCount.setText(str(self.runCount))
        self.progressCounterRemCount.setText(str(self.remainingCount))
        
        # update the progressbar
        if self.errorCount:
            self.__setProgressColor("red")
        elif self.failCount:
            self.__setProgressColor("orange")
        self.progressProgressBar.setValue(self.runCount)
        
    def on_errorsListWidget_itemDoubleClicked(self, lbitem):
        """
        Private slot called by doubleclicking an errorlist entry.
        
        It will popup a dialog showing the stacktrace.
        If called from eric, an additional button is displayed
        to show the python source in an eric source viewer (in
        erics main window.
        
        @param lbitem the listbox item that was double clicked
        """
        self.errListIndex = self.errorsListWidget.row(lbitem)
        text = lbitem.text()

        # get the error info
        test, tracebackLines = self.errorInfo[self.errListIndex]
        tracebackText = "".join(tracebackLines)

        # now build the dialog
        self.dlg = QDialog()
        ui = Ui_UnittestStacktraceDialog()
        ui.setupUi(self.dlg)
        
        ui.showButton = ui.buttonBox.addButton(
            self.trUtf8("Show Source"), QDialogButtonBox.ActionRole)
        ui.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        
        self.dlg.setWindowTitle(text)
        ui.testLabel.setText(test)
        ui.traceback.setPlainText(tracebackText)
        
        # one more button if called from eric
        if self.dbs:
            ui.showButton.clicked[()].connect(self.__showSource)
        else:
            ui.showButton.hide()

        # and now fire it up
        self.dlg.show()
        self.dlg.exec_()
        
    def __showSource(self):
        """
        Private slot to show the source of a traceback in an eric5 editor.
        """
        if not self.dbs:
            return
            
        # get the error info
        test, tracebackLines = self.errorInfo[self.errListIndex]
        # find the last entry matching the pattern
        for index in range(len(tracebackLines) - 1, -1, -1):
            fmatch = re.search(r'File "(.*?)", line (\d*?),.*', tracebackLines[index])
            if fmatch:
                break
        if fmatch:
            fn, ln = fmatch.group(1, 2)
            self.unittestFile.emit(fn, int(ln), 1)


class QtTestResult(unittest.TestResult):
    """
    A TestResult derivative to work with a graphical GUI.
    
    For more details see pyunit.py of the standard python distribution.
    """
    def __init__(self, parent):
        """
        Constructor
        
        @param parent The parent widget.
        """
        unittest.TestResult.__init__(self)
        self.parent = parent
        
    def addFailure(self, test, err):
        """
        Method called if a test failed.
        
        @param test Reference to the test object
        @param err The error traceback
        """
        unittest.TestResult.addFailure(self, test, err)
        tracebackLines = traceback.format_exception(*err + (10,))
        self.parent.testFailed(str(test), tracebackLines)
        
    def addError(self, test, err):
        """
        Method called if a test errored.
        
        @param test Reference to the test object
        @param err The error traceback
        """
        unittest.TestResult.addError(self, test, err)
        tracebackLines = traceback.format_exception(*err + (10,))
        self.parent.testErrored(str(test), tracebackLines)
        
    def startTest(self, test):
        """
        Method called at the start of a test.
        
        @param test Reference to the test object
        """
        unittest.TestResult.startTest(self, test)
        self.parent.testStarted(str(test), test.shortDescription())

    def stopTest(self, test):
        """
        Method called at the end of a test.
        
        @param test Reference to the test object
        """
        unittest.TestResult.stopTest(self, test)
        self.parent.testFinished()


class UnittestWindow(QMainWindow):
    """
    Main window class for the standalone dialog.
    """
    def __init__(self, prog=None, parent=None):
        """
        Constructor
        
        @param prog filename of the program to open
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.cw = UnittestDialog(prog=prog, parent=self)
        self.cw.installEventFilter(self)
        size = self.cw.size()
        self.setCentralWidget(self.cw)
        self.resize(size)
    
    def eventFilter(self, obj, event):
        """
        Public method to filter events.
        
        @param obj reference to the object the event is meant for (QObject)
        @param event reference to the event object (QEvent)
        @return flag indicating, whether the event was handled (boolean)
        """
        if event.type() == QEvent.Close:
            QApplication.exit()
            return True
        
        return False
