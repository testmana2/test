# -*- coding: utf-8 -*-

# Copyright (c) 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to ask for a download action.
"""

from PyQt4.QtGui import QDialog

from .Ui_DownloadAskActionDialog import Ui_DownloadAskActionDialog

import Preferences


class DownloadAskActionDialog(QDialog, Ui_DownloadAskActionDialog):
    """
    Class implementing a dialog to ask for a download action.
    """
    def __init__(self, fileName, mimeType, baseUrl, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        self.infoLabel.setText("<b>{0}</b>".format(fileName))
        self.typeLabel.setText(mimeType)
        self.siteLabel.setText(baseUrl)
        
        if not Preferences.getHelp("VirusTotalEnabled") or \
           Preferences.getHelp("VirusTotalServiceKey") == "":
            self.scanButton.setHidden(True)
    
    def getAction(self):
        """
        Public method to get the selected action.
        
        @return selected action ("save", "open", "scan" or "cancel")
        """
        if self.openButton.isChecked():
            return "open"
        elif self.scanButton.isChecked():
            return "scan"
        elif self.saveButton.isChecked():
            return "save"
        else:
            # should not happen, but keep it safe
            return "cancel"
