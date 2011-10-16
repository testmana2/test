# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show SSL certificate infos.
"""

from PyQt4.QtCore import QCryptographicHash, QDateTime, Qt
from PyQt4.QtGui import QDialog
from PyQt4.QtNetwork import QSslCertificate

from .Ui_SslInfoDialog import Ui_SslInfoDialog

import Utilities


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
        
        self.blacklistedLabel.setVisible(False)
        self.blacklistedLabel.setStyleSheet(
            "QLabel { color : white; background-color : red; }")
        self.expiredLabel.setVisible(False)
        self.expiredLabel.setStyleSheet(
            "QLabel { color : white; background-color : red; }")
        
        self.subjectCommonNameLabel.setText(self.__certificateString(
            certificate.subjectInfo(QSslCertificate.CommonName)))
        self.subjectOrganizationLabel.setText(self.__certificateString(
            certificate.subjectInfo(QSslCertificate.Organization)))
        self.subjectOrganizationalUnitLabel.setText(self.__certificateString(
            certificate.subjectInfo(QSslCertificate.OrganizationalUnitName)))
        self.serialNumberLabel.setText(self.__serialNumber(certificate))
        self.issuerCommonNameLabel.setText(self.__certificateString(
            certificate.issuerInfo(QSslCertificate.CommonName)))
        self.issuerOrganizationLabel.setText(self.__certificateString(
            certificate.issuerInfo(QSslCertificate.Organization)))
        self.issuerOrganizationalUnitLabel.setText(self.__certificateString(
            certificate.issuerInfo(QSslCertificate.OrganizationalUnitName)))
        self.effectiveLabel.setText(Qt.escape(
            certificate.effectiveDate().toString("yyyy-MM-dd")))
        self.expiresLabel.setText(Qt.escape(
            certificate.expiryDate().toString("yyyy-MM-dd")))
        self.sha1Label.setText(self.__formatHexString(
            str(certificate.digest(QCryptographicHash.Sha1).toHex(), encoding="ascii")))
        self.md5Label.setText(self.__formatHexString(
            str(certificate.digest(QCryptographicHash.Md5).toHex(), encoding="ascii")))
        
        if not certificate.isValid():
            # something is wrong; indicate it to the user
            if self.__hasExpired(certificate.effectiveDate(), certificate.expiryDate()):
                self.expiredLabel.setVisible(True)
            else:
                self.blacklistedLabel.setVisible(True)
    
    def __certificateString(self, txt):
        """
        Private method to prepare some text for display.
        
        @param txt text to be displayed (string)
        @return prepared text (string)
        """
        if txt is None or txt == "":
            return self.trUtf8("<not part of the certificate>")
        
        return Qt.escape(Utilities.decodeString(txt))
    
    def __serialNumber(self, cert):
        """
        Private slot to format the certificate serial number.
        
        @param cert reference to the SSL certificate (QSslCertificate)
        @return formated serial number (string)
        """
        serial = cert.serialNumber()
        if serial == "":
            return self.trUtf8("<not part of the certificate>")
        
        if ':' in serial:
            return str(serial, encoding="ascii").upper()
        else:
            hexString = hex(int(serial))[2:]
            return self.__formatHexString(hexString)
    
    def __formatHexString(self, hexString):
        """
        Private method to format a hex string for display.
        
        @param hexString hex string to be formatted (string)
        @return formatted string (string)
        """
        hexString = hexString.upper()
        
        if len(hexString) % 2 == 1:
            hexString = '0' + hexString
        
        hexList = []
        while hexString:
            hexList.append(hexString[:2])
            hexString = hexString[2:]
        
        return Qt.escape(':'.join(hexList))
    
    def __hasExpired(self, effectiveDate, expiryDate):
        """
        Private method to check for a certificate expiration.
        
        @param effectiveDate date the certificate becomes effective (QDateTime)
        @param expiryDate date the certificate expires (QDateTime)
        @return flag indicating the expiration status (boolean)
        """
        now = QDateTime.currentDateTime()
        
        return now < effectiveDate or now >= expiryDate
