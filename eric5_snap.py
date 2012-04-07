#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Eric5 Snap

This is the main Python script that performs the necessary initialization
of the snapshot module and starts the Qt event loop.
"""

import sys

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
    from Snapshot.SnapWidget import SnapWidget
    return SnapWidget()


def main():
    """
    Main entry point into the application.
    """
    options = [\
        ("--config=configDir",
         "use the given directory as the one containing the config files"),
    ]
    appinfo = Startup.makeAppInfo(sys.argv,
                                  "Eric5 Snap",
                                  "",
                                  "Simple utility to do snapshots of the screen.",
                                  options)
    res = Startup.simpleAppStartup(sys.argv,
                                   appinfo,
                                   createMainWidget)
    sys.exit(res)

if __name__ == '__main__':
    main()
