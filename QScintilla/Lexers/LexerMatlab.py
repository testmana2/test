# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a Matlab lexer with some additional methods.
"""

from __future__ import unicode_literals    # __IGNORE_WARNING__

from PyQt4.Qsci import QsciLexerMatlab

from .Lexer import Lexer


class LexerMatlab(QsciLexerMatlab, Lexer):
    """
    Subclass to implement some additional lexer dependent methods.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent parent widget of this lexer
        """
        super(LexerMatlab, self).__init__(parent)
        Lexer.__init__(self)
        
        self.commentString = "%~"
    
    def isCommentStyle(self, style):
        """
        Public method to check, if a style is a comment style.
        
        @param style style to check (integer)
        @return flag indicating a comment style (boolean)
        """
        return style in [QsciLexerMatlab.Comment]
    
    def isStringStyle(self, style):
        """
        Public method to check, if a style is a string style.
        
        @param style style to check (integer)
        @return flag indicating a string style (boolean)
        """
        return style in [QsciLexerMatlab.DoubleQuotedString,
                         QsciLexerMatlab.SingleQuotedString]
    
    def defaultKeywords(self, kwSet):
        """
        Public method to get the default keywords.
        
        @param kwSet number of the keyword set (integer)
        @return string giving the keywords (string) or None
        """
        return QsciLexerMatlab.keywords(self, kwSet)
