# -*- coding: utf-8 -*-

# Copyright (c) 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the QRegularExpression wizard dialog.
"""

import os
import re

from PyQt4.QtCore import QFileInfo, pyqtSlot, qVersion
try:
    from PyQt5.QtCore import QRegularExpression
    AVAILABLE = True
except ImportError:
    AVAILABLE = False
from PyQt4.QtGui import QWidget, QDialog, QInputDialog, QApplication, QClipboard, \
    QTextCursor, QDialogButtonBox, QVBoxLayout, QTableWidgetItem

from E5Gui import E5MessageBox, E5FileDialog
from E5Gui.E5MainWindow import E5MainWindow

from .Ui_QRegularExpressionWizardDialog import Ui_QRegularExpressionWizardDialog

import UI.PixmapCache

import Utilities
import Preferences


class QRegularExpressionWizardWidget(QWidget, Ui_QRegularExpressionWizardDialog):
    """
    Class implementing the QRegularExpression wizard dialog.
    """
    def __init__(self, parent=None, fromEric=True):
        """
        Constructor
        
        @param parent parent widget (QWidget)
        @param fromEric flag indicating a call from within eric5
        """
        super().__init__(parent)
        self.setupUi(self)
        
        # initialize icons of the tool buttons
        self.commentButton.setIcon(UI.PixmapCache.getIcon("comment.png"))
        self.charButton.setIcon(UI.PixmapCache.getIcon("characters.png"))
        self.anycharButton.setIcon(UI.PixmapCache.getIcon("anychar.png"))
        self.repeatButton.setIcon(UI.PixmapCache.getIcon("repeat.png"))
        self.nonGroupButton.setIcon(UI.PixmapCache.getIcon("nongroup.png"))
        self.atomicGroupButton.setIcon(UI.PixmapCache.getIcon("atomicgroup.png"))
        self.groupButton.setIcon(UI.PixmapCache.getIcon("group.png"))
        self.namedGroupButton.setIcon(UI.PixmapCache.getIcon("namedgroup.png"))
        self.namedReferenceButton.setIcon(UI.PixmapCache.getIcon("namedreference.png"))
        self.altnButton.setIcon(UI.PixmapCache.getIcon("altn.png"))
        self.beglineButton.setIcon(UI.PixmapCache.getIcon("begline.png"))
        self.endlineButton.setIcon(UI.PixmapCache.getIcon("endline.png"))
        self.wordboundButton.setIcon(UI.PixmapCache.getIcon("wordboundary.png"))
        self.nonwordboundButton.setIcon(UI.PixmapCache.getIcon("nonwordboundary.png"))
        self.poslookaheadButton.setIcon(UI.PixmapCache.getIcon("poslookahead.png"))
        self.neglookaheadButton.setIcon(UI.PixmapCache.getIcon("neglookahead.png"))
        self.poslookbehindButton.setIcon(UI.PixmapCache.getIcon("poslookbehind.png"))
        self.neglookbehindButton.setIcon(UI.PixmapCache.getIcon("neglookbehind.png"))
        self.undoButton.setIcon(UI.PixmapCache.getIcon("editUndo.png"))
        self.redoButton.setIcon(UI.PixmapCache.getIcon("editRedo.png"))
        
        self.namedGroups = re.compile(r"""\(?P<([^>]+)>""").findall
        
        self.saveButton = \
            self.buttonBox.addButton(self.trUtf8("Save"), QDialogButtonBox.ActionRole)
        self.saveButton.setToolTip(self.trUtf8("Save the regular expression to a file"))
        self.loadButton = \
            self.buttonBox.addButton(self.trUtf8("Load"), QDialogButtonBox.ActionRole)
        self.loadButton.setToolTip(self.trUtf8("Load a regular expression from a file"))
        if qVersion() >= "5.0.0" and AVAILABLE:
            self.validateButton = self.buttonBox.addButton(
                self.trUtf8("Validate"), QDialogButtonBox.ActionRole)
            self.validateButton.setToolTip(self.trUtf8("Validate the regular expression"))
            self.executeButton = self.buttonBox.addButton(
                self.trUtf8("Execute"), QDialogButtonBox.ActionRole)
            self.executeButton.setToolTip(self.trUtf8("Execute the regular expression"))
            self.nextButton = self.buttonBox.addButton(
                self.trUtf8("Next match"), QDialogButtonBox.ActionRole)
            self.nextButton.setToolTip(
                self.trUtf8("Show the next match of the regular expression"))
            self.nextButton.setEnabled(False)
        else:
            self.validateButton = None
            self.executeButton = None
            self.nextButton = None
        
        if fromEric:
            self.buttonBox.button(QDialogButtonBox.Close).hide()
            self.copyButton = None
        else:
            self.copyButton = \
                self.buttonBox.addButton(self.trUtf8("Copy"), QDialogButtonBox.ActionRole)
            self.copyButton.setToolTip(
                self.trUtf8("Copy the regular expression to the clipboard"))
            self.buttonBox.button(QDialogButtonBox.Ok).hide()
            self.buttonBox.button(QDialogButtonBox.Cancel).hide()
            self.variableLabel.hide()
            self.variableLineEdit.hide()
            self.variableLine.hide()
            self.importCheckBox.hide()
            self.regexpTextEdit.setFocus()

    def __insertString(self, s, steps=0):
        """
        Private method to insert a string into line edit and move cursor.
        
        @param s string to be inserted into the regexp line edit
            (string)
        @param steps number of characters to move the cursor (integer).
            Negative steps moves cursor back, positives forward.
        """
        self.regexpTextEdit.insertPlainText(s)
        tc = self.regexpTextEdit.textCursor()
        if steps != 0:
            if steps < 0:
                act = QTextCursor.Left
                steps = abs(steps)
            else:
                act = QTextCursor.Right
            for i in range(steps):
                tc.movePosition(act)
        self.regexpTextEdit.setTextCursor(tc)
    
    @pyqtSlot()
    def on_commentButton_clicked(self):
        """
        Private slot to handle the comment toolbutton.
        """
        self.__insertString("(?#)", -1)
    
    @pyqtSlot()
    def on_charButton_clicked(self):
        """
        Private slot to handle the characters toolbutton.
        """
        from .QRegularExpressionWizardCharactersDialog import \
            QRegularExpressionWizardCharactersDialog
        dlg = QRegularExpressionWizardCharactersDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            self.__insertString(dlg.getCharacters())
    
    @pyqtSlot()
    def on_anycharButton_clicked(self):
        """
        Private slot to handle the any character toolbutton.
        """
        self.__insertString(".")
    
    @pyqtSlot()
    def on_repeatButton_clicked(self):
        """
        Private slot to handle the repeat toolbutton.
        """
        from .QRegularExpressionWizardRepeatDialog import \
            QRegularExpressionWizardRepeatDialog
        dlg = QRegularExpressionWizardRepeatDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            self.__insertString(dlg.getRepeat())
    
    @pyqtSlot()
    def on_nonGroupButton_clicked(self):
        """
        Private slot to handle the non group toolbutton.
        """
        self.__insertString("(?:)", -1)
    
    @pyqtSlot()
    def on_atomicGroupButton_clicked(self):
        """
        Private slot to handle the atomic non group toolbutton.
        """
        self.__insertString("(?>)", -1)
    
    @pyqtSlot()
    def on_groupButton_clicked(self):
        """
        Private slot to handle the group toolbutton.
        """
        self.__insertString("()", -1)
    
    @pyqtSlot()
    def on_namedGroupButton_clicked(self):
        """
        Private slot to handle the named group toolbutton.
        """
        self.__insertString("(?P<>)", -2)
    
    @pyqtSlot()
    def on_namedReferenceButton_clicked(self):
        """
        Private slot to handle the named reference toolbutton.
        """
        # determine cursor position as length into text
        length = self.regexpTextEdit.textCursor().position()
        
        # only present group names that occur before the current cursor position
        regex = self.regexpTextEdit.toPlainText()[:length]
        names = self.namedGroups(regex)
        if not names:
            E5MessageBox.information(self,
                self.trUtf8("Named reference"),
                self.trUtf8("""No named groups have been defined yet."""))
            return
        
        groupName, ok = QInputDialog.getItem(
            self,
            self.trUtf8("Named reference"),
            self.trUtf8("Select group name:"),
            names,
            0, True)
        if ok and groupName:
            self.__insertString("(?P={0})".format(groupName))
    
    @pyqtSlot()
    def on_altnButton_clicked(self):
        """
        Private slot to handle the alternatives toolbutton.
        """
        self.__insertString("(|)", -2)
    
    @pyqtSlot()
    def on_beglineButton_clicked(self):
        """
        Private slot to handle the begin line toolbutton.
        """
        self.__insertString("^")
    
    @pyqtSlot()
    def on_endlineButton_clicked(self):
        """
        Private slot to handle the end line toolbutton.
        """
        self.__insertString("$")
    
    @pyqtSlot()
    def on_wordboundButton_clicked(self):
        """
        Private slot to handle the word boundary toolbutton.
        """
        self.__insertString("\\b")
    
    @pyqtSlot()
    def on_nonwordboundButton_clicked(self):
        """
        Private slot to handle the non word boundary toolbutton.
        """
        self.__insertString("\\B")
    
    @pyqtSlot()
    def on_poslookaheadButton_clicked(self):
        """
        Private slot to handle the positive lookahead toolbutton.
        """
        self.__insertString("(?=)", -1)
    
    @pyqtSlot()
    def on_neglookaheadButton_clicked(self):
        """
        Private slot to handle the negative lookahead toolbutton.
        """
        self.__insertString("(?!)", -1)
    
    @pyqtSlot()
    def on_poslookbehindButton_clicked(self):
        """
        Private slot to handle the positive lookbehind toolbutton.
        """
        self.__insertString("(?<=)", -1)
    
    @pyqtSlot()
    def on_neglookbehindButton_clicked(self):
        """
        Private slot to handle the negative lookbehind toolbutton.
        """
        self.__insertString("(?<!)", -1)
    
    @pyqtSlot()
    def on_undoButton_clicked(self):
        """
        Private slot to handle the undo action.
        """
        self.regexpTextEdit.document().undo()
    
    @pyqtSlot()
    def on_redoButton_clicked(self):
        """
        Private slot to handle the redo action.
        """
        self.regexpTextEdit.document().redo()
    
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.validateButton:
            self.on_validateButton_clicked()
        elif button == self.executeButton:
            self.on_executeButton_clicked()
        elif button == self.saveButton:
            self.on_saveButton_clicked()
        elif button == self.loadButton:
            self.on_loadButton_clicked()
        elif button == self.nextButton:
            self.on_nextButton_clicked()
        elif self.copyButton and button == self.copyButton:
            self.on_copyButton_clicked()
    
    @pyqtSlot()
    def on_saveButton_clicked(self):
        """
        Private slot to save the QRegularExpression to a file.
        """
        fname, selectedFilter = E5FileDialog.getSaveFileNameAndFilter(
            self,
            self.trUtf8("Save regular expression"),
            "",
            self.trUtf8("RegExp Files (*.rx);;All Files (*)"), 
            None,
            E5FileDialog.Options(E5FileDialog.DontConfirmOverwrite))
        if fname:
            ext = QFileInfo(fname).suffix()
            if not ext:
                ex = selectedFilter.split("(*")[1].split(")")[0]
                if ex:
                    fname += ex
            if QFileInfo(fname).exists():
                res = E5MessageBox.yesNo(self,
                    self.trUtf8("Save regular expression"),
                    self.trUtf8("<p>The file <b>{0}</b> already exists."
                            " Overwrite it?</p>").format(fname),
                    icon=E5MessageBox.Warning)
                if not res:
                    return
            
            try:
                f = open(Utilities.toNativeSeparators(fname), "w", encoding="utf-8")
                f.write(self.regexpTextEdit.toPlainText())
                f.close()
            except IOError as err:
                E5MessageBox.information(self,
                    self.trUtf8("Save regular expression"),
                    self.trUtf8("""<p>The regular expression could not be saved.</p>"""
                                """<p>Reason: {0}</p>""").format(str(err)))
    
    @pyqtSlot()
    def on_loadButton_clicked(self):
        """
        Private slot to load a QRegularExpression from a file.
        """
        fname = E5FileDialog.getOpenFileName(
            self,
            self.trUtf8("Load regular expression"),
            "",
            self.trUtf8("RegExp Files (*.rx);;All Files (*)"))
        if fname:
            try:
                f = open(Utilities.toNativeSeparators(fname), "r", encoding="utf-8")
                regexp = f.read()
                f.close()
                self.regexpTextEdit.setPlainText(regexp)
            except IOError as err:
                E5MessageBox.information(self,
                    self.trUtf8("Save regular expression"),
                    self.trUtf8("""<p>The regular expression could not be saved.</p>"""
                                """<p>Reason: {0}</p>""").format(str(err)))

    @pyqtSlot()
    def on_copyButton_clicked(self):
        """
        Private slot to copy the QRegularExpression string into the clipboard.
        
        This slot is only available, if not called from within eric5.
        """
        escaped = self.regexpTextEdit.toPlainText()
        if escaped:
            escaped = escaped.replace("\\", "\\\\")
            cb = QApplication.clipboard()
            cb.setText(escaped, QClipboard.Clipboard)
            if cb.supportsSelection():
                cb.setText(escaped, QClipboard.Selection)

    @pyqtSlot()
    def on_validateButton_clicked(self):
        """
        Private slot to validate the entered QRegularExpression.
        """
        if qVersion() < "5.0.0" or not AVAILABLE:
            # only available for Qt5
            return
        
        regex = self.regexpTextEdit.toPlainText()
        if regex:
            options = QRegularExpression.NoPatternOption
            if self.caseInsensitiveCheckBox.isChecked():
                options |= QRegularExpression.CaseInsensitiveOption
            if self.multilineCheckBox.isChecked():
                options |= QRegularExpression.MultilineOption
            if self.dotallCheckBox.isChecked():
                options |= QRegularExpression.DotMatchesEverythingOption
            if self.extendedCheckBox.isChecked():
                options |= QRegularExpression.ExtendedPatternSyntaxOption
            if self.greedinessCheckBox.isChecked():
                options |= QRegularExpression.InvertedGreedinessOption
            if self.unicodeCheckBox.isChecked():
                options |= QRegularExpression.UseUnicodePropertiesOption
            if self.captureCheckBox.isChecked():
                options |= QRegularExpression.DontCaptureOption
            
            re = QRegularExpression(regex, options)
            if re.isValid():
                E5MessageBox.information(self,
                    self.trUtf8("Validation"),
                    self.trUtf8("""The regular expression is valid."""))
            else:
                E5MessageBox.critical(self,
                    self.trUtf8("Error"),
                    self.trUtf8("""Invalid regular expression: {0}""")
                        .format(re.errorString()))
                # move cursor to error offset
                offset = re.errorPatternOffset()
                tc = self.regexpTextEdit.textCursor()
                tc.setPosition(offset)
                self.regexpTextEdit.setTextCursor(tc)
                return
        else:
            E5MessageBox.critical(self,
                self.trUtf8("Error"),
                self.trUtf8("""A regular expression must be given."""))

    @pyqtSlot()
    def on_executeButton_clicked(self, startpos=0):
        """
        Private slot to execute the entered QRegularExpression on the test text.
        
        This slot will execute the entered QRegularExpression on the entered test
        data and will display the result in the table part of the dialog.
        
        @param startpos starting position for the QRegularExpression matching
        """
        if qVersion() < "5.0.0" or not AVAILABLE:
            # only available for Qt5
            return
        
        regex = self.regexpTextEdit.toPlainText()
        text = self.textTextEdit.toPlainText()
        if regex and text:
            options = QRegularExpression.NoPatternOption
            if self.caseInsensitiveCheckBox.isChecked():
                options |= QRegularExpression.CaseInsensitiveOption
            if self.multilineCheckBox.isChecked():
                options |= QRegularExpression.MultilineOption
            if self.dotallCheckBox.isChecked():
                options |= QRegularExpression.DotMatchesEverythingOption
            if self.extendedCheckBox.isChecked():
                options |= QRegularExpression.ExtendedPatternSyntaxOption
            if self.greedinessCheckBox.isChecked():
                options |= QRegularExpression.InvertedGreedinessOption
            if self.unicodeCheckBox.isChecked():
                options |= QRegularExpression.UseUnicodePropertiesOption
            if self.captureCheckBox.isChecked():
                options |= QRegularExpression.DontCaptureOption
            
            re = QRegularExpression(regex, options)
            if not re.isValid():
                E5MessageBox.critical(self,
                    self.trUtf8("Error"),
                    self.trUtf8("""Invalid regular expression: {0}""")
                        .format(re.errorString()))
                # move cursor to error offset
                offset = re.errorPatternOffset()
                tc = self.regexpTextEdit.textCursor()
                tc.setPosition(offset)
                self.regexpTextEdit.setTextCursor(tc)
                return
            
            match = re.match(text, startpos)
            if match.hasMatch():
                captures = match.lastCapturedIndex()
            else:
                captures = 0
            row = 0
            OFFSET = 5
            
            self.resultTable.setColumnCount(0)
            self.resultTable.setColumnCount(3)
            self.resultTable.setRowCount(0)
            self.resultTable.setRowCount(OFFSET)
            self.resultTable.setItem(row, 0, QTableWidgetItem(self.trUtf8("Regexp")))
            self.resultTable.setItem(row, 1, QTableWidgetItem(regex))
            
            if match.hasMatch():
                # index 0 is the complete match
                offset = match.capturedStart(0)
                self.lastMatchEnd = match.capturedEnd(0)
                self.nextButton.setEnabled(True)
                row += 1
                self.resultTable.setItem(row, 0,
                    QTableWidgetItem(self.trUtf8("Offset")))
                self.resultTable.setItem(row, 1,
                    QTableWidgetItem("{0:d}".format(match.capturedStart(0))))
                
                row += 1
                self.resultTable.setItem(row, 0,
                    QTableWidgetItem(self.trUtf8("Captures")))
                self.resultTable.setItem(row, 1,
                    QTableWidgetItem("{0:d}".format(captures)))
                row += 1
                self.resultTable.setItem(row, 1,
                    QTableWidgetItem(self.trUtf8("Text")))
                self.resultTable.setItem(row, 2,
                    QTableWidgetItem(self.trUtf8("Characters")))
                
                row += 1
                self.resultTable.setItem(row, 0,
                    QTableWidgetItem(self.trUtf8("Match")))
                self.resultTable.setItem(row, 1,
                    QTableWidgetItem(match.captured(0)))
                self.resultTable.setItem(row, 2,
                    QTableWidgetItem("{0:d}".format(match.capturedLength(0))))
                
                for i in range(1, captures + 1):
                    if match.captured(i):
                        row += 1
                        self.resultTable.insertRow(row)
                        self.resultTable.setItem(row, 0,
                            QTableWidgetItem(self.trUtf8("Capture #{0}").format(i)))
                        self.resultTable.setItem(row, 1,
                            QTableWidgetItem(match.captured(i)))
                        self.resultTable.setItem(row, 2,
                            QTableWidgetItem("{0:d}".format(match.capturedLength(i))))
                
                # highlight the matched text
                tc = self.textTextEdit.textCursor()
                tc.setPosition(offset)
                tc.setPosition(self.lastMatchEnd, QTextCursor.KeepAnchor)
                self.textTextEdit.setTextCursor(tc)
            else:
                self.nextButton.setEnabled(False)
                self.resultTable.setRowCount(2)
                row += 1
                if startpos > 0:
                    self.resultTable.setItem(row, 0,
                        QTableWidgetItem(self.trUtf8("No more matches")))
                else:
                    self.resultTable.setItem(row, 0,
                        QTableWidgetItem(self.trUtf8("No matches")))
                
                # remove the highlight
                tc = self.textTextEdit.textCursor()
                tc.setPosition(0)
                self.textTextEdit.setTextCursor(tc)
            
            self.resultTable.resizeColumnsToContents()
            self.resultTable.resizeRowsToContents()
            self.resultTable.verticalHeader().hide()
            self.resultTable.horizontalHeader().hide()
        else:
            E5MessageBox.critical(self,
                self.trUtf8("Error"),
                self.trUtf8("""A regular expression and a text must be given."""))
    
    @pyqtSlot()
    def on_nextButton_clicked(self):
        """
        Private slot to find the next match.
        """
        self.on_executeButton_clicked(self.lastMatchEnd)
    
    @pyqtSlot()
    def on_regexpTextEdit_textChanged(self):
        """
        Private slot called when the regexp changes.
        """
        if self.nextButton:
            self.nextButton.setEnabled(False)
    
    def getCode(self, indLevel, indString):
        """
        Public method to get the source code.
        
        @param indLevel indentation level (int)
        @param indString string used for indentation (space or tab) (string)
        @return generated code (string)
        """
        # calculate the indentation string
        i1string = (indLevel + 1) * indString
        estring = os.linesep + indLevel * indString
        
        # now generate the code
        reVar = self.variableLineEdit.text()
        if not reVar:
            reVar = "regexp"
        
        regexp = self.regexpTextEdit.toPlainText()
        
        options = []
        if self.caseInsensitiveCheckBox.isChecked():
            options.append("QRegularExpression.CaseInsensitiveOption")
        if self.multilineCheckBox.isChecked():
            options.append("QRegularExpression.MultilineOption")
        if self.dotallCheckBox.isChecked():
            options.append("QRegularExpression.DotMatchesEverythingOption")
        if self.extendedCheckBox.isChecked():
            options.append("QRegularExpression.ExtendedPatternSyntaxOption")
        if self.greedinessCheckBox.isChecked():
            options.append("QRegularExpression.InvertedGreedinessOption")
        if self.unicodeCheckBox.isChecked():
            options.append("QRegularExpression.UseUnicodePropertiesOption")
        if self.captureCheckBox.isChecked():
            options.append("QRegularExpression.DontCaptureOption")
        options = " | \\{0}{1}".format(os.linesep, i1string).join(options)
        
        code = '{0} = QRegularExpression(r"""{1}"""'.format(
            reVar, regexp.replace('"', '\\"'))
        if options:
            code += ', {0}{1}{2}'.format(os.linesep, i1string, options)
        code += '){0}'.format(estring)
        return code


class QRegularExpressionWizardDialog(QDialog):
    """
    Class for the dialog variant.
    """
    def __init__(self, parent=None, fromEric=True):
        """
        Constructor
        
        @param parent parent widget (QWidget)
        @param fromEric flag indicating a call from within eric5
        """
        super().__init__(parent)
        self.setModal(fromEric)
        self.setSizeGripEnabled(True)
        
        self.__layout = QVBoxLayout(self)
        self.__layout.setMargin(0)
        self.setLayout(self.__layout)
        
        self.cw = QRegularExpressionWizardWidget(self, fromEric)
        size = self.cw.size()
        self.__layout.addWidget(self.cw)
        self.resize(size)
        self.setWindowTitle(self.cw.windowTitle())
        
        self.cw.buttonBox.accepted[()].connect(self.accept)
        self.cw.buttonBox.rejected[()].connect(self.reject)
    
    def getCode(self, indLevel, indString):
        """
        Public method to get the source code.
        
        @param indLevel indentation level (int)
        @param indString string used for indentation (space or tab) (string)
        @return generated code (string)
        """
        return self.cw.getCode(indLevel, indString)


class QRegularExpressionWizardWindow(E5MainWindow):
    """
    Main window class for the standalone dialog.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.cw = QRegularExpressionWizardWidget(self, fromEric=False)
        size = self.cw.size()
        self.setCentralWidget(self.cw)
        self.resize(size)
        self.setWindowTitle(self.cw.windowTitle())
        
        self.setStyle(Preferences.getUI("Style"), Preferences.getUI("StyleSheet"))
        
        self.cw.buttonBox.accepted[()].connect(self.close)
        self.cw.buttonBox.rejected[()].connect(self.close)
