# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2009 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to generate code for a Qt4 dialog.
"""

import os
import sys

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import uic

from E4Gui.E4Application import e4App

from .NewDialogClassDialog import NewDialogClassDialog
from .Ui_CreateDialogCodeDialog import Ui_CreateDialogCodeDialog

from Utilities import ModuleParser

import UI.PixmapCache

from eric4config import getConfig

pyqtSignatureRole   = Qt.UserRole + 1
pythonSignatureRole = Qt.UserRole + 2
rubySignatureRole   = Qt.UserRole + 3

class CreateDialogCodeDialog(QDialog, Ui_CreateDialogCodeDialog):
    """
    Class implementing a dialog to generate code for a Qt4 dialog.
    """
    def __init__(self, formName, project, parent = None):
        """
        Constructor
        
        @param formName name of the file containing the form (string)
        @param project reference to the project object
        @param parent parent widget if the dialog (QWidget)
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        
        self.okButton = self.buttonBox.button(QDialogButtonBox.Ok)
        
        self.slotsView.header().hide()
        
        self.project = project
        
        self.formFile = formName
        filename, ext = os.path.splitext(self.formFile)
        self.srcFile = '%s%s' % (filename, self.project.getDefaultSourceExtension())
        
        self.slotsModel = QStandardItemModel()
        self.proxyModel = QSortFilterProxyModel()
        self.proxyModel.setDynamicSortFilter(True)
        self.proxyModel.setSourceModel(self.slotsModel)
        self.slotsView.setModel(self.proxyModel)
        
        self.clearFilterButton.setIcon(UI.PixmapCache.getIcon("clearLeft.png"))
        
        # initialize some member variables
        self.__initError = False
        self.__module = None
        
        if os.path.exists(self.srcFile):
            vm = e4App().getObject("ViewManager")
            ed = vm.getOpenEditor(self.srcFile)
            if ed and not vm.checkDirty(ed):
                self.__initError = True
                return
            
            self.__module = ModuleParser.readModule(self.srcFile, caching = False)
        
        if self.__module is not None:
            self.filenameEdit.setText(self.srcFile)
            
            classesList = []
            for cls in list(self.__module.classes.values()):
                classesList.append(cls.name)
            classesList.sort()
            self.classNameCombo.addItems(classesList)
        
        if os.path.exists(self.srcFile) and self.classNameCombo.count() == 0:
            self.__initError = True
            QMessageBox.critical(None,
                self.trUtf8("Create Dialog Code"),
                self.trUtf8("""The file <b>{0}</b> exists but does not contain"""
                            """ any classes.""").format(self.srcFile),
                QMessageBox.StandardButtons(\
                    QMessageBox.Abort))
        
        self.okButton.setEnabled(self.classNameCombo.count() > 0)
        
        self.__updateSlotsModel()
        
    def initError(self):
        """
        Public method to determine, if there was an initialzation error.
        
        @return flag indicating an initialzation error (boolean)
        """
        return self.__initError
        
    def __objectName(self):
        """
        Private method to get the object name of the dialog.
        
        @return object name (string)
        """
        try:
            dlg = uic.loadUi(self.formFile)
            return dlg.objectName()
        except AttributeError as err:
            QMessageBox.critical(self,
                self.trUtf8("uic error"),
                self.trUtf8("""<p>There was an error loading the form <b>{0}</b>.</p>"""
                            """<p>{1}</p>""").format(self.formFile, str(err)),
                QMessageBox.StandardButtons(\
                    QMessageBox.Ok))
            return ""
        
    def __className(self):
        """
        Private method to get the class name of the dialog.
        
        @return class name (sting)
        """
        try:
            dlg = uic.loadUi(self.formFile)
            return dlg.metaObject().className()
        except AttributeError as err:
            QMessageBox.critical(self,
                self.trUtf8("uic error"),
                self.trUtf8("""<p>There was an error loading the form <b>{0}</b>.</p>"""
                            """<p>{1}</p>""").format(self.formFile, str(err)),
                QMessageBox.StandardButtons(\
                    QMessageBox.Ok))
            return ""
        
    def __signatures(self):
        """
        Private slot to get the signatures.
        
        @return list of signatures (list of strings)
        """
        if self.__module is None:
            return []
            
        signatures = []
        clsName = self.classNameCombo.currentText()
        if clsName:
            cls = self.__module.classes[clsName]
            for meth in list(cls.methods.values()):
                if meth.name.startswith("on_"):
                    if meth.pyqtSignature is not None:
                        sig = ", ".join([str(QMetaObject.normalizedType(t)) \
                                         for t in meth.pyqtSignature.split(",")])
                        signatures.append("%s(%s)" % (meth.name, sig))
                    else:
                        signatures.append(meth.name)
        return signatures
        
    def __updateSlotsModel(self):
        """
        Private slot to update the slots tree display.
        """
        self.filterEdit.clear()
        
        try:
            dlg = uic.loadUi(self.formFile)
            objects = dlg.findChildren(QWidget) + dlg.findChildren(QAction)
            
            signatureList = self.__signatures()
            
            self.slotsModel.clear()
            self.slotsModel.setHorizontalHeaderLabels([""])
            for obj in objects:
                name = obj.objectName()
                if not name:
                    continue
                
                metaObject = obj.metaObject()
                className = metaObject.className()
                itm = QStandardItem("%s (%s)" % (name, className))
                self.slotsModel.appendRow(itm)
                for index in range(metaObject.methodCount()):
                    metaMethod = metaObject.method(index)
                    if metaMethod.methodType() == QMetaMethod.Signal:
                        itm2 = QStandardItem("on_%s_%s" % (name, metaMethod.signature()))
                        itm.appendRow(itm2)
                        if self.__module is not None:
                            method = "on_%s_%s" % \
                                (name, metaMethod.signature().split("(")[0])
                            method2 = "on_%s_%s" % \
                                (name, 
                                 QMetaObject.normalizedSignature(metaMethod.signature()))
                            
                            if method2 in signatureList or method in signatureList:
                                itm2.setFlags(Qt.ItemFlags(Qt.ItemIsEnabled))
                                itm2.setCheckState(Qt.Checked)
                                itm2.setForeground(QBrush(Qt.blue))
                                continue
                        
                        pyqtSignature = \
                            ", ".join([str(t) for t in metaMethod.parameterTypes()])
                        
                        parameterNames = metaMethod.parameterNames()
                        if parameterNames:
                            for index in range(len(parameterNames)):
                                if not parameterNames[index]:
                                    parameterNames[index] = QByteArray("p%d" % index)
                        methNamesSig = \
                            ", ".join([str(n) for n in parameterNames])
                        
                        if methNamesSig:
                            pythonSignature = "on_%s_%s(self, %s)" % \
                                (name, 
                                 metaMethod.signature().split("(")[0], 
                                 methNamesSig
                                )
                        else:
                            pythonSignature = "on_%s_%s(self)" % \
                                (name, 
                                 metaMethod.signature().split("(")[0]
                                )
                        itm2.setData(pyqtSignature, pyqtSignatureRole)
                        itm2.setData(pythonSignature, pythonSignatureRole)
                        
                        itm2.setFlags(Qt.ItemFlags(\
                            Qt.ItemIsUserCheckable | \
                            Qt.ItemIsEnabled | \
                            Qt.ItemIsSelectable)
                        )
                        itm2.setCheckState(Qt.Unchecked)
            
            self.slotsView.sortByColumn(0, Qt.AscendingOrder)
        except (AttributeError, ImportError) as err:
            QMessageBox.critical(self,
                self.trUtf8("uic error"),
                self.trUtf8("""<p>There was an error loading the form <b>{0}</b>.</p>"""
                            """<p>{1}</p>""").format(self.formFile, str(err)),
                QMessageBox.StandardButtons(\
                    QMessageBox.Ok))
        
    def __generateCode(self):
        """
        Private slot to generate the code as requested by the user.
        """
        # first decide on extension
        if self.filenameEdit.text().endswith(".py") or \
           self.filenameEdit.text().endswith(".pyw"):
            self.__generatePythonCode()
        elif self.filenameEdit.text().endswith(".rb"):
            pass
        # second decide on project language
        elif self.project.getProjectLanguage() in ["Python", "Python3"]:
            self.__generatePythonCode()
        elif self.project.getProjectLanguage() == "Ruby":
            pass
        else:
            # assume Python (our global default)
            self.__generatePythonCode()
        
    def __generatePythonCode(self):
        """
        Private slot to generate Python code as requested by the user.
        """
        # init some variables
        sourceImpl = []
        appendAtIndex = -1
        indentStr = "    "
        slotsCode = []
        
        if self.__module is None:
            # new file
            try:
                tmplName = os.path.join(getConfig('ericCodeTemplatesDir'), "impl.py.tmpl")
                tmplFile = open(tmplName, 'r')
                template = tmplFile.read()
                tmplFile.close()
            except IOError as why:
                QMessageBox.critical(self,
                    self.trUtf8("Code Generation"),
                    self.trUtf8("""<p>Could not open the code template file "{0}".</p>"""
                                """<p>Reason: {1}</p>""")\
                        .format(tmplName, str(why)),
                    QMessageBox.StandardButtons(\
                        QMessageBox.Ok))
                return
            
            objName = self.__objectName()
            if objName:
                template = template\
                    .replace("$FORMFILE$", 
                             os.path.splitext(os.path.basename(self.formFile))[0])\
                    .replace("$FORMCLASS$", objName)\
                    .replace("$CLASSNAME$", self.classNameCombo.currentText())\
                    .replace("$SUPERCLASS$", self.__className())
                
                sourceImpl = template.splitlines(True)
                appendAtIndex = -1
                
                # determine indent string
                for line in sourceImpl:
                    if line.lstrip().startswith("def __init__"):
                        indentStr = line.replace(line.lstrip(), "")
                        break
        else:
            # extend existing file
            try:
                srcFile = open(self.srcFile, 'r')
                sourceImpl = srcFile.readlines()
                srcFile.close()
                if not sourceImpl[-1].endswith(os.linesep):
                    sourceImpl[-1] = "%s%s" % (sourceImpl[-1], os.linesep)
            except IOError as why:
                QMessageBox.critical(self,
                    self.trUtf8("Code Generation"),
                    self.trUtf8("""<p>Could not open the source file "{0}".</p>"""
                                """<p>Reason: {1}</p>""")\
                        .format(self.srcFile, str(why)),
                    QMessageBox.StandardButtons(\
                        QMessageBox.Ok))
                return
            
            cls = self.__module.classes[self.classNameCombo.currentText()]
            if cls.endlineno == len(sourceImpl) or cls.endlineno == -1:
                appendAtIndex = -1
                # delete empty lines at end
                while not sourceImpl[-1].strip():
                    del sourceImpl[-1]
            else:
                appendAtIndex = cls.endlineno - 1
            
            # determine indent string
            for line in sourceImpl[cls.lineno:cls.endlineno+1]:
                if line.lstrip().startswith("def __init__"):
                    indentStr = line.replace(line.lstrip(), "")
                    break
        
        # do the coding stuff
        for row in range(self.slotsModel.rowCount()):
            topItem = self.slotsModel.item(row)
            for childRow in range(topItem.rowCount()):
                child = topItem.child(childRow)
                if child.checkState() and \
                   child.flags() & Qt.ItemFlags(Qt.ItemIsUserCheckable):
                    slotsCode.append('%s\n' % indentStr)
                    # TODO: adjust to new signal/slot mechanism
                    slotsCode.append('%s@pyqtSlot(%s)\n' % \
                        (indentStr, child.data(pyqtSignatureRole)))
                    slotsCode.append('%sdef %s:\n' % \
                        (indentStr, child.data(pythonSignatureRole)))
                    slotsCode.append('%s"""\n' % (indentStr * 2,))
                    slotsCode.append('%sSlot documentation goes here.\n' % \
                        (indentStr * 2,))
                    slotsCode.append('%s"""\n' % (indentStr * 2,))
                    slotsCode.append('%s# %s: not implemented yet\n' % \
                        (indentStr * 2, "TODO"))
                    slotsCode.append('%sraise NotImplementedError\n' % (indentStr * 2,))
        
        if appendAtIndex == -1:
            sourceImpl.extend(slotsCode)
        else:
            sourceImpl[appendAtIndex:appendAtIndex] = slotsCode
        
        # write the new code
        try:
            srcFile = open(self.filenameEdit.text(), 'w')
            srcFile.write("".join(sourceImpl))
            srcFile.close()
        except IOError as why:
            QMessageBox.critical(self,
                self.trUtf8("Code Generation"),
                self.trUtf8("""<p>Could not write the source file "{0}".</p>"""
                            """<p>Reason: {1}</p>""")\
                    .format(self.filenameEdit.text(), str(why)),
                QMessageBox.StandardButtons(\
                    QMessageBox.Ok))
            return
        
        self.project.appendFile(self.filenameEdit.text())
        
    @pyqtSlot(int)
    def on_classNameCombo_activated(self, index):
        """
        Private slot to handle the activated signal of the classname combo.
        
        @param index index of the activated item (integer)
        """
        self.__updateSlotsModel()
        
    def on_filterEdit_textChanged(self, text):
        """
        Private slot called, when thext of the filter edit has changed.
        
        @param text changed text (string)
        """
        re = QRegExp(text, Qt.CaseInsensitive, QRegExp.RegExp2)
        self.proxyModel.setFilterRegExp(re)
        
    @pyqtSlot()
    def on_clearFilterButton_clicked(self):
        """
        Private slot called by a click of the clear filter button.
        """
        self.filterEdit.clear()
        
    @pyqtSlot()
    def on_newButton_clicked(self):
        """
        Private slot called to enter the data for a new dialog class.
        """
        path, file = os.path.split(self.srcFile)
        objName = self.__objectName()
        if objName:
            dlg = NewDialogClassDialog(objName, file, path, self)
            if dlg.exec_() == QDialog.Accepted:
                className, fileName = dlg.getData()
                
                self.classNameCombo.clear()
                self.classNameCombo.addItem(className)
                self.srcFile = fileName
                self.filenameEdit.setText(self.srcFile)
                self.__module = None
            
            self.okButton.setEnabled(self.classNameCombo.count() > 0)
        
    def on_buttonBox_clicked(self, button):
        """
        Private slot to handle the buttonBox clicked signal.
        
        @param button reference to the button that was clicked (QAbstractButton)
        """
        if button == self.okButton:
            self.__generateCode()
            self.accept()
