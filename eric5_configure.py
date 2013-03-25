#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Eric5 Configure

This is the main Python script to configure the eric5 IDE from the outside.
"""

from __future__ import unicode_literals    # __IGNORE_WARNING__
try: # Only for Py2
    import sip
    sip.setapi('QString', 2)
    sip.setapi('QVariant', 2)
    import Utilities.compatibility_fixes     # __IGNORE_WARNING__
except (ImportError):
    pass

import sys
import os

for arg in sys.argv:
    if arg.startswith("--config="):
        import Globals
        configDir = arg.replace("--config=", "")
        Globals.setConfigDir(configDir)
        sys.argv.remove(arg)
        break

# make ThirdParty package available as a packages repository
try:
    import pygments     # __IGNORE_EXCEPTION__ __IGNORE_WARNING__
except ImportError:
    sys.path.insert(2, os.path.join(os.path.dirname(__file__), "ThirdParty", "Pygments"))

from Globals import AppInfo

from Toolbox import Startup


def createMainWidget(argv):
    """
    Function to create the main widget.
    
    @param argv list of commandline parameters (list of strings)
    @return reference to the main widget (QWidget)
    """
    from Preferences.ConfigurationDialog import ConfigurationWindow
    w = ConfigurationWindow()
    w.show()
    w.showConfigurationPageByName("empty")
    return w


def main():
    """
    Main entry point into the application.
    """
    options = [\
        ("--config=configDir",
         "use the given directory as the one containing the config files"),
    ]
    appinfo = AppInfo.makeAppInfo(sys.argv,
                                  "Eric5 Configure",
                                  "",
                                  "Configuration editor for eric5",
                                  options)
    res = Startup.simpleAppStartup(sys.argv,
                                   appinfo,
                                   createMainWidget)
    sys.exit(res)

if __name__ == '__main__':
    main()
