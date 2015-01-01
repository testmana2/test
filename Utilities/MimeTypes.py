# -*- coding: utf-8 -*-

# Copyright (c) 2014 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing mimetype dependent functions.
"""

from __future__ import unicode_literals

import mimetypes

TextMimeTypes = [
    "application/bookmarks.xbel",
    "application/opensearchdescription+xml",
    "application/x-actionscript",
    "application/x-actionscript3",
    "application/x-awk",
    "application/x-sh",
    "application/x-shellscript",
    "application/x-shell-session",
    "application/x-dos-batch",
    "application/x-befunge",
    "application/x-brainfuck",
    "application/x-javascript+cheetah",
    "application/x-javascript+spitfire",
    "application/x-cheetah",
    "application/x-spitfire",
    "application/xml+cheetah",
    "application/xml+spitfire",
    "application/x-clojure",
    "application/x-coldfusion",
    "application/x-cython",
    "application/x-django-templating",
    "application/x-jinja",
    "application/xml-dtd",
    "application/x-ecl",
    "application/x-ruby-templating",
    "application/x-evoque",
    "application/xml+evoque",
    "application/x-fantom",
    "application/x-genshi",
    "application/x-kid",
    "application/x-genshi-text",
    "application/x-gettext",
    "application/x-troff",
    "application/xhtml+xml",
    "application/x-php",
    "application/x-httpd-php",
    "application/x-httpd-php3",
    "application/x-httpd-php4",
    "application/x-httpd-php5",
    "application/x-hybris",
    "application/x-javascript+django",
    "application/x-javascript+jinja",
    "application/x-javascript+ruby",
    "application/x-javascript+genshi",
    "application/javascript",
    "application/x-javascript",
    "application/x-javascript+php",
    "application/x-javascript+smarty",
    "application/json",
    "application/x-jsp",
    "application/x-julia",
    "application/x-httpd-lasso",
    "application/x-httpd-lasso[89]",
    "application/x-httpd-lasso8",
    "application/x-httpd-lasso9",
    "application/x-javascript+lasso",
    "application/xml+lasso",
    "application/x-lua",
    "application/x-javascript+mako",
    "application/x-mako",
    "application/xml+mako",
    "application/x-gooddata-maql",
    "application/x-mason",
    "application/x-moonscript",
    "application/x-javascript+myghty",
    "application/x-myghty",
    "application/xml+myghty",
    "application/x-newlisp",
    "application/x-openedge",
    "application/x-perl",
    "application/postscript",
    "application/x-pypylog",
    "application/x-python3",
    "application/x-python",
    "application/x-qml",
    "application/x-racket",
    "application/x-pygments-tokens",
    "application/x-ruby",
    "application/x-standardml",
    "application/x-scheme",
    "application/x-sh-session",
    "application/x-smarty",
    "application/x-ssp",
    "application/x-tcl",
    "application/x-csh",
    "application/x-urbiscript",
    "application/xml+velocity",
    "application/xquery",
    "application/xml+django",
    "application/xml+jinja",
    "application/xml+ruby",
    "application/xml",
    "application/rss+xml",
    "application/atom+xml",
    "application/xml+php",
    "application/xml+smarty",
    "application/xsl+xml",
    "application/xslt+xml",
    "application/x-desktop",
    
    "image/svg+xml",
]


def isTextFile(filename):
    """
    Function to test, if the given file is a text (i.e. editable) file.
    
    @param filename name of the file to be checked (string)
    @return flag indicating an editable file (boolean)
    """
    type_ = mimetypes.guess_type(filename)[0]
    if (type_ is None or
        type_.split("/")[0] == "text" or
            type_ in TextMimeTypes):
        return True
    else:
        return False
