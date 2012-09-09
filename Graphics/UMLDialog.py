# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog showing UML like diagrams.
"""

from PyQt4.QtCore import Qt, QFileInfo
from PyQt4.QtGui import QMainWindow, QAction, QToolBar, QGraphicsScene

from E5Gui import E5MessageBox, E5FileDialog

from .UMLGraphicsView import UMLGraphicsView

import UI.Config
import UI.PixmapCache


class UMLDialog(QMainWindow):
    """
    Class implementing a dialog showing UML like diagrams.
    """
    ClassDiagram = 0
    PackageDiagram = 1
    ImportsDiagram = 2
    ApplicationDiagram = 3
    
    def __init__(self, diagramType, project, path="", parent=None, initBuilder=True,
                 **kwargs):
        """
        Constructor
        
        @param diagramType type of the diagram
            (one of ApplicationDiagram, ClassDiagram, ImportsDiagram, PackageDiagram)
        @param project reference to the project object (Project)
        @param path file or directory path to build the diagram from (string)
        @param parent parent widget of the dialog (QWidget)
        @keyparam initBuilder flag indicating to initialize the diagram builder (boolean)
        @param kwargs diagram specific data
        """
        super().__init__(parent)
        self.setObjectName("UMLDialog")
        
        self.__diagramType = diagramType
        
        self.scene = QGraphicsScene(0.0, 0.0, 800.0, 600.0)
        self.umlView = UMLGraphicsView(self.scene, parent=self)
        self.builder = self.__diagramBuilder(self.__diagramType, project, path, **kwargs)
        if initBuilder:
            self.builder.initialize()
        
        self.__fileName = ""
        
        self.__initActions()
        self.__initToolBars()
        
        self.setCentralWidget(self.umlView)
        
        self.umlView.relayout.connect(self.__relayout)
    
    def __initActions(self):
        """
        Private slot to initialize the actions.
        """
        self.closeAct = \
            QAction(UI.PixmapCache.getIcon("close.png"),
                    self.trUtf8("Close"), self)
        self.closeAct.triggered[()].connect(self.close)
        
        self.saveAct = \
            QAction(UI.PixmapCache.getIcon("fileSave.png"),
                    self.trUtf8("Save"), self)
        self.saveAct.triggered[()].connect(self.__save)
        
        self.saveAsAct = \
            QAction(UI.PixmapCache.getIcon("fileSaveAs.png"),
                    self.trUtf8("Save As..."), self)
        self.saveAsAct.triggered[()].connect(self.__saveAs)
        
        self.saveImageAct = \
            QAction(UI.PixmapCache.getIcon("fileSavePixmap.png"),
                    self.trUtf8("Save as PNG"), self)
        self.saveImageAct.triggered[()].connect(self.umlView.saveImage)
        
        self.printAct = \
            QAction(UI.PixmapCache.getIcon("print.png"),
                    self.trUtf8("Print"), self)
        self.printAct.triggered[()].connect(self.umlView.printDiagram)
        
        self.printPreviewAct = \
            QAction(UI.PixmapCache.getIcon("printPreview.png"),
                    self.trUtf8("Print Preview"), self)
        self.printPreviewAct.triggered[()].connect(self.umlView.printPreviewDiagram)
    
    def __initToolBars(self):
        """
        Private slot to initialize the toolbars.
        """
        self.windowToolBar = QToolBar(self.trUtf8("Window"), self)
        self.windowToolBar.setIconSize(UI.Config.ToolBarIconSize)
        self.windowToolBar.addAction(self.closeAct)
        
        self.fileToolBar = QToolBar(self.trUtf8("File"), self)
        self.fileToolBar.setIconSize(UI.Config.ToolBarIconSize)
        self.fileToolBar.addAction(self.saveAct)
        self.fileToolBar.addAction(self.saveAsAct)
        self.fileToolBar.addAction(self.saveImageAct)
        self.fileToolBar.addSeparator()
        self.fileToolBar.addAction(self.printPreviewAct)
        self.fileToolBar.addAction(self.printAct)
        
        self.umlToolBar = self.umlView.initToolBar()
        
        self.addToolBar(Qt.TopToolBarArea, self.fileToolBar)
        self.addToolBar(Qt.TopToolBarArea, self.windowToolBar)
        self.addToolBar(Qt.TopToolBarArea, self.umlToolBar)
    
    def show(self):
        """
        Overriden method to show the dialog.
        """
        self.builder.buildDiagram()
        super().show()
    
    def __relayout(self):
        """
        Private method to relayout the diagram.
        """
        self.builder.buildDiagram()
    
    def __diagramBuilder(self, diagramType, project, path, **kwargs):
        """
        Private method to instantiate a diagram builder object.
        
        @param diagramType type of the diagram
            (one of ApplicationDiagram, ClassDiagram, ImportsDiagram, PackageDiagram)
        @param project reference to the project object (Project)
        @param path file or directory path to build the diagram from (string)
        @param kwargs diagram specific data
        """
        if diagramType == UMLDialog.ClassDiagram:
            from .UMLClassDiagramBuilder import UMLClassDiagramBuilder
            return UMLClassDiagramBuilder(self, self.umlView, project, path, **kwargs)
        elif diagramType == UMLDialog.PackageDiagram:
            from .PackageDiagramBuilder import PackageDiagramBuilder
            return PackageDiagramBuilder(self, self.umlView, project, path, **kwargs)
        elif diagramType == UMLDialog.ImportsDiagram:
            from .ImportsDiagramBuilder import ImportsDiagramBuilder
            return ImportsDiagramBuilder(self, self.umlView, project, path, **kwargs)
        elif diagramType == UMLDialog.ApplicationDiagram:
            from .ApplicationDiagramBuilder import ApplicationDiagramBuilder
            return ApplicationDiagramBuilder(self, self.umlView, project, **kwargs)
        else:
            raise ValueError(
                self.trUtf8("Illegal diagram type '{0}' given.").format(diagramType))
    
    def __diagramTypeString(self):
        """
        Private method to generate a readable string for the diagram type.
        
        @return readable type string (string)
        """
        if self.__diagramType == UMLDialog.ClassDiagram:
            return "Class Diagram"
        elif self.__diagramType == UMLDialog.PackageDiagram:
            return "Package Diagram"
        elif self.__diagramType == UMLDialog.ImportsDiagram:
            return "Imports Diagram"
        elif self.__diagramType == UMLDialog.ApplicationDiagram:
            return "Application Diagram"
        else:
            return "Illegal Diagram Type"
    
    def __save(self):
        """
        Private slot to save the diagram with the current name.
        """
        self.__saveAs(self.__fileName)
    
    def __saveAs(self, filename=""):
        """
        Private slot to save the diagram.
        
        @param filename name of the file to write to (string)
        """
        if not filename:
            fname, selectedFilter = E5FileDialog.getSaveFileNameAndFilter(
                self,
                self.trUtf8("Save Diagram"),
                "",
                self.trUtf8("Eric5 Graphics File (*.e5g);;All Files (*)"),
                "",
                E5FileDialog.Options(E5FileDialog.DontConfirmOverwrite))
            if not fname:
                return
            ext = QFileInfo(fname).suffix()
            if not ext:
                ex = selectedFilter.split("(*")[1].split(")")[0]
                if ex:
                    fname += ex
            if QFileInfo(fname).exists():
                res = E5MessageBox.yesNo(self,
                    self.trUtf8("Save Diagram"),
                    self.trUtf8("<p>The file <b>{0}</b> already exists."
                                " Overwrite it?</p>").format(fname),
                    icon=E5MessageBox.Warning)
                if not res:
                    return
            filename = fname
        
        lines = [
            "version: 1.0",
            "diagram_type: {0} ({1})".format(self.__diagramType,
                self.__diagramTypeString()),
            "scene_size: {0};{1}".format(self.scene.width(), self.scene.height()),
        ]
        persistenceData = self.builder.getPersistenceData()
        if persistenceData:
            lines.append("builder_data: {0}".format(persistenceData))
        lines.extend(self.umlView.getPersistenceData())
        
        try:
            f = open(filename, "w", encoding="utf-8")
            f.write("\n".join(lines))
            f.close()
        except (IOError, OSError) as err:
            E5MessageBox.critical(self,
                self.trUtf8("Save Diagram"),
                self.trUtf8("""<p>The file <b>{0}</b> could not be saved.</p>"""
                             """<p>Reason: {1}</p>""").format(fname, str(err)))
        
        self.__fileName = filename
    
    @classmethod
    def generateDialogFromFile(cls, project, parent=None):
        """
        Class method to generate a dialog reading data from a file.
        
        @param project reference to the project object (Project)
        @param parent parent widget of the dialog (QWidget)
        @return generated dialog (UMLDialog)
        """
        # TODO: implement this
        return None
