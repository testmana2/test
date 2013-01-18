# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show SSL certificate infos.
"""

from PyQt4.QtGui import QDialog

from .Ui_E5SslInfoDialog import Ui_E5SslInfoDialog


class E5SslInfoDialog(QDialog, Ui_E5SslInfoDialog):
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
