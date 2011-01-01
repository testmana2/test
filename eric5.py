#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Eric5 Python IDE

This is the main Python script that performs the necessary initialization
of the IDE and starts the Qt event loop.
"""

import sys
import os
import traceback
import io
import time
import logging

from PyQt4.QtCore import QTextCodec, SIGNAL, SLOT, qWarning, \
    QLibraryInfo, QTimer
from PyQt4.QtGui import QApplication, QErrorMessage

# some global variables needed to start the application
args = None
mainWindow = None
splash = None

# generate list of arguments to be remembered for a restart
restartArgsList = ["--nosplash", "--plugin", "--debug", "--config"]
restartArgs = [arg for arg in sys.argv[1:] if arg.split("=", 1)[0] in restartArgsList]

if "--debug" in sys.argv:
    del sys.argv[sys.argv.index("--debug")]
    logging.basicConfig(level = logging.DEBUG)

for arg in sys.argv:
    if arg.startswith("--config="):
        import Utilities
        configDir = arg.replace("--config=", "")
        Utilities.setConfigDir(configDir)
        sys.argv.remove(arg)
        break

# make Third-Party package available as a packages repository
try:
    import pygments     # __IGNORE_WARNING__
except ImportError:
    sys.path.insert(2, os.path.join(os.path.dirname(__file__), "ThirdParty", "Pygments"))

from E5Gui.E5Application import E5Application

from UI.Info import BugAddress
from UI.SplashScreen import SplashScreen, NoneSplashScreen
from E5Gui.E5SingleApplication import E5SingleApplicationClient

import Utilities
from Utilities import Startup

logging.debug("Importing Preferences")
import Preferences

def handleSingleApplication(ddindex):
    """
    Global function to handle the single application mode.
    
    @param ddindex index of a '--' option in the options list
    """
    client = E5SingleApplicationClient()
    res = client.connect()
    if res > 0:
        if "--nosplash" in sys.argv and sys.argv.index("--nosplash") < ddindex:
            del sys.argv[sys.argv.index("--nosplash")]
        if "--noopen" in sys.argv and sys.argv.index("--noopen") < ddindex:
            del sys.argv[sys.argv.index("--noopen")]
        if "--debug" in sys.argv and sys.argv.index("--debug") < ddindex:
            del sys.argv[sys.argv.index("--debug")]
        for arg in sys.argv:
            if arg.startswith("--config="):
                sys.argv.remove(arg)
                break
        if len(sys.argv) > 1:
            client.processArgs(sys.argv[1:])
        sys.exit(0)
    elif res < 0:
        print("eric5: %s" % client.errstr())
        sys.exit(res)

def excepthook(excType, excValue, tracebackobj):
    """
    Global function to catch unhandled exceptions.
    
    @param excType exception type
    @param excValue exception value
    @param tracebackobj traceback object
    """
    separator = '-' * 80
    logFile = os.path.join(Utilities.getConfigDir(), "eric5_error.log")
    notice = \
        """An unhandled exception occurred. Please report the problem\n"""\
        """using the error reporting dialog or via email to <%s>.\n"""\
        """A log has been written to "%s".\n\nError information:\n""" % \
        (BugAddress, logFile)
    timeString = time.strftime("%Y-%m-%d, %H:%M:%S")
    
    versionInfo = "\n%s\n%s" % (separator, Utilities.generateVersionInfo())
    pluginVersionInfo = Utilities.generatePluginsVersionInfo()
    if pluginVersionInfo:
        versionInfo += "%s\n%s" % (separator, pluginVersionInfo)
    distroInfo = Utilities.generateDistroInfo()
    if distroInfo:
        versionInfo += "%s\n%s" % (separator, distroInfo)
    
    tbinfofile = io.StringIO()
    traceback.print_tb(tracebackobj, None, tbinfofile)
    tbinfofile.seek(0)
    tbinfo = tbinfofile.read()
    errmsg = '%s: \n%s' % (str(excType), str(excValue))
    sections = [separator, timeString, separator, errmsg, separator, tbinfo]
    msg = '\n'.join(sections)
    try:
        f = open(logFile, "w", encoding = "utf-8")
        f.write(msg)
        f.write(versionInfo)
        f.close()
    except IOError:
        pass
    qWarning(str(notice) + str(msg) + str(versionInfo))

def uiStartUp():
    """
    Global function to finalize the start up of the main UI.
    
    Note: It is activated by a zero timeout single-shot timer.
    """
    global args, mainWindow, splash
    
    if splash:
        splash.finish(mainWindow)
        del splash
    
    mainWindow.checkForErrorLog()
    mainWindow.processArgs(args)
    mainWindow.performVersionCheck(False)
    mainWindow.checkConfigurationStatus()

def main():
    """
    Main entry point into the application.
    """
    global args, mainWindow, splash, restartArgs
    
    sys.excepthook = excepthook
    
    options = [\
        ("--config=configDir", 
         "use the given directory as the one containing the config files"), 
        ("--debug", "activate debugging output to the console"), 
        ("--nosplash", "don't show the splash screen"),
        ("--noopen", "don't open anything at startup except that given in command"), 
        ("--plugin=plugin-file", "load the given plugin file (plugin development)"), 
        ("--start-session", "load the global session file"), 
        ("--", "indicate that there are options for the program to be debugged"),
        ("", "(everything after that is considered arguments for this program)")
    ]
    appinfo = Startup.makeAppInfo(sys.argv,
                                  "Eric5",
                                  "[project | files... [--] [debug-options]]",
                                  "A Python IDE",
                                  options)
    ddindex = Startup.handleArgs(sys.argv, appinfo)
    
    if not Utilities.checkBlacklistedVersions():
        sys.exit(100)
    
    app = E5Application(sys.argv)
    
    if Preferences.getUI("SingleApplicationMode"):
        handleSingleApplication(ddindex)
    
    # set the library paths for plugins
    Startup.setLibraryPaths()

    # set the search path for icons
    Startup.initializeResourceSearchPath()

    # generate and show a splash window, if not suppressed
    if "--nosplash" in sys.argv and sys.argv.index("--nosplash") < ddindex:
        del sys.argv[sys.argv.index("--nosplash")]
        splash = NoneSplashScreen()
    elif not Preferences.getUI("ShowSplash"):
        splash = NoneSplashScreen()
    else:
        splash = SplashScreen()

    # modify the executable search path for the PyQt4 installer
    try:
        from PyQt4 import pyqtconfig
        pyqtDataDir = pyqtconfig._pkg_config["pyqt_mod_dir"]
        if os.path.exists(os.path.join(pyqtDataDir, "bin")):
            path = os.path.join(pyqtDataDir, "bin") + os.pathsep + os.environ["PATH"]
            os.environ["PATH"] = path
    except (AttributeError, ImportError):
        pass
    
    pluginFile = None
    noopen = False
    if "--noopen" in sys.argv and sys.argv.index("--noopen") < ddindex:
        del sys.argv[sys.argv.index("--noopen")]
        noopen = True
    for arg in sys.argv:
        if arg.startswith("--plugin=") and sys.argv.index(arg) < ddindex:
            # extract the plugin development option
            pluginFile = arg.replace("--plugin=", "").replace('"', "")
            sys.argv.remove(arg)
            pluginFile = os.path.expanduser(pluginFile)
            pluginFile = Utilities.normabspath(pluginFile)
            break
    
    # is there a set of filenames or options on the command line,
    # if so, pass them to the UI
    if len(sys.argv) > 1:
        args = sys.argv[1:]
    
    # get the Qt4 translations directory
    qt4TransDir = Preferences.getQt4TranslationsDir()
    if not qt4TransDir:
        qt4TransDir = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
    
    # Load translation files and install them
    loc = Startup.loadTranslators(qt4TransDir, app, ("qscintilla",))
    
    QTextCodec.setCodecForCStrings(QTextCodec.codecForName(\
        str(Preferences.getSystem("StringEncoding"))))
    
    splash.showMessage(QApplication.translate("eric5", "Importing packages..."))
    # We can only import these after creating the E5Application because they
    # make Qt calls that need the E5Application to exist.
    from UI.UserInterface import UserInterface

    splash.showMessage(QApplication.translate("eric5", "Generating Main Window..."))
    try:
        mainWindow = UserInterface(app, loc, splash, pluginFile, noopen, restartArgs)
        app.connect(app, SIGNAL("lastWindowClosed()"), app, SLOT("quit()"))
        mainWindow.show()
        
        QTimer.singleShot(0, uiStartUp)
        
        # generate a graphical error handler
        eMsg = QErrorMessage.qtHandler()
        eMsg.setMinimumSize(600, 400)
        
        # start the event loop
        res = app.exec_()
        logging.debug("Shutting down, result %d" % res)
        logging.shutdown()
        sys.exit(res)
    except Exception as err:
        raise err

if __name__ == '__main__':
    main()
