# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2009 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing an IDL lexer with some additional methods.
"""

from PyQt4.Qsci import QsciLexerIDL,  QsciScintilla

from .Lexer import Lexer
import Preferences

class LexerIDL(QsciLexerIDL, Lexer):
    """ 
    Subclass to implement some additional lexer dependant methods.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent parent widget of this lexer
        """
        QsciLexerIDL.__init__(self, parent)
        Lexer.__init__(self)
        
        self.commentString = "//"
        self.streamCommentString = {
            'start' : '/* ',
            'end'   : ' */'
        }
        self.boxCommentString = {
            'start'  : '/* ',
            'middle' : ' * ',
            'end'    : ' */'
        }

    def initProperties(self):
        """
        Public slot to initialize the properties.
        """
        self.setFoldComments(Preferences.getEditor("CppFoldComment"))
        self.setFoldPreprocessor(Preferences.getEditor("CppFoldPreprocessor"))
        self.setFoldAtElse(Preferences.getEditor("CppFoldAtElse"))
        indentStyle = 0
        if Preferences.getEditor("CppIndentOpeningBrace"):
            indentStyle |= QsciScintilla.AiOpening
        if Preferences.getEditor("CppIndentClosingBrace"):
            indentStyle |= QsciScintilla.AiClosing
        self.setAutoIndentStyle(indentStyle)
        self.setFoldCompact(Preferences.getEditor("AllFoldCompact"))
    
    def isCommentStyle(self, style):
        """
        Public method to check, if a style is a comment style.
        
        @return flag indicating a comment style (boolean)
        """
        return style in [QsciLexerIDL.Comment, 
                         QsciLexerIDL.CommentDoc, 
                         QsciLexerIDL.CommentLine, 
                         QsciLexerIDL.CommentLineDoc]
    
    def isStringStyle(self, style):
        """
        Public method to check, if a style is a string style.
        
        @return flag indicating a string style (boolean)
        """
        return style in [QsciLexerIDL.DoubleQuotedString, 
                         QsciLexerIDL.SingleQuotedString, 
                         QsciLexerIDL.UnclosedString, 
                         QsciLexerIDL.VerbatimString]
