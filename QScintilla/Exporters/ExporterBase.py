# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the exporter base class.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import Utilities

class ExporterBase(QObject):
    """
    Class implementing the exporter base class.
    """
    def __init__(self, editor, parent = None):
        """
        Constructor
        
        @param editor reference to the editor object (QScintilla.Editor.Editor)
        @param parent parent object of the exporter (QObject)
        """
        QObject.__init__(self, parent)
        self.editor = editor
    
    def _getFileName(self, filter):
        """
        Protected method to get the file name of the export file from the user.
        
        @param filter the filter string to be used (string). The filter for
            "All Files (*)" is appended by this method.
        """
        filter_ = filter
        filter_ += ";;"
        filter_ += QApplication.translate('Exporter', "All Files (*)")
        fn, selectedFilter = QFileDialog.getSaveFileNameAndFilter(
            self.editor,
            self.trUtf8("Export source"),
            "",
            filter_,
            "",
            QFileDialog.Options(QFileDialog.DontConfirmOverwrite))
        
        if fn:
            ext = QFileInfo(fn).suffix()
            if not ext:
                ex = selectedFilter.split("(*")[1].split(")")[0]
                if ex:
                    fileName += ex
            if QFileInfo(fn).exists():
                res = QMessageBox.warning(self.editor,
                    self.trUtf8("Export source"),
                    self.trUtf8("<p>The file <b>{0}</b> already exists.</p>")
                        .format(fn),
                    QMessageBox.StandardButtons(\
                        QMessageBox.Abort | \
                        QMessageBox.Save),
                    QMessageBox.Abort)
                if res == QMessageBox.Abort or res == QMessageBox.Cancel:
                    return ""
            
            fn = Utilities.toNativeSeparators(fn)
        
        return fn
    
    def exportSource(self):
        """
        Public method performing the export.
        
        This method must be overridden by the real exporters.
        """
        raise NotImplementedError
