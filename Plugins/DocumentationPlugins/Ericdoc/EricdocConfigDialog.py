# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2009 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter the parameters for eric4-doc.
"""

import sys
import os
import copy

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from E4Gui.E4Completers import E4DirCompleter

from .Ui_EricdocConfigDialog import Ui_EricdocConfigDialog
from DocumentationTools.Config import eric4docDefaultColors, eric4docColorParameterNames
import Utilities

from eric4config import getConfig

class EricdocConfigDialog(QDialog, Ui_EricdocConfigDialog):
    """
    Class implementing a dialog to enter the parameters for eric4-doc.
    """
    def __init__(self, ppath, parms = None, parent = None):
        """
        Constructor
        
        @param ppath project path of the current project (string)
        @param parms parameters to set in the dialog
        @param parent parent widget of this dialog
        """
        QDialog.__init__(self,parent)
        self.setupUi(self)
        
        self.__okButton = self.buttonBox.button(QDialogButtonBox.Ok)
        
        self.__initializeDefaults()
        
        self.sampleText = self.trUtf8(\
            '''<?xml version="1.0" encoding="utf-8"?>'''
            '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"'''
            '''"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">'''
            '''<html><head>'''
            '''<title>%%(Title)s</title>'''
            '''</head>'''
            '''<body style="background-color:%(BodyBgColor)s;color:%(BodyColor)s">'''
            '''<h1 style="background-color:%(Level1HeaderBgColor)s;color:%(Level1HeaderColor)s">'''
            '''Level 1 Header</h1>'''
            '''<h3 style="background-color:%(Level2HeaderBgColor)s;color:%(Level2HeaderColor)s">'''
            '''Level 2 Header</h3>'''
            '''<h2 style="background-color:%(CFBgColor)s;color:%(CFColor)s">'''
            '''Class and Function Header</h2>'''
            '''Standard body text with '''
            '''<a style="color:%(LinkColor)s">some links</a> embedded.'''
            '''</body></html>'''
        )
        
        # get a copy of the defaults to store the user settings
        self.parameters = copy.deepcopy(self.defaults)
        self.colors = eric4docDefaultColors.copy()
        
        # combine it with the values of parms
        if parms is not None:
            for key, value in list(parms.items()):
                if key.endswith("Color"):
                    self.colors[key] = parms[key]
                else:
                    self.parameters[key] = parms[key]
        
        self.ppath = ppath
        
        self.outputDirCompleter = E4DirCompleter(self.outputDirEdit)
        self.ignoreDirCompleter = E4DirCompleter(self.ignoreDirEdit)
        self.qtHelpDirCompleter = E4DirCompleter(self.qtHelpDirEdit)
        
        self.recursionCheckBox.setChecked(self.parameters['useRecursion'])
        self.noindexCheckBox.setChecked(self.parameters['noindex'])
        self.noemptyCheckBox.setChecked(self.parameters['noempty'])
        self.outputDirEdit.setText(self.parameters['outputDirectory'])
        self.ignoreDirsList.clear()
        for d in self.parameters['ignoreDirectories']:
            self.ignoreDirsList.addItem(d)
        self.cssEdit.setText(self.parameters['cssFile'])
        self.sourceExtEdit.setText(", ".join(self.parameters['sourceExtensions']))
        self.excludeFilesEdit.setText(", ".join(self.parameters['ignoreFilePatterns']))
        self.sample.setHtml(self.sampleText % self.colors)
        
        self.qtHelpGroup.setChecked(self.parameters['qtHelpEnabled'])
        self.qtHelpDirEdit.setText(self.parameters['qtHelpOutputDirectory'])
        self.qtHelpNamespaceEdit.setText(self.parameters['qtHelpNamespace'])
        self.qtHelpFolderEdit.setText(self.parameters['qtHelpVirtualFolder'])
        self.qtHelpFilterNameEdit.setText(self.parameters['qtHelpFilterName'])
        self.qtHelpFilterAttributesEdit.setText(self.parameters['qtHelpFilterAttributes'])
        self.qtHelpTitleEdit.setText(self.parameters['qtHelpTitle'])
        self.qtHelpGenerateCollectionCheckBox.setChecked(
            self.parameters['qtHelpCreateCollection'])
    
    def __initializeDefaults(self):
        """
        Private method to set the default values. 
        
        These are needed later on to generate the commandline
        parameters.
        """
        self.defaults = {
            'useRecursion' : 0,
            'noindex' : 0,
            'noempty' : 0,
            'outputDirectory' : '',
            'ignoreDirectories' : [],
            'ignoreFilePatterns' : [],
            'cssFile' : '',
            'sourceExtensions' : [],
            
            'qtHelpEnabled' : False, 
            'qtHelpOutputDirectory' : '', 
            'qtHelpNamespace' : '', 
            'qtHelpVirtualFolder' : 'source', 
            'qtHelpFilterName' : 'unknown', 
            'qtHelpFilterAttributes' : '', 
            'qtHelpTitle' : '', 
            'qtHelpCreateCollection' : False, 
        }
    
    def generateParameters(self):
        """
        Public method that generates the commandline parameters.
        
        It generates a list of strings to be used
        to set the QProcess arguments for the ericdoc call and
        a dictionary containing the non default parameters. This
        dictionary can be passed back upon object generation to overwrite
        the default settings.
        
        @return a tuple of the commandline parameters and non default parameters
            (list of strings, dictionary)
        """
        parms = {}
        args = []
        
        # 1. the program name
        args.append(sys.executable)
        args.append(Utilities.normabsjoinpath(getConfig('ericDir'), "eric4-doc.py"))
        
        # 2. the commandline options
        # 2a. general commandline options
        if self.parameters['outputDirectory'] != self.defaults['outputDirectory']:
            parms['outputDirectory'] = self.parameters['outputDirectory']
            args.append('-o')
            if os.path.isabs(self.parameters['outputDirectory']):
                args.append(self.parameters['outputDirectory'])
            else:
                args.append(os.path.join(self.ppath, self.parameters['outputDirectory']))
        if self.parameters['ignoreDirectories'] != self.defaults['ignoreDirectories']:
            parms['ignoreDirectories'] = self.parameters['ignoreDirectories'][:]
            for d in self.parameters['ignoreDirectories']:
                args.append('-x')
                args.append(d)
        if self.parameters['ignoreFilePatterns'] != self.defaults['ignoreFilePatterns']:
            parms['ignoreFilePatterns'] = self.parameters['ignoreFilePatterns'][:]
            for pattern in self.parameters['ignoreFilePatterns']:
                args.append("--exclude-file=%s" % pattern)
        if self.parameters['useRecursion'] != self.defaults['useRecursion']:
            parms['useRecursion'] = self.parameters['useRecursion']
            args.append('-r')
        if self.parameters['noindex'] != self.defaults['noindex']:
            parms['noindex'] = self.parameters['noindex']
            args.append('-i')
        if self.parameters['noempty'] != self.defaults['noempty']:
            parms['noempty'] = self.parameters['noempty']
            args.append('-e')
        if self.parameters['sourceExtensions'] != self.defaults['sourceExtensions']:
            parms['sourceExtensions'] = self.parameters['sourceExtensions'][:]
            for ext in self.parameters['sourceExtensions']:
                args.append('-t')
                args.append(ext)
        
        # 2b. style commandline options
        if self.parameters['cssFile'] != self.defaults['cssFile']:
            parms['cssFile'] = self.parameters['cssFile']
            args.append('-c')
            if os.path.isabs(self.parameters['cssFile']):
                args.append(self.parameters['cssFile'])
            else:
                args.append(os.path.join(self.ppath, self.parameters['cssFile']))
        for key, value in list(self.colors.items()):
            if self.colors[key] != eric4docDefaultColors[key]:
                parms[key] = self.colors[key]
                args.append("--%s=%s" % \
                            (eric4docColorParameterNames[key], self.colors[key]))
        
        # 2c. QtHelp commandline options
        parms['qtHelpEnabled'] = self.parameters['qtHelpEnabled']
        if self.parameters['qtHelpEnabled']:
            args.append('--create-qhp')
        if self.parameters['qtHelpOutputDirectory'] != \
           self.defaults['qtHelpOutputDirectory']:
            parms['qtHelpOutputDirectory'] = self.parameters['qtHelpOutputDirectory']
            if os.path.isabs(self.parameters['outputDirectory']):
                args.append("--qhp-outdir=%s" % self.parameters['qtHelpOutputDirectory'])
            else:
                args.append("--qhp-outdir=%s" % \
                    os.path.join(self.ppath, self.parameters['qtHelpOutputDirectory']))
        if self.parameters['qtHelpNamespace'] != self.defaults['qtHelpNamespace']:
            parms['qtHelpNamespace'] = self.parameters['qtHelpNamespace']
            args.append("--qhp-namespace=%s" % self.parameters['qtHelpNamespace'])
        if self.parameters['qtHelpVirtualFolder'] != self.defaults['qtHelpVirtualFolder']:
            parms['qtHelpVirtualFolder'] = self.parameters['qtHelpVirtualFolder']
            args.append("--qhp-virtualfolder=%s" % self.parameters['qtHelpVirtualFolder'])
        if self.parameters['qtHelpFilterName'] != self.defaults['qtHelpFilterName']:
            parms['qtHelpFilterName'] = self.parameters['qtHelpFilterName']
            args.append("--qhp-filtername=%s" % self.parameters['qtHelpFilterName'])
        if self.parameters['qtHelpFilterAttributes'] != \
           self.defaults['qtHelpFilterAttributes']:
            parms['qtHelpFilterAttributes'] = self.parameters['qtHelpFilterAttributes']
            args.append("--qhp-filterattribs=%s" % \
                self.parameters['qtHelpFilterAttributes'])
        if self.parameters['qtHelpTitle'] != self.defaults['qtHelpTitle']:
            parms['qtHelpTitle'] = self.parameters['qtHelpTitle']
            args.append("--qhp-title=%s" % self.parameters['qtHelpTitle'])
        if self.parameters['qtHelpCreateCollection'] != \
           self.defaults['qtHelpCreateCollection']:
            parms['qtHelpCreateCollection'] = self.parameters['qtHelpCreateCollection']
            args.append('--create-qhc')
        
        return (args, parms)

    @pyqtSlot()
    def on_outputDirButton_clicked(self):
        """
        Private slot to select the output directory.
        
        It displays a directory selection dialog to
        select the directory the documentations is written to.
        """
        directory = QFileDialog.getExistingDirectory(\
            self,
            self.trUtf8("Select output directory"),
            self.outputDirEdit.text(),
            QFileDialog.Options(QFileDialog.ShowDirsOnly))
            
        if directory:
            # make it relative, if it is a subdirectory of the project path 
            dn = Utilities.toNativeSeparators(directory)
            dn = dn.replace(self.ppath + os.sep, '')
            while dn.endswith(os.sep):
                dn = dn[:-1]
            self.outputDirEdit.setText(dn)

    @pyqtSlot()
    def on_ignoreDirButton_clicked(self):
        """
        Private slot to select a directory to be ignored.
        
        It displays a directory selection dialog to
        select a directory to be ignored.
        """
        startDir = self.ignoreDirEdit.text()
        if not startDir:
            startDir = self.ppath
        directory = QFileDialog.getExistingDirectory(\
            self,
            self.trUtf8("Select directory to exclude"),
            startDir,
            QFileDialog.Options(QFileDialog.ShowDirsOnly))
            
        if directory:
            # make it relative, if it is a subdirectory of the project path 
            dn = Utilities.toNativeSeparators(directory)
            dn = dn.replace(self.ppath + os.sep, '')
            while dn.endswith(os.sep):
                dn = dn[:-1]
            self.ignoreDirEdit.setText(dn)

    @pyqtSlot()
    def on_addButton_clicked(self):
        """
        Private slot to add the directory displayed to the listview.
        
        The directory in the ignore directories
        line edit is moved to the listbox above and the edit is cleared.
        """
        self.ignoreDirsList.addItem(os.path.basename(self.ignoreDirEdit.text()))
        self.ignoreDirEdit.clear()

    @pyqtSlot()
    def on_deleteButton_clicked(self):
        """
        Private slot to delete the currently selected directory of the listbox.
        """
        itm = self.ignoreDirsList.takeItem(self.ignoreDirsList.currentRow())
        del itm

    @pyqtSlot()
    def on_cssButton_clicked(self):
        """
        Private slot to select a css style sheet.
        """
        cssFile = QFileDialog.getOpenFileName(\
            self,
            self.trUtf8("Select CSS style sheet"),
            getConfig('ericCSSDir'),
            self.trUtf8("Style sheet (*.css);;All files (*)"))
            
        if cssFile:
            # make it relative, if it is in a subdirectory of the project path 
            cf = Utilities.toNativeSeparators(cssFile)
            cf = cf.replace(self.ppath + os.sep, '')
            self.cssEdit.setText(cf)

    def __selectColor(self, colorKey):
        """
        Private method to select a color.
        
        @param colorKey key of the color to select (string)
        """
        color = QColorDialog.getColor(QColor(self.colors[colorKey]))
        if color.isValid():
            self.colors[colorKey] = color.name()
            self.sample.setHtml(self.sampleText % self.colors)

    @pyqtSlot()
    def on_bodyFgButton_clicked(self):
        """
        Private slot to select the body foreground color.
        """
        self.__selectColor('BodyColor')
    
    @pyqtSlot()
    def on_bodyBgButton_clicked(self):
        """
        Private slot to select the body background color.
        """
        self.__selectColor('BodyBgColor')
    
    @pyqtSlot()
    def on_l1FgButton_clicked(self):
        """
        Private slot to select the level 1 header foreground color.
        """
        self.__selectColor('Level1HeaderColor')
    
    @pyqtSlot()
    def on_l1BgButton_clicked(self):
        """
        Private slot to select the level 1 header background color.
        """
        self.__selectColor('Level1HeaderBgColor')
    
    @pyqtSlot()
    def on_l2FgButton_clicked(self):
        """
        Private slot to select the level 2 header foreground color.
        """
        self.__selectColor('Level2HeaderColor')
    
    @pyqtSlot()
    def on_l2BgButton_clicked(self):
        """
        Private slot to select the level 2 header background color.
        """
        self.__selectColor('Level2HeaderBgColor')
    
    @pyqtSlot()
    def on_cfFgButton_clicked(self):
        """
        Private slot to select the class/function header foreground color.
        """
        self.__selectColor('CFColor')
    
    @pyqtSlot()
    def on_cfBgButton_clicked(self):
        """
        Private slot to select the class/function header background color.
        """
        self.__selectColor('CFBgColor')
    
    @pyqtSlot()
    def on_linkFgButton_clicked(self):
        """
        Private slot to select the foreground color of links.
        """
        self.__selectColor('LinkColor')
    
    def __checkQtHelpOptions(self):
        """
        Private slot to check the QtHelp options and set the ok button accordingly.
        """
        setOn = True
        if self.qtHelpGroup.isChecked():
            if not self.qtHelpNamespaceEdit.text():
                setOn = False
            if not self.qtHelpFolderEdit.text():
                setOn = False
            else:
                if '/' in self.qtHelpFolderEdit.text():
                    setOn = False
            if not self.qtHelpTitleEdit.text():
                setOn = False
        
        self.__okButton.setEnabled(setOn)
    
    @pyqtSlot(bool)
    def on_qtHelpGroup_toggled(self, enabled):
        """
        Private slot to toggle the generation of QtHelp files.
        
        @param enabled flag indicating the state (boolean)
        """
        self.__checkQtHelpOptions()
    
    @pyqtSlot(str)
    def on_qtHelpNamespaceEdit_textChanged(self, txt):
        """
        Private slot to check the namespace.
        
        @param txt text of the line edit (string)
        """
        self.__checkQtHelpOptions()
    
    @pyqtSlot(str)
    def on_qtHelpFolderEdit_textChanged(self, txt):
        """
        Private slot to check the virtual folder.
        
        @param txt text of the line edit (string)
        """
        self.__checkQtHelpOptions()
    
    @pyqtSlot(str)
    def on_qtHelpTitleEdit_textChanged(self, p0):
        """
        Private slot to check the title.
        
        @param txt text of the line edit (string)
        """
        self.__checkQtHelpOptions()
    
    @pyqtSlot()
    def on_qtHelpDirButton_clicked(self):
        """
        Private slot to select the output directory for the QtHelp files.
        
        It displays a directory selection dialog to
        select the directory the QtHelp files are written to.
        """
        directory = QFileDialog.getExistingDirectory(\
            self,
            self.trUtf8("Select output directory for QtHelp files"),
            self.qtHelpDirEdit.text(),
            QFileDialog.Options(QFileDialog.ShowDirsOnly))
            
        if directory:
            # make it relative, if it is a subdirectory of the project path 
            dn = Utilities.toNativeSeparators(directory)
            dn = dn.replace(self.ppath + os.sep, '')
            while dn.endswith(os.sep):
                dn = dn[:-1]
            self.qtHelpDirEdit.setText(dn)
    
    def accept(self):
        """
        Protected slot called by the Ok button. 
        
        It saves the values in the parameters dictionary.
        """
        self.parameters['useRecursion'] = self.recursionCheckBox.isChecked()
        self.parameters['noindex'] = self.noindexCheckBox.isChecked()
        self.parameters['noempty'] = self.noemptyCheckBox.isChecked()
        outdir = self.outputDirEdit.text()
        if outdir != '':
            outdir = os.path.normpath(outdir)
            if outdir.endswith(os.sep):
                outdir = outdir[:-1]
        self.parameters['outputDirectory'] = outdir
        self.parameters['ignoreDirectories'] = []
        for row in range(0, self.ignoreDirsList.count()):
            itm = self.ignoreDirsList.item(row)
            self.parameters['ignoreDirectories'].append(\
                os.path.normpath(itm.text()))
        cssFile = self.cssEdit.text()
        if cssFile != '':
            cssFile = os.path.normpath(cssFile)
        self.parameters['cssFile'] = cssFile
        extensions = self.sourceExtEdit.text().split(',')
        self.parameters['sourceExtensions'] = \
            [ext.strip() for ext in extensions]
        patterns = self.excludeFilesEdit.text().split(',')
        self.parameters['ignoreFilePatterns'] = \
            [pattern.strip() for pattern in patterns]
        
        self.parameters['qtHelpEnabled'] = self.qtHelpGroup.isChecked()
        self.parameters['qtHelpOutputDirectory'] = self.qtHelpDirEdit.text()
        self.parameters['qtHelpNamespace'] = self.qtHelpNamespaceEdit.text()
        self.parameters['qtHelpVirtualFolder'] = self.qtHelpFolderEdit.text()
        self.parameters['qtHelpFilterName'] = self.qtHelpFilterNameEdit.text()
        self.parameters['qtHelpFilterAttributes'] = \
            self.qtHelpFilterAttributesEdit.text()
        self.parameters['qtHelpTitle'] = self.qtHelpTitleEdit.text()
        self.parameters['qtHelpCreateCollection'] = \
            self.qtHelpGenerateCollectionCheckBox.isChecked()
        
        # call the accept slot of the base class
        QDialog.accept(self)
