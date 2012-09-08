# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog showing a UML like class diagram of a package.
"""

import glob
import os.path
import itertools

from PyQt4.QtGui import QProgressDialog, QApplication, QGraphicsTextItem

from .UMLDialog import UMLDialog
from .ClassItem import ClassItem, ClassModel
from .AssociationItem import AssociationItem, Generalisation
from . import GraphicsUtilities

import Utilities.ModuleParser
import Utilities
import Preferences


class PackageDiagram(UMLDialog):
    """
    Class implementing a dialog showing a UML like class diagram of a package.
    """
    def __init__(self, project, package, parent=None, name=None, noAttrs=False):
        """
        Constructor
        
        @param project reference to the project object
        @param package name of a python package to be shown (string)
        @param parent parent widget of the view (QWidget)
        @param name name of the view widget (string)
        @keyparam noAttrs flag indicating, that no attributes should be shown (boolean)
        """
        UMLDialog.__init__(self, buildFunction=self.__buildClasses, parent=parent)
        
        self.package = Utilities.normabspath(package)
        self.allClasses = {}
        self.noAttrs = noAttrs
        
        pname = project.getProjectName()
        if pname:
            name = self.trUtf8("Package Diagram {0}: {1}").format(
                pname, project.getRelativePath(self.package))
        else:
            name = self.trUtf8("Package Diagram: {0}").format(self.package)
        self.setDiagramName(name)
        
        if not name:
            self.setObjectName("PackageDiagram")
        else:
            self.setObjectName(name)
        
        self.umlView.relayout.connect(self.relayout)
        
    def __getCurrentShape(self, name):
        """
        Private method to get the named shape.
        
        @param name name of the shape (string)
        @return shape (QCanvasItem)
        """
        return self.allClasses.get(name)
        
    def __buildModulesDict(self):
        """
        Private method to build a dictionary of modules contained in the package.
        
        @return dictionary of modules contained in the package.
        """
        supportedExt = \
            ['*{0}'.format(ext) for ext in Preferences.getPython("PythonExtensions")] + \
            ['*{0}'.format(ext) for ext in Preferences.getPython("Python3Extensions")] + \
            ['*.rb']
        extensions = Preferences.getPython("PythonExtensions") + \
            Preferences.getPython("Python3Extensions") + ['.rb']
        
        moduleDict = {}
        modules = []
        for ext in supportedExt:
            modules.extend(glob.glob(Utilities.normjoinpath(self.package, ext)))
        tot = len(modules)
        try:
            prog = 0
            progress = QProgressDialog(self.trUtf8("Parsing modules..."),
                None, 0, tot, self)
            progress.show()
            QApplication.processEvents()
            for module in modules:
                progress.setValue(prog)
                QApplication.processEvents()
                prog += 1
                try:
                    mod = Utilities.ModuleParser.readModule(module, extensions=extensions)
                except ImportError:
                    continue
                else:
                    name = mod.name
                    if name.startswith(self.package):
                        name = name[len(self.package) + 1:]
                    moduleDict[name] = mod
        finally:
            progress.setValue(tot)
        return moduleDict
        
    def __buildClasses(self):
        """
        Private method to build the class shapes of the package diagram.
        
        The algorithm is borrowed from Boa Constructor.
        """
        initlist = glob.glob(os.path.join(self.package, '__init__.*'))
        if len(initlist) == 0:
            ct = QGraphicsTextItem(None, self.scene)
            ct.setHtml(
                self.trUtf8("The directory <b>'{0}'</b> is not a package.")\
                    .format(self.package))
            return
        
        modules = self.__buildModulesDict()
        if not modules:
            ct = QGraphicsTextItem(None, self.scene)
            ct.setHtml(
                self.trUtf8("The package <b>'{0}'</b> does not contain any modules.")
                    .format(self.package))
            return
            
        # step 1: build all classes found in the modules
        classesFound = False
        
        for modName in list(modules.keys()):
            module = modules[modName]
            for cls in list(module.classes.keys()):
                classesFound = True
                self.__addLocalClass(cls, module.classes[cls], 0, 0)
        if not classesFound:
            ct = QGraphicsTextItem(None, self.scene)
            ct.setHtml(
                self.trUtf8("The package <b>'{0}'</b> does not contain any classes.")
                    .format(self.package))
            return
        
        # step 2: build the class hierarchies
        routes = []
        nodes = []
        
        for modName in list(modules.keys()):
            module = modules[modName]
            todo = [module.createHierarchy()]
            while todo:
                hierarchy = todo[0]
                for className in list(hierarchy.keys()):
                    cw = self.__getCurrentShape(className)
                    if not cw and className.find('.') >= 0:
                        cw = self.__getCurrentShape(className.split('.')[-1])
                        if cw:
                            self.allClasses[className] = cw
                    if cw and cw.noAttrs != self.noAttrs:
                        cw = None
                    if cw and not (cw.external and \
                                   (className in module.classes or
                                    className in module.modules)
                                  ):
                        if className not in nodes:
                            nodes.append(className)
                    else:
                        if className in module.classes:
                            # this is a local class (defined in this module)
                            self.__addLocalClass(className, module.classes[className],
                                                 0, 0)
                        elif className in module.modules:
                            # this is a local module (defined in this module)
                            self.__addLocalClass(className, module.modules[className],
                                                 0, 0, True)
                        else:
                            self.__addExternalClass(className, 0, 0)
                        nodes.append(className)
                    
                    if hierarchy.get(className):
                        todo.append(hierarchy.get(className))
                        children = list(hierarchy.get(className).keys())
                        for child in children:
                            if (className, child) not in routes:
                                routes.append((className, child))
                
                del todo[0]
            
        self.__arrangeClasses(nodes, routes[:])
        self.__createAssociations(routes)
        self.umlView.autoAdjustSceneSize(limit=True)
        
    def __arrangeClasses(self, nodes, routes, whiteSpaceFactor=1.2):
        """
        Private method to arrange the shapes on the canvas.
        
        The algorithm is borrowed from Boa Constructor.
        """
        generations = GraphicsUtilities.sort(nodes, routes)
        
        # calculate width and height of all elements
        sizes = []
        for generation in generations:
            sizes.append([])
            for child in generation:
                sizes[-1].append(self.__getCurrentShape(child).sceneBoundingRect())
                
        # calculate total width and total height
        width = 0
        height = 0
        widths = []
        heights = []
        for generation in sizes:
            currentWidth = 0
            currentHeight = 0
            
            for rect in generation:
                if rect.bottom() > currentHeight:
                    currentHeight = rect.bottom()
                currentWidth = currentWidth + rect.right()
                
            # update totals
            if currentWidth > width:
                width = currentWidth
            height = height + currentHeight
            
            # store generation info
            widths.append(currentWidth)
            heights.append(currentHeight)
            
        # add in some whitespace
        width = width * whiteSpaceFactor
        rawHeight = height
        height = height * whiteSpaceFactor - 20
        verticalWhiteSpace = (height - rawHeight) / (len(generations) - 1.0 or 2.0)
        
        sceneRect = self.umlView.sceneRect()
        width += 50.0
        height += 50.0
        swidth = width < sceneRect.width() and sceneRect.width() or width
        sheight = height < sceneRect.height() and sceneRect.height() or height
        self.umlView.setSceneSize(swidth, sheight)
        
        # distribute each generation across the width and the
        # generations across height
        y = 10.0
        for currentWidth, currentHeight, generation in \
                itertools.zip_longest(widths, heights, generations):
            x = 10.0
            # whiteSpace is the space between any two elements
            whiteSpace = (width - currentWidth - 20) / (len(generation) - 1.0 or 2.0)
            for className in generation:
                cw = self.__getCurrentShape(className)
                cw.setPos(x, y)
                rect = cw.sceneBoundingRect()
                x = x + rect.width() + whiteSpace
            y = y + currentHeight + verticalWhiteSpace
            
    def __addLocalClass(self, className, _class, x, y, isRbModule=False):
        """
        Private method to add a class defined in the module.
        
        @param className name of the class to be as a dictionary key (string)
        @param _class class to be shown (ModuleParser.Class)
        @param x x-coordinate (float)
        @param y y-coordinate (float)
        @param isRbModule flag indicating a Ruby module (boolean)
        """
        meths = sorted(_class.methods.keys())
        attrs = sorted(_class.attributes.keys())
        name = _class.name
        if isRbModule:
            name = "{0} (Module)".format(name)
        cl = ClassModel(name, meths[:], attrs[:])
        cw = ClassItem(cl, False, x, y, noAttrs=self.noAttrs, scene=self.scene)
        self.allClasses[className] = cw
        
    def __addExternalClass(self, _class, x, y):
        """
        Private method to add a class defined outside the module.
        
        If the canvas is too small to take the shape, it
        is enlarged.
        
        @param _class class to be shown (string)
        @param x x-coordinate (float)
        @param y y-coordinate (float)
        """
        cl = ClassModel(_class)
        cw = ClassItem(cl, True, x, y, noAttrs=self.noAttrs, scene=self.scene)
        self.allClasses[_class] = cw
        
    def __createAssociations(self, routes):
        """
        Private method to generate the associations between the class shapes.
        
        @param routes list of relationsships
        """
        for route in routes:
            if len(route) > 1:
                assoc = AssociationItem(
                        self.__getCurrentShape(route[1]),
                        self.__getCurrentShape(route[0]),
                        Generalisation,
                        topToBottom=True)
                self.scene.addItem(assoc)
        
    def relayout(self):
        """
        Method to relayout the diagram.
        """
        self.allClasses.clear()
        self.__buildClasses()
