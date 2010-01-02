# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a template viewer and associated classes.
"""

import datetime
import os
import sys
import re
import io

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from E4Gui.E4Application import e4App

from .TemplatePropertiesDialog import TemplatePropertiesDialog
from .TemplateMultipleVariablesDialog import TemplateMultipleVariablesDialog
from .TemplateSingleVariableDialog import TemplateSingleVariableDialog

import Preferences

from E4XML.XMLUtilities import make_parser
from E4XML.XMLErrorHandler import XMLErrorHandler, XMLFatalParseError
from E4XML.XMLEntityResolver import XMLEntityResolver
from E4XML.TemplatesHandler import TemplatesHandler
from E4XML.TemplatesWriter import TemplatesWriter

import UI.PixmapCache
import Utilities

from E4Gui.E4Application import e4App

class TemplateGroup(QTreeWidgetItem):
    """
    Class implementing a template group.
    """
    def __init__(self, parent, name, language = "All"):
        """
        Constructor
        
        @param parent parent widget of the template group (QWidget)
        @param name name of the group (string)
        @param language programming language for the group (string)
        """
        self.name = name
        self.language = language
        self.entries = {}
        
        QTreeWidgetItem.__init__(self, parent, [name])
        
        if Preferences.getTemplates("ShowTooltip"):
            self.setToolTip(0, language)
    
    def setName(self, name):
        """
        Public method to update the name of the group.
        
        @param name name of the group (string)
        """
        self.name = name
        self.setText(0, name)

    def getName(self):
        """
        Public method to get the name of the group.
        
        @return name of the group (string)
        """
        return self.name
        
    def setLanguage(self, language):
        """
        Public method to update the name of the group.
        
        @param language programming language for the group (string)
        """
        self.language = language
        if Preferences.getTemplates("ShowTooltip"):
            self.setToolTip(0, language)

    def getLanguage(self):
        """
        Public method to get the name of the group.
        
        @return language of the group (string)
        """
        return self.language
        
    def addEntry(self, name, description, template, quiet = False):
        """
        Public method to add a template entry to this group.
        
        @param name name of the entry (string)
        @param description description of the entry to add (string)
        @param template template text of the entry (string)
        @param quiet flag indicating quiet operation (boolean)
        """
        if name in self.entries:
            if not quiet:
                QMessageBox.critical(None,
                    QApplication.translate("TemplateGroup", "Add Template"),
                    QApplication.translate("TemplateGroup",
                                """<p>The group <b>{0}</b> already contains a"""
                                """ template named <b>{1}</b>.</p>""")\
                        .format(self.name, name))
            return
        
        self.entries[name] = TemplateEntry(self, name, description, template)
        
        if Preferences.getTemplates("AutoOpenGroups") and not self.isExpanded():
            self.setExpanded(True)
    
    def removeEntry(self, name):
        """
        Public method to remove a template entry from this group.
        
        @param name name of the entry to be removed (string)
        """
        if name in self.entries:
            index = self.indexOfChild(self.entries[name])
            self.takeChild(index)
            del self.entries[name]
            
            if len(self.entries) == 0:
                if Preferences.getTemplates("AutoOpenGroups") and self.isExpanded():
                    self.setExpanded(False)
    
    def removeAllEntries(self):
        """
        Public method to remove all template entries of this group.
        """
        for name in list(self.entries.keys())[:]:
            self.removeEntry(name)

    def hasEntry(self, name):
        """
        Public method to check, if the group has an entry with the given name.
        
        @param name name of the entry to check for (string)
        @return flag indicating existence (boolean)
        """
        return name in self.entries
    
    def getEntry(self, name):
        """
        Public method to get an entry.
        
        @param name name of the entry to retrieve (string)
        @return reference to the entry (TemplateEntry)
        """
        try:
            return self.entries[name]
        except KeyError:
            return None

    def getEntryNames(self, beginning):
        """
        Public method to get the names of all entries, who's name starts with the 
        given string.
        
        @param beginning string denoting the beginning of the template name
            (string)
        @return list of entry names found (list of strings)
        """
        names = []
        for name in self.entries:
            if name.startswith(beginning):
                names.append(name)
        
        return names

    def getAllEntries(self):
        """
        Public method to retrieve all entries.
        
        @return list of all entries (list of TemplateEntry)
        """
        return list(self.entries.values())

class TemplateEntry(QTreeWidgetItem):
    """
    Class immplementing a template entry.
    """
    def __init__(self, parent, name, description, templateText):
        """
        Constructor
        
        @param parent parent widget of the template entry (QWidget)
        @param name name of the entry (string)
        @param description descriptive text for the template (string)
        @param templateText text of the template entry (string)
        """
        self.name = name
        self.description = description
        self.template = templateText
        self.__extractVariables()
        
        QTreeWidgetItem.__init__(self, parent, [self.__displayText()])
        if Preferences.getTemplates("ShowTooltip"):
            self.setToolTip(0, self.template)

    def __displayText(self):
        """
        Private method to generate the display text.
        
        @return display text (string)
        """
        if self.description:
            txt = "{0} - {1}".format(self.name, self.description)
        else:
            txt = self.name
        return txt
    
    def setName(self, name):
        """
        Public method to update the name of the entry.
        
        @param name name of the entry (string)
        """
        self.name = name
        self.setText(0, self.__displayText())

    def getName(self):
        """
        Public method to get the name of the entry.
        
        @return name of the entry (string)
        """
        return self.name

    def setDescription(self, description):
        """
        Public method to update the description of the entry.
        
        @param description description of the entry (string)
        """
        self.description = description
        self.setText(0, self.__displayText())

    def getDescription(self):
        """
        Public method to get the description of the entry.
        
        @return description of the entry (string)
        """
        return self.description

    def getGroupName(self):
        """
        Public method to get the name of the group this entry belongs to.
        
        @return name of the group containing this entry (string)
        """
        return self.parent().getName()
        
    def setTemplateText(self, templateText):
        """
        Public method to update the template text.
        
        @param templateText text of the template entry (string)
        """
        self.template = templateText
        self.__extractVariables()
        if Preferences.getTemplates("ShowTooltip"):
            self.setToolTip(0, self.template)

    def getTemplateText(self):
        """
        Public method to get the template text.
        
        @return the template text (string)
        """
        return self.template

    def getExpandedText(self, varDict, indent):
        """
        Public method to get the template text with all variables expanded.
        
        @param varDict dictionary containing the texts of each variable
            with the variable name as key.
        @param indent indentation of the line receiving he expanded 
            template text (string)
        @return a tuple of the expanded template text (string), the
            number of lines (integer) and the length of the last line (integer)
        """
        txt = self.template
        for var, val in list(varDict.items()):
            if var in self.formatedVariables:
                txt = self.__expandFormattedVariable(var, val, txt)
            else:
                txt = txt.replace(var, val)
        sepchar = Preferences.getTemplates("SeparatorChar")
        txt = txt.replace("%s%s" % (sepchar, sepchar), sepchar)
        prefix = "%s%s" % (os.linesep, indent)
        trailingEol = txt.endswith(os.linesep)
        lines = txt.splitlines()
        lineCount = len(lines)
        lineLen = len(lines[-1])
        txt = prefix.join(lines).lstrip()
        if trailingEol:
            txt = "%s%s" % (txt, os.linesep)
            lineCount += 1
            lineLen = 0
        return txt, lineCount, lineLen

    def __expandFormattedVariable(self, var, val, txt):
        """
        Private method to expand a template variable with special formatting.
        
        @param var template variable name (string)
        @param val value of the template variable (string)
        @param txt template text (string)
        """
        t = ""
        for line in txt.splitlines():
            ind = line.find(var)
            if ind >= 0:
                format = var[1:-1].split(':', 1)[1]
                if format == 'rl':
                    prefix = line[:ind]
                    postfix = line [ind + len(var):]
                    for v in val.splitlines():
                        t = "%s%s%s%s%s" % (t, os.linesep, prefix, v, postfix)
                elif format == 'ml':
                    indent = line.replace(line.lstrip(), "")
                    prefix = line[:ind]
                    postfix = line[ind + len(var):]
                    count = 0
                    for v in val.splitlines():
                        if count:
                            t = "%s%s%s%s" % (t, os.linesep, indent, v)
                        else:
                            t = "%s%s%s%s" % (t, os.linesep, prefix, v)
                        count += 1
                    t = "%s%s" % (t, postfix)
                else:
                    t = "%s%s%s" % (t, os.linesep, line)
            else:
                t = "%s%s%s" % (t, os.linesep, line)
        return "".join(t.splitlines(1)[1:])

    def getVariables(self):
        """
        Public method to get the list of variables.
        
        @return list of variables (list of strings)
        """
        return self.variables

    def __extractVariables(self):
        """
        Private method to retrieve the list of variables.
        """
        sepchar = Preferences.getTemplates("SeparatorChar")
        variablesPattern = \
            re.compile(r"""\%s[a-zA-Z][a-zA-Z0-9_]*(?::(?:ml|rl))?\%s""" % \
                       (sepchar, sepchar))
        variables = variablesPattern.findall(self.template)
        self.variables = []
        self.formatedVariables = []
        for var in variables:
            if not var in self.variables:
                self.variables.append(var)
            if var.find(':') >= 0 and not var in self.formatedVariables:
                self.formatedVariables.append(var)

class TemplateViewer(QTreeWidget):
    """
    Class implementing the template viewer.
    """
    def __init__(self, parent, viewmanager):
        """
        Constructor
        
        @param parent the parent (QWidget)
        @param viewmanager reference to the viewmanager object
        """
        QTreeWidget.__init__(self, parent)
        
        self.viewmanager = viewmanager
        self.groups = {}
        
        self.setHeaderLabels(["Template"])
        self.header().hide()
        self.header().setSortIndicator(0, Qt.AscendingOrder)
        self.setRootIsDecorated(True)
        self.setAlternatingRowColors(True)
        
        self.__menu = QMenu(self)
        self.applyAct = \
            self.__menu.addAction(self.trUtf8("Apply"), self.__templateItemActivated)
        self.__menu.addSeparator()
        self.__menu.addAction(self.trUtf8("Add entry..."), self.__addEntry)
        self.__menu.addAction(self.trUtf8("Add group..."), self.__addGroup)
        self.__menu.addAction(self.trUtf8("Edit..."), self.__edit)
        self.__menu.addAction(self.trUtf8("Remove"), self.__remove)
        self.__menu.addSeparator()
        self.__menu.addAction(self.trUtf8("Save"), self.__save)
        self.__menu.addAction(self.trUtf8("Import..."), self.__import)
        self.__menu.addAction(self.trUtf8("Export..."), self.__export)
        self.__menu.addSeparator()
        self.__menu.addAction(self.trUtf8("Help about Templates..."), self.__showHelp)
        self.__menu.addSeparator()
        self.__menu.addAction(self.trUtf8("Configure..."), self.__configure)
        
        self.__backMenu = QMenu(self)
        self.__backMenu.addAction(self.trUtf8("Add group..."), self.__addGroup)
        self.__backMenu.addSeparator()
        self.__backMenu.addAction(self.trUtf8("Save"), self.__save)
        self.__backMenu.addAction(self.trUtf8("Import..."), self.__import)
        self.__backMenu.addAction(self.trUtf8("Export..."), self.__export)
        self.__backMenu.addSeparator()
        self.__backMenu.addAction(self.trUtf8("Help about Templates..."), self.__showHelp)
        self.__backMenu.addSeparator()
        self.__backMenu.addAction(self.trUtf8("Configure..."), self.__configure)
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.connect(self, SIGNAL("customContextMenuRequested(const QPoint &)"),
                     self.__showContextMenu)
        self.connect(self, SIGNAL("itemActivated(QTreeWidgetItem *, int)"),
                     self.__templateItemActivated)
        
        self.setWindowIcon(UI.PixmapCache.getIcon("eric.png"))
        
    def __resort(self):
        """
        Private method to resort the tree.
        """
        self.sortItems(self.sortColumn(), self.header().sortIndicatorOrder())
        
    def __templateItemActivated(self, itm = None, col = 0):
        """
        Private slot to handle the activation of an item. 
        
        @param itm reference to the activated item (QTreeWidgetItem)
        @param col column the item was activated in (integer)
        """
        itm = self.currentItem()
        if isinstance(itm, TemplateEntry):
            self.applyTemplate(itm)
        
    def __showContextMenu(self, coord):
        """
        Private slot to show the context menu of the list.
        
        @param coord the position of the mouse pointer (QPoint)
        """
        itm = self.itemAt(coord)
        coord = self.mapToGlobal(coord)
        if itm is None:
            self.__backMenu.popup(coord)
        else:
            self.applyAct.setEnabled(self.viewmanager.activeWindow() is not None)
            self.__menu.popup(coord)
    
    def __addEntry(self):
        """
        Private slot to handle the Add Entry context menu action.
        """
        itm = self.currentItem()
        if isinstance(itm, TemplateGroup):
            groupName = itm.getName()
        else:
            groupName = itm.getGroupName()
        
        dlg = TemplatePropertiesDialog(self)
        dlg.setSelectedGroup(groupName)
        if dlg.exec_() == QDialog.Accepted:
            name, description, groupName, template = dlg.getData()
            self.addEntry(groupName, name, description, template)
        
    def __addGroup(self):
        """
        Private slot to handle the Add Group context menu action.
        """
        dlg = TemplatePropertiesDialog(self, True)
        if dlg.exec_() == QDialog.Accepted:
            name, language = dlg.getData()
            self.addGroup(name, language)
        
    def __edit(self):
        """
        Private slot to handle the Edit context menu action.
        """
        itm = self.currentItem()
        if isinstance(itm, TemplateEntry):
            editGroup = False
        else:
            editGroup = True
        dlg = TemplatePropertiesDialog(self, editGroup, itm)
        if dlg.exec_() == QDialog.Accepted:
            if editGroup:
                name, language = dlg.getData()
                self.changeGroup(itm.getName(), name, language)
            else:
                name, description, groupName, template = dlg.getData()
                self.changeEntry(itm, name, groupName, description, template)
        
    def __remove(self):
        """
        Private slot to handle the Remove context menu action.
        """
        itm = self.currentItem()
        res = QMessageBox.question(self,
            self.trUtf8("Remove Template"),
            self.trUtf8("""<p>Do you really want to remove <b>{0}</b>?</p>""")\
                .format(itm.getName()),
            QMessageBox.StandardButtons(\
                QMessageBox.No | \
                QMessageBox.Yes),
            QMessageBox.No)
        if res != QMessageBox.Yes:
            return

        if isinstance(itm, TemplateGroup):
            self.removeGroup(itm)
        else:
            self.removeEntry(itm)

    def __save(self):
        """
        Private slot to handle the Save context menu action.
        """
        self.writeTemplates()

    def __import(self):
        """
        Private slot to handle the Import context menu action.
        """
        fn = QFileDialog.getOpenFileName(\
            self,
            self.trUtf8("Import Templates"),
            "",
            self.trUtf8("Templates Files (*.e4c);; All Files (*)"))
        
        if fn:
            self.readTemplates(fn)

    def __export(self):
        """
        Private slot to handle the Export context menu action.
        """
        fn, selectedFilter = QFileDialog.getSaveFileNameAndFilter(\
            self,
            self.trUtf8("Export Templates"),
            "",
            self.trUtf8("Templates Files (*.e4c);; All Files (*)"),
            "",
            QFileDialog.Options(QFileDialog.DontConfirmOverwrite))
        
        if fn:
            ext = QFileInfo(fn).suffix()
            if not ext:
                ex = selectedFilter.split("(*")[1].split(")")[0]
                if ex:
                    fn += ex
            self.writeTemplates(fn)

    def __showHelp(self):
        """
        Private method to show some help.
        """
        QMessageBox.information(self,
            self.trUtf8("Template Help"),
            self.trUtf8("""<p><b>Template groups</b> are a means of grouping individual"""
                        """ templates. Groups have an attribute that specifies,"""
                        """ which programming language they apply for."""
                        """ In order to add template entries, at least one group"""
                        """ has to be defined.</p>"""
                        """<p><b>Template entries</b> are the actual templates."""
                        """ They are grouped by the template groups. Help about"""
                        """ how to define them is available in the template edit"""
                        """ dialog. There is an example template available in the"""
                        """ Examples subdirectory of the eric5 distribution.</p>"""))

    def __getPredefinedVars(self):
        """
        Private method to return predefined variables.
        
        @return dictionary of predefined variables and their values
        """
        project = e4App().getObject("Project")
        editor = self.viewmanager.activeWindow()
        today = datetime.datetime.now().date()
        sepchar = Preferences.getTemplates("SeparatorChar")
        if sepchar == '%':
            sepchar = '%%'
        keyfmt = sepchar + "%s" + sepchar
        varValues = {keyfmt % 'date': today.isoformat(),
                     keyfmt % 'year': str(today.year)}

        if project.name:
            varValues[keyfmt % 'project_name'] = project.name

        path_name = editor.getFileName()
        if path_name:
            dir_name, file_name = os.path.split(path_name)
            base_name, ext = os.path.splitext(file_name)
            if ext:
                ext = ext[1:]
            varValues.update({
                    keyfmt % 'path_name': path_name,
                    keyfmt % 'dir_name': dir_name,
                    keyfmt % 'file_name': file_name,
                    keyfmt % 'base_name': base_name,
                    keyfmt % 'ext': ext
            })
        return varValues

    def applyTemplate(self, itm):
        """
        Public method to apply the template.
        
        @param itm reference to the template item to apply (TemplateEntry)
        """
        editor = self.viewmanager.activeWindow()
        if editor is None:
            return
        
        ok = False
        vars = itm.getVariables()
        varValues = self.__getPredefinedVars()
        
        # Remove predefined variables from list so user doesn't have to fill
        # these values out in the dialog.
        for v in list(varValues.keys()):
            if v in vars:
                vars.remove(v)
        
        if vars:
            if Preferences.getTemplates("SingleDialog"):
                dlg = TemplateMultipleVariablesDialog(vars, self)
                if dlg.exec_() == QDialog.Accepted:
                    varValues.update(dlg.getVariables())
                    ok = True
            else:
                for var in vars:
                    dlg = TemplateSingleVariableDialog(var, self)
                    if dlg.exec_() == QDialog.Accepted:
                        varValues[var] = dlg.getVariable()
                    else:
                        return
                    del dlg
                ok = True
        else:
            ok = True
        
        if ok:
            line = editor.text(editor.getCursorPosition()[0])\
                   .replace(os.linesep, "")
            indent = line.replace(line.lstrip(), "")
            txt, lines, count = itm.getExpandedText(varValues, indent)
            # It should be done in this way to allow undo
            editor.beginUndoAction()
            if editor.hasSelectedText():
                editor.removeSelectedText()
            line, index = editor.getCursorPosition()
            editor.insert(txt)
            editor.setCursorPosition(line + lines - 1, 
                count and index + count or 0)
            editor.endUndoAction()
            editor.setFocus()

    def applyNamedTemplate(self, templateName):
        """
        Public method to apply a template given a template name.
        
        @param templateName name of the template item to apply (string)
        """
        for group in list(self.groups.values()):
            template = group.getEntry(templateName)
            if template is not None:
                self.applyTemplate(template)
                break
    
    def addEntry(self, groupName, name, description, template, quiet = False):
        """
        Public method to add a template entry.
        
        @param groupName name of the group to add to (string)
        @param name name of the entry to add (string)
        @param description description of the entry to add (string)
        @param template template text of the entry (string)
        @param quiet flag indicating quiet operation (boolean)
        """
        self.groups[groupName].addEntry(name, description, template, quiet = quiet)
        self.__resort()
        
    def addGroup(self, name, language = "All"):
        """
        Public method to add a group.
        
        @param name name of the group to be added (string)
        @param language programming language for the group (string)
        """
        if name not in self.groups:
            self.groups[name] = TemplateGroup(self, name, language)
        self.__resort()

    def changeGroup(self, oldname, newname, language = "All"):
        """
        Public method to rename a group.
        
        @param oldname old name of the group (string)
        @param newname new name of the group (string)
        @param language programming language for the group (string)
        """
        if oldname != newname:
            if newname in self.groups:
                QMessageBox.warning(self,
                    self.trUtf8("Edit Template Group"),
                    self.trUtf8("""<p>A template group with the name"""
                                """ <b>{0}</b> already exists.</p>""")\
                        .format(newname))
                return
            
            self.groups[newname] = self.groups[oldname]
            del self.groups[oldname]
            self.groups[newname].setName(newname)
        
        self.groups[newname].setLanguage(language)
        self.__resort()

    def getAllGroups(self):
        """
        Public method to get all groups.
        
        @return list of all groups (list of TemplateGroup)
        """
        return list(self.groups.values())
    
    def getGroupNames(self):
        """
        Public method to get all group names.
        
        @return list of all group names (list of strings)
        """
        groups = sorted(list(self.groups.keys())[:])
        return groups

    def removeGroup(self, itm):
        """
        Public method to remove a group.
        
        @param itm template group to be removed (TemplateGroup)
        """
        name = itm.getName()
        itm.removeAllEntries()
        index = self.indexOfTopLevelItem(itm)
        self.takeTopLevelItem(index)
        del self.groups[name]

    def removeEntry(self, itm):
        """
        Public method to remove a template entry.
        
        @param itm template entry to be removed (TemplateEntry)
        """
        groupName = itm.getGroupName()
        self.groups[groupName].removeEntry(itm.getName())

    def changeEntry(self, itm, name, groupName, description, template):
        """
        Public method to change a template entry.
        
        @param itm template entry to be changed (TemplateEntry)
        @param name new name for the entry (string)
        @param groupName name of the group the entry should belong to
            (string)
        @param description description of the entry (string)
        @param template template text of the entry (string)
        """
        if itm.getGroupName() != groupName:
            # move entry to another group
            self.groups[itm.getGroupName()].removeEntry(itm.getName())
            self.groups[groupName].addEntry(name, description, template)
            return
        
        if itm.getName() != name:
            # entry was renamed
            self.groups[groupName].removeEntry(itm.getName())
            self.groups[groupName].addEntry(name, description, template)
            return
        
        tmpl = self.groups[groupName].getEntry(name)
        tmpl.setDescription(description)
        tmpl.setTemplateText(template)
        self.__resort()

    def writeTemplates(self, filename = None):
        """
        Public method to write the templates data to an XML file (.e4c).
        
        @param filename name of a templates file to read (string)
        """
        try:
            if filename is None:
                filename = os.path.join(Utilities.getConfigDir(), "eric5templates.e4c")
            f = open(filename, "w")
            
            TemplatesWriter(f, self).writeXML()
            
            f.close()
        except IOError:
            QMessageBox.critical(None,
                self.trUtf8("Save templates"),
                self.trUtf8("<p>The templates file <b>{0}</b> could not be written.</p>")
                    .format(filename))
        
    def readTemplates(self, filename = None):
        """
        Public method to read in the templates file (.e4c)
        
        @param filename name of a templates file to read (string)
        """
        try:
            if filename is None:
                filename = os.path.join(Utilities.getConfigDir(), "eric5templates.e4c")
                if not os.path.exists(filename):
                    return
            f = open(filename, "r")
            line = f.readline()
            dtdLine = f.readline()
            f.close()
        except IOError:
            QMessageBox.critical(None,
                self.trUtf8("Read templates"),
                self.trUtf8("<p>The templates file <b>{0}</b> could not be read.</p>")
                    .format(filename))
            return
            
        # now read the file
        if line.startswith('<?xml'):
            parser = make_parser(dtdLine.startswith("<!DOCTYPE"))
            handler = TemplatesHandler(templateViewer = self)
            er = XMLEntityResolver()
            eh = XMLErrorHandler()
            
            parser.setContentHandler(handler)
            parser.setEntityResolver(er)
            parser.setErrorHandler(eh)
            
            try:
                f = open(filename, "r")
                try:
                    try:
                        parser.parse(f)
                    except UnicodeEncodeError:
                        f.seek(0)
                        buf = io.StringIO(f.read())
                        parser.parse(buf)
                finally:
                    f.close()
            except IOError:
                QMessageBox.critical(None,
                    self.trUtf8("Read templates"),
                    self.trUtf8("<p>The templates file <b>{0}</b> could not be read.</p>")
                        .format(filename))
                return
            except XMLFatalParseError:
                pass
                
            eh.showParseMessages()
        else:
            QMessageBox.critical(None,
                self.trUtf8("Read templates"),
                self.trUtf8("<p>The templates file <b>{0}</b> has an"
                            " unsupported format.</p>")
                    .format(filename))
    
    def __configure(self):
        """
        Private method to open the configuration dialog.
        """
        e4App().getObject("UserInterface").showPreferences("templatesPage")
    
    def hasTemplate(self, entryName):
        """
        Public method to check, if an entry of the given name exists.
        
        @param entryName name of the entry to check for (string)
        @return flag indicating the existence (boolean)
        """
        for group in list(self.groups.values()):
            if group.hasEntry(entryName):
                return True
        
        return False
    
    def getTemplateNames(self, start):
        """
        Public method to get the names of templates starting with the given string.
        
        @param start start string of the name (string)
        @return sorted list of matching template names (list of strings)
        """
        names = []
        for group in list(self.groups.values()):
            names.extend(group.getEntryNames(start))
        return sorted(names)
