#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2009 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Eric4 UI Previewer

This is the main Python script that performs the necessary initialization
of the ui previewer and starts the Qt event loop. This is a standalone version
of the integrated ui previewer.
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
    from Tools.UIPreviewer import UIPreviewer
    
    if len(argv) > 1:
        fn = argv[1]
    else:
        fn = None
    
    previewer = UIPreviewer(fn, None, 'UIPreviewer')
    return previewer

def main():
    """
    Main entry point into the application.
    """
    options = [\
        ("--config=configDir", 
         "use the given directory as the one containing the config files"), 
    ]
    appinfo = Startup.makeAppInfo(sys.argv,
                                  "Eric4 UI Previewer",
                                  "file",
                                  "UI file previewer",
                                  options)
    res = Startup.simpleAppStartup(sys.argv,
                                   appinfo,
                                   createMainWidget)
    sys.exit(res)

if __name__ == '__main__':
    main()
