#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2009 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Eric4 QRegExp

This is the main Python script that performs the necessary initialization
of the QRegExp wizard module and starts the Qt event loop. This is a standalone 
version of the integrated QRegExp wizard.
"""

import sys
import os

import sip
sip.setapi("QString", 2)

for arg in sys.argv:
    if arg.startswith("--config="):
        import Utilities
        configDir = arg.replace("--config=", "")
        Utilities.setConfigDir(configDir)
        sys.argv.remove(arg)
        break

from Utilities import Startup


def createMainWidget(argv):
    """
    Function to create the main widget.
    
    @param argv list of commandline parameters (list of strings)
    @return reference to the main widget (QWidget)
    """
    from Plugins.WizardPlugins.QRegExpWizard.QRegExpWizardDialog import \
        QRegExpWizardWindow
    return QRegExpWizardWindow()

def main():
    """
    Main entry point into the application.
    """
    options = [\
        ("--config=configDir", 
         "use the given directory as the one containing the config files"), 
    ]
    appinfo = Startup.makeAppInfo(sys.argv,
                                  "Eric4 QRegExp",
                                  "",
                                  "Regexp editor for Qt's QRegExp class",
                                  options)
    res = Startup.simpleAppStartup(sys.argv,
                                   appinfo,
                                   createMainWidget)
    sys.exit(res)

if __name__ == '__main__':
    main()
