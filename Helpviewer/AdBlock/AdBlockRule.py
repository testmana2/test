# -*- coding: utf-8 -*-

# Copyright (c) 2009 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the AdBlock rule class.
"""

import re

from PyQt4.QtCore import *

class AdBlockRule(object):
    """
    Class implementing the AdBlock rule.
    """
    def __init__(self, filter = ""):
        """
        Constructor
        """
        self.__regExp = QRegExp()
        self.__options = []
        
        self.setFilter(filter)
    
    def filter(self):
        """
        Public method to get the rule filter string.
        
        @return rule filter string (string)
        """
        return self.__filter
    
    def setFilter(self, filter):
        """
        Public method to set the rule filter string.
        
        @param filter rule filter string (string)
        """
        self.__filter = filter
        
        self.__cssRule = False
        self.__enabled = True
        self.__exception = False
        regExpRule = False
        
        if filter.startswith("!") or not filter.strip():
            self.__enabled = False
        
        if "##" in filter:
            self.__cssRule = True
        
        parsedLine = filter
        if parsedLine.startswith("@@"):
            self.__exception = True
            parsedLine = parsedLine[2:]
        if parsedLine.startswith("/"):
            if parsedLine.endswith("/"):
                parsedLine = parsedLine[1:-1]
                regExpRule = True
        
        options = parsedLine.find("$")
        if options >= 0:
            self.__options = parsedLine[options + 1].split(",")
            parsedLine = parsedLine[:options]
        
        self.setPattern(parsedLine, regExpRule)
        
        if "match-case" in self.__options:
            self.__regExp.setCaseSensitivity(Qt.CaseSensitive)
            self.__options.remove("match-case")
    
    def networkMatch(self, encodedUrl):
        """
        Public method to check the rule for a match.
        
        @param encodedUrl string encoded URL to be checked (string)
        @return flag indicating a match (boolean)
        """
        if self.__cssRule:
            return False
        
        if not self.__enabled:
            return False
        
        matched = self.__regExp.indexIn(encodedUrl) != -1
        
        if matched and not len(self.__options) == 0:
            # only domain rules are supported
            if len(self.__options) == 1:
                for option in self.__options:
                    if option.startswith("domain="):
                        url = QUrl.fromEncoded(encodedUrl)
                        host = url.host()
                        domainOptions = option[7:].split("|")
                        for domainOption in domainOptions:
                            negate = domainOption.startswith("~")
                            if negate:
                                domainOption = domainOption[1:]
                            hostMatched = domainOption == host
                            if hostMatched and not negate:
                                return True
                            if not hostMatched and negate:
                                return True
            
            return False
        
        return matched
    
    def isException(self):
        """
        Public method to check, if the rule defines an exception.
        
        @return flag indicating an exception (boolean)
        """
        return self.__exception
    
    def setException(self, exception):
        """
        Public method to set the rule's exception flag.
        
        @param exception flag indicating an exception rule (boolean)
        """
        self.__exception = exception
    
    def isEnabled(self):
        """
        Public method to check, if the rule is enabled.
        
        @return flag indicating enabled state (boolean)
        """
        return self.__enabled
    
    def setEnabled(self, enabled):
        """
        Public method to set the rule's enabled state.
        
        @param enabled flag indicating the new enabled state (boolean)
        """
        self.__enabled = enabled
        if not enabled:
            self.__filter = "!" + self.__filter
        else:
            self.__filter = self.__filter[1:]
    
    def isCSSRule(self):
        """
        Public method to check, if the rule is a CSS rule.
        
        @return flag indicating a CSS rule (boolean)
        """
        return self.__cssRule
    
    def regExpPattern(self):
        """
        Public method to get the regexp pattern of the rule.
        
        @return regexp pattern (QRegExp)
        """
        return self.__regExp.pattern()
    
    def __convertPatternToRegExp(self, wildcardPattern):
        """
        Private method to convert a wildcard pattern to a regular expression.
        
        @param wildcardPattern string containing the wildcard pattern (string)
        @return string containing a regular expression (string)
        """
        pattern = wildcardPattern
        
        pattern = re.sub(r"\*+", "*", pattern)      # remove multiple wildcards
        pattern = re.sub(r"\^\|$", "^", pattern)    # remove anchors following separator placeholder
        pattern = re.sub(r"^(\*)", "", pattern)     # remove leading wildcards
        pattern = re.sub(r"(\*)$", "", pattern)     # remove trailing wildcards
        pattern = re.sub(r"(\W)", "", pattern)      # escape special symbols
        pattern = re.sub(r"^\\\|\\\|",
            r"^[\w\-]+:\/+(?!\/)(?:[^\/]+\.)?", pattern) # process extended anchor at expression start
        pattern = re.sub(r"\\\^", 
            r"(?:[^\w\d\-.%]|$)", pattern)          # process separator placeholders
        pattern = re.sub(r"^\\\|", "^", pattern)    # process anchor at expression start
        pattern = re.sub(r"\\\|$", "$", pattern)    # process anchor at expression end
        pattern = re.sub(r"\\\*", ".*", pattern)    # replace wildcards by .*
        
        return pattern
    
    def setPattern(self, pattern, isRegExp):
        """
        Public method to set the rule pattern.
        
        @param pattern string containing the pattern (string)
        @param isRegExp flag indicating a reg exp pattern (boolean)
        """
        if isRegExp:
            self.__regExp = QRegExp(pattern, Qt.CaseInsensitive, QRegExp.RegExp2)
        else:
            self.__regExp = QRegExp(self.__convertPatternToRegExp(pattern), 
                                    Qt.CaseInsensitive, QRegExp.RegExp2)
