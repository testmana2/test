# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing QMessageBox replacements and more convenience function.
"""

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QMessageBox, QApplication

def information(parent, title, text, 
                buttons = QMessageBox.Ok, defaultButton = QMessageBox.NoButton):
    """
    Function to show a modal information message box.
    
    @param parent parent widget of the message box
    @param title caption of the message box
    @param text text to be shown by the message box
    @param buttons flags indicating which buttons to show 
        (QMessageBox.StandardButtons)
    @param defaultButton flag indicating the default button
        (QMessageBox.StandardButton)
    @return button pressed by the user 
        (QMessageBox.StandardButton)
    """
    messageBox = QMessageBox(parent)
    messageBox.setIcon(QMessageBox.Information)
    if parent is not None:
        messageBox.setWindowModality(Qt.WindowModal)
    messageBox.setWindowTitle("{0} - {1}".format(
        QApplication.applicationName(), title))
    messageBox.setText(text)
    messageBox.setStandardButtons(buttons)
    messageBox.setDefaultButton(defaultButton)
    messageBox.exec_()
    clickedButton = messageBox.clickedButton()
    if clickedButton is None:
        return QMessageBox.NoButton
    else:
        return messageBox.standardButton(clickedButton)
