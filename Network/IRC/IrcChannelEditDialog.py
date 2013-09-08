# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to edit channel data.
"""

from __future__ import unicode_literals    # __IGNORE_WARNING__

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QDialog, QDialogButtonBox

from .Ui_IrcChannelEditDialog import Ui_IrcChannelEditDialog


class IrcChannelEditDialog(QDialog, Ui_IrcChannelEditDialog):
    """
    Class implementing a dialog to edit channel data.
    """
    def __init__(self, name, key, autoJoin, edit, parent=None):
        """
        Constructor
        
        @param name channel name (string)
        @param key channel key (string)
        @param autoJoin flag indicating, that the channel should
            be joined automatically (boolean)
        @param edit flag indicating an edit of an existing
            channel (boolean)
        @param parent reference to the parent widget (QWidget)
        """
        super(IrcChannelEditDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.nameEdit.setText(name)
        self.keyEdit.setText(key)
        self.autoJoinCheckBox.setChecked(autoJoin)
        
        self.nameEdit.setReadOnly(edit)
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(name != "")
    
    @pyqtSlot(str)
    def on_nameEdit_textChanged(self, txt):
        """
        Private slot to handle changes of the given name.
        """
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(txt != "")
    
    def getData(self):
        """
        Public method to get the channel data.
        
        @return tuple giving the channel name, channel key and a flag
            indicating, that the channel should be joined automatically
            (string, string, boolean)
        """
        return (self.nameEdit.text(),
                self.keyEdit.text(),
                self.autoJoinCheckBox.isChecked())
