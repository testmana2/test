# -*- coding: utf-8 -*-

# Copyright (c) 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show the VirusTotal domain report.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QTreeWidgetItem

from .Ui_VirusTotalDomainReportDialog import Ui_VirusTotalDomainReportDialog


class VirusTotalDomainReportDialog(QDialog, Ui_VirusTotalDomainReportDialog):
    """
    Class implementing a dialog to show the VirusTotal domain report.
    """
    def __init__(self, domain, resolutions, urls, subdomains,
                 bdCategory, tmCategory, wtsCategory, categories, parent=None):
        """
        Constructor
        
        @param domain domain name
        @type str
        @param resolutions list of resolved host names
        @type list of dict
        @param urls list of detected URLs
        @type list of dict
        @param subdomains list of subdomains
        @type list of str
        @param bdCategory BitDefender categorization
        @type str
        @param tmCategory TrendMicro categorization
        @type str
        @param wtsCategory Websense ThreatSeeker categorization
        @type str
        @param categories list of categorizations
        @type list of str
        @param parent reference to the parent widget
        @type QWidget
        """
        super(VirusTotalDomainReportDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        
        self.headerLabel.setText(
            self.tr("<b>Report for domain {0}</b>").format(domain))
        
        for resolution in resolutions:
            QTreeWidgetItem(
                self.resolutionsList,
                [resolution["ip_address"],
                 resolution["last_resolved"].split()[0]]
            )
        self.resolutionsList.resizeColumnToContents(0)
        self.resolutionsList.resizeColumnToContents(1)
        self.resolutionsList.sortByColumn(0, Qt.AscendingOrder)
        
        if not urls:
            self.detectedUrlsGroup.setVisible(False)
        for url in urls:
            QTreeWidgetItem(
                self.urlsList,
                [url["url"],
                 self.tr("{0}/{1}", "positives / total").format(
                    url["positives"], url["total"]),
                 url["scan_date"].split()[0]]
            )
        self.urlsList.resizeColumnToContents(0)
        self.urlsList.resizeColumnToContents(1)
        self.urlsList.resizeColumnToContents(2)
        self.urlsList.sortByColumn(0, Qt.AscendingOrder)
        
        if not subdomains:
            self.subdomainsGroup.setVisible(False)
        else:
            self.subdomainsList.addItems(subdomains)
            self.subdomainsList.sortItems()
        
        self.bdLabel.setText(bdCategory)
        self.tmLabel.setText(tmCategory)
        self.wtsLabel.setText(wtsCategory)
##        
##        if not categories:
##            self.categoriesList.setVisible(False)
##        else:
##            self.categoriesList.addItems(categories)
##            self.categoriesList.sortItems()
