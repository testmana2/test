# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing QMessageBox replacements and more convenience function.
"""

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QMessageBox, QApplication

def __messageBox(parent, title, text, icon, 
                 buttons = QMessageBox.Ok, defaultButton = QMessageBox.NoButton):
    """
    Private module function to show a modal message box.
    
    @param parent parent widget of the message box (QWidget)
    @param title caption of the message box (string)
    @param text text to be shown by the message box (string)
    @param icon type of icon to be shown (QMessageBox.Icon)
    @param buttons flags indicating which buttons to show 
        (QMessageBox.StandardButtons)
    @param defaultButton flag indicating the default button
        (QMessageBox.StandardButton)
    @return button pressed by the user 
        (QMessageBox.StandardButton)
    """
    messageBox = QMessageBox(parent)
    messageBox.setIcon(icon)
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

# the about functions are here for consistancy
about = QMessageBox.about
aboutQt = QMessageBox.aboutQt

def critical(parent, title, text, 
             buttons = QMessageBox.Ok, defaultButton = QMessageBox.NoButton):
    """
    Function to show a modal critical message box.
    
    @param parent parent widget of the message box (QWidget)
    @param title caption of the message box (string)
    @param text text to be shown by the message box (string)
    @param buttons flags indicating which buttons to show 
        (QMessageBox.StandardButtons)
    @param defaultButton flag indicating the default button
        (QMessageBox.StandardButton)
    @return button pressed by the user 
        (QMessageBox.StandardButton)
    """
    return __messageBox(parent, title, text, QMessageBox.Critical, 
                        buttons, defaultButton)

def information(parent, title, text, 
                buttons = QMessageBox.Ok, defaultButton = QMessageBox.NoButton):
    """
    Function to show a modal information message box.
    
    @param parent parent widget of the message box (QWidget)
    @param title caption of the message box (string)
    @param text text to be shown by the message box (string)
    @param buttons flags indicating which buttons to show 
        (QMessageBox.StandardButtons)
    @param defaultButton flag indicating the default button
        (QMessageBox.StandardButton)
    @return button pressed by the user 
        (QMessageBox.StandardButton)
    """
    return __messageBox(parent, title, text, QMessageBox.Information, 
                        buttons, defaultButton)

def question(parent, title, text, 
             buttons = QMessageBox.Ok, defaultButton = QMessageBox.NoButton):
    """
    Function to show a modal question message box.
    
    @param parent parent widget of the message box (QWidget)
    @param title caption of the message box (string)
    @param text text to be shown by the message box (string)
    @param buttons flags indicating which buttons to show 
        (QMessageBox.StandardButtons)
    @param defaultButton flag indicating the default button
        (QMessageBox.StandardButton)
    @return button pressed by the user 
        (QMessageBox.StandardButton)
    """
    return __messageBox(parent, title, text, QMessageBox.Question, 
                        buttons, defaultButton)

def warning(parent, title, text, 
            buttons = QMessageBox.Ok, defaultButton = QMessageBox.NoButton):
    """
    Function to show a modal warning message box.
    
    @param parent parent widget of the message box (QWidget)
    @param title caption of the message box (string)
    @param text text to be shown by the message box (string)
    @param buttons flags indicating which buttons to show 
        (QMessageBox.StandardButtons)
    @param defaultButton flag indicating the default button
        (QMessageBox.StandardButton)
    @return button pressed by the user 
        (QMessageBox.StandardButton)
    """
    return __messageBox(parent, title, text, QMessageBox.Warning, 
                        buttons, defaultButton)

Critical    = 0
Information = 1
Question    = 2
Warning     = 3

def yesNo(parent, title, text, type_ = Question, yesDefault = False):
    """
    Function to show a model yes/no message box.
    
    @param parent parent widget of the message box (QWidget)
    @param title caption of the message box (string)
    @param text text to be shown by the message box (string)
    @keyparam type_ type of the dialog (Critical, Information, Question or Warning)
    @keyparam yesDefault flag indicating that the Yes button should be the default
        button (boolean)
    @return flag indicating the selection of the Yes button (boolean)
    """
    assert type_ in [Critical, Information, Question, Warning]
    
    if type_ == Question:
        icon = QMessageBox.Question
    elif type_ == Warning:
        icon = QMessageBox.Warning
    elif type_ == Critical:        
        icon = QMessageBox.Critical
    elif type_ == Information:
        icon = QMessageBox.Information
    
    res = __messageBox(parent, title, text, icon, 
                       QMessageBox.StandardButtons(QMessageBox.Yes | QMessageBox.No), 
                       yesDefault and QMessageBox.Yes or QMessageBox.No)
    return res == QMessageBox.Yes
