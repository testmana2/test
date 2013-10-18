#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Eric5 QRegularExpression.

This is the main Python script that performs the necessary initialization
of the QRegularExpression wizard module and starts the Qt event loop. This is
a standalone version of the integrated QRegularExpression wizard.
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
    from Plugins.WizardPlugins.QRegularExpressionWizard\
        .QRegularExpressionWizardDialog import QRegularExpressionWizardWindow
    return QRegularExpressionWizardWindow()


def main():
    """
    Main entry point into the application.
    """
    options = [\
        ("--config=configDir",
         "use the given directory as the one containing the config files"),
    ]
    appinfo = AppInfo.makeAppInfo(
        sys.argv,
        "Eric5 QRegularExpression",
        "",
        "Regexp editor for Qt's QRegularExpression class",
        options)
    res = Startup.simpleAppStartup(sys.argv,
                                   appinfo,
                                   createMainWidget)
    sys.exit(res)

if __name__ == '__main__':
    main()
