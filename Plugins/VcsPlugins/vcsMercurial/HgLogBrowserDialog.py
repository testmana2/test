# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to browse the log history.
"""

import os

from PyQt4.QtCore import pyqtSlot, SIGNAL, Qt, QDate, QProcess, QTimer, QRegExp, QSize
from PyQt4.QtGui import QDialog, QDialogButtonBox, QHeaderView, QTreeWidgetItem, \
    QApplication, QMessageBox, QCursor, QWidget, QLineEdit, QColor, QPixmap, \
    QPainter, QPen, QBrush, QIcon

from E5Gui.E5Application import e5App

from .Ui_HgLogBrowserDialog import Ui_HgLogBrowserDialog
from .HgDiffDialog import HgDiffDialog

import UI.PixmapCache

import Preferences

COLORNAMES = ["blue", "darkgreen", "red", "green", "darkblue", "purple",
              "cyan", "olive", "magenta", "darkred", "darkmagenta",
              "darkcyan", "gray", "yellow"]
COLORS = [str(QColor(x).name()) for x in COLORNAMES]

class HgLogBrowserDialog(QDialog, Ui_HgLogBrowserDialog):
    """
    Class implementing a dialog to browse the log history.
    """
    IconColumn     = 0
    BranchColumn   = 1
    RevisionColumn = 2
    AuthorColumn   = 3
    DateColumn     = 4
    MessageColumn  = 5
    TagsColumn     = 6
    
    def __init__(self, vcs, mode = "log", bundle = None, parent = None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param mode mode of the dialog (string; one of log, incoming, outgoing)
        @param bundle name of a bundle file (string)
        @param parent parent widget (QWidget)
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.filesTree.headerItem().setText(self.filesTree.columnCount(), "")
        self.filesTree.header().setSortIndicator(0, Qt.AscendingOrder)
        
        self.vcs = vcs
        if mode in ("log", "incoming", "outgoing"):
            self.commandMode = mode
        else:
            self.commandMode = "log"
        self.bundle = bundle
        
        self.__maxDate = QDate()
        self.__minDate = QDate()
        self.__filterLogsEnabled = True
        
        self.fromDate.setDisplayFormat("yyyy-MM-dd")
        self.toDate.setDisplayFormat("yyyy-MM-dd")
        self.fromDate.setDate(QDate.currentDate())
        self.toDate.setDate(QDate.currentDate())
        self.fieldCombo.setCurrentIndex(self.fieldCombo.findText(self.trUtf8("Message")))
        self.clearRxEditButton.setIcon(UI.PixmapCache.getIcon("clearLeft.png"))
        self.limitSpinBox.setValue(self.vcs.getPlugin().getPreferences("LogLimit"))
        self.stopCheckBox.setChecked(self.vcs.getPlugin().getPreferences("StopLogOnCopy"))
        
        self.__messageRole = Qt.UserRole
        self.__changesRole = Qt.UserRole + 1
        self.__edgesRole   = Qt.UserRole + 2
        self.__parentsRole = Qt.UserRole + 3
        
        self.process = QProcess()
        self.connect(self.process, SIGNAL('finished(int, QProcess::ExitStatus)'),
            self.__procFinished)
        self.connect(self.process, SIGNAL('readyReadStandardOutput()'),
            self.__readStdout)
        self.connect(self.process, SIGNAL('readyReadStandardError()'),
            self.__readStderr)
        
        self.flags = {
            'A' : self.trUtf8('Added'),
            'D' : self.trUtf8('Deleted'),
            'M' : self.trUtf8('Modified'), 
        }
        
        self.buf = []        # buffer for stdout
        self.diff = None
        self.__started = False
        self.__lastRev = 0
        self.projectMode = False
        
        # attributes to store log graph data
        self.__revs = []
        self.__revColors = {}
        self.__revColor = 0
        
        self.__dotRadius = 8
        self.__rowHeight = 20
        
        self.__branchColors = {}
        
        self.logTree.setIconSize(QSize(100 * self.__rowHeight, self.__rowHeight))
    
    def closeEvent(self, e):
        """
        Private slot implementing a close event handler.
        
        @param e close event (QCloseEvent)
        """
        if self.process is not None and \
           self.process.state() != QProcess.NotRunning:
            self.process.terminate()
            QTimer.singleShot(2000, self.process.kill)
            self.process.waitForFinished(3000)
        
        e.accept()
    
    def __resizeColumnsLog(self):
        """
        Private method to resize the log tree columns.
        """
        self.logTree.header().resizeSections(QHeaderView.ResizeToContents)
        self.logTree.header().setStretchLastSection(True)
    
    def __resizeColumnsFiles(self):
        """
        Private method to resize the changed files tree columns.
        """
        self.filesTree.header().resizeSections(QHeaderView.ResizeToContents)
        self.filesTree.header().setStretchLastSection(True)
    
    def __resortFiles(self):
        """
        Private method to resort the changed files tree.
        """
        sortColumn = self.filesTree.sortColumn()
        self.filesTree.sortItems(1, 
            self.filesTree.header().sortIndicatorOrder())
        self.filesTree.sortItems(sortColumn, 
            self.filesTree.header().sortIndicatorOrder())
    
    def __getColor(self, n):
        """
        Private method to get the (rotating) name of the color given an index.
        
        @param n color index (integer)
        @return color name (string)
        """
        return COLORS[n % len(COLORS)]
    
    def __branchColor(self, branchName):
        """
        Private method to calculate a color for a given branch name.
        
        @param branchName name of the branch (string)
        @return name of the color to use (string)
        """
        if branchName not in self.__branchColors:
            self.__branchColors[branchName] = self.__getColor(len(self.__branchColors))
        return self.__branchColors[branchName]
    
    def __generateEdges(self, rev, parents):
        """
        Private method to generate edge info for the give data.
        
        @param rev revision to calculate edge info for (integer)
        @param parents list of parent revisions (list of integers)
        @return tuple containing the column and color index for
            the given node and a list of tuples indicating the edges
            between the given node and its parents 
            (integer, integer, [(integer, integer, integer), ...])
        """
        if rev not in self.__revs:
            # new head
            self.__revs.append(rev)
            self.__revColors[rev] = self.__revColor
            self.__revColor += 1
        
        col = self.__revs.index(rev)
        color = self.__revColors.pop(rev)
        next = self.__revs[:]
        
        # add parents to next
        addparents = [p for p in parents if p not in next]
        next[col:col + 1] = addparents
        
        # set colors for the parents
        for i, p in enumerate(addparents):
            if not i:
                self.__revColors[p] = color
            else:
                self.__revColors[p] = self.__revColor
                self.__revColor += 1
        
        # add edges to the graph
        edges = []
        if parents[0] != -1:
            for ecol, erev in enumerate(self.__revs):
                if erev in next:
                    edges.append((ecol, next.index(erev), self.__revColors[erev]))
                elif erev == rev:
                    for p in parents:
                        edges.append((ecol, next.index(p), self.__revColors[p]))
        
        self.__revs = next
        return col, color, edges
    
    def __generateIcon(self, column, color, bottomedges, topedges, dotColor):
        """
        Private method to generate an icon containing the revision tree for the
        given data.
        
        @param column column index of the revision (integer)
        @param color color of the node (integer)
        @param bottomedges list of edges for the bottom of the node 
            (list of tuples of three integers)
        @param topedges list of edges for the top of the node 
            (list of tuples of three integers)
        @param dotColor color to be used for the dot (QColor)
        @return icon for the node (QIcon)
        """
        def col2x(col, radius):
            return int(1.2 * radius) * col + radius // 2 + 3
        
        radius = self.__dotRadius
        w = len(bottomedges) * radius + 20
        h = self.__rowHeight

        dot_x = col2x(column, radius) - radius // 2
        dot_y = h // 2

        pix = QPixmap(w, h)
        pix.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen(Qt.blue)
        pen.setWidth(2)
        painter.setPen(pen)

        lpen = QPen(pen)
        lpen.setColor(Qt.black)
        painter.setPen(lpen)

        for y1, y2, lines in ((0, h, bottomedges),
                              (-h, 0, topedges)):
            if lines:
                for start, end, ecolor in lines:
                    lpen = QPen(pen)
                    lpen.setColor(QColor(self.__getColor(ecolor)))
                    lpen.setWidth(2)
                    painter.setPen(lpen)
                    x1 = col2x(start, radius)
                    x2 = col2x(end, radius)
                    painter.drawLine(x1, dot_y + y1, x2, dot_y + y2)

        penradius = 1
        pencolor = Qt.black

        dot_y = (h // 2) - radius // 2

        painter.setBrush(dotColor)
        pen = QPen(pencolor)
        pen.setWidth(penradius)
        painter.setPen(pen)
        painter.drawEllipse(dot_x, dot_y, radius, radius)
        painter.end()
        return QIcon(pix)
    
    def __getParents(self, rev):
        """
        Private method to get the parents of the currently viewed file/directory.
        
        @param rev revision number to get parents for (string)
        @return list of parent revisions (list of integers)
        """
        errMsg = ""
        parents = [-1]
        
        process = QProcess()
        args = []
        args.append("parents")
        if self.commandMode == "incoming":
            if self.bundle:
                args.append("--repository")
                args.append(self.bundle)
            elif self.vcs.bundleFile:
                args.append("--repository")
                args.append(self.vcs.bundleFile)
        args.append("--template")
        args.append("{rev}\n")
        args.append("-r")
        args.append(rev)
        if not self.projectMode:
            args.append(self.filename)
        
        process.setWorkingDirectory(self.repodir)
        process.start('hg', args)
        procStarted = process.waitForStarted()
        if procStarted:
            finished = process.waitForFinished(30000)
            if finished and process.exitCode() == 0:
                output = \
                    str(process.readAllStandardOutput(), 
                        Preferences.getSystem("IOEncoding"), 
                        'replace')
                parents = [int(p) for p in output.strip().splitlines()]
            else:
                if not finished:
                    errMsg = self.trUtf8("The hg process did not finish within 30s.")
        else:
            errMsg = self.trUtf8("Could not start the hg executable.")
        
        if errMsg:
            QMessageBox.critical(self,
                self.trUtf8("Mercurial Error"),
                errMsg)
        
        return parents
    
    def __generateLogItem(self, author, date, message, revision, changedPaths, parents, 
                          branches, tags):
        """
        Private method to generate a log tree entry.
        
        @param author author info (string)
        @param date date info (string)
        @param message text of the log message (list of strings)
        @param revision revision info (string)
        @param changedPaths list of dictionary objects containing
            info about the changed files/directories
        @param parents list of parent revisions (list of integers)
        @param branches list of branches (list of strings)
        @param tags list of tags (string)
        @return reference to the generated item (QTreeWidgetItem)
        """
        msg = []
        for line in message:
            msg.append(line.strip())
        
        rev, node = revision.split(":")
        msgtxt = msg[0]
        if len(msgtxt) > 30:
            msgtxt = "{0}...".format(msgtxt[:30])
        itm = QTreeWidgetItem(self.logTree, [
            "", 
            branches[0], 
            "{0:>7}:{1}".format(rev, node), 
            author, 
            date, 
            msgtxt, 
            ", ".join(tags), 
        ])
        
        itm.setForeground(self.BranchColumn, 
                          QBrush(QColor(self.__branchColor(branches[0]))))
        
        if not self.projectMode:
            parents = self.__getParents(rev)
        if not parents:
            parents = [int(rev) - 1]
        column, color, edges = self.__generateEdges(int(rev), parents)
        
        itm.setData(0, self.__messageRole, message)
        itm.setData(0, self.__changesRole, changedPaths)
        itm.setData(0, self.__edgesRole, edges)
        itm.setData(0, self.__parentsRole, parents)
        
        if self.logTree.topLevelItemCount() > 1:
            topedges = \
                self.logTree.topLevelItem(self.logTree.indexOfTopLevelItem(itm) - 1)\
                .data(0, self.__edgesRole)
        else:
            topedges = None
        
        icon = self.__generateIcon(column, color, edges, topedges, 
                                   QColor(self.__branchColor(branches[0])))
        itm.setIcon(0, icon)
        
        try:
            self.__lastRev = int(revision.split(":")[0])
        except ValueError:
            self.__lastRev = 0
        
        return itm
    
    def __generateFileItem(self, action, path, copyfrom):
        """
        Private method to generate a changed files tree entry.
        
        @param action indicator for the change action ("A", "D" or "M")
        @param path path of the file in the repository (string)
        @param copyfrom path the file was copied from (string)
        @return reference to the generated item (QTreeWidgetItem)
        """
        itm = QTreeWidgetItem(self.filesTree, [
            self.flags[action], 
            path, 
            copyfrom, 
        ])
        
        return itm
    
    def __getLogEntries(self, startRev = None):
        """
        Private method to retrieve log entries from the repository.
        
        @param startRev revision number to start from (integer, string)
        """
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        QApplication.processEvents()
        
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QApplication.processEvents()
        
        self.intercept = False
        self.process.kill()
        
        self.buf = []
        self.cancelled = False
        self.errors.clear()
        
        self.inputGroup.show()
        
        args = []
        args.append(self.commandMode)
        self.vcs.addArguments(args, self.vcs.options['global'])
        self.vcs.addArguments(args, self.vcs.options['log'])
        args.append('--verbose')
        args.append('--limit')
        args.append(str(self.limitSpinBox.value()))
        if self.commandMode in ("incoming", "outgoing"):
            args.append("--newest-first")
        if startRev is not None:
            args.append('--rev')
            args.append('{0}:0'.format(startRev))
        if not self.projectMode and \
           not self.fname == "." and \
           not self.stopCheckBox.isChecked():
            args.append('--follow')
        if self.commandMode == "log":
            args.append('--copies')
        args.append('--style')
        args.append(os.path.join(os.path.dirname(__file__), "styles", "logBrowser.style"))
        if self.commandMode == "incoming":
            if self.bundle:
                args.append(self.bundle)
            else:
                project = e5App().getObject("Project")
                self.vcs.bundleFile = os.path.join(
                    project.getProjectManagementDir(), "hg-bundle.hg")
                args.append('--bundle')
                args.append(self.vcs.bundleFile)
        if not self.projectMode:
            args.append(self.filename)
        
        self.process.setWorkingDirectory(self.repodir)
        
        self.process.start('hg', args)
        procStarted = self.process.waitForStarted()
        if not procStarted:
            self.inputGroup.setEnabled(False)
            QMessageBox.critical(None,
                self.trUtf8('Process Generation Error'),
                self.trUtf8(
                    'The process {0} could not be started. '
                    'Ensure, that it is in the search path.'
                ).format('hg'))
    
    def start(self, fn):
        """
        Public slot to start the hg log command.
        
        @param fn filename to show the log for (string)
        """
        self.errorGroup.hide()
        QApplication.processEvents()
        
        self.filename = fn
        self.dname, self.fname = self.vcs.splitPath(fn)
        
        # find the root of the repo
        self.repodir = self.dname
        while not os.path.isdir(os.path.join(self.repodir, self.vcs.adminDir)):
            self.repodir = os.path.dirname(self.repodir)
            if self.repodir == os.sep:
                return
        
        self.projectMode = (self.fname == "." and self.dname == self.repodir)
        self.stopCheckBox.setDisabled(self.projectMode or self.fname == ".")
        self.activateWindow()
        self.raise_()
        
        self.logTree.clear()
        self.__started = True
        self.__getLogEntries()
    
    def __procFinished(self, exitCode, exitStatus):
        """
        Private slot connected to the finished signal.
        
        @param exitCode exit code of the process (integer)
        @param exitStatus exit status of the process (QProcess.ExitStatus)
        """
        self.__processBuffer()
        self.__finish()
    
    def __finish(self):
        """
        Private slot called when the process finished or the user pressed the button.
        """
        if self.process is not None and \
           self.process.state() != QProcess.NotRunning:
            self.process.terminate()
            QTimer.singleShot(2000, self.process.kill)
            self.process.waitForFinished(3000)
        
        QApplication.restoreOverrideCursor()
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        
        self.inputGroup.setEnabled(False)
        self.inputGroup.hide()
    
    def __processBuffer(self):
        """
        Private method to process the buffered output of the hg log command.
        """
        noEntries = 0
        log = {"message" : []}
        changedPaths = []
        initialText = True
        fileCopies = {}
        for s in self.buf:
            if s != "@@@\n":
                try:
                    key, value = s.split("|", 1)
                except ValueError:
                    key = ""
                    value = s
                if key == "change":
                    initialText = False
                    log["revision"] = value.strip()
                elif key == "user":
                    log["author"] = value.strip()
                elif key == "parents":
                    log["parents"] = \
                        [int(x.split(":", 1)[0]) for x in value.strip().split()]
                elif key == "date":
                    log["date"] = " ".join(value.strip().split()[:2])
                elif key == "description":
                    log["message"].append(value.strip())
                elif key == "file_adds":
                    if value.strip():
                        for f in value.strip().split(", "):
                            if f in fileCopies:
                                changedPaths.append({
                                    "action"   : "A", 
                                    "path"     : f, 
                                    "copyfrom" : fileCopies[f], 
                                })
                            else:
                                changedPaths.append({
                                    "action"   : "A", 
                                    "path"     : f, 
                                    "copyfrom" : "", 
                                })
                elif key == "files_mods":
                    if value.strip():
                        for f in value.strip().split(", "):
                            changedPaths.append({
                                "action"   : "M", 
                                "path"     : f, 
                                "copyfrom" : "", 
                            })
                elif key == "file_dels":
                    if value.strip():
                        for f in value.strip().split(", "):
                            changedPaths.append({
                                "action"   : "D", 
                                "path"     : f, 
                                "copyfrom" : "", 
                            })
                elif key == "file_copies":
                    if value.strip():
                        for entry in value.strip().split(", "):
                            newName, oldName = entry[:-1].split(" (")
                            fileCopies[newName] = oldName
                elif key == "branches":
                    if value.strip():
                        log["branches"] = value.strip().split(", ")
                    else:
                        log["branches"] = ["default"]
                elif key == "tags":
                    log["tags"] = value.strip().split(", ")
                else:
                    if initialText:
                        continue
                    if value.strip():
                        log["message"].append(value.strip())
            else:
                if len(log) > 1:
                    self.__generateLogItem(log["author"], log["date"], 
                        log["message"], log["revision"], changedPaths,
                        log["parents"], log["branches"], log["tags"])
                    dt = QDate.fromString(log["date"], Qt.ISODate)
                    if not self.__maxDate.isValid() and not self.__minDate.isValid():
                        self.__maxDate = dt
                        self.__minDate = dt
                    else:
                        if self.__maxDate < dt:
                            self.__maxDate = dt
                        if self.__minDate > dt:
                            self.__minDate = dt
                    noEntries += 1
                    log = {"message" : []}
                    changedPaths = []
                    fileCopies = {}
        
        self.logTree.doItemsLayout()
        self.__resizeColumnsLog()
        
        if self.__started:
            self.logTree.setCurrentItem(self.logTree.topLevelItem(0))
            self.__started = False
        
        if noEntries < self.limitSpinBox.value() and not self.cancelled:
            self.nextButton.setEnabled(False)
            self.limitSpinBox.setEnabled(False)
        
        self.__filterLogsEnabled = False
        self.fromDate.setMinimumDate(self.__minDate)
        self.fromDate.setMaximumDate(self.__maxDate)
        self.fromDate.setDate(self.__minDate)
        self.toDate.setMinimumDate(self.__minDate)
        self.toDate.setMaximumDate(self.__maxDate)
        self.toDate.setDate(self.__maxDate)
        self.__filterLogsEnabled = True
        self.__filterLogs()
    
    def __readStdout(self):
        """
        Private slot to handle the readyReadStandardOutput signal. 
        
        It reads the output of the process and inserts it into a buffer.
        """
        self.process.setReadChannel(QProcess.StandardOutput)
        
        while self.process.canReadLine():
            line = str(self.process.readLine(), 
                        Preferences.getSystem("IOEncoding"), 
                        'replace')
            self.buf.append(line)
    
    def __readStderr(self):
        """
        Private slot to handle the readyReadStandardError signal.
        
        It reads the error output of the process and inserts it into the
        error pane.
        """
        if self.process is not None:
            self.errorGroup.show()
            s = str(self.process.readAllStandardError(), 
                     Preferences.getSystem("IOEncoding"), 
                     'replace')
            self.errors.insertPlainText(s)
            self.errors.ensureCursorVisible()
    
    def __diffRevisions(self, rev1, rev2):
        """
        Private method to do a diff of two revisions.
        
        @param rev1 first revision number (integer)
        @param rev2 second revision number (integer)
        """
        if self.diff:
            self.diff.close()
            del self.diff
        self.diff = HgDiffDialog(self.vcs)
        self.diff.show()
        self.diff.start(self.filename, [rev1, rev2], self.bundle)
    
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.buttonBox.button(QDialogButtonBox.Close):
            self.close()
        elif button == self.buttonBox.button(QDialogButtonBox.Cancel):
            self.cancelled = True
            self.__finish()
    
    @pyqtSlot(QTreeWidgetItem, QTreeWidgetItem)
    def on_logTree_currentItemChanged(self, current, previous):
        """
        Private slot called, when the current item of the log tree changes.
        
        @param current reference to the new current item (QTreeWidgetItem)
        @param previous reference to the old current item (QTreeWidgetItem)
        """
        self.messageEdit.clear()
        for line in current.data(0, self.__messageRole):
            self.messageEdit.append(line.strip())
        
        self.filesTree.clear()
        changes = current.data(0, self.__changesRole)
        if len(changes) > 0:
            for change in changes:
                self.__generateFileItem(
                    change["action"], change["path"], change["copyfrom"])
            self.__resizeColumnsFiles()
            self.__resortFiles()
        
        parents = current.data(0, self.__parentsRole)
        self.diffP1Button.setEnabled(len(parents) > 0)
        self.diffP2Button.setEnabled(len(parents) > 1)
    
    @pyqtSlot()
    def on_nextButton_clicked(self):
        """
        Private slot to handle the Next button.
        """
        if self.__lastRev > 1:
            self.__getLogEntries(self.__lastRev - 1)
    
    @pyqtSlot()
    def on_diffP1Button_clicked(self):
        """
        Private slot to handle the Diff to Parent 1 button.
        """
        itm = self.logTree.currentItem()
        if itm is None:
            self.diffP1Button.setEnabled(False)
            return
        rev2 = int(itm.text(self.RevisionColumn).split(":")[0])
        
        rev1 = itm.data(0, self.__parentsRole)[0]
        if rev1 < 0:
            self.diffP1Button.setEnabled(False)
            return
        
        self.__diffRevisions(rev1, rev2)
    
    @pyqtSlot()
    def on_diffP2Button_clicked(self):
        """
        Private slot to handle the Diff to Parent 2 button.
        """
        itm = self.logTree.currentItem()
        if itm is None:
            self.diffP2Button.setEnabled(False)
            return
        rev2 = int(itm.text(self.RevisionColumn).split(":")[0])
        
        rev1 = itm.data(0, self.__parentsRole)[1]
        if rev1 < 0:
            self.diffP2Button.setEnabled(False)
            return
        
        self.__diffRevisions(rev1, rev2)
    
    @pyqtSlot(QDate)
    def on_fromDate_dateChanged(self, date):
        """
        Private slot called, when the from date changes.
        
        @param date new date (QDate)
        """
        self.__filterLogs()
    
    @pyqtSlot(QDate)
    def on_toDate_dateChanged(self, date):
        """
        Private slot called, when the from date changes.
        
        @param date new date (QDate)
        """
        self.__filterLogs()
    
    @pyqtSlot(str)
    def on_fieldCombo_activated(self, txt):
        """
        Private slot called, when a new filter field is selected.
        
        @param txt text of the selected field (string)
        """
        self.__filterLogs()
    
    @pyqtSlot(str)
    def on_rxEdit_textChanged(self, txt):
        """
        Private slot called, when a filter expression is entered.
        
        @param txt filter expression (string)
        """
        self.__filterLogs()
    
    def __filterLogs(self):
        """
        Private method to filter the log entries.
        """
        if self.__filterLogsEnabled:
            from_ = self.fromDate.date().toString("yyyy-MM-dd")
            to_ = self.toDate.date().addDays(1).toString("yyyy-MM-dd")
            txt = self.fieldCombo.currentText()
            if txt == self.trUtf8("Author"):
                fieldIndex = self.AuthorColumn
                searchRx = QRegExp(self.rxEdit.text(), Qt.CaseInsensitive)
            elif txt == self.trUtf8("Revision"):
                fieldIndex = self.RevisionColumn
                txt = self.rxEdit.text()
                if txt.startswith("^"):
                    searchRx = QRegExp("^\s*%s" % txt[1:], Qt.CaseInsensitive)
                else:
                    searchRx = QRegExp(txt, Qt.CaseInsensitive)
            else:
                fieldIndex = self.MessageColumn
                searchRx = QRegExp(self.rxEdit.text(), Qt.CaseInsensitive)
            
            currentItem = self.logTree.currentItem()
            for topIndex in range(self.logTree.topLevelItemCount()):
                topItem = self.logTree.topLevelItem(topIndex)
                if topItem.text(self.DateColumn) <= to_ and \
                   topItem.text(self.DateColumn) >= from_ and \
                   searchRx.indexIn(topItem.text(fieldIndex)) > -1:
                    topItem.setHidden(False)
                    if topItem is currentItem:
                        self.on_logTree_currentItemChanged(topItem, None)
                else:
                    topItem.setHidden(True)
                    if topItem is currentItem:
                        self.messageEdit.clear()
                        self.filesTree.clear()
    
    @pyqtSlot()
    def on_clearRxEditButton_clicked(self):
        """
        Private slot called by a click of the clear RX edit button.
        """
        self.rxEdit.clear()
    
    @pyqtSlot(bool)
    def on_stopCheckBox_clicked(self, checked):
        """
        Private slot called, when the stop on copy/move checkbox is clicked
        """
        self.vcs.getPlugin().setPreferences("StopLogOnCopy", 
                                            self.stopCheckBox.isChecked())
        self.nextButton.setEnabled(True)
        self.limitSpinBox.setEnabled(True)
    
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
        Private slot to send the input to the merurial process.
        """
        input = self.input.text()
        input += os.linesep
        
        if self.passwordCheckBox.isChecked():
            self.errors.insertPlainText(os.linesep)
            self.errors.ensureCursorVisible()
        else:
            self.errors.insertPlainText(input)
            self.errors.ensureCursorVisible()
        self.errorGroup.show()
        
        self.process.write(input)
        
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
        QWidget.keyPressEvent(self, evt)
