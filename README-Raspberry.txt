Readme for Raspberry Pi usage
=============================

This Readme file describes how to prepare a Raspberry Pi computer for eric.
The recommended way to do this is to install the software packages from the
distributors web pages. This procedure assumes, that the Raspbian "Wheezy"
immage available via the Raspberry.org web site was used to prepare the
SD card and that the initial setup steps have been completed.


1. Finalisation of setup
------------------------
Perform these steps to get your installation up-to-date and remove obsolete
packages.

sudo apt-get update
sudo apt-get upgrade
sudo apt-get autoremove


2. Complete Python3 and Python2 installation
--------------------------------------------
Perform these steps to install the Python documentation and examples.

sudo apt-get install python3-doc python3-examples python3-dev
sudo apt-get install python-doc python-examples python-dev


3. Install Qt4
--------------
Perform these steps to install Qt4.

sudo apt-get install qt4-designer qt4-dev-tools qt4-doc qt4-doc-html
    qt4-linguist-tools qt4-qtconfig libqt4-sql-sqlite

Note: Enter the above command on ONE line!

This command will install all required packages as well. Once installation
has finished you may change the Qt4 configuration using the 'qtconfig'
tool (e.g. to select another GUI style).


4. Install PyQt4
----------------
Perform these steps to install PyQt4.

sudo apt-get install python3-pyqt4 python3-pyqt4.qsci python3-pyqt4.qtopengl
    python3-pyqt4.qtsql pyqt4-dev-tools python3-dbus.mainloop.qt python-qt4-doc

Note: Enter the above command on ONE line!

This command will install all required packages as well.


5. Install Spell Checker and Dictionaries
-----------------------------------------
Perform these steps to install the spell checker and spelling dictionaries.

sudo apt-get install python3-enchant
sudo apt-get install aspell-<xx>

Replace <xx> by the desired language. To see which dictionaries are available
execute this command.

apt-cache search aspell


6. Install Version Control Systems
----------------------------------
Perform these steps to install the version control systems supported by eric5.

Mercurial:  sudo apt-get install mercurial kdiff3-qt
Subversion: sudo apt-get install subversion subversion-tools


7. Install eric5
----------------
Get the latest eric5 distribution package from 

http://eric-ide.python-projects.org/eric-download.html

Just follow the link on this page to the latest download.

Extract the downloaded package and language packs into a directory and install
it with this command

sudo python3 install.py

This step concludes the installation procedure. You are ready for the first
start of eric5.

The eric5 installer created an entry in the Development menu. You may add it to
the desktop.


8. First start of eric5
-----------------------
When eric5 is started for the first time it will recognize that it hasn't been
configured yet. Therefore it will start the configuration dialog with the
default configuration. At this point you could simply close the dialog by
pressing the OK button. However, it is strongly recommended that you go through
the configuration pages to get a feeling for the configuration possibilities.

It is recommended to configure at least the paths to the various help pages on
the Help Documentation page. The values to be entered are given below.

Python2:    /usr/share/doc/python/html/index.html
Python3:    /usr/share/doc/python3/html/index.html
Qt4:        /usr/share/qt4/doc/html/classes.html
PyQt4:      /usr/share/doc/python-qt4-doc/html/index.html


9. Install optional packages for eric5 (for plug-ins)
-----------------------------------------------------
eric5 provides an extension mechanism via plug-ins. Some of them require the
installation of additional python packages. The plug-ins themselves are
available via the Plugin Repository from within eric5.


9.1 Installation of pylint
--------------------------
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

Note: You may receive some errors during the above steps. They just relate to
the tests included in the packages. If this occurs, please delete the faulty
test file and retry. As of pylint 0.25.0 this file was 
"test/input/func_unknown_encoding.py".


9.2 Installation of cx_freeze
-----------------------------
cx_freeze is a tool that packages a Python application into executables. It is
like py2exe and py2app. Get the sources from

http://cx-freeze.sourceforge.net/

and extract the downloaded source archive. In the extracted cx_freeze directory
execute the command

sudo python3 setup.py install

This completes this installation instruction. Please enjoy using eric5 and let
the world know about it.


Appendix A.
-----------
In order to keep your system up-to-date execute these commands.

sudo apt-get update
sudo apt-get upgrade
sudo apt-get autoremove
