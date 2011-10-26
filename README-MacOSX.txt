Readme for Mac usage
====================

This Readme file describes how to prepare a Mac computer for eric. The
recommended way to do this is to install the software packages from the
distributors web pages. Because some software is only available as source
and compilation is a bit tricky because of the dependencies, these packages
should be installed via a packaging system. The recommended one is MacPorts
because of it's completeness. This is the way described below.

1. Install Xcode 3 (for Snow Leopard)
------------------
The installation of various packages require the Xcode package that is
available from Apple for free. Xcode 3 is contained on the Install DVD
that came with your Mac. Just insert it and select the optional packages.
In this window select Xcode. Make sure, you have the following selected:

 - Essentials
 - System Tools
 - UNIX Development
 - Documentation

After the installation has finished perform an update of your system
software via the Apple menu.

Alternatively you may install the Xcode 3 package from the Apple developer
web site. Just open your browser and enter the URL "http://developer.apple.com/xcode/".
Follow the instructions on this page. This page requires to log in first. If
you don't have an AppleID yet, follow the link next to the "Log in" button.
After you have been logged in follow the download link for Xcode 3. After you
downloaded the package install it as described above. 

1. Install Xcode 4 (for Lion)
------------------
Open the Mac App Store and enter "xcode" into the search entry at the top
right of the window. From the list of results select the Xcode entry. Xcode 4
is provided free of charge. On the Xcode page select the button to get the
package. Follow the usual procedure to start the download. Once the download
has finished open the applications folder and select the "Install Xcode" entry.
In contrast to the Xcode 3 procedure described above, the installer does not
ask for a selection of sub-packages.

2. Install Python 3.2
---------------------
Although Mac OS X comes with a python installation it is recommended to
install the python package provided by the Python community. Download it
from 

http://www.python.org/download/

After the download finished open the downloaded package and install it.

Note: The Python documentation can be found in these locations

/Library/Frameworks/Python.framework/Versions/3.2/Resources/English.lproj/Documentation/index.html
/Applications/Python 3.2/Python Documentation.html

3. Install Qt4
--------------
Download the Qt4 package from

http://qt.nokia.com/downloads/qt-for-open-source-cpp-development-on-mac-os-x

After the download finished open the downloaded package and install it. The
tools (e.g. Designer, Linguist) can be found in the location

/Developer/Tools/Qt

The documentation can be found in these locations

/Developer/Documentation/Qt/html (HTML format)
/Developer/Documentation/Qt/qch (QtHelp format)

The translation files can be found in this location

/Developer/Applications/Qt/translations

4. Install QScintilla2
----------------------
Download the QScintilla2 source code package from

http://www.riverbankcomputing.com/software/qscintilla/download

After the download has finished open a Finder window and extract the downloaded
archive in the Downloads folder (or any other folder of your choice). Change to
the Qt4 directory within the extracted folder and enter these commands in a
terminal window

qmake qscintilla.pro -spec macx-g++
make
sudo make install

5. Install sip
--------------
Download the sip source code package from

http://www.riverbankcomputing.com/software/sip/download

After the download has finished open a Finder window and extract the downloaded
archive in the Downloads folder (or any other folder of your choice). Change to
the extracted folder and enter these commands in a terminal window

python3 configure.py
make
sudo make install

6. Install PyQt4
----------------
Download the PyQt4 source code package from

http://www.riverbankcomputing.com/software/pyqt/download

After the download has finished open a Finder window and extract the downloaded
archive in the Downloads folder (or any other folder of your choice). Change to
the extracted folder and enter these commands in a terminal window

python3 configure.py -c -j 8 (number of cores including hyper threaded ones)
make -j
sudo make install

7. Install QScintilla2 Python bindings
--------------------------------------
Change back to the extracted QScintilla2 directory and in there change to the
Python subdirectory. Enter these commands in a terminal window

python3 configure.py -c -j 8 (number of cores including hyper threaded ones)
make -j
sudo make install

8. Install MacPorts
-------------------
MacPorts is a packaging system for the Mac. I recommend to install it to use
some applications and libraries, that are a bit tricky to compile from source
or for which the supplier doesn't offer ready built Mac OS X packages. In order
to install MacPorts get the proper disk image (for Lion or Snow Leopard) from

http://www.macports.org/install.php

and install it with the usual procedure. You may read about it's usage via

http://guide.macports.org/#using.port

9. Install aspell and dictionaries
-----------------------------------
eric4 includes the capability to perform spell checking of certain parts of
the sources. This is done via enchant which works with various spell checking
libraries as it's backend. It depends upon aspell and hunspell. In order to 
install aspell enter this command in a terminal window

sudo port install aspell

This installs aspell and a bunch of dependancies. Once aspell has been installed
install the dictionaries of your desire. To get a list of available dictionaries
enter

port search aspell-dict

Then install them with a command like this

sudo port install aspell-dict-de aspell-dict-en

10. Install hunspell and dictionaries
-------------------------------------
penchant depends on hunspell as well. Enter these commands to install it

sudo port install hunspell

This installs hunspell and a bunch of dependancies. Once hunspell has been
installed, install the dictionaries of your desire. To get a list of hunspell
dictionaries enter

port search hunspell-dict

Then install them with a command like this


11. Install enchant
-------------------
In order to install enchant and penchant via MacPorts enter these commands

sudo port install enchant

12. Install pyenchant
---------------------
Get the penchant sources from

http://pypi.python.org/pypi/pyenchant/1.6.5

Extract the downloaded sources, change to the sources directory and enter
this command

sudo python3 setup.py install

If you get a TypeError during the above operations open the file listed
last (easy_install.py, line 1447) add a comment sign in front of it and
enter this line right after it

first_line_re = re.compile('^#!.*python[0-9.]*([ \t].*)?$')

In order to test, if everything worked ok open a Python shell and enter
these commands

>>> import enchant
>>> enchant.list_dicts()

If you get an error (ImportError for the first command or no dictionaries
are show for the second command) please recheck the installation checks.

13. Install pysvn
-----------------
Mac OS X already provides subversion. However, best performance for eric5 is
gained with the pysvn interface to subversion. Therefore it is recommended to
install pysvn. That should be done from sources. Please note, that pysvn needs
an updated pycxx if you installed Python 3.2.x. Get pysvn via 

http://pysvn.tigris.org/project_downloads.html

Extract the downloaded sources, change to the sources directory and enter this
command

sudo python3 setup.py install

In order to test, if everything worked ok open a Python shell and enter these
commands

>>> import pysvn
>>> pysvn.version

This should print the pysvn version as a tuple like '(1, 7, 5, 0)'. If you get
an error please check your installation.

14. Install Mercurial
---------------------
Get Mercurial from

http://mercurial.selenic.com/

Extract the downloaded package and install it.

15. Install eric5
-----------------
Get the latest eric5 distribution package from 

http://eric-ide.python-projects.org/eric-download.html

Just follow the link on this page to the latest download.

Extract the downloaded package and language packs into a directory and install
it with this command

sudo python3 install.py

This step concludes the installation procedure. You are ready for the first
start of eric5.

The eric5 installer created an application bundle in the location

/Developer/Applications/Eric5

You may drag it to the dock to have it ready.

16. First start of eric5
------------------------
When eric5 is started for the first time it will recognize that it hasn't been
configured yet. Therefore it will start the configuration dialog with the
default configuration. At this point you could simply close the dialog by
pressing the OK button. However, it is strongly recommended that you go through
the configuration pages to get a feeling for the configuration possibilities.

It is recommended to configure at least the path to the Qt tools on the Qt page
and the paths to the various help pages on the Help Documentation page. The
values to be entered are given above in the Python and Qt installation sections.

17. Install optional packages for eric5 (for plug-ins)
------------------------------------------------------
eric5 provides an extension mechanism via plug-ins. Some of them require the
installation of additional python packages. The plug-ins themselves are
available via the Plugin Repository from within eric5.

17.1 Installation of pylint
---------------------------
pylint is a tool to check Python sources for issues. In order to get it
installed you have to download these packages with the latest version each.

http://download.logilab.org/pub/pylint
http://download.logilab.org/pub/astng 
http://download.logilab.org/pub/common

Once the downloads have been finished, extract all three packages and install
them with these commands.

In the logilab-common-<version> directory do

sudo python3 setup.py install

In the logilab-astng-<version> directory do

sudo python3 setup.py install

In the pylint-<version> directory do

sudo python3 setup.py install

Note: You may receive some errors during the above steps. However, they just
relate to the tests included in the packages. Nevertheless, the installation
will be fine.

17.2 Installation of cx_freeze
------------------------------
cx_freeze is a tool that packages a Python application into executables. It is
like py2exe and py2app. Get the sources from

http://cx-freeze.sourceforge.net/

and extract the downloaded source archive. cx_freeze needs to compile some
C sources and expects the compiler to be called gcc-4.2. This is not in the
executable path. In order to get this changed, cd to /usr/bin and do

sudo ln -s gcc gcc-4.2

In the extracted cx_freeze directory execute the command

sudo python3 setup.py install

This completes this installation instruction. Please enjoy using eric4 and let
the world know about it.
