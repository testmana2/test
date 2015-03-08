#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Eric6 Snap.

This is the main Python script that performs the necessary initialization
of the snapshot module and starts the Qt event loop.
"""

from __future__ import unicode_literals

import Toolbox.PyQt4ImportHook  # __IGNORE_WARNING__ 

try:  # Only for Py2
    import Utilities.compatibility_fixes     # __IGNORE_WARNING__
except (ImportError):
    pass

import sys

for arg in sys.argv:
    if arg.startswith("--config="):
        import Globals
        configDir = arg.replace("--config=", "")
        Globals.setConfigDir(configDir)
        sys.argv.remove(arg)
        break

from Globals import AppInfo

from Toolbox import Startup


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
    options = [
        ("--config=configDir",
         "use the given directory as the one containing the config files"),
    ]
    appinfo = AppInfo.makeAppInfo(
        sys.argv,
        "Eric6 Snap",
        "",
        "Simple utility to do snapshots of the screen.",
        options)
    res = Startup.simpleAppStartup(sys.argv,
                                   appinfo,
                                   createMainWidget)
    sys.exit(res)

if __name__ == '__main__':
    main()
