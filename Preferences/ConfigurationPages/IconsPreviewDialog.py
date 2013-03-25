# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to preview the contents of an icon directory.
"""

from __future__ import unicode_literals    # __IGNORE_WARNING__

import os.path

from PyQt4.QtGui import QListWidgetItem, QDialog, QIcon
from PyQt4.QtCore import QDir

from .Ui_IconsPreviewDialog import Ui_IconsPreviewDialog


class IconsPreviewDialog(QDialog, Ui_IconsPreviewDialog):
    """
    Class implementing a dialog to preview the contents of an icon directory.
    """
    def __init__(self, parent, dirName):
        """
        Constructor
        
        @param parent parent widget (QWidget)
        @param dirName name of directory to show (string)
        """
        super(IconsPreviewDialog, self).__init__(parent)
        self.setupUi(self)
        
        dir = QDir(dirName)
        for icon in dir.entryList(["*.png"]):
            QListWidgetItem(QIcon(os.path.join(dirName, icon)),
                icon, self.iconView)
