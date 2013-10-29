# -*- coding: utf-8 -*-

# Copyright (c) 2008 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a YAML lexer with some additional methods.
"""

from PyQt4.Qsci import QsciLexerYAML

from .Lexer import Lexer
import Preferences


class LexerYAML(QsciLexerYAML, Lexer):
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
        
        self.commentString = "---"
    
    def initProperties(self):
        """
        Public slot to initialize the properties.
        """
        self.setFoldComments(Preferences.getEditor("YAMLFoldComment"))
    
    def isCommentStyle(self, style):
        """
        Public method to check, if a style is a comment style.
        
        @param style style to check (integer)
        @return flag indicating a comment style (boolean)
        """
        return style in [QsciLexerYAML.Comment]
    
    def isStringStyle(self, style):
        """
        Public method to check, if a style is a string style.
        
        @param style style to check (integer)
        @return flag indicating a string style (boolean)
        """
        return False
    
    def defaultKeywords(self, kwSet):
        """
        Public method to get the default keywords.
        
        @param kwSet number of the keyword set (integer)
        @return string giving the keywords (string) or None
        """
        return QsciLexerYAML.keywords(self, kwSet)
