# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show SSL certificate infos.
"""

from PyQt4.QtGui import QDialog

from .Ui_SslInfoDialog import Ui_SslInfoDialog


class SslInfoDialog(QDialog, Ui_SslInfoDialog):
    """
    Class implementing a dialog to show SSL certificate infos.
    """
    def __init__(self, certificate, parent=None):
        """
        Constructor
        
        @param certificate reference to the SSL certificate (QSslCertificate)
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        self.sslWidget.showCertificate(certificate)
