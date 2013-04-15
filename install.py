#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2002-2013 Detlev Offenbach <detlev@die-offenbachs.de>
#
# This is the install script for eric5.

"""
Installation script for the eric5 IDE and all eric5 related tools.
"""

import sys
import os
import re
import compileall
import py_compile
import glob
import shutil
import fnmatch
import distutils.sysconfig

# Define the globals.
progName = None
currDir = os.getcwd()
modDir = None
pyModDir = None
platBinDir = None
distDir = None
apisDir = None
doCleanup = True
doCompile = True
cfg = {}
progLanguages = ["Python", "Ruby"]
sourceDir = "eric"
configName = 'eric5config.py'
defaultMacAppBundleName = "eric5.app"
macAppBundleName = "eric5.app"
macPythonExe = "{0}/Resources/Python.app/Contents/MacOS/Python".format(sys.exec_prefix)

# Define blacklisted versions of the prerequisites
BlackLists = {
    "sip": ["4.11", "4.12.3"],
    "PyQt4": ["4.7.5"],
    "QScintilla2": [],
}
PlatformsBlackLists = {
    "windows": {
        "sip": [],
        "PyQt4": ["4.9.2", "4.9.3"],
        "QScintilla2": [],
    },
    
    "linux": {
        "sip": [],
        "PyQt4": [],
        "QScintilla2": [],
    },
    
    "mac": {
        "sip": [],
        "PyQt4": ["4.9.2", "4.9.3"],
        "QScintilla2": [],
    },
}


def exit(rcode=0):
    """
    Exit the install script.
    """
    global currDir
    
    if sys.platform.startswith("win"):
        try:
            input("Press enter to continue...")
        except EOFError:
            pass
    
    os.chdir(currDir)
    
    sys.exit(rcode)


def usage(rcode=2):
    """
    Display a usage message and exit.

    @param rcode the return code passed back to the calling process.
    """
    global progName, modDir, distDir, apisDir, macAppBundleName
    global macPythonExe

    print()
    print("Usage:")
    if sys.platform == "darwin":
        print("    {0} [-chxz] [-a dir] [-b dir] [-d dir] [-f file] [-i dir] [-m name] [-p python]"\
        .format(progName))
    elif sys.platform.startswith("win"):
        print("    {0} [-chxz] [-a dir] [-b dir] [-d dir] [-f file]"\
        .format(progName))
    else:
        print("    {0} [-chxz] [-a dir] [-b dir] [-d dir] [-f file] [-i dir]"\
        .format(progName))
    print("where:")
    print("    -h        display this help message")
    print("    -a dir    where the API files will be installed")
    if apisDir:
        print("              (default: {0})".format(apisDir))
    else:
        print("              (no default value)")
    print("    -b dir    where the binaries will be installed")
    print("              (default: {0})".format(platBinDir))
    print("    -d dir    where eric5 python files will be installed")
    print("              (default: {0})".format(modDir))
    print("    -f file   configuration file naming the various installation paths")
    if not sys.platform.startswith("win"):
        print("    -i dir    temporary install prefix")
        print("              (default: {0})".format(distDir))
    if sys.platform == "darwin":
        print("    -m name   name of the Mac app bundle")
        print("              (default: {0})".format(macAppBundleName))
        print("    -p python name of the python executable")
        print("              (default: {0})".format(macPythonExe))
    print("    -x        don't perform dependency checks (use on your own risk)")
    print("    -c        don't cleanup old installation first")
    print("    -z        don't compile the installed python files")
    print()
    print("The file given to the -f option must be valid Python code defining a")
    print("dictionary called 'cfg' with the keys 'ericDir', 'ericPixDir', 'ericIconDir',")
    print("'ericDTDDir', 'ericCSSDir', 'ericStylesDir', 'ericDocDir', 'ericExamplesDir',")
    print("'ericTranslationsDir', 'ericTemplatesDir', 'ericCodeTemplatesDir',")
    print("'ericOthersDir','bindir', 'mdir' and 'apidir.")
    print("These define the directories for the installation of the various parts of"\
          " eric5.")

    exit(rcode)


def initGlobals():
    """
    Sets the values of globals that need more than a simple assignment.
    """
    global platBinDir, modDir, pyModDir, apisDir

    if sys.platform.startswith("win"):
        platBinDir = sys.exec_prefix
        if platBinDir.endswith("\\"):
            platBinDir = platBinDir[:-1]
    else:
        platBinDir = "/usr/local/bin"

    modDir = distutils.sysconfig.get_python_lib(True)
    pyModDir = modDir
    
    try:
        from PyQt4 import pyqtconfig
        pyqtDataDir = pyqtconfig._pkg_config["pyqt_mod_dir"]
        if os.path.exists(os.path.join(pyqtDataDir, "qsci")):
            # it's the installer
            qtDataDir = pyqtDataDir
        else:
            qtDataDir = pyqtconfig._pkg_config["qt_data_dir"]
    except (AttributeError, ImportError):
        qtDataDir = None
    if qtDataDir:
        apisDir = os.path.join(qtDataDir, "qsci", "api")
    else:
        apisDir = None


def copyToFile(name, text):
    """
    Copy a string to a file.

    @param name the name of the file.
    @param text the contents to copy to the file.
    """
    f = open(name, "w", encoding="utf-8")
    f.write(text)
    f.close()


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


def createPyWrapper(pydir, wfile, isGuiScript=True):
    """
    Create an executable wrapper for a Python script.

    @param pydir the name of the directory where the Python script will
        eventually be installed
    @param wfile the basename of the wrapper
    @param isGuiScript flag indicating a wrapper script for a GUI
        application (boolean)
    @return the platform specific name of the wrapper
    """
    # all kinds of Windows systems
    if sys.platform.startswith("win"):
        wname = wfile + ".bat"
        if isGuiScript:
            wrapper = \
                '''@echo off\n''' \
                '''start "" "{2}\\pythonw.exe"''' \
                ''' "{0}\\{1}.pyw"''' \
                ''' %1 %2 %3 %4 %5 %6 %7 %8 %9\n'''.format(pydir, wfile, sys.exec_prefix)
        else:
            wrapper = \
                '''@"{0}\\python" "{1}\\{2}.py"''' \
                ''' %1 %2 %3 %4 %5 %6 %7 %8 %9\n'''.format(
                    sys.exec_prefix, pydir, wfile)

    # Mac OS X
    elif sys.platform == "darwin":
        wname = wfile
        wrapper = \
'''#!/bin/sh

exec "{0}/bin/pythonw3" "{1}/{2}.py" "$@"
'''.format(sys.exec_prefix, pydir, wfile)

    # *nix systems
    else:
        wname = wfile
        wrapper = \
'''#!/bin/sh

exec "{0}" "{1}/{2}.py" "$@"
'''.format(sys.executable, pydir, wfile)

    copyToFile(wname, wrapper)
    os.chmod(wname, 0o755)

    return wname


def copyTree(src, dst, filters, excludeDirs=[], excludePatterns=[]):
    """
    Copy Python, translation, documentation, wizards configuration,
    designer template files and DTDs of a directory tree.
    
    @param src name of the source directory
    @param dst name of the destination directory
    @param filters list of filter pattern determining the files to be copied
    @param excludeDirs list of (sub)directories to exclude from copying
    @keyparam excludePatterns list of filter pattern determining the files to be skipped
    """
    try:
        names = os.listdir(src)
    except OSError:
        return      # ignore missing directories (most probably the i18n directory)
    
    for name in names:
        skipIt = False
        for excludePattern in excludePatterns:
            if fnmatch.fnmatch(name, excludePattern):
                skipIt = True
                break
        if not skipIt:
            srcname = os.path.join(src, name)
            dstname = os.path.join(dst, name)
            for filter in filters:
                if fnmatch.fnmatch(srcname, filter):
                    if not os.path.isdir(dst):
                        os.makedirs(dst)
                    shutil.copy2(srcname, dstname)
                    os.chmod(dstname, 0o644)
                    break
            else:
                if os.path.isdir(srcname) and not srcname in excludeDirs:
                    copyTree(srcname, dstname, filters, excludePatterns=excludePatterns)


def createGlobalPluginsDir():
    """
    Create the global plugins directory, if it doesn't exist.
    """
    global cfg, distDir
    
    pdir = os.path.join(cfg['mdir'], "eric5plugins")
    fname = os.path.join(pdir, "__init__.py")
    if not os.path.exists(fname):
        if not os.path.exists(pdir):
            os.mkdir(pdir,  0o755)
        f = open(fname, "w", encoding="utf-8")
        f.write(
'''# -*- coding: utf-8 -*-

"""
Package containing the global plugins.
"""
'''
        )
        f.close()
        os.chmod(fname, 0o644)


def cleanUp():
    """
    Uninstall the old eric files.
    """
    global macAppBundleName, platBinDir
    
    try:
        from eric5config import getConfig
    except ImportError:
        # eric5 wasn't installed previously
        return
    
    global pyModDir, progLanguages
    
    # Remove the menu entry for Linux systems
    if sys.platform.startswith("linux"):
        for name in ["/usr/share/pixmaps/eric.png",
                     "/usr/share/applications/eric5.desktop",
                     "/usr/share/pixmaps/ericWeb.png",
                     "/usr/share/applications/eric5_webbrowser.desktop"]:
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
        "eric5_snap",
    ]
    
    try:
        for rem_wname in rem_wnames:
            for d in [platBinDir, getConfig('bindir')]:
                rwname = wrapperName(d, rem_wname)
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
                     'ericIconDir', 'ericPixDir', 'ericTemplatesDir',
                     'ericCodeTemplatesDir', 'ericOthersDir', 'ericStylesDir', 'ericDir']:
            if os.path.exists(getConfig(name)):
                shutil.rmtree(getConfig(name), True)
        
        # Cleanup translations
        for name in glob.glob(
                os.path.join(getConfig('ericTranslationsDir'), 'eric5_*.qm')):
            if os.path.exists(name):
                os.remove(name)
        
        # Cleanup API files
        try:
            apidir = getConfig('apidir')
            for progLanguage in progLanguages:
                for name in getConfig('apis'):
                    apiname = os.path.join(apidir, progLanguage.lower(), name)
                    if os.path.exists(apiname):
                        os.remove(apiname)
                for apiname in glob.glob(
                        os.path.join(apidir, progLanguage.lower(), "*.bas")):
                    os.remove(apiname)
        except AttributeError:
            pass
        
        if sys.platform == "darwin":
            # delete the Mac app bundle
            if os.path.exists("/Developer/Applications/Eric5"):
                shutil.rmtree("/Developer/Applications/Eric5")
            if os.path.exists("/Applications/" + macAppBundleName):
                shutil.rmtree("/Applications/" + macAppBundleName)
        
    except (IOError, OSError) as msg:
        sys.stderr.write('Error: {0}\nTry install with admin rights.\n'.format(msg))
        exit(7)


def shutilCopy(src, dst, perm=0o644):
    """
    Wrapper function around shutil.copy() to ensure the permissions.
    
    @param src source file name (string)
    @param dst destination file name or directory name (string)
    @keyparam perm permissions to be set (integer)
    """
    shutil.copy(src, dst)
    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))
    os.chmod(dst, perm)


def installEric():
    """
    Actually perform the installation steps.
    
    @return result code (integer)
    """
    global distDir, doCleanup, cfg, progLanguages, sourceDir, configName
    
    # Create the platform specific wrappers.
    wnames = []
    wnames.append(createPyWrapper(cfg['ericDir'], "eric5_api", False))
    wnames.append(createPyWrapper(cfg['ericDir'], "eric5_compare"))
    wnames.append(createPyWrapper(cfg['ericDir'], "eric5_configure"))
    wnames.append(createPyWrapper(cfg['ericDir'], "eric5_diff"))
    wnames.append(createPyWrapper(cfg['ericDir'], "eric5_doc", False))
    wnames.append(createPyWrapper(cfg['ericDir'], "eric5_editor"))
    wnames.append(createPyWrapper(cfg['ericDir'], "eric5_iconeditor"))
    wnames.append(createPyWrapper(cfg['ericDir'], "eric5_plugininstall"))
    wnames.append(createPyWrapper(cfg['ericDir'], "eric5_pluginrepository"))
    wnames.append(createPyWrapper(cfg['ericDir'], "eric5_pluginuninstall"))
    wnames.append(createPyWrapper(cfg['ericDir'], "eric5_qregexp"))
    wnames.append(createPyWrapper(cfg['ericDir'], "eric5_re"))
    wnames.append(createPyWrapper(cfg['ericDir'], "eric5_snap"))
    wnames.append(createPyWrapper(cfg['ericDir'], "eric5_sqlbrowser"))
    wnames.append(createPyWrapper(cfg['ericDir'], "eric5_tray"))
    wnames.append(createPyWrapper(cfg['ericDir'], "eric5_trpreviewer"))
    wnames.append(createPyWrapper(cfg['ericDir'], "eric5_uipreviewer"))
    wnames.append(createPyWrapper(cfg['ericDir'], "eric5_unittest"))
    wnames.append(createPyWrapper(cfg['ericDir'], "eric5_webbrowser"))
    wnames.append(createPyWrapper(cfg['ericDir'], "eric5"))
    
    # set install prefix, if not None
    if distDir:
        for key in list(cfg.keys()):
            cfg[key] = os.path.normpath(distDir + os.sep + cfg[key])
    
    try:
        # Install the files
        # make the install directories
        for key in list(cfg.keys()):
            if not os.path.isdir(cfg[key]):
                os.makedirs(cfg[key])
        
        # copy the eric5 config file
        if distDir:
            shutilCopy(configName, cfg['mdir'])
            if os.path.exists(configName + 'c'):
                shutilCopy(configName + 'c', cfg['mdir'])
        else:
            shutilCopy(configName, modDir)
            if os.path.exists(configName + 'c'):
                shutilCopy(configName + 'c', modDir)
        
        # copy the various parts of eric5
        copyTree(sourceDir, cfg['ericDir'], ['*.py', '*.pyc', '*.pyo', '*.pyw'],
            ['{1}{0}Examples'.format(os.sep, sourceDir)],
            excludePatterns=["eric5config.py*"])
        copyTree(sourceDir, cfg['ericDir'], ['*.rb'],
            ['{1}{0}Examples'.format(os.sep, sourceDir)])
        copyTree('{1}{0}Plugins'.format(os.sep, sourceDir),
            '{0}{1}Plugins'.format(cfg['ericDir'], os.sep),
            ['*.png', '*.style'])
        copyTree('{1}{0}Documentation'.format(os.sep, sourceDir), cfg['ericDocDir'],
            ['*.html', '*.qch'])
        copyTree('{1}{0}DTDs'.format(os.sep, sourceDir), cfg['ericDTDDir'],
            ['*.dtd'])
        copyTree('{1}{0}CSSs'.format(os.sep, sourceDir), cfg['ericCSSDir'],
            ['*.css'])
        copyTree('{1}{0}Styles'.format(os.sep, sourceDir), cfg['ericStylesDir'],
            ['*.qss'])
        copyTree('{1}{0}i18n'.format(os.sep, sourceDir), cfg['ericTranslationsDir'],
            ['*.qm'])
        copyTree('{1}{0}icons'.format(os.sep, sourceDir), cfg['ericIconDir'],
            ['*.png', 'LICENSE*.*', 'readme.txt'])
        copyTree('{1}{0}pixmaps'.format(os.sep, sourceDir), cfg['ericPixDir'],
            ['*.png', '*.xpm', '*.ico', '*.gif'])
        copyTree('{1}{0}DesignerTemplates'.format(os.sep, sourceDir),
            cfg['ericTemplatesDir'],
            ['*.tmpl'])
        copyTree('{1}{0}CodeTemplates'.format(os.sep, sourceDir),
            cfg['ericCodeTemplatesDir'],
            ['*.tmpl'])
        copyTree('{1}{0}Examples'.format(os.sep, sourceDir), cfg['ericExamplesDir'],
            ['*.py', '*.pyc', '*.pyo'])
        
        # copy the wrappers
        for wname in wnames:
            shutilCopy(wname, cfg['bindir'], perm=0o755)
            os.remove(wname)
        
        # copy the license file
        shutilCopy('{1}{0}LICENSE.GPL3'.format(os.sep, sourceDir), cfg['ericDir'])
        
        # create the global plugins directory
        createGlobalPluginsDir()
        
    except (IOError, OSError) as msg:
        sys.stderr.write('Error: {0}\nTry install with admin rights.\n'.format(msg))
        return(7)
    
    # copy some text files to the doc area
    for name in ["LICENSE.GPL3", "THANKS", "changelog"]:
        try:
            shutilCopy('{2}{0}{1}'.format(os.sep, name, sourceDir), cfg['ericDocDir'])
        except EnvironmentError:
            print("Could not install '{2}{0}{1}'.".format(os.sep, name, sourceDir))
    for name in glob.glob(os.path.join(sourceDir, 'README*.*')):
        try:
            shutilCopy(name, cfg['ericDocDir'])
        except EnvironmentError:
            print("Could not install '{1}'.".format(name))
   
    # copy some more stuff
    for name in ['default.e4k', 'default_Mac.e4k']:
        try:
            shutilCopy('{2}{0}{1}'.format(os.sep, name, sourceDir), cfg['ericOthersDir'])
        except EnvironmentError:
            print("Could not install '{2}{0}{1}'.".format(os.sep, name, sourceDir))
    
    # install the API file
    for progLanguage in progLanguages:
        apidir = os.path.join(cfg['apidir'], progLanguage.lower())
        if not os.path.exists(apidir):
            os.makedirs(apidir)
        for apiName in glob.glob(os.path.join(sourceDir, "APIs", progLanguage, "*.api")):
            try:
                shutilCopy(apiName, apidir)
            except EnvironmentError:
                print("Could not install '{0}'.".format(apiName))
        for apiName in glob.glob(os.path.join(sourceDir, "APIs", progLanguage, "*.bas")):
            try:
                shutilCopy(apiName, apidir)
            except EnvironmentError:
                print("Could not install '{0}'.".format(apiName))
        if progLanguage == "Python":
            # copy Python3 API files to the same destination
            for apiName in glob.glob(os.path.join(sourceDir, "APIs", "Python3", "*.api")):
                try:
                    shutilCopy(apiName, apidir)
                except EnvironmentError:
                    print("Could not install '{0}'.".format(apiName))
            for apiName in glob.glob(os.path.join(sourceDir, "APIs", "Python3", "*.bas")):
                try:
                    shutilCopy(apiName, apidir)
                except EnvironmentError:
                    print("Could not install '{0}'.".format(apiName))
    
    # create menu entry for Linux systems
    if sys.platform.startswith("linux"):
        if distDir:
            dst = os.path.normpath(os.path.join(distDir, "usr/share/pixmaps"))
            if not os.path.exists(dst):
                os.makedirs(dst)
            shutilCopy(os.path.join(sourceDir, "icons", "default", "eric.png"),
                       os.path.join(dst, "eric.png"))
            dst = os.path.normpath(os.path.join(distDir, "usr/share/applications"))
            if not os.path.exists(dst):
                os.makedirs(dst)
            shutilCopy(os.path.join(sourceDir, "eric5.desktop"), dst)
        else:
            shutilCopy(os.path.join(sourceDir, "icons", "default", "eric.png"),
                "/usr/share/pixmaps/eric.png")
            shutilCopy(os.path.join(sourceDir, "eric5.desktop"),
                "/usr/share/applications")
            shutilCopy(os.path.join(sourceDir, "icons", "default", "ericWeb48.png"),
                "/usr/share/pixmaps/ericWeb.png")
            shutilCopy(os.path.join(sourceDir, "eric5_webbrowser.desktop"),
                "/usr/share/applications")
    
    # Create a Mac application bundle
    if sys.platform == "darwin":
        createMacAppBundle(cfg['ericDir'])
    
    return 0


def createMacAppBundle(pydir):
    """
    Create a Mac application bundle.

    @param pydir the name of the directory where the Python script will eventually
        be installed (string)
    """
    global cfg, sourceDir, macAppBundleName, macPythonExe
    
    dirs = {"contents": "/Applications/{0}/Contents/".format(macAppBundleName),
            "exe": "/Applications/{0}/Contents/MacOS".format(macAppBundleName),
            "icns": "/Applications/{0}/Contents/Resources".format(macAppBundleName)}
    os.makedirs(dirs["contents"])
    os.mkdir(dirs["exe"])
    os.mkdir(dirs["icns"])
    
    if macAppBundleName == defaultMacAppBundleName:
        starter = os.path.join(dirs["exe"], "eric")
        os.symlink(macPythonExe, starter)
    else:
        starter = "python3"
    
    wname = os.path.join(dirs["exe"], "eric5")
    path = os.getenv("PATH", "")
    if path:
        pybin = os.path.join(sys.exec_prefix, "bin")
        pathlist = path.split(os.pathsep)
        if pybin not in pathlist:
            pathlist.insert(0, pybin)
        path = os.pathsep.join(pathlist)
        wrapper = \
'''#!/bin/sh

PATH={0}
exec "{1}" "{2}/{3}.py" "$@"
'''.format(path, starter, pydir, "eric5")
    else:
        wrapper = \
'''#!/bin/sh

exec "{0}" "{1}/{2}.py" "$@"
'''.format(starter, pydir, "eric5")
    copyToFile(wname, wrapper)
    os.chmod(wname, 0o755)
    
    shutilCopy(os.path.join(sourceDir, "pixmaps", "eric_2.icns"),
               os.path.join(dirs["icns"], "eric.icns"))
    
    copyToFile(os.path.join(dirs["contents"], "Info.plist"),
'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
          "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>eric5</string>
    <key>CFBundleIconFile</key>
    <string>eric.icns</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>1.0</string>
    <key>CFBundleName</key>
    <string>{0}</string>
    <key>CFBundleDisplayName</key>
    <string>{0}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
</dict>
</plist>
'''.format(macAppBundleName.replace(".app", ""))
    )


def createInstallConfig():
    """
    Create the installation config dictionary.
    """
    global modDir, platBinDir, cfg, apisDir
        
    ericdir = os.path.join(modDir, "eric5")
    cfg = {
        'ericDir': ericdir,
        'ericPixDir': os.path.join(ericdir, "pixmaps"),
        'ericIconDir': os.path.join(ericdir, "icons"),
        'ericDTDDir': os.path.join(ericdir, "DTDs"),
        'ericCSSDir': os.path.join(ericdir, "CSSs"),
        'ericStylesDir': os.path.join(ericdir, "Styles"),
        'ericDocDir': os.path.join(ericdir, "Documentation"),
        'ericExamplesDir': os.path.join(ericdir, "Examples"),
        'ericTranslationsDir': os.path.join(ericdir, "i18n"),
        'ericTemplatesDir': os.path.join(ericdir, "DesignerTemplates"),
        'ericCodeTemplatesDir': os.path.join(ericdir, 'CodeTemplates'),
        'ericOthersDir': ericdir,
        'bindir': platBinDir,
        'mdir': modDir,
    }
    if apisDir:
        cfg['apidir'] = apisDir
    else:
        cfg['apidir'] = os.path.join(ericdir, "api")
configLength = 15
    

def createConfig():
    """
    Create a config file with the respective config entries.
    """
    global cfg, sourceDir
    
    apis = []
    for progLanguage in progLanguages:
        for apiName in glob.glob(os.path.join(sourceDir, "APIs", progLanguage, "*.api")):
            apis.append(os.path.basename(apiName))
        if progLanguage == "Python":
            # treat Python3 API files the same as Python API files
            for apiName in glob.glob(os.path.join(sourceDir, "APIs", "Python3", "*.api")):
                apis.append(os.path.basename(apiName))
    
    fn = 'eric5config.py'
    config = \
"""# -*- coding: utf-8 -*-
#
# This module contains the configuration of the individual eric5 installation
#

_pkg_config = {{
    'ericDir': r'{0}',
    'ericPixDir': r'{1}',
    'ericIconDir': r'{2}',
    'ericDTDDir': r'{3}',
    'ericCSSDir': r'{4}',
    'ericStylesDir': r'{5}',
    'ericDocDir': r'{6}',
    'ericExamplesDir': r'{7}',
    'ericTranslationsDir': r'{8}',
    'ericTemplatesDir': r'{9}',
    'ericCodeTemplatesDir': r'{10}',
    'ericOthersDir': r'{11}',
    'bindir': r'{12}',
    'mdir': r'{13}',
    'apidir': r'{14}',
    'apis': {15},
}}

def getConfig(name):
    '''
    Module function to get a configuration value.

    @param name the name of the configuration value (string).
    '''
    try:
        return _pkg_config[name]
    except KeyError:
        pass

    raise AttributeError('"{{0}}" is not a valid configuration value'.format(name))
""".format(cfg['ericDir'], cfg['ericPixDir'], cfg['ericIconDir'],
           cfg['ericDTDDir'], cfg['ericCSSDir'],
           cfg['ericStylesDir'], cfg['ericDocDir'],
           cfg['ericExamplesDir'], cfg['ericTranslationsDir'],
           cfg['ericTemplatesDir'],
           cfg['ericCodeTemplatesDir'], cfg['ericOthersDir'],
           cfg['bindir'], cfg['mdir'],
           cfg['apidir'], apis)
    copyToFile(fn, config)


def doDependancyChecks():
    """
    Perform some dependency checks.
    """
    print('Checking dependencies')
    
    # perform dependency checks
    if sys.version_info < (3, 1, 0):
        print('Sorry, you must have Python 3.1.0 or higher.')
        exit(5)
    if sys.version_info > (3, 9, 9):
        print('Sorry, eric5 requires Python 3 for running.')
        exit(5)
    print("Python Version: {0:d}.{1:d}.{2:d}".format(*sys.version_info[:3]))
    
    try:
        import xml.etree            # __IGNORE_WARNING__
    except ImportError as msg:
        print('Your Python3 installation is missing the XML module.')
        print('Please install it and try again.')
        exit(5)
    
    try:
        from PyQt4.QtCore import qVersion
    except ImportError as msg:
        print('Sorry, please install PyQt4.')
        print('Error: {0}'.format(msg))
        exit(1)
    print("Found PyQt4")
    
    try:
        from PyQt4 import Qsci      # __IGNORE_WARNING__
    except ImportError as msg:
        print("Sorry, please install QScintilla2 and")
        print("it's PyQt4 wrapper.")
        print('Error: {0}'.format(msg))
        exit(1)
    print("Found QScintilla2")
    
    for impModule in [
        "PyQt4.QtGui", "PyQt4.QtNetwork", "PyQt4.QtSql",
        "PyQt4.QtSvg", "PyQt4.QtWebKit",
    ]:
        name = impModule.split(".")[1]
        modulesOK = True
        try:
            __import__(impModule)
            print("Found", name)
        except ImportError as msg:
            print('Sorry, please install {0}.'.format(name))
            print('Error: {0}'.format(msg))
            modulesOK = False
    if not modulesOK:
        exit(1)
    
    # determine the platform dependent black list
    if sys.platform.startswith("win"):
        PlatformBlackLists = PlatformsBlackLists["windows"]
    elif sys.platform.startswith("linux"):
        PlatformBlackLists = PlatformsBlackLists["linux"]
    else:
        PlatformBlackLists = PlatformsBlackLists["mac"]
    
    # check version of Qt
    qtMajor = int(qVersion().split('.')[0])
    qtMinor = int(qVersion().split('.')[1])
    if qtMajor < 4 or (qtMajor == 4 and qtMinor < 6):
        print('Sorry, you must have Qt version 4.6.0 or higher.')
        exit(2)
    print("Qt Version: {0}".format(qVersion()))
    
    # check version of sip
    try:
        import sipconfig
        sipVersion = sipconfig.Configuration().sip_version_str
        # always assume, that snapshots are new enough
        if "snapshot" not in sipVersion:
            # check for blacklisted versions
            for vers in BlackLists["sip"] + PlatformBlackLists["sip"]:
                if vers == sipVersion:
                    print('Sorry, sip version {0} is not compatible with eric5.'\
                          .format(vers))
                    print('Please install another version.')
                    exit(3)
    except ImportError:
        pass
    
    # check version of PyQt
    from PyQt4.QtCore import PYQT_VERSION_STR
    pyqtVersion = PYQT_VERSION_STR
    # always assume, that snapshots are new enough
    if "snapshot" not in pyqtVersion:
        while pyqtVersion.count('.') < 2:
            pyqtVersion += '.0'
        (maj, min, pat) = pyqtVersion.split('.')
        maj = int(maj)
        min = int(min)
        pat = int(pat)
        if maj < 4 or (maj == 4 and min < 8):
            print('Sorry, you must have PyQt 4.8.0 or higher or' \
                  ' a recent snapshot release.')
            exit(4)
        # check for blacklisted versions
        for vers in BlackLists["PyQt4"] + PlatformBlackLists["PyQt4"]:
            if vers == pyqtVersion:
                print('Sorry, PyQt4 version {0} is not compatible with eric5.'\
                      .format(vers))
                print('Please install another version.')
                exit(4)
    print("PyQt Version: ", pyqtVersion)
    
    # check version of QScintilla
    from PyQt4.Qsci import QSCINTILLA_VERSION_STR
    scintillaVersion = QSCINTILLA_VERSION_STR
    # always assume, that snapshots are new enough
    if "snapshot" not in scintillaVersion:
        while scintillaVersion.count('.') < 2:
            scintillaVersion += '.0'
        (maj, min, pat) = scintillaVersion.split('.')
        maj = int(maj)
        min = int(min)
        pat = int(pat)
        if maj < 2 or (maj == 2 and min < 6):
            print('Sorry, you must have QScintilla 2.6.0 or higher or' \
                  ' a recent snapshot release.')
            exit(5)
        # check for blacklisted versions
        for vers in BlackLists["QScintilla2"] + PlatformBlackLists["QScintilla2"]:
            if vers == scintillaVersion:
                print('Sorry, QScintilla2 version {0} is not compatible with eric5.'\
                      .format(vers))
                print('Please install another version.')
                exit(5)
    print("QScintilla Version: ", QSCINTILLA_VERSION_STR)
    print("All dependencies ok.")
    print()


def compileUiFiles():
    """
    Compile the .ui files to Python sources.
    """
    global sourceDir
    try:
        from PyQt4.uic import compileUiDir
    except ImportError:
        from PyQt4.uic import compileUi
        
        def compileUiDir(dir, recurse = False, map = None,  # __IGNORE_WARNING__
            ** compileUi_args):
            """
            Creates Python modules from Qt Designer .ui files in a directory or
            directory tree.
            
            Note: This function is a modified version of the one found in PyQt4.

            @param dir Name of the directory to scan for files whose name ends with
                '.ui'. By default the generated Python module is created in the same
                directory ending with '.py'.
            @param recurse flag indicating that any sub-directories should be scanned.
            @param map an optional callable that is passed the name of the directory
                containing the '.ui' file and the name of the Python module that will be
                created. The callable should return a tuple of the name of the directory
                in which the Python module will be created and the (possibly modified)
                name of the module.
            @param compileUi_args any additional keyword arguments that are passed to
                the compileUi() function that is called to create each Python module.
            """
            def compile_ui(ui_dir, ui_file):
                """
                Local function to compile a single .ui file.
                
                @param ui_dir directory containing the .ui file (string)
                @param ui_file file name of the .ui file (string)
                """
                # Ignore if it doesn't seem to be a .ui file.
                if ui_file.endswith('.ui'):
                    py_dir = ui_dir
                    py_file = ui_file[:-3] + '.py'

                    # Allow the caller to change the name of the .py file or generate
                    # it in a different directory.
                    if map is not None:
                        py_dir, py_file = list(map(py_dir, py_file))

                    # Make sure the destination directory exists.
                    try:
                        os.makedirs(py_dir)
                    except:
                        pass

                    ui_path = os.path.join(ui_dir, ui_file)
                    py_path = os.path.join(py_dir, py_file)

                    ui_file = open(ui_path, 'r')
                    py_file = open(py_path, 'w')

                    try:
                        compileUi(ui_file, py_file, **compileUi_args)
                    finally:
                        ui_file.close()
                        py_file.close()

            if recurse:
                for root, _, files in os.walk(dir):
                    for ui in files:
                        compile_ui(root, ui)
            else:
                for ui in os.listdir(dir):
                    if os.path.isfile(os.path.join(dir, ui)):
                        compile_ui(dir, ui)
    
    def pyName(py_dir, py_file):
        """
        Local function to create the Python source file name for the compiled .ui file.
        
        @param py_dir suggested name of the directory (string)
        @param py_file suggested name for the compile source file (string)
        @return tuple of directory name (string) and source file name (string)
        """
        return py_dir, "Ui_{0}".format(py_file)
    
    compileUiDir(sourceDir, True, pyName)


def main(argv):
    """
    The main function of the script.

    @param argv the list of command line arguments.
    """
    import getopt

    # Parse the command line.
    global progName, modDir, doCleanup, doCompile, distDir, cfg, apisDir
    global sourceDir, configName, macAppBundleName, macPythonExe
    
    progName = os.path.basename(argv[0])
    
    if os.path.dirname(argv[0]):
        os.chdir(os.path.dirname(argv[0]))

    initGlobals()

    try:
        if sys.platform.startswith("win"):
            optlist, args = getopt.getopt(argv[1:], "chxza:b:d:f:")
        elif sys.platform == "darwin":
            optlist, args = getopt.getopt(argv[1:], "chxza:b:d:f:i:m:p:")
        else:
            optlist, args = getopt.getopt(argv[1:], "chxza:b:d:f:i:")
    except getopt.GetoptError:
        usage()

    global platBinDir
    
    depChecks = True

    for opt, arg in optlist:
        if opt == "-h":
            usage(0)
        elif opt == "-a":
            apisDir = arg
        elif opt == "-b":
            platBinDir = arg
        elif opt == "-d":
            modDir = arg
        elif opt == "-i":
            distDir = os.path.normpath(arg)
        elif opt == "-x":
            depChecks = False
        elif opt == "-c":
            doCleanup = False
        elif opt == "-z":
            doCompile = False
        elif opt == "-f":
            try:
                exec(compile(open(arg).read(), arg, 'exec'), globals())
                if len(cfg) != configLength:
                    print("The configuration dictionary in '{0}' is incorrect. Aborting"\
                        .format(arg))
                    exit(6)
            except:
                cfg = {}
        elif opt == "-m":
            macAppBundleName = arg
        elif opt == "-p":
            macPythonExe = arg
    
    installFromSource = not os.path.isdir(sourceDir)
    if installFromSource:
        sourceDir = os.path.dirname(__file__) or "."
        configName = os.path.join(sourceDir, "eric5config.py")
    
    if len(cfg) == 0:
        createInstallConfig()
    
    if depChecks:
        doDependancyChecks()
    
    # get rid of development config file, if it exists
    try:
        if installFromSource:
            os.rename(configName, configName + ".orig")
            configNameC = configName + 'c'
            if os.path.exists(configNameC):
                os.remove(configNameC)
        os.remove(configName)
    except EnvironmentError:
        pass
    
    # cleanup old installation
    try:
        if doCleanup:
            if distDir:
                shutil.rmtree(distDir, True)
            else:
                cleanUp()
    except (IOError, OSError) as msg:
        sys.stderr.write('Error: {0}\nTry install as root.\n'.format(msg))
        exit(7)

    # Create a config file and delete the default one
    createConfig()

    # Compile .ui files
    print("Compiling user interface files...")
    # step 1: remove old Ui_*.py files
    for root, _, files in os.walk(sourceDir):
        for file in [f for f in files if fnmatch.fnmatch(f, 'Ui_*.py')]:
            os.remove(os.path.join(root, file))
    # step 2: compile the forms
    compileUiFiles()
    
    if doCompile:
        print("\nCompiling source files...")
        if distDir:
            compileall.compile_dir(sourceDir,
                ddir=os.path.join(distDir, modDir, cfg['ericDir']),
                rx=re.compile(r"DebugClients[\\/]Python[\\/]|UtilitiesPython2[\\/]"),
                quiet=True)
            py_compile.compile(configName,
                               dfile=os.path.join(distDir, modDir, "eric5config.py"))
        else:
            compileall.compile_dir(sourceDir,
                ddir=os.path.join(modDir, cfg['ericDir']),
                rx=re.compile(r"DebugClients[\\/]Python[\\/]|UtilitiesPython2[\\/]"),
                quiet=True)
            py_compile.compile(configName,
                               dfile=os.path.join(modDir, "eric5config.py"))
    print("\nInstalling eric5 ...")
    res = installEric()
    
    # do some cleanup
    try:
        if installFromSource:
            os.remove(configName)
            configNameC = configName + 'c'
            if os.path.exists(configNameC):
                os.remove(configNameC)
            os.rename(configName + ".orig", configName)
    except EnvironmentError:
        pass
    
    print("\nInstallation complete.")
    print()
    
    exit(res)
    
    
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
