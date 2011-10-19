#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2002-2011 Detlev Offenbach <detlev@die-offenbachs.de>
#
# This is the uninstall script for eric5.

"""
Uninstallation script for the eric5 IDE and all eric5 related tools.
"""

import sys
import os
import shutil
import glob
import distutils.sysconfig

from eric5config import getConfig

# Define the globals.
progName = None
pyModDir = None
progLanguages = ["Python", "Ruby"]


def usage(rcode=2):
    """Display a usage message and exit.

    rcode is the return code passed back to the calling process.
    """
    global progName

    print("Usage:")
    print("    {0} [-h]".format(progName))
    print("where:")
    print("    -h             display this help message")

    sys.exit(rcode)


def initGlobals():
    """
    Sets the values of globals that need more than a simple assignment.
    """
    global pyModDir

    pyModDir = distutils.sysconfig.get_python_lib(True)


def wrapperName(dname, wfile):
    """Create the platform specific name for the wrapper script.
    """
    if sys.platform.startswith("win"):
        wname = dname + "\\" + wfile + ".bat"
    else:
        wname = dname + "/" + wfile

    return wname


def uninstallEric():
    """
    Uninstall the eric files.
    """
    global pyModDir
    
    # Remove the menu entry for Linux systems
    if sys.platform.startswith("linux"):
        for name in ["/usr/share/pixmaps/eric.png",
                     "/usr/share/applications/eric5.desktop"]:
            if os.path.exists(name):
                os.remove(name)
    
    # Remove the wrapper scripts
    rem_wnames = [
        "eric5-api", "eric5-compare",
        "eric5-configure", "eric5-diff",
        "eric5-doc",
        "eric5-qregexp", "eric5-re",
        "eric5-trpreviewer", "eric5-uipreviewer",
        "eric5-unittest", "eric5",
        "eric5-tray", "eric5-editor",
        "eric5-plugininstall", "eric5-pluginuninstall",
        "eric5-pluginrepository", "eric5-sqlbrowser",
        "eric5-webbrowser", "eric5-iconeditor",
        "eric5_api", "eric5_compare",
        "eric5_configure", "eric5_diff",
        "eric5_doc",
        "eric5_qregexp", "eric5_re",
        "eric5_trpreviewer", "eric5_uipreviewer",
        "eric5_unittest", "eric5",
        "eric5_tray", "eric5_editor",
        "eric5_plugininstall", "eric5_pluginuninstall",
        "eric5_pluginrepository", "eric5_sqlbrowser",
        "eric5_webbrowser", "eric5_iconeditor",
    ]
    for rem_wname in rem_wnames:
        rwname = wrapperName(getConfig('bindir'), rem_wname)
        if os.path.exists(rwname):
            os.remove(rwname)
    
    # Cleanup our config file(s)
    for name in ['eric5config.py', 'eric5config.pyc', 'eric5.pth']:
        e5cfile = os.path.join(pyModDir, name)
        if os.path.exists(e5cfile):
            os.remove(e5cfile)
        e5cfile = os.path.join(pyModDir, "__pycache__", name)
        path, ext = os.path.splitext(e5cfile)
        for f in glob.glob("{0}.*{1}".format(path, ext)):
            os.remove(f)
    
    # Cleanup the install directories
    for name in ['ericExamplesDir', 'ericDocDir', 'ericDTDDir', 'ericCSSDir',
                 'ericIconDir', 'ericPixDir', 'ericTemplatesDir', 'ericCodeTemplatesDir',
                 'ericOthersDir', 'ericStylesDir', 'ericDir']:
        dirpath = getConfig(name)
        if os.path.exists(dirpath):
            shutil.rmtree(dirpath, True)
    
    # Cleanup translations
    for name in glob.glob(os.path.join(getConfig('ericTranslationsDir'), 'eric5_*.qm')):
        if os.path.exists(name):
            os.remove(name)
    
    # Cleanup API files
    apidir = getConfig('apidir')
    for progLanguage in progLanguages:
        for name in getConfig('apis'):
            apiname = os.path.join(apidir, progLanguage.lower(), name)
            if os.path.exists(apiname):
                os.remove(apiname)
        for apiname in glob.glob(os.path.join(apidir, progLanguage.lower(), "*.bas")):
            os.remove(apiname)
    

def main(argv):
    """The main function of the script.

    argv is the list of command line arguments.
    """
    import getopt

    initGlobals()

    # Parse the command line.
    global progName
    progName = os.path.basename(argv[0])

    try:
        optlist, args = getopt.getopt(argv[1:], "h")
    except getopt.GetoptError:
        usage()

    global platBinDir

    for opt, arg in optlist:
        if opt == "-h":
            usage(0)
    
    try:
        uninstallEric()
    except IOError as msg:
        sys.stderr.write('IOError: {0}\nTry uninstall as root.\n'.format(msg))
    
    
if __name__ == "__main__":
    try:
        main(sys.argv)
    except SystemExit:
        raise
    except:
        print("""An internal error occured.  Please report all the output of the program,
including the following traceback, to eric5-bugs@eric-ide.python-projects.org.
""")
        raise
