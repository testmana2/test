# -*- coding: utf-8 -*-

# Copyright (c) 2008 - 2009 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a Fortran lexer with some additional methods.
"""

from PyQt4.Qsci import QsciLexerFortran77, QsciScintilla

from Lexer import Lexer
import Preferences

class LexerFortran77(QsciLexerFortran77, Lexer):
    """ 
    Subclass to implement some additional lexer dependant methods.
    """
    def __init__(self, parent = None):
        """
        Constructor
        
        @param parent parent widget of this lexer
        """
        QsciLexerFortran77.__init__(self, parent)
        Lexer.__init__(self)
        
        self.commentString = "c"
    
    def initProperties(self):
        """
        Public slot to initialize the properties.
        """
        self.setFoldCompact(Preferences.getEditor("AllFoldCompact"))
    
    def autoCompletionWordSeparators(self):
        """
        Public method to return the list of separators for autocompletion.
        
        @return list of separators (list of strings)
        """
        return ['.']
    
    def isCommentStyle(self, style):
        """
        Public method to check, if a style is a comment style.
        
        @return flag indicating a comment style (boolean)
        """
        return style in [QsciLexerFortran77.Comment]
    
    def isStringStyle(self, style):
        """
        Public method to check, if a style is a string style.
        
        @return flag indicating a string style (boolean)
        """
        return style in [QsciLexerFortran77.DoubleQuotedString, 
                         QsciLexerFortran77.SingleQuotedString, 
                         QsciLexerFortran77.UnclosedString]
