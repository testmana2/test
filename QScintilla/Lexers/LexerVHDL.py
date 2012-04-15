# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a VHDL lexer with some additional methods.
"""

from PyQt4.Qsci import QsciLexerVHDL

from .Lexer import Lexer
import Preferences


class LexerVHDL(QsciLexerVHDL, Lexer):
    """
    Subclass to implement some additional lexer dependant methods.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent parent widget of this lexer
        """
        super().__init__(parent)
        Lexer.__init__(self)
        
        self.commentString = "--"
    
    def initProperties(self):
        """
        Public slot to initialize the properties.
        """
        self.setFoldComments(Preferences.getEditor("VHDLFoldComment"))
        self.setFoldAtElse(Preferences.getEditor("VHDLFoldAtElse"))
        self.setFoldAtBegin(Preferences.getEditor("VHDLFoldAtBegin"))
        self.setFoldAtParenthesis(
            Preferences.getEditor("VHDLFoldAtParenthesis"))
        self.setFoldCompact(Preferences.getEditor("AllFoldCompact"))
    
    def isCommentStyle(self, style):
        """
        Public method to check, if a style is a comment style.
        
        @return flag indicating a comment style (boolean)
        """
        return style in [QsciLexerVHDL.Comment,
                         QsciLexerVHDL.CommentLine]
    
    def isStringStyle(self, style):
        """
        Public method to check, if a style is a string style.
        
        @return flag indicating a string style (boolean)
        """
        return style in [QsciLexerVHDL.String,
                         QsciLexerVHDL.UnclosedString]
    
    def defaultKeywords(self, kwSet):
        """
        Public method to get the default keywords.
        
        @param kwSet number of the keyword set (integer)
        @return string giving the keywords (string) or None
        """
        return QsciLexerVHDL.keywords(self, kwSet)
