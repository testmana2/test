#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Eric6 Plugin Uninstaller.

This is the main Python script to uninstall eric6 plugins from outside of the
IDE.
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
    from PluginManager.PluginUninstallDialog import PluginUninstallWindow
    return PluginUninstallWindow()


def main():
    """
    Main entry point into the application.
    """
    options = [
        ("--config=configDir",
         "use the given directory as the one containing the config files"),
    ]
    appinfo = AppInfo.makeAppInfo(sys.argv,
                                  "Eric6 Plugin Uninstaller",
                                  "",
                                  "Plugin uninstallation utility for eric6",
                                  options)
    res = Startup.simpleAppStartup(sys.argv,
                                   appinfo,
                                   createMainWidget)
    sys.exit(res)

if __name__ == '__main__':
    main()
