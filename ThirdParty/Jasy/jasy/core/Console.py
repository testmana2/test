# -*- coding: utf-8 -*-

# Copyright (c) 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

from __future__ import unicode_literals    # __IGNORE_WARNING__

import logging

def error(text, *argv):
    """Outputs an error message"""

    logging.error(text, *argv)

def warn(text, *argv):
    """Outputs an warning"""

    logging.warn(text, *argv)

def info(text, *argv):
    """Outputs an info message"""

    logging.info(text, *argv)

def debug(text, *argv):
    """Output a debug message"""

    logging.debug(text, *argv)
