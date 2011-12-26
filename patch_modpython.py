# -*- coding: utf-8 -*-

# Copyright (c) 2003-2012 Detlev Offenbach <detlev@die-offenbachs.de>
#
# This is a  script to patch mod_python for eric5. 

"""
Script to patch mod_python for usage with the eric5 IDE.
"""

import sys
import os
import shutil
import py_compile
import distutils.sysconfig

# Define the globals.
progName = None
modDir = None

def usage(rcode = 2):
    """
    Display a usage message and exit.

    rcode is the return code passed back to the calling process.
    """
    global progName, modDir
    
    print("Usage:")
    print("    {0} [-h] [-d dir]".format(progName))
    print("where:")
    print("    -h             display this help message")
    print("    -d dir         where Mod_python files are installed [default {0}]".format(
        modDir))
    print()
    print("This script patches the file apache.py of the Mod_python distribution")
    print("so that it will work with the eric5 debugger instead of pdb.")
    print("Please see mod_python.html for more details.")
    print()

    sys.exit(rcode)


def initGlobals():
    """
    Sets the values of globals that need more than a simple assignment.
    """
    global modDir

    modDir = os.path.join(distutils.sysconfig.get_python_lib(True), "mod_python")

def main(argv):
    """The main function of the script.

    argv is the list of command line arguments.
    """
    import getopt

    # Parse the command line.
    global progName, modDir
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
            global modDir
            modDir = arg
    
    try:
        filename = os.path.join(modDir, "apache.py")
        f = open(filename, "r", encoding = "utf-8")
    except EnvironmentError:
        print("The file {0} does not exist. Aborting.".format(filename))
        sys.exit(1)
    
    lines = f.readlines()
    f.close()
    
    pdbFound = False
    ericFound = False
    
    sn = "apache.py"
    s = open(sn, "w", encoding = "utf-8")
    for line in lines:
        if not pdbFound and line.startswith("import pdb"):
            s.write("import eric5.DebugClients.Python.eric5dbgstub as pdb\n")
            pdbFound = True
        else:
            s.write(line)
            if line.startswith("import eric5"):
                ericFound = True
    
    if not ericFound:
        s.write("\n")
        s.write('def initDebugger(name):\n')
        s.write('    """\n')
        s.write('    Initialize the debugger and set the script name to be reported \n')
        s.write('    by the debugger. This is a patch for eric5.\n')
        s.write('    """\n')
        s.write('    if not pdb.initDebugger("standard"):\n')
        s.write('        raise ImportError("Could not initialize debugger")\n')
        s.write('    pdb.setScriptname(name)\n')
        s.write("\n")
    s.close()
    
    if ericFound:
        print("Mod_python is already patched for eric5.")
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
        
        shutil.copy(os.path.join(modDir, "apache.py"),
                    os.path.join(modDir, "apache.py.orig"))
        shutil.copy(sn, modDir)
        os.remove(sn)
        if os.path.exists("{0}c".format(sn)):
            shutil.copy("{0}c".format(sn), modDir)
            os.remove("{0}c".format(sn))
        if os.path.exists("{0}o".format(sn)):
            shutil.copy("{0}o".format(sn), modDir)
            os.remove("{0}o".format(sn))
            
        print("Mod_python patched successfully.")
        print("Unpatched file copied to {0}.".format(
            os.path.join(modDir, "apache.py.orig")))
    
    
if __name__ == "__main__":
    try:
        main(sys.argv)
    except SystemExit:
        raise
    except:
        print("""An internal error occured.  Please report all the output of the program,
including the following traceback, to eric-bugs@die-offenbachs.de.
""")
        raise
