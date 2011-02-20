#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Eric5 Re

This is the main Python script that performs the necessary initialization
of the PyRegExp wizard module and starts the Qt event loop. This is a standalone 
version of the integrated PyRegExp wizard.
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
    from Plugins.WizardPlugins.PyRegExpWizard.PyRegExpWizardDialog import \
        PyRegExpWizardWindow
    return PyRegExpWizardWindow()

def main():
    """
    Main entry point into the application.
    """
    options = [\
        ("--config=configDir", 
         "use the given directory as the one containing the config files"), 
    ]
    appinfo = Startup.makeAppInfo(sys.argv,
                                  "Eric5 RE",
                                  "",
                                  "Regexp editor for the Python re module",
                                  options)
    res = Startup.simpleAppStartup(sys.argv,
                                   appinfo,
                                   createMainWidget)
    sys.exit(res)

if __name__ == '__main__':
    main()