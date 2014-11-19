#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#
# This is the uninstall script for eric5.

"""
Uninstallation script for the eric5 IDE and all eric5 related tools.
"""

from __future__ import unicode_literals

import sys
import os
import shutil
import glob
import distutils.sysconfig

# get a local eric5config.py out of the way
if os.path.exists("eric5config.py"):
    os.rename("eric5config.py", "eric5config.py.orig")
from eric5config import getConfig

# Define the globals.
progName = None
pyModDir = None
progLanguages = ["Python", "Ruby", "QSS"]
includePythonVariant = False
defaultMacAppBundleName = "eric5.app"
defaultMacAppBundlePath = "/Applications"

# Define file name markers for Python variants
PythonMarkers = {
    2: "_py2",
    3: "_py3",
}


def exit(rcode=0):
    """
    Exit the uninstall script.
    
    @param rcode result code to report back (integer)
    """
    # restore the local eric5config.py
    if os.path.exists("eric5config.py.orig"):
        if os.path.exists("eric5config.py"):
            os.remove("eric5config.py")
        os.rename("eric5config.py.orig", "eric5config.py")


def usage(rcode=2):
    """
    Display a usage message and exit.

    @param rcode return code passed back to the calling process (integer)
    """
    global progName

    print("Usage:")
    print("    {0} [-h]".format(progName))
    print("where:")
    print("    -h             display this help message")
    print("    -y             remove executables with Python variant in name")

    exit(rcode)


def initGlobals():
    """
    Set the values of globals that need more than a simple assignment.
    """
    global pyModDir

    pyModDir = distutils.sysconfig.get_python_lib(True)


def wrapperName(dname, wfile):
    """
    Create the platform specific name for the wrapper script.
    
    @param dname name of the directory to place the wrapper into
    @param wfile basename (without extension) of the wrapper script
    @return the name of the wrapper script
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
    if sys.platform.startswith("linux") and os.getuid() == 0:
        for name in ["/usr/share/pixmaps/eric.png",
                     "/usr/share/pixmaps/ericWeb.png"]:
            if os.path.exists(name):
                os.remove(name)
        if includePythonVariant:
            marker = PythonMarkers[sys.version_info.major]
        else:
            marker = ""
        for name in ["/usr/share/applications/eric5" + marker + ".desktop",
                     "/usr/share/appdata/eric5" + marker + ".appdata.xml",
                     "/usr/share/applications/eric5_webbrowser" + marker + 
                     ".desktop"]:
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
    ]
    rem_wnames2 = [
        "eric5_api", "eric5_compare",
        "eric5_configure", "eric5_diff",
        "eric5_doc", "eric5_qregularexpression",
        "eric5_qregexp", "eric5_re",
        "eric5_trpreviewer", "eric5_uipreviewer",
        "eric5_unittest", "eric5",
        "eric5_tray", "eric5_editor",
        "eric5_plugininstall", "eric5_pluginuninstall",
        "eric5_pluginrepository", "eric5_sqlbrowser",
        "eric5_webbrowser", "eric5_iconeditor",
        "eric5_snap",
    ]
    if includePythonVariant:
        marker = PythonMarkers[sys.version_info.major]
        rem_wnames.extend([n + marker for n in rem_wnames2])
    else:
        rem_wnames.extend(rem_wnames2)
    
    try:
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
        for name in ['ericExamplesDir', 'ericDocDir', 'ericDTDDir',
                     'ericCSSDir', 'ericIconDir', 'ericPixDir',
                     'ericTemplatesDir', 'ericCodeTemplatesDir',
                     'ericOthersDir', 'ericStylesDir', 'ericDir']:
            dirpath = getConfig(name)
            if os.path.exists(dirpath):
                shutil.rmtree(dirpath, True)
        
        # Cleanup translations
        for name in glob.glob(
                os.path.join(getConfig('ericTranslationsDir'), 'eric5_*.qm')):
            if os.path.exists(name):
                os.remove(name)
        
        # Cleanup API files
        apidir = getConfig('apidir')
        for progLanguage in progLanguages:
            for name in getConfig('apis'):
                apiname = os.path.join(apidir, progLanguage.lower(), name)
                if os.path.exists(apiname):
                    os.remove(apiname)
            for apiname in glob.glob(
                    os.path.join(apidir, progLanguage.lower(), "*.bas")):
                if os.path.basename(apiname) != "eric5.bas":
                    os.remove(apiname)
        
        if sys.platform == "darwin":
            # delete the Mac app bundle
            if os.path.exists("/Developer/Applications/Eric5"):
                shutil.rmtree("/Developer/Applications/Eric5")
            try:
                macAppBundlePath = getConfig("macAppBundlePath")
                macAppBundleName = getConfig("macAppBundleName")
            except AttributeError:
                macAppBundlePath = defaultMacAppBundlePath
                macAppBundleName = defaultMacAppBundleName
            for bundlePath in [os.path.join(defaultMacAppBundleName,
                                            macAppBundleName),
                               os.path.join(macAppBundlePath,
                                            macAppBundleName),
                               ]:
                if os.path.exists(bundlePath):
                    shutil.rmtree(bundlePath)
    except (IOError, OSError) as msg:
        sys.stderr.write(
            'Error: {0}\nTry uninstall with admin rights.\n'.format(msg))
        exit(7)


def main(argv):
    """
    The main function of the script.

    @param argv list of command line arguments
    """
    import getopt

    global includePythonVariant
    
    initGlobals()

    # Parse the command line.
    global progName
    progName = os.path.basename(argv[0])

    try:
        optlist, args = getopt.getopt(argv[1:], "hy")
    except getopt.GetoptError:
        usage()

    global platBinDir

    for opt, arg in optlist:
        if opt == "-h":
            usage(0)
        if opt == "-y":
            includePythonVariant = True
    
    try:
        uninstallEric()
    except IOError as msg:
        sys.stderr.write(
            'IOError: {0}\nTry uninstall with admin rights.\n'.format(msg))
    except OSError as msg:
        sys.stderr.write(
            'OSError: {0}\nTry uninstall with admin rights.\n'.format(msg))
    
    exit(0)


if __name__ == "__main__":
    try:
        main(sys.argv)
    except SystemExit:
        raise
    except:
        print("""An internal error occured.  Please report all the output of"""
              """ the program,\n"""
              """including the following traceback, to"""
              """ eric5-bugs@eric-ide.python-projects.org.\n""")
        raise
