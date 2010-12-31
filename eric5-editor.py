#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Eric5 Editor

This is the main Python script that performs the necessary initialization
of the MiniEditor module and starts the Qt event loop. This is a standalone 
version of the integrated MiniEditor module.
"""

import sys
import os

for arg in sys.argv:
    if arg.startswith("--config="):
        import Utilities
        configDir = arg.replace("--config=", "")
        Utilities.setConfigDir(configDir)
        sys.argv.remove(arg)
        break

# make ThirdParty package available as a packages repository
try:
    import pygments     # __IGNORE_WARNING__
except ImportError:
    sys.path.insert(2, os.path.join(os.path.dirname(__file__), "ThirdParty", "Pygments"))

from Utilities import Startup


def createMainWidget(argv):
    """
    Function to create the main widget.
    
    @param argv list of commandline parameters (list of strings)
    @return reference to the main widget (QWidget)
    """
    from QScintilla.MiniEditor import MiniEditor
    if len(argv) > 1:
        return MiniEditor(argv[1])
    else:
        return MiniEditor()

def main():
    """
    Main entry point into the application.
    """
    options = [\
        ("--config=configDir", 
         "use the given directory as the one containing the config files"), 
        ("", "name of file to edit")
    ]
    appinfo = Startup.makeAppInfo(sys.argv,
                                  "Eric5 Editor",
                                  "",
                                  "Simplified version of the eric5 editor",
                                  options)
    res = Startup.simpleAppStartup(sys.argv,
                                   appinfo,
                                   createMainWidget)
    sys.exit(res)

if __name__ == '__main__':
    main()
