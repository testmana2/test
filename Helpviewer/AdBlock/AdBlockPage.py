# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a class to apply AdBlock rules to a web page.
"""

from PyQt4.QtCore import *
from PyQt4 import QtWebKit

import Helpviewer.HelpWindow

class AdBlockPage(QObject):
    """
    Class to apply AdBlock rules to a web page.
    """
    def __checkRule(self, rule, page, host):
        """
        Private method to check, if a rule applies to the given web page and host.
        
        @param rule reference to the rule to check (AdBlockRule)
        @param page reference to the web page (QWebPage)
        @param host host name (string)
        """
        if hasattr(QtWebKit, 'QWebElement'):
            if not rule.isEnabled():
                return
            
            filter = rule.filter()
            offset = filter.find("##")
            if offset == -1:
                return
            
            selectorQuery = ""
            if offset > 0:
                domainRules = filter[:offset]
                selectorQuery = filter[offset + 2:]
                domains = domainRules.split(",")
                
                match = False
                for domain in domains:
                    reverse = domain[0] == '~'
                    if reverse:
                        xdomain = domain[1:]
                        if host.endswith(xdomain):
                            return
                        match = True
                    if host.endswith(domain):
                        match = True
                if not match:
                    return
            
            if offset == 0:
                selectorQuery = filter[2:]
            
            document = page.mainFrame().documentElement()
            elements = document.findAll(selectorQuery)
            for element in elements.toList():
                element.setStyleProperty("visibility", "hidden")
                element.removeFromDocument()
    
    def applyRulesToPage(self, page):
        """
        Public method to applay AdBlock rules to a web page.
        
        @param page reference to the web page (QWebPage)
        """
        if hasattr(QtWebKit, 'QWebElement'):
            if page is None or page.mainFrame() is None:
                return
            
            manager = Helpviewer.HelpWindow.HelpWindow.adblockManager()
            if not manager.isEnabled():
                return
            
            host = page.mainFrame().url().host()
            subscriptions = manager.subscriptions()
            for subscription in subscriptions:
                rules = subscription.pageRules()
                for rule in rules:
                    self.__checkRule(rule, page, host)
