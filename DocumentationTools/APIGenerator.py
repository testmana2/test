# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the builtin API generator.
"""


from __future__ import unicode_literals


class APIGenerator(object):
    """
    Class implementing the builtin documentation generator.
    """
    def __init__(self, module):
        """
        Constructor
        
        @param module The information of the parsed Python file.
        """
        self.module = module
        
    def genAPI(self, newStyle, basePackage, includePrivate):
        """
        Public method to generate the API information.
        
        @param newStyle flag indicating the api generation for QScintilla 1.7
            and newer (boolean) (ignored)
        @param basePackage name of the base package (string)
        @param includePrivate flag indicating to include
            private methods/functions (boolean)
        @return API information (list of strings)
        """
        self.includePrivate = includePrivate
        modulePath = self.module.name.split('.')
        if modulePath[-1] == '__init__':
            del modulePath[-1]
        if basePackage:
            modulePath[0] = basePackage
        self.moduleName = "{0}.".format('.'.join(modulePath))
        self.api = []
        self.__addGlobalsAPI()
        self.__addClassesAPI()
        self.__addFunctionsAPI()
        return self.api
        
    def genBases(self, includePrivate):
        """
        Public method to generate the base classes information.
        
        @param includePrivate flag indicating to include private classes
            (boolean)
        @return base classes information (dictionary of list of strings)
        """
        bases = {}
        self.includePrivate = includePrivate
        classNames = sorted(list(self.module.classes.keys()))
        for className in classNames:
            if not self.__isPrivate(self.module.classes[className]):
                if className not in bases:
                    bases[className] = [
                        b for b in self.module.classes[className].super
                        if b != "object"]
        return bases
        
    def __isPrivate(self, obj):
        """
        Private method to check, if an object is considered private.
        
        @param obj reference to the object to be checked
        @return flag indicating, that object is considered private (boolean)
        """
        private = obj.isPrivate() and not self.includePrivate
        return private
        
    def __addGlobalsAPI(self):
        """
        Private method to generate the api section for global variables.
        """
        from QScintilla.Editor import Editor
        
        moduleNameStr = "{0}".format(self.moduleName)
        
        for globalName in sorted(self.module.globals.keys()):
            if not self.__isPrivate(self.module.globals[globalName]):
                if self.module.globals[globalName].isPublic():
                    id = Editor.AttributeID
                elif self.module.globals[globalName].isProtected():
                    id = Editor.AttributeProtectedID
                else:
                    id = Editor.AttributePrivateID
                self.api.append("{0}{1}?{2:d}".format(
                    moduleNameStr, globalName, id))
        
    def __addClassesAPI(self):
        """
        Private method to generate the api section for classes.
        """
        classNames = sorted(list(self.module.classes.keys()))
        for className in classNames:
            if not self.__isPrivate(self.module.classes[className]):
                self.__addClassVariablesAPI(className)
                self.__addMethodsAPI(className)
        
    def __addMethodsAPI(self, className):
        """
        Private method to generate the api section for class methods.
        
        @param className name of the class containing the method (string)
        """
        from QScintilla.Editor import Editor
        
        _class = self.module.classes[className]
        methods = sorted(list(_class.methods.keys()))
        if '__init__' in methods:
            methods.remove('__init__')
            if _class.isPublic():
                id = Editor.ClassID
            elif _class.isProtected():
                id = Editor.ClassProtectedID
            else:
                id = Editor.ClassPrivateID
            self.api.append(
                '{0}{1}?{2:d}({3})'.format(
                    self.moduleName, _class.name, id,
                    ', '.join(_class.methods['__init__'].parameters[1:])))
            
        classNameStr = "{0}{1}.".format(self.moduleName, className)
        for method in methods:
            if not self.__isPrivate(_class.methods[method]):
                if _class.methods[method].isPublic():
                    id = Editor.MethodID
                elif _class.methods[method].isProtected():
                    id = Editor.MethodProtectedID
                else:
                    id = Editor.MethodPrivateID
                self.api.append(
                    '{0}{1}?{2:d}({3})'.format(
                        classNameStr, method, id,
                        ', '.join(_class.methods[method].parameters[1:])))
        
    def __addClassVariablesAPI(self, className):
        """
        Private method to generate class api section for class variables.
        
        @param className name of the class containing the class variables
            (string)
        """
        from QScintilla.Editor import Editor
        
        _class = self.module.classes[className]
        classNameStr = "{0}{1}.".format(self.moduleName, className)
        for variable in sorted(_class.globals.keys()):
            if not self.__isPrivate(_class.globals[variable]):
                if _class.globals[variable].isPublic():
                    id = Editor.AttributeID
                elif _class.globals[variable].isProtected():
                    id = Editor.AttributeProtectedID
                else:
                    id = Editor.AttributePrivateID
                self.api.append('{0}{1}?{2:d}'.format(
                    classNameStr, variable, id))
        
    def __addFunctionsAPI(self):
        """
        Private method to generate the api section for functions.
        """
        from QScintilla.Editor import Editor
        
        funcNames = sorted(list(self.module.functions.keys()))
        for funcName in funcNames:
            if not self.__isPrivate(self.module.functions[funcName]):
                if self.module.functions[funcName].isPublic():
                    id = Editor.MethodID
                elif self.module.functions[funcName].isProtected():
                    id = Editor.MethodProtectedID
                else:
                    id = Editor.MethodPrivateID
                self.api.append(
                    '{0}{1}?{2:d}({3})'.format(
                        self.moduleName, self.module.functions[funcName].name,
                        id,
                        ', '.join(self.module.functions[funcName].parameters)))
