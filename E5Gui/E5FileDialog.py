# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing alternative functions for the QFileDialog static methods
to cope with dustributor's usage of KDE wrapper dialogs for Qt file dialogs.
"""

from PyQt4.QtGui import QFileDialog

def __reorderFilter(filter, initialFilter = ""):
    """
    Private function to reorder the file filter to cope with a KDE issue introduced
    by distributor's usage of KDE file dialogs.
    
    @param filter Qt file filter (string)
    @param initialFilter initial filter (string)
    @return the rearranged Qt file filter (string)
    """
    if initialFilter:
        fileFilters = filter.split(';;')
        if len(fileFilters) < 10 and initialFilter in fileFilters:
            fileFilters.remove(initialFilter)
        fileFilters.insert(0, initialFilter)
        return ";;".join(fileFilters)
    else:
        return filter

def getOpenFileNameAndFilter(parent = None, caption = "", directory = "",
                             filter = "", initialFilter = "", 
                             options = QFileDialog.Options()):
    """
    Module function to get the name of a file for opening it and the selected
    file name filter.
    
    @param parent parent widget of the dialog (QWidget)
    @param caption window title of the dialog (string)
    @param directory working directory of the dialog (string)
    @param filter filter string for the dialog (string)
    @param initialFilter initial filter for the dialog (string)
    @param options various options for the dialog (QFileDialog.Options)
    @return name of file to be opened and selected filter (string, string)
    """
    newfilter = __reorderFilter(filter, initialFilter)
    return QFileDialog.getOpenFileNameAndFilter(parent, caption, directory, 
                                                newfilter, initialFilter, options)

def getOpenFileNamesAndFilter(parent = None, caption = "", directory = "",
                              filter = "", initialFilter = "", 
                              options = QFileDialog.Options()):
    """
    Module function to get a list of names of files for opening and the selected
    file name filter.
    
    @param parent parent widget of the dialog (QWidget)
    @param caption window title of the dialog (string)
    @param directory working directory of the dialog (string)
    @param filter filter string for the dialog (string)
    @param initialFilter initial filter for the dialog (string)
    @param options various options for the dialog (QFileDialog.Options)
    @return list of file names to be opened and selected filter 
        (list of string, string)
    """
    newfilter = __reorderFilter(filter, initialFilter)
    return QFileDialog.getOpenFileNamesAndFilter(parent, caption, directory, 
                                                newfilter, initialFilter, options)

def getSaveFileNameAndFilter(parent = None, caption = "", directory = "",
                             filter = "", initialFilter = "", 
                             options = QFileDialog.Options()):
    """
    Module function to get the name of a file for saving it and the selected
    file name filter.
    
    @param parent parent widget of the dialog (QWidget)
    @param caption window title of the dialog (string)
    @param directory working directory of the dialog (string)
    @param filter filter string for the dialog (string)
    @param initialFilter initial filter for the dialog (string)
    @param options various options for the dialog (QFileDialog.Options)
    @return name of file to be saved and selected filter (string, string)
    """
    newfilter = __reorderFilter(filter, initialFilter)
    return QFileDialog.getSaveFileNameAndFilter(parent, caption, directory, 
                                                newfilter, initialFilter, options)
