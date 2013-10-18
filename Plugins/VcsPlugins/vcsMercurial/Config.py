# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module defining configuration variables for the Mercurial package.
"""

from __future__ import unicode_literals    # __IGNORE_WARNING__

# Available protocols fpr the repository URL
ConfigHgProtocols = [
    'file://',
    'http://',
    'https://',
    'ssh://',
]
