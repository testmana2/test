# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to compare two files and show the result side by side.
"""

import re
from difflib import _mdiff, IS_CHARACTER_JUNK

from PyQt4.QtCore import QTimer, QEvent, pyqtSlot
from PyQt4.QtGui import QWidget, QColor, QFontMetrics, QBrush, QApplication, \
    QTextCursor, QDialogButtonBox, QMainWindow

from E5Gui.E5Completers import E5FileCompleter
from E5Gui import E5MessageBox, E5FileDialog

import UI.PixmapCache

from .Ui_CompareDialog import Ui_CompareDialog

import Utilities


def sbsdiff(a, b, linenumberwidth=4):
    """
    Compare two sequences of lines; generate the delta for display side by side.
    
    @param a first sequence of lines (list of strings)
    @param b second sequence of lines (list of strings)
    @param linenumberwidth width (in characters) of the linenumbers (integer)
    @return a generator yielding tuples of differences. The tuple is composed
        of strings as follows.
        <ul>
            <li>opcode -- one of e, d, i, r for equal, delete, insert, replace</li>
            <li>lineno a -- linenumber of sequence a</li>
            <li>line a -- line of sequence a</li>
            <li>lineno b -- linenumber of sequence b</li>
            <li>line b -- line of sequence b</li>
        </ul>
    """
    def removeMarkers(line):
        """
        Internal function to remove all diff markers.
        
        @param line line to work on (string)
        @return line without diff markers (string)
        """
        return line\
            .replace('\0+', "")\
            .replace('\0-', "")\
            .replace('\0^', "")\
            .replace('\1', "")

    linenumberformat = "{{0:{0:d}d}}".format(linenumberwidth)
    emptylineno = ' ' * linenumberwidth
    
    for (ln1, l1), (ln2, l2), flag in _mdiff(a, b, None, None, IS_CHARACTER_JUNK):
        if not flag:
            yield ('e', linenumberformat.format(ln1), l1,
                        linenumberformat.format(ln2), l2)
            continue
        if ln2 == "" and l2 == "\n":
            yield ('d', linenumberformat.format(ln1), removeMarkers(l1),
                        emptylineno, '\n')
            continue
        if ln1 == "" and l1 == "\n":
            yield ('i', emptylineno, '\n',
                        linenumberformat.format(ln2), removeMarkers(l2))
            continue
        yield ('r', linenumberformat.format(ln1), l1,
                    linenumberformat.format(ln2), l2)


class CompareDialog(QWidget, Ui_CompareDialog):
    """
    Class implementing a dialog to compare two files and show the result side by side.
    """
    def __init__(self, files=[], parent=None):
        """
        Constructor
        
        @param files list of files to compare and their label
            (list of two tuples of two strings)
        @param parent parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        self.file1Completer = E5FileCompleter(self.file1Edit)
        self.file2Completer = E5FileCompleter(self.file2Edit)
        
        self.diffButton = \
            self.buttonBox.addButton(self.trUtf8("Compare"), QDialogButtonBox.ActionRole)
        self.diffButton.setToolTip(
            self.trUtf8("Press to perform the comparison of the two files"))
        self.diffButton.setEnabled(False)
        self.diffButton.setDefault(True)
        
        self.firstButton.setIcon(UI.PixmapCache.getIcon("2uparrow.png"))
        self.upButton.setIcon(UI.PixmapCache.getIcon("1uparrow.png"))
        self.downButton.setIcon(UI.PixmapCache.getIcon("1downarrow.png"))
        self.lastButton.setIcon(UI.PixmapCache.getIcon("2downarrow.png"))
        
        self.totalLabel.setText(self.trUtf8('Total: {0}').format(0))
        self.changedLabel.setText(self.trUtf8('Changed: {0}').format(0))
        self.addedLabel.setText(self.trUtf8('Added: {0}').format(0))
        self.deletedLabel.setText(self.trUtf8('Deleted: {0}').format(0))
        
        self.updateInterval = 20    # update every 20 lines
        
        self.vsb1 = self.contents_1.verticalScrollBar()
        self.hsb1 = self.contents_1.horizontalScrollBar()
        self.vsb2 = self.contents_2.verticalScrollBar()
        self.hsb2 = self.contents_2.horizontalScrollBar()
        
        self.on_synchronizeCheckBox_toggled(True)
        
        if Utilities.isWindowsPlatform():
            self.contents_1.setFontFamily("Lucida Console")
            self.contents_2.setFontFamily("Lucida Console")
        else:
            self.contents_1.setFontFamily("Monospace")
            self.contents_2.setFontFamily("Monospace")
        self.fontHeight = QFontMetrics(self.contents_1.currentFont()).height()
        
        self.cNormalFormat = self.contents_1.currentCharFormat()
        self.cInsertedFormat = self.contents_1.currentCharFormat()
        self.cInsertedFormat.setBackground(QBrush(QColor(190, 237, 190)))
        self.cDeletedFormat = self.contents_1.currentCharFormat()
        self.cDeletedFormat.setBackground(QBrush(QColor(237, 190, 190)))
        self.cReplacedFormat = self.contents_1.currentCharFormat()
        self.cReplacedFormat.setBackground(QBrush(QColor(190, 190, 237)))
        
        # connect some of our widgets explicitly
        self.file1Edit.textChanged.connect(self.__fileChanged)
        self.file2Edit.textChanged.connect(self.__fileChanged)
        self.synchronizeCheckBox.toggled[bool].connect(
            self.on_synchronizeCheckBox_toggled)
        self.vsb1.valueChanged.connect(self.__scrollBarMoved)
        self.vsb1.valueChanged.connect(self.vsb2.setValue)
        self.vsb2.valueChanged.connect(self.vsb1.setValue)
        
        self.diffParas = []
        self.currentDiffPos = -1
        
        self.markerPattern = "\0\+|\0\^|\0\-"
        
        if len(files) == 2:
            self.filesGroup.hide()
            self.file1Edit.setText(files[0][1])
            self.file2Edit.setText(files[1][1])
            self.file1Label.setText(files[0][0])
            self.file2Label.setText(files[1][0])
            self.diffButton.hide()
            QTimer.singleShot(0, self.on_diffButton_clicked)
        else:
            self.file1Label.hide()
            self.file2Label.hide()

    def show(self, filename=None):
        """
        Public slot to show the dialog.
        
        @param filename name of a file to use as the first file (string)
        """
        if filename:
            self.file1Edit.setText(filename)
        super().show()
        
    def __appendText(self, pane, linenumber, line, format, interLine=False):
        """
        Private method to append text to the end of the contents pane.
        
        @param pane text edit widget to append text to (QTextedit)
        @param linenumber number of line to insert (string)
        @param line text to insert (string)
        @param format text format to be used (QTextCharFormat)
        @param interLine flag indicating interline changes (boolean)
        """
        tc = pane.textCursor()
        tc.movePosition(QTextCursor.End)
        pane.setTextCursor(tc)
        pane.setCurrentCharFormat(format)
        if interLine:
            pane.insertPlainText("{0} ".format(linenumber))
            for txt in re.split(self.markerPattern, line):
                if txt:
                    if txt.count('\1'):
                        txt1, txt = txt.split('\1', 1)
                        tc = pane.textCursor()
                        tc.movePosition(QTextCursor.End)
                        pane.setTextCursor(tc)
                        pane.setCurrentCharFormat(format)
                        pane.insertPlainText(txt1)
                    tc = pane.textCursor()
                    tc.movePosition(QTextCursor.End)
                    pane.setTextCursor(tc)
                    pane.setCurrentCharFormat(self.cNormalFormat)
                    pane.insertPlainText(txt)
        else:
            pane.insertPlainText("{0} {1}".format(linenumber, line))

    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.diffButton:
            self.on_diffButton_clicked()
        
    @pyqtSlot()
    def on_diffButton_clicked(self):
        """
        Private slot to handle the Compare button press.
        """
        filename1 = Utilities.toNativeSeparators(self.file1Edit.text())
        try:
            f1 = open(filename1, "r", encoding="utf-8")
            lines1 = f1.readlines()
            f1.close()
        except IOError:
            E5MessageBox.critical(self,
                self.trUtf8("Compare Files"),
                self.trUtf8("""<p>The file <b>{0}</b> could not be read.</p>""")
                    .format(filename1))
            return

        filename2 = Utilities.toNativeSeparators(self.file2Edit.text())
        try:
            f2 = open(filename2, "r", encoding="utf-8")
            lines2 = f2.readlines()
            f2.close()
        except IOError:
            E5MessageBox.critical(self,
                self.trUtf8("Compare Files"),
                self.trUtf8("""<p>The file <b>{0}</b> could not be read.</p>""")
                    .format(filename2))
            return
        
        self.contents_1.clear()
        self.contents_2.clear()
        
        # counters for changes
        added = 0
        deleted = 0
        changed = 0
        
        paras = 1
        self.diffParas = []
        self.currentDiffPos = -1
        oldOpcode = ''
        for opcode, ln1, l1, ln2, l2 in sbsdiff(lines1, lines2):
            if opcode in 'idr':
                if oldOpcode != opcode:
                    oldOpcode = opcode
                    self.diffParas.append(paras)
                    # update counters
                    if opcode == 'i':
                        added += 1
                    elif opcode == 'd':
                        deleted += 1
                    elif opcode == 'r':
                        changed += 1
                if opcode == 'i':
                    format1 = self.cNormalFormat
                    format2 = self.cInsertedFormat
                elif opcode == 'd':
                    format1 = self.cDeletedFormat
                    format2 = self.cNormalFormat
                elif opcode == 'r':
                    if ln1.strip():
                        format1 = self.cReplacedFormat
                    else:
                        format1 = self.cNormalFormat
                    if ln2.strip():
                        format2 = self.cReplacedFormat
                    else:
                        format2 = self.cNormalFormat
            else:
                oldOpcode = ''
                format1 = self.cNormalFormat
                format2 = self.cNormalFormat
            self.__appendText(self.contents_1, ln1, l1, format1, opcode == 'r')
            self.__appendText(self.contents_2, ln2, l2, format2, opcode == 'r')
            paras += 1
            if not (paras % self.updateInterval):
                QApplication.processEvents()
        
        self.vsb1.setValue(0)
        self.vsb2.setValue(0)
        self.firstButton.setEnabled(False)
        self.upButton.setEnabled(False)
        self.downButton.setEnabled(len(self.diffParas) > 0)
        self.lastButton.setEnabled(len(self.diffParas) > 0)
        
        self.totalLabel.setText(self.trUtf8('Total: {0}')\
                                    .format(added + deleted + changed))
        self.changedLabel.setText(self.trUtf8('Changed: {0}').format(changed))
        self.addedLabel.setText(self.trUtf8('Added: {0}').format(added))
        self.deletedLabel.setText(self.trUtf8('Deleted: {0}').format(deleted))

    def __moveTextToCurrentDiffPos(self):
        """
        Private slot to move the text display to the current diff position.
        """
        value = (self.diffParas[self.currentDiffPos] - 1) * self.fontHeight
        self.vsb1.setValue(value)
        self.vsb2.setValue(value)
    
    def __scrollBarMoved(self, value):
        """
        Private slot to enable the buttons and set the current diff position
        depending on scrollbar position.
        
        @param value scrollbar position (integer)
        """
        tPos = value / self.fontHeight + 1
        bPos = (value + self.vsb1.pageStep()) / self.fontHeight + 1
        
        self.currentDiffPos = -1
        
        if self.diffParas:
            self.firstButton.setEnabled(tPos > self.diffParas[0])
            self.upButton.setEnabled(tPos > self.diffParas[0])
            self.downButton.setEnabled(bPos < self.diffParas[-1])
            self.lastButton.setEnabled(bPos < self.diffParas[-1])
            
            if tPos >= self.diffParas[0]:
                for diffPos in self.diffParas:
                    self.currentDiffPos += 1
                    if tPos <= diffPos:
                        break
    
    @pyqtSlot()
    def on_upButton_clicked(self):
        """
        Private slot to go to the previous difference.
        """
        self.currentDiffPos -= 1
        self.__moveTextToCurrentDiffPos()
    
    @pyqtSlot()
    def on_downButton_clicked(self):
        """
        Private slot to go to the next difference.
        """
        self.currentDiffPos += 1
        self.__moveTextToCurrentDiffPos()
    
    @pyqtSlot()
    def on_firstButton_clicked(self):
        """
        Private slot to go to the first difference.
        """
        self.currentDiffPos = 0
        self.__moveTextToCurrentDiffPos()
    
    @pyqtSlot()
    def on_lastButton_clicked(self):
        """
        Private slot to go to the last difference.
        """
        self.currentDiffPos = len(self.diffParas) - 1
        self.__moveTextToCurrentDiffPos()
    
    def __fileChanged(self):
        """
        Private slot to enable/disable the Compare button.
        """
        if not self.file1Edit.text() or \
           not self.file2Edit.text():
            self.diffButton.setEnabled(False)
        else:
            self.diffButton.setEnabled(True)

    def __selectFile(self, lineEdit):
        """
        Private slot to display a file selection dialog.
        
        @param lineEdit field for the display of the selected filename
                (QLineEdit)
        """
        filename = E5FileDialog.getOpenFileName(
            self,
            self.trUtf8("Select file to compare"),
            lineEdit.text(),
            "")
            
        if filename:
            lineEdit.setText(Utilities.toNativeSeparators(filename))

    @pyqtSlot()
    def on_file1Button_clicked(self):
        """
        Private slot to handle the file 1 file selection button press.
        """
        self.__selectFile(self.file1Edit)

    @pyqtSlot()
    def on_file2Button_clicked(self):
        """
        Private slot to handle the file 2 file selection button press.
        """
        self.__selectFile(self.file2Edit)

    @pyqtSlot(bool)
    def on_synchronizeCheckBox_toggled(self, sync):
        """
        Private slot to connect or disconnect the scrollbars of the displays.
        
        @param sync flag indicating synchronisation status (boolean)
        """
        if sync:
            self.hsb2.setValue(self.hsb1.value())
            self.hsb1.valueChanged.connect(self.hsb2.setValue)
            self.hsb2.valueChanged.connect(self.hsb1.setValue)
        else:
            self.hsb1.valueChanged.disconnect(self.hsb2.setValue)
            self.hsb2.valueChanged.disconnect(self.hsb1.setValue)


class CompareWindow(QMainWindow):
    """
    Main window class for the standalone dialog.
    """
    def __init__(self, files=[], parent=None):
        """
        Constructor
        
        @param files list of files to compare and their label
            (list of two tuples of two strings)
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.cw = CompareDialog(files, self)
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
