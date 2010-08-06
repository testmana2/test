# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#
# This is a  script to patch pyxml to correct a bug. 

"""
Script to patch pyXML to correct a bug.
"""

import sys
import os
import shutil
import py_compile
import distutils.sysconfig

# Define the globals.
progName = None
pyxmlModDir = None

def usage(rcode = 2):
    """
    Display a usage message and exit.

    rcode is the return code passed back to the calling process.
    """
    global progName, pyxmlModDir
    
    print("Usage:")
    print("    {0} [-h] [-d dir]".format(progName))
    print("where:")
    print("    -h             display this help message")
    print("    -d dir         where pyXML is installed [default {0}]".format(
        pyxmlModDir))
    print()
    print("This script patches the file _xmlplus/parsers/xmlproc/xmlutils.py")
    print("of the pyXML distribution to fix a bug causing it to fail")
    print("for XML files containing non ASCII characters.")
    print()

    sys.exit(rcode)


def initGlobals():
    """
    Sets the values of globals that need more than a simple assignment.
    """
    global pyxmlModDir

    pyxmlModDir = os.path.join(distutils.sysconfig.get_python_lib(True), "_xmlplus")

def isPatched():
    """
    Function to check, if pyXML is already patched.
    
    @return flag indicating patch status (boolean)
    """
    global pyxmlModDir
    
    initGlobals()

    try:
        filename = \
            os.path.join(pyxmlModDir, "parsers", "xmlproc", "xmlutils.py")
        f = open(filename, "r", encoding = "utf-8")
    except EnvironmentError:
        print("Could not find the pyXML distribution. Please use the patch_pyxml.py")
        print("script to apply a patch needed to fix a bug causing it to fail for")
        print("XML files containing non ASCII characters.")
        return True # fake a found patch
    
    lines = f.readlines()
    f.close()
    
    patchPositionFound = False
    
    for line in lines:
        if patchPositionFound and \
            (line.startswith(\
                "                # patched by eric5 install script.") or \
             line.startswith(\
                "                self.datasize = len(self.data)")):
                return True
        if line.startswith(\
              "                self.data = self.charset_converter(self.data)"):
            patchPositionFound = True
            continue
    
    return False
    
def patchPyXML():
    """
    The patch function.
    """
    global pyxmlModDir
    
    initGlobals()

    try:
        filename = \
            os.path.join(pyxmlModDir, "parsers", "xmlproc", "xmlutils.py")
        f = open(filename, "r", encoding = "utf-8")
    except EnvironmentError:
        print("The file {0} does not exist. Aborting.".format(filename))
        sys.exit(1)
    
    lines = f.readlines()
    f.close()
    
    patchPositionFound = False
    patched = False
    
    sn = "xmlutils.py"
    s = open(sn, "w", encoding = "utf-8")
    for line in lines:
        if patchPositionFound:
            if not line.startswith(\
                    "                # patched by eric5 install script.") and \
               not line.startswith(\
                    "                self.datasize = len(self.data)"):
                s.write("                # patched by eric5 install script.\n")
                s.write("                self.datasize = len(self.data)\n")
                patched = True
            patchPositionFound = False
        s.write(line)
        if line.startswith(\
              "                self.data = self.charset_converter(self.data)"):
            patchPositionFound = True
            continue
    s.close()
    
    if not patched:
        print("xmlutils.py is already patched.")
        os.remove(sn)
    else:
        try:
            py_compile.compile(sn)
        except py_compile.PyCompileError as e:
            print("Error compiling {0}. Aborting".format(sn))
            print(e)
            os.remove(sn)
            sys.exit(1)
        except SyntaxError as e:
            print("Error compiling {0}. Aborting".format(sn))
            print(e)
            os.remove(sn)
            sys.exit(1)
        
        shutil.copy(filename, "{0}.orig".format(filename))
        shutil.copy(sn, filename)
        os.remove(sn)
        if os.path.exists("{0}c".format(sn)):
            shutil.copy("{0}c".format(sn), "{0}c".format(filename))
            os.remove("{0}c".format(sn))
        if os.path.exists("{0}o".format(sn)):
            shutil.copy("{0}o".format(sn), "{0}o".format(filename))
            os.remove("{0}o".format(sn))
            
        print("xmlutils.py patched successfully.")
        print("Unpatched file copied to {0}.orig.".format(filename))
    
def main(argv):
    """
    The main function of the script.

    argv is the list of command line arguments.
    """
    import getopt

    # Parse the command line.
    global progName, pyxmlModDir
    progName = os.path.basename(argv[0])

    initGlobals()

    try:
        optlist, args = getopt.getopt(argv[1:],"hd:")
    except getopt.GetoptError:
        usage()

    for opt, arg in optlist:
        if opt == "-h":
            usage(0)
        elif opt == "-d":
            global pyxmlModDir
            pyxmlModDir = arg
    
    patchPyXML()
    
if __name__ == "__main__":
    main()
