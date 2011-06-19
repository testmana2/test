# -*- coding: utf-8 -*-

# Copyright (c) 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Package implementing cryptography related functionality.
"""

##import os
##import sys
##sys.path.insert(1, os.path.join(os.path.dirname(__file__), "../.."))
##
import random
import base64

from PyQt4.QtCore import QCoreApplication
from PyQt4.QtGui import QLineEdit, QInputDialog

from E5Gui import E5MessageBox

from .py3AES import encryptData, decryptData
from .py3PBKDF2 import verifyPassword, hashPasswordTuple, rehashPassword
##from py3AES import encryptData, decryptData
##from py3PBKDF2 import verifyPassword, hashPasswordTuple, rehashPassword

import Preferences

################################################################################
## password handling functions below
################################################################################


EncodeMarker = "CE4"
CryptoMarker = "CR5"

Delimiter = "$"

MasterPassword = None


def pwEncode(pw):
    """
    Module function to encode a password.
    
    @param pw password to encode (string)
    @return encoded password (string)
    """
    pop = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,;:-_!$?*+#"
    rpw = "".join(random.sample(pop, 32)) + pw + "".join(random.sample(pop, 32))
    return EncodeMarker + base64.b64encode(rpw.encode("utf-8")).decode("ascii")


def pwDecode(epw):
    """
    Module function to decode a password.
    
    @param epw encoded password to decode (string)
    @return decoded password (string)
    """
    if not epw.startswith(EncodeMarker):
        return epw  # it was not encoded using pwEncode
    
    return base64.b64decode(epw[3:].encode("ascii"))[32:-32].decode("utf-8")


##def passwordHash(pw):
##    """
##    Module function to calculate the hash for the given password.
##    
##    This is done by hashing it 65.000 times with SHA1 in order to make brute force
##    attacks a bit harder.
##    
##    @param pw password to be hashed (string)
##    @return password hash (string)
##    """
##    hash = QCryptographicHash.hash(QByteArray(pw.encode("utf-8")),
##                                   QCryptographicHash.Sha1)
##    for i in range(65000):
##        hash = QCryptographicHash.hash(hash, QCryptographicHash.Sha1)
##    return base64.b64encode(bytes(hash)).decode("ascii")
##
##
##def generateCryptoKey(pw, keyLength=32):
##    """
##    Module function to calculate a crypto key given a password.
##    
##    This is done by hashing the password 32.000 times MD5 and 32.000 times with MD4.
##    These hashes are concatenated and and the first bytes are taken depending on the
##    desired key length.
##    
##    @param pw password to be used (string)
##    @param keyLength length of the desired key (16, 24 or 32) (default is
##        32 bytes suitable for AES256 encryption)
##    @return crypto key (bytes)
##    """
##    if keyLength not in [16, 24, 32]:
##        raise ValueError(QCoreApplication.translate(
##            "Crypto", "Illegal key length ({0}) given.").format(keyLength))
##    
##    hash1 = QCryptographicHash.hash(QByteArray(pw.encode("utf-8")),
##                                    QCryptographicHash.Md5)
##    hash2 = QCryptographicHash.hash(QByteArray(pw.encode("utf-8")),
##                                    QCryptographicHash.Md4)
##    for i in range(32000):
##        hash1 = QCryptographicHash.hash(hash1, QCryptographicHash.Md5)
##        hash2 = QCryptographicHash.hash(hash2, QCryptographicHash.Md4)
##    hash = (hash1 + hash2)[:keyLength]
##    return bytes(hash)


def __getMasterPassword():
    """
    Private module function to get the password from the user.
    """
    global MasterPassword
    
    pw, ok = QInputDialog.getText(
        None,
        QCoreApplication.translate("Crypto", "Master Password"),
        QCoreApplication.translate("Crypto", "Enter the master password:"),
        QLineEdit.Password)
    if ok:
        masterPassword = Preferences.getUser("MasterPassword")
        try:
            if masterPassword:
                if verifyPassword(pw, masterPassword):
                    MasterPassword = pwEncode(pw)
                else:
                    E5MessageBox.warning(None,
                        QCoreApplication.translate("Crypto", "Master Password"),
                        QCoreApplication.translate("Crypto", 
                            """The given password is incorrect."""))
            else:
                E5MessageBox.critical(None,
                    QCoreApplication.translate("Crypto", "Master Password"),
                    QCoreApplication.translate("Crypto", 
                        """There is no master password registered."""))
        except ValueError as why:
            E5MessageBox.warning(None,
                QCoreApplication.translate("Crypto", "Master Password"),
                QCoreApplication.translate("Crypto",
                    """<p>The given password cannot be verified.</p>"""
                    """<p>Reason: {0}""".format(str(why))))


def pwEncrypt(pw, masterPW=None):
    """
    Module function to encrypt a password.
    
    @param pw password to encrypt (string)
    @param masterPW password to be used for encryption (string)
    @return encrypted password (string) and flag indicating
        success (boolean)
    """
    if masterPW is None:
        if MasterPassword is None:
            __getMasterPassword()
            if MasterPassword is None:
                return "", False
        
        masterPW = pwDecode(MasterPassword)
    
    digestname, iterations, salt, hash = hashPasswordTuple(masterPW)
    key = hash[:32]
    try:
        cipher = encryptData(key, pw.encode("utf-8"))
    except ValueError:
        return "", False
    return CryptoMarker + Delimiter.join([
        digestname,
        str(iterations),
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(cipher).decode("ascii")
    ]), True


def pwDecrypt(epw, masterPW=None):
    """
    Module function to decrypt a password.
    
    @param epw hashed password to decrypt (string)
    @param masterPW password to be used for encryption (string)
    @return decrypted password (string) and flag indicating
        success (boolean)
    """
    if not epw.startswith(CryptoMarker):
        return epw, False  # it was not encoded using pwEncrypt
    
    if masterPW is None:
        if MasterPassword is None:
            __getMasterPassword()
            if MasterPassword is None:
                return "", False
        
        masterPW = pwDecode(MasterPassword)
    
    hashParameters, epw = epw[3:].rsplit(Delimiter, 1)
    try:
        # recreate the key used to encrypt
        key = rehashPassword(masterPW, hashParameters)[:32]
        plaintext = decryptData(key, base64.b64decode(epw.encode("ascii")))
    except ValueError:
        return "", False
    return plaintext.decode("utf-8"), True


def pwReencrypt(epw, oldPassword, newPassword):
    """
    Module function to re-encrypt a password.
    
    @param epw hashed password to re-encrypt (string)
    @param oldPassword password used to encrypt (string)
    @param newPassword new password to be used (string)
    @return encrypted password (string) and flag indicating
        success (boolean)
    """
    plaintext, ok = pwDecrypt(epw, oldPassword)
    if ok:
        return pwEncrypt(plaintext, newPassword)
    else:
        return "", False


def pwRecode(epw, oldPassword, newPassword):
    """
    Module function to re-encode a password.
    
    In case of an error the encoded password is returned unchanged.
    
    @param epw encoded password to re-encode (string)
    @param oldPassword password used to encode (string)
    @param newPassword new password to be used (string)
    @return encoded password (string)
    """
    if epw == "":
        return epw
    
    if newPassword == "":
        plaintext, ok = pwDecrypt(epw)
        return (pwEncode(plaintext) if ok else epw)
    else:
        if oldPassword == "":
            plaintext = pwDecode(epw)
            cipher, ok = pwEncrypt(plaintext, newPassword)
            return (cipher if ok else epw)
        else:
            npw, ok = pwReencrypt(epw, oldPassword, newPassword)
            return (npw if ok else epw)


def pwConvert(pw, encode=True):
    """
    Module function to convert a plaintext password to the encoded form or
    vice versa.
    
    If there is an error, an empty code is returned for the encode function
    or the given encoded password for the decode function.
    
    @param pw password to encode (string)
    @param encode flag indicating an encode or decode function (boolean)
    @return encode or decoded password (string)
    """
    if pw == "":
        return pw
    
    if encode:
        # plain text -> encoded
        if Preferences.getUser("UseMasterPassword"):
            epw = pwEncrypt(pw)[0]
        else:
            epw = pwEncode(pw)
        return epw
    else:
        # encoded -> plain text
        if Preferences.getUser("UseMasterPassword"):
            plain, ok = pwDecrypt(pw)
        else:
            plain, ok = pwDecode(pw), True
        return (plain if ok else pw)


def changeRememberedMaster(newPassword):
    """
    Module function to change the remembered master password.
    
    @param newPassword new password to be used (string)
    """
    global MasterPassword
    
    if newPassword == "":
        MasterPassword = None
    else:
        MasterPassword = pwEncode(newPassword)
    
if __name__ == "__main__":
    import sys
    from PyQt4.QtGui import QApplication
    
    app = QApplication([])
    
    mpw = "blahblah"
    cpw = "SomeSecret"
    
    cipher, ok = pwEncrypt(cpw)
    print(ok, cipher)
    plain, ok = pwDecrypt(cipher)
    print(ok, plain)
    
    cipher, ok = pwEncrypt(cpw, mpw)
    print(ok, cipher)
    plain, ok = pwDecrypt(cipher, mpw)
    print(ok, plain)
    
    sys.exit(0)
