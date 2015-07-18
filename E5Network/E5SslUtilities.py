# -*- coding: utf-8 -*-

# Copyright (c) 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing SSL utility functions.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import qVersion

def initSSL():
    """
    Function to initialize some global SSL stuff.
    """
    if qVersion() < "5.3.0":
        # Qt 5.3.0 and newer don't use weak ciphers anymore
        try:
            from PyQt5.QtNetwork import QSslSocket
        except ImportError:
            # no SSL available, so there is nothing to initialize
            return
        
        strongCiphers = [c for c in QSslSocket.supportedCiphers()
                         if c.usedBits() >= 128]
        QSslSocket.setDefaultCiphers(strongCiphers)
