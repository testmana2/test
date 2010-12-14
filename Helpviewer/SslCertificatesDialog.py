# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show and edit all certificates.
"""

from PyQt4.QtCore import pyqtSlot, Qt, QByteArray
from PyQt4.QtGui import QDialog, QTreeWidgetItem
try:
    from PyQt4.QtNetwork import QSslCertificate, QSslSocket, QSslConfiguration
except ImportError:
    pass

from E5Gui import E5MessageBox

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
        self.__populateCaCertificatesTree()
    
    def __populateServerCertificatesTree(self):
        """
        Private slot to populate the server certificates tree.
        """
        certificateDict = Preferences.toDict(
                Preferences.Prefs.settings.value("Help/CaCertificatesDict"))
        for server in certificateDict:
            for cert in QSslCertificate.fromData(certificateDict[server]):
                self.__createServerCertificateEntry(server, cert)
        
        self.serversCertificatesTree.expandAll()
        for i in range(self.serversCertificatesTree.columnCount()):
            self.serversCertificatesTree.resizeColumnToContents(i)
    
    def __createServerCertificateEntry(self, server, cert):
        """
        Private method to create a server certificate entry.
        
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
        items = self.serversCertificatesTree.findItems(organisation, 
            Qt.MatchFixedString | Qt.MatchCaseSensitive)
        if len(items) == 0:
            parent = QTreeWidgetItem(self.serversCertificatesTree, [organisation])
        else:
            parent = items[0]
        
        itm = QTreeWidgetItem(parent, [commonName, server, expiryDate])
        itm.setData(0, self.CertRole, cert)
    
    @pyqtSlot(QTreeWidgetItem, QTreeWidgetItem)
    def on_serversCertificatesTree_currentItemChanged(self, current, previous):
        """
        Private slot handling a change of the current item in the
        server certificates list.
        
        @param current new current item (QTreeWidgetItem)
        @param previous previous current item (QTreeWidgetItem)
        """
        enable = current is not None and current.parent() is not None
        self.serversViewButton.setEnabled(enable)
        self.serversDeleteButton.setEnabled(enable)
    
    @pyqtSlot()
    def on_serversViewButton_clicked(self):
        """
        Private slot to show data of the selected server certificate.
        """
        cert = self.serversCertificatesTree.currentItem().data(0, self.CertRole)
        dlg = SslInfoDialog(cert, self)
        dlg.exec_()
    
    @pyqtSlot()
    def on_serversDeleteButton_clicked(self):
        """
        Private slot to delete the selected server certificate.
        """
        itm = self.serversCertificatesTree.currentItem()
        res = E5MessageBox.yesNo(self,
            self.trUtf8("Delete Server Certificate"),
            self.trUtf8("""<p>Shall the server certificate really be deleted?</p>"""
                        """<p>{0}</p>"""
                        """<p>If the server certificate is deleted, the normal security"""
                        """ checks will be reinstantiated and the server has to"""
                        """ present a valid certificate.</p>""")\
                .format(itm.text(0)))
        if res:
            server = itm.text(1)
            
            # delete the selected entry and it's parent entry, if it was the only one
            parent = itm.parent()
            parent.takeChild(parent.indexOfChild(itm))
            if parent.childCount() == 0:
                self.serversCertificatesTree.takeTopLevelItem(
                    self.serversCertificatesTree.indexOfTopLevelItem(parent))
            
            # delete the certificate from the user certificate store
            certificateDict = Preferences.toDict(
                    Preferences.Prefs.settings.value("Help/CaCertificatesDict"))
            del certificateDict[server]
            Preferences.Prefs.settings.setValue("Help/CaCertificatesDict", 
                certificateDict)
            
            # delete the certificate from the default certificates
            caNew = []
            for topLevelIndex in range(self.serversCertificatesTree.topLevelItemCount()):
                parent = self.serversCertificatesTree.topLevelItem(topLevelIndex)
                for childIndex in range(parent.childCount()):
                    cert = parent.child(childIndex).data(0, self.CertRole)
                    if cert not in caNew:
                        caNew.append(cert)
            caList = QSslSocket.systemCaCertificates()
            caList.extend(caNew)
            sslCfg = QSslConfiguration.defaultConfiguration()
            sslCfg.setCaCertificates(caList)
            QSslConfiguration.setDefaultConfiguration(sslCfg)
    
    def __populateCaCertificatesTree(self):
        """
        Private slot to populate the CA certificates tree.
        """
        for cert in QSslSocket.systemCaCertificates():
            self.__createCaCertificateEntry(cert)
        
        self.caCertificatesTree.expandAll()
        for i in range(self.caCertificatesTree.columnCount()):
            self.caCertificatesTree.resizeColumnToContents(i)
        self.caCertificatesTree.sortItems(0, Qt.AscendingOrder)
    
    def __createCaCertificateEntry(self, cert):
        """
        Private method to create a CA certificate entry.
        
        @param cert certificate to insert (QSslCertificate)
        """
        # step 1: extract the info to be shown
        organisation = str(
            QByteArray(cert.subjectInfo(QSslCertificate.Organization)), 
            encoding = "utf-8")
        if organisation is None or organisation == "":
            organisation = self.trUtf8("(Unknown)")
        commonName = cert.subjectInfo(QSslCertificate.CommonName)
        if commonName is None or commonName == "":
            commonName = self.trUtf8("(Unknown common name)")
        expiryDate = cert.expiryDate().toString("yyyy-MM-dd")
        
        # step 2: create the entry
        items = self.caCertificatesTree.findItems(organisation, 
            Qt.MatchFixedString | Qt.MatchCaseSensitive)
        if len(items) == 0:
            parent = QTreeWidgetItem(self.caCertificatesTree, [organisation])
        else:
            parent = items[0]
        
        itm = QTreeWidgetItem(parent, [commonName, expiryDate])
        itm.setData(0, self.CertRole, cert)
    
    @pyqtSlot(QTreeWidgetItem, QTreeWidgetItem)
    def on_caCertificatesTree_currentItemChanged(self, current, previous):
        """
        Private slot handling a change of the current item 
        in the CA certificates list.
        
        @param current new current item (QTreeWidgetItem)
        @param previous previous current item (QTreeWidgetItem)
        """
        enable = current is not None and current.parent() is not None
        self.caViewButton.setEnabled(enable)
    
    @pyqtSlot()
    def on_caViewButton_clicked(self):
        """
        Private slot to show data of the selected CA certificate.
        """
        cert = self.caCertificatesTree.currentItem().data(0, self.CertRole)
        dlg = SslInfoDialog(cert, self)
        dlg.exec_()
