# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show and edit all certificates.
"""

from PyQt4.QtCore import pyqtSlot, Qt
from PyQt4.QtGui import QDialog, QTreeWidgetItem
try:
    from PyQt4.QtNetwork import QSslCertificate
except ImportError:
    pass

from .Ui_SslCertificatesDialog import Ui_SslCertificatesDialog

from .SslInfoDialog import SslInfoDialog

import Preferences

class SslCertificatesDialog(QDialog, Ui_SslCertificatesDialog):
    """
    Class implementing a dialog to show and edit all certificates.
    """
    CertRole = Qt.UserRole + 1
    
    def __init__(self, parent = None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        
        self.__populateServerCertificatesTree()
    
    def __populateServerCertificatesTree(self):
        """
        Private slot to populate the server certificates tree.
        """
        certificateDict = Preferences.toDict(
                Preferences.Prefs.settings.value("Help/CaCertificatesDict"))
        for server in certificateDict:
            for cert in QSslCertificate.fromData(certificateDict[server]):
                self.__createCertificateEntry(self.serversCertificatesTree, server, cert)
        
        self.serversCertificatesTree.expandAll()
        for i in range(self.serversCertificatesTree.columnCount()):
            self.serversCertificatesTree.resizeColumnToContents(i)
    
    def __createCertificateEntry(self, tree, server, cert):
        """
        Private method to create a certificate entry.
        
        @param tree reference to the tree to insert the certificate (QTreeWidget)
        @param server server name of the certificate (string)
        @param cert certificate to insert (QSslCertificate)
        """
        # step 1: extract the info to be shown
        organisation = cert.subjectInfo(QSslCertificate.Organization)
        if organisation is None or organisation == "":
            organisation = self.trUtf8("(Unknown)")
        commonName = cert.subjectInfo(QSslCertificate.CommonName)
        if commonName is None or commonName == "":
            commonName = self.trUtf8("(Unknown common name)")
        expiryDate = cert.expiryDate().toString("yyyy-MM-dd")
        
        # step 2: create the entry
        items = tree.findItems(organisation, Qt.MatchFixedString | Qt.MatchCaseSensitive)
        if len(items) == 0:
            parent = QTreeWidgetItem(tree, [organisation])
        else:
            parent = items[0]
        
        itm = QTreeWidgetItem(parent, [commonName, server, expiryDate])
        itm.setData(0, self.CertRole, cert)
    
    @pyqtSlot(QTreeWidgetItem, QTreeWidgetItem)
    def on_serversCertificatesTree_currentItemChanged(self, current, previous):
        """
        Private slot handling a change of the current item.
        
        @param current new current item (QTreeWidgetItem)
        @param previous previous current item (QTreeWidgetItem)
        """
        enable = current is not None and current.parent() is not None
        self.serversViewButton.setEnabled(enable)
        self.serversDeleteButton.setEnabled(enable)
    
    @pyqtSlot()
    def on_serversViewButton_clicked(self):
        """
        Private slot to show data of the selected certificate
        """
        cert = self.serversCertificatesTree.currentItem().data(0, self.CertRole)
        dlg = SslInfoDialog(cert, self)
        dlg.exec_()
    
    @pyqtSlot()
    def on_serversDeleteButton_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError
