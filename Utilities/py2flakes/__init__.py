# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Package containg the pyflakes Python2 port adapted for Qt.
"""

""" License
Copyright 2005-2011 Divmod, Inc.
Copyright 2013 Florent Xicluna

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

""" Changes
0.6.1 (2013-01-29):
  - Fix detection of variables in augmented assignments.

0.6.0 (2013-01-29):
  - Support Python 3 up to 3.3, based on the pyflakes3k project.
  - Preserve compatibility with Python 2.5 and all recent versions of Python.
  - Support custom reporters in addition to the default Reporter.
  - Allow function redefinition for modern property construction via
    property.setter/deleter.
  - Fix spurious redefinition warnings in conditionals.
  - Do not report undefined name in __all__ if import * is used.
  - Add WindowsError as a known built-in name on all platforms.
  - Support specifying additional built-ins in the `Checker` constructor.
  - Don't issue Unused Variable warning when using locals() in current scope.
  - Handle problems with the encoding of source files.
  - Remove dependency on Twisted for the tests.
  - Support `python setup.py test` and `python setup.py develop`.
  - Create script using setuptools `entry_points` to support all platforms,
    including Windows.

0.5.0 (2011-09-02):
  - Convert pyflakes to use newer _ast infrastructure rather than compiler.
  - Support for new syntax in 2.7 (including set literals, set comprehensions,
    and dictionary comprehensions).
  - Make sure class names don't get bound until after class definition.
"""

__version__ = '0.6.1'
