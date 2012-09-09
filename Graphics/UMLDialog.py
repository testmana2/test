# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog showing UML like diagrams.
"""

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QMainWindow, QAction, QToolBar, QGraphicsScene

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
    
    def __init__(self, diagramType, project, path, parent=None, **kwargs):
        """
        Constructor
        
        @param diagramType type of the diagram
            (one of ApplicationDiagram, ClassDiagram, ImportsDiagram, PackageDiagram)
        @param project reference to the project object (Project)
        @param path file or directory path to build the diagram from (string)
        @param parent parent widget of the view (QWidget)
        @param kwargs diagram specific data
        """
        super().__init__(parent)
        self.setObjectName("UMLDialog")
        
        self.scene = QGraphicsScene(0.0, 0.0, 800.0, 600.0)
        self.umlView = UMLGraphicsView(self.scene, diagramType, parent=self)
        self.builder = self.__diagramBuilder(diagramType, project, path, **kwargs)
        
        self.closeAct = \
            QAction(UI.PixmapCache.getIcon("close.png"),
                    self.trUtf8("Close"), self)
        self.closeAct.triggered[()].connect(self.close)
        
        self.windowToolBar = QToolBar(self.trUtf8("Window"), self)
        self.windowToolBar.setIconSize(UI.Config.ToolBarIconSize)
        self.windowToolBar.addAction(self.closeAct)
        
        self.umlToolBar = self.umlView.initToolBar()
        
        self.addToolBar(Qt.TopToolBarArea, self.windowToolBar)
        self.addToolBar(Qt.TopToolBarArea, self.umlToolBar)
        
        self.setCentralWidget(self.umlView)
        
        self.umlView.relayout.connect(self.__relayout)
    
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
    
    def diagramTypeToString(self, diagramType):
        """
        Public method to convert the diagram type to a readable string.
        
        @param diagramType type of the diagram
            (one of ApplicationDiagram, ClassDiagram, ImportsDiagram, PackageDiagram)
        @return readable type string (string)
        """
        if diagramType == UMLDialog.ClassDiagram:
            return "Class Diagram"
        elif diagramType == UMLDialog.PackageDiagram:
            return "Package Diagram"
        elif diagramType == UMLDialog.ImportsDiagram:
            return "Imports Diagram"
        elif diagramType == UMLDialog.ApplicationDiagram:
            return "Application Diagram"
        else:
            return "Illegal Diagram Type"
