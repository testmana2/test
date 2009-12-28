#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2009 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Eric4 Compare

This is the main Python script that performs the necessary initialization
of the Compare module and starts the Qt event loop. This is a standalone 
version of the integrated Compare module.
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
    from UI.CompareDialog import CompareWindow
    if len(argv) >= 6:
        # assume last two entries are the files to compare
        return CompareWindow([(argv[-5], argv[-2]), (argv[-3], argv[-1])])
    elif len(argv) >= 2:
        return CompareWindow([("", argv[-2]), ("", argv[-1])])
    else:
        return CompareWindow()

def main():
    """
    Main entry point into the application.
    """
    options = [\
        ("--config=configDir", 
         "use the given directory as the one containing the config files"), 
    ]
    appinfo = Startup.makeAppInfo(sys.argv,
                                  "Eric4 Compare",
                                  "",
                                  "Simple graphical compare tool",
                                  options)
    res = Startup.simpleAppStartup(sys.argv,
                                   appinfo,
                                   createMainWidget)
    sys.exit(res)

if __name__ == '__main__':
    main()
