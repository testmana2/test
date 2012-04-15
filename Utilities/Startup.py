# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing some startup helper funcions
"""

import os
import sys

from PyQt4.QtCore import QTranslator, QTextCodec, QLocale, QLibraryInfo
from PyQt4.QtGui import QApplication

from E5Gui.E5Application import E5Application

import Preferences
import Utilities
from UI.Info import Version

import UI.PixmapCache

from eric5config import getConfig


def makeAppInfo(argv, name, arg, description, options=[]):
    """
    Module function to generate a dictionary describing the application.
    
    @param argv list of commandline parameters (list of strings)
    @param name name of the application (string)
    @param arg commandline arguments (string)
    @param description text describing the application (string)
    @param options list of additional commandline options
        (list of tuples of two strings (commandline option, option description)).
        The options --version, --help and -h are always present and must not
        be repeated in this list.
    @return dictionary describing the application
    """
    return {
        "bin": argv[0],
        "arg": arg,
        "name": name,
        "description": description,
        "version": Version,
        "options": options
        }


def usage(appinfo, optlen=12):
    """
    Module function to show the usage information.
    
    @param appinfo dictionary describing the application
    @param optlen length of the field for the commandline option (integer)
    """
    options = [\
        ("--version",  "show the program's version number and exit"),
        ("-h, --help", "show this help message and exit")
    ]
    options.extend(appinfo["options"])
    
    print("""
Usage: {bin} [OPTIONS] {arg}

{name} - {description}
    
Options:""".format(**appinfo))
    for opt in options:
        print("  {0}  {1}".format(opt[0].ljust(optlen), opt[1]))
    sys.exit(0)


def version(appinfo):
    """
    Module function to show the version information.
    
    @param appinfo dictionary describing the application
    """
    print("""
{name} {version}

{description}

Copyright (c) 2002 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
This is free software; see LICENSE.GPL3 for copying conditions.
There is NO warranty; not even for MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.""".format(**appinfo))
    sys.exit(0)


def handleArgs(argv, appinfo):
    """
    Module function to handle the always present commandline options.
    
    @param argv list of commandline parameters (list of strings)
    @param appinfo dictionary describing the application
    @return index of the '--' option (integer). This is used to tell
        the application, that all additional options don't belong to
        the application.
    """
    ddindex = 30000     # arbitrarily large number
    args = {
        "--version": version,
        "--help": usage,
        "-h": usage
        }
    if '--' in argv:
        ddindex = argv.index("--")
    for a in args:
        if a in argv and argv.index(a) < ddindex:
            args[a](appinfo)
    return ddindex


def loadTranslatorForLocale(dirs, tn):
    """
    Module function to find and load a specific translation.

    @param dirs Searchpath for the translations. (list of strings)
    @param tn The translation to be loaded. (string)
    @return Tuple of a status flag and the loaded translator. (int, QTranslator)
    """
    trans = QTranslator(None)
    for dir in dirs:
        loaded = trans.load(tn, dir)
        if loaded:
            return (trans, True)
    
    print("Warning: translation file '" + tn + "'could not be loaded.")
    print("Using default.")
    return (None, False)


def initializeResourceSearchPath():
    """
    Module function to initialize the default mime source factory.
    """
    defaultIconPath = os.path.join(getConfig('ericIconDir'), "default")
    iconPaths = Preferences.getIcons("Path")
    for iconPath in iconPaths:
        if iconPath:
            UI.PixmapCache.addSearchPath(iconPath)
    if not defaultIconPath in iconPaths:
        UI.PixmapCache.addSearchPath(defaultIconPath)


def setLibraryPaths():
    """
    Module function to set the Qt library paths correctly for windows systems.
    """
    if Utilities.isWindowsPlatform():
        from PyQt4 import pyqtconfig
        libPath = os.path.join(pyqtconfig._pkg_config["pyqt_mod_dir"], "plugins")
        if os.path.exists(libPath):
            libPath = Utilities.fromNativeSeparators(libPath)
            libraryPaths = QApplication.libraryPaths()
            if libPath not in libraryPaths:
                libraryPaths.insert(0, libPath)
                QApplication.setLibraryPaths(libraryPaths)

# the translator must not be deleted, therefore we save them here
loaded_translators = {}


def loadTranslators(qtTransDir, app, translationFiles=()):
    """
    Module function to load all required translations.
    
    @param qtTransDir directory of the Qt translations files (string)
    @param app reference to the application object (QApplication)
    @param translationFiles tuple of additional translations to
        be loaded (tuple of strings)
    @return the requested locale (string)
    """
    global loaded_translators
    translations = ("qt", "eric5") + translationFiles
    loc = Preferences.getUILanguage()
    if loc is None:
        return

    if loc == "System":
        loc = QLocale.system().name()
    if loc != "C":
        dirs = [getConfig('ericTranslationsDir'), Utilities.getConfigDir()]
        if qtTransDir is not None:
            dirs.append(qtTransDir)

        loca = loc
        for tf in ["{0}_{1}".format(tr, loc) for tr in translations]:
            translator, ok = loadTranslatorForLocale(dirs, tf)
            loaded_translators[tf] = translator
            if ok:
                app.installTranslator(translator)
            else:
                if tf.startswith("eric5"):
                    loca = None
        loc = loca
    else:
        loc = None
    return loc


def simpleAppStartup(argv, appinfo, mwFactory, quitOnLastWindowClosed=True,
    app=None):
    """
    Module function to start up an application that doesn't need a specialized start up.
    
    This function is used by all of eric5's helper programs.
    
    @param argv list of commandline parameters (list of strings)
    @param appinfo dictionary describing the application
    @param mwFactory factory function generating the main widget. This
        function must accept the following parameter.
        <dl>
            <dt>argv</dt>
            <dd>list of commandline parameters (list of strings)</dd>
        </dl>
    @keyparam quitOnLastWindowClosed flag indicating to quit the application,
        if the last window was closed (boolean)
    @keyparam app reference to the application object (QApplication or None)
    """
    handleArgs(argv, appinfo)
    if app is None:
        app = E5Application(argv)
    app.setQuitOnLastWindowClosed(quitOnLastWindowClosed)
    
    setLibraryPaths()
    initializeResourceSearchPath()
    QApplication.setWindowIcon(UI.PixmapCache.getIcon("eric.png"))
    
    qt4TransDir = Preferences.getQt4TranslationsDir()
    if not qt4TransDir:
        qt4TransDir = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
    loadTranslators(qt4TransDir, app)
    
    QTextCodec.setCodecForCStrings(
        QTextCodec.codecForName(Preferences.getSystem("StringEncoding"))
    )
    
    w = mwFactory(argv)
    if quitOnLastWindowClosed:
        app.lastWindowClosed.connect(app.quit)
    w.show()
    w.raise_()
    
    return app.exec_()
