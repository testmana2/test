# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a SQL lexer with some additional methods.
"""

from PyQt4.Qsci import QsciLexerSQL

from .Lexer import Lexer
import Preferences


class LexerSQL(QsciLexerSQL, Lexer):
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
        self.setFoldComments(Preferences.getEditor("SqlFoldComment"))
        self.setBackslashEscapes(Preferences.getEditor("SqlBackslashEscapes"))
        self.setFoldCompact(Preferences.getEditor("AllFoldCompact"))
        try:
            self.setDottedWords(Preferences.getEditor("SqlDottedWords"))
            self.setFoldAtElse(Preferences.getEditor("SqlFoldAtElse"))
            self.setFoldOnlyBegin(Preferences.getEditor("SqlFoldOnlyBegin"))
            self.setHashComments(Preferences.getEditor("SqlHashComments"))
            self.setQuotedIdentifiers(
                Preferences.getEditor("SqlQuotedIdentifiers"))
        except AttributeError:
            pass
    
    def isCommentStyle(self, style):
        """
        Public method to check, if a style is a comment style.
        
        @param style style to check (integer)
        @return flag indicating a comment style (boolean)
        """
        return style in [QsciLexerSQL.Comment,
                         QsciLexerSQL.CommentDoc,
                         QsciLexerSQL.CommentLine,
                         QsciLexerSQL.CommentLineHash]
    
    def isStringStyle(self, style):
        """
        Public method to check, if a style is a string style.
        
        @param style style to check (integer)
        @return flag indicating a string style (boolean)
        """
        return style in [QsciLexerSQL.DoubleQuotedString,
                         QsciLexerSQL.SingleQuotedString]
    
    def defaultKeywords(self, kwSet):
        """
        Public method to get the default keywords.
        
        @param kwSet number of the keyword set (integer)
        @return string giving the keywords (string) or None
        """
        return QsciLexerSQL.keywords(self, kwSet)
