# -*- coding: utf-8 -*-

# Copyright (c) 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a CoffeeScript lexer with some additional methods.
"""

from __future__ import unicode_literals

from PyQt4.Qsci import QsciLexerCoffeScript

from .Lexer import Lexer
import Preferences


class LexerJavaScript(Lexer, QsciLexerCoffeScript):
    """
    Subclass to implement some additional lexer dependant methods.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent parent widget of this lexer
        """
        QsciLexerCoffeScript.__init__(self, parent)
        Lexer.__init__(self)
        
        self.commentString = "#"
        self.streamCommentString = {
            'start': '###\n',
            'end': '\n###'
        }

    def initProperties(self):
        """
        Public slot to initialize the properties.
        """
        self.setDollarsAllowed(
            Preferences.getEditor("CoffeeScriptDollarsAllowed"))
        self.setFoldComments(
            Preferences.getEditor("CoffeScriptFoldComment"))
        self.setStylePreprocessor(
            Preferences.getEditor("CoffeeScriptStylePreprocessor"))
        self.setFoldCompact(
            Preferences.getEditor("AllFoldCompact"))
    
    def isCommentStyle(self, style):
        """
        Public method to check, if a style is a comment style.
        
        @param style style to check (integer)
        @return flag indicating a comment style (boolean)
        """
        return style in [QsciLexerCoffeScript.Comment,
                         QsciLexerCoffeScript.CommentDoc,
                         QsciLexerCoffeScript.CommentLine,
                         QsciLexerCoffeScript.CommentLineDoc,
                         QsciLexerCoffeScript.CommentBlock,
                         QsciLexerCoffeScript.BlockRegexComment]
    
    def isStringStyle(self, style):
        """
        Public method to check, if a style is a string style.
        
        @param style style to check (integer)
        @return flag indicating a string style (boolean)
        """
        return style in [QsciLexerCoffeScript.DoubleQuotedString,
                         QsciLexerCoffeScript.SingleQuotedString,
                         QsciLexerCoffeScript.UnclosedString,
                         QsciLexerCoffeScript.VerbatimString]
    
    def defaultKeywords(self, kwSet):
        """
        Public method to get the default keywords.
        
        @param kwSet number of the keyword set (integer)
        @return string giving the keywords (string) or None
        """
        return QsciLexerCoffeScript.keywords(self, kwSet)
