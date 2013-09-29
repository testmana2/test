#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Eric5 Plugin Installer.

This is the main Python script to install eric5 plugins from outside of the IDE.
"""

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
    from PluginManager.PluginRepositoryDialog import PluginRepositoryWindow
    return PluginRepositoryWindow(None)


def main():
    """
    Main entry point into the application.
    """
    options = [\
        ("--config=configDir",
         "use the given directory as the one containing the config files"),
    ]
    appinfo = AppInfo.makeAppInfo(sys.argv,
                                  "Eric5 Plugin Repository",
                                  "",
                                  "Utility to show the contents of the eric5"
                                  " Plugin repository.",
                                  options)
    res = Startup.simpleAppStartup(sys.argv,
                                   appinfo,
                                   createMainWidget)
    sys.exit(res)

if __name__ == '__main__':
    main()
