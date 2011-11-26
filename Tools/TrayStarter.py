# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a starter for the system tray.
"""

import sys
import os

from PyQt4.QtCore import QProcess, QSettings, QFileInfo
from PyQt4.QtGui  import QSystemTrayIcon, QMenu, qApp, QCursor, QApplication, QDialog

from E5Gui import E5MessageBox

import Globals
import UI.PixmapCache

import Utilities
import Preferences

from eric5config import getConfig


class TrayStarter(QSystemTrayIcon):
    """
    Class implementing a starter for the system tray.
    """
    def __init__(self):
        """
        Constructor
        """
        super().__init__(
            UI.PixmapCache.getIcon(Preferences.getTrayStarter("TrayStarterIcon")))
        
        self.maxMenuFilePathLen = 75
        
        self.rsettings = QSettings(QSettings.IniFormat,
            QSettings.UserScope,
            Globals.settingsNameOrganization,
            Globals.settingsNameRecent)
        
        self.recentProjects = []
        self.__loadRecentProjects()
        self.recentMultiProjects = []
        self.__loadRecentMultiProjects()
        self.recentFiles = []
        self.__loadRecentFiles()
        
        self.activated.connect(self.__activated)
        
        self.__menu = QMenu(self.trUtf8("Eric5 tray starter"))
        
        self.recentProjectsMenu = QMenu(self.trUtf8('Recent Projects'), self.__menu)
        self.recentProjectsMenu.aboutToShow.connect(self.__showRecentProjectsMenu)
        self.recentProjectsMenu.triggered.connect(self.__openRecent)
        
        self.recentMultiProjectsMenu = \
            QMenu(self.trUtf8('Recent Multiprojects'), self.__menu)
        self.recentMultiProjectsMenu.aboutToShow.connect(
            self.__showRecentMultiProjectsMenu)
        self.recentMultiProjectsMenu.triggered.connect(self.__openRecent)
        
        self.recentFilesMenu = QMenu(self.trUtf8('Recent Files'), self.__menu)
        self.recentFilesMenu.aboutToShow.connect(self.__showRecentFilesMenu)
        self.recentFilesMenu.triggered.connect(self.__openRecent)
        
        act = self.__menu.addAction(
            self.trUtf8("Eric5 tray starter"), self.__about)
        font = act.font()
        font.setBold(True)
        act.setFont(font)
        self.__menu.addSeparator()
        
        self.__menu.addAction(self.trUtf8("QRegExp editor"), self.__startQRegExp)
        self.__menu.addAction(self.trUtf8("Python re editor"), self.__startPyRe)
        self.__menu.addSeparator()
        
        self.__menu.addAction(UI.PixmapCache.getIcon("uiPreviewer.png"),
            self.trUtf8("UI Previewer"), self.__startUIPreviewer)
        self.__menu.addAction(UI.PixmapCache.getIcon("trPreviewer.png"),
            self.trUtf8("Translations Previewer"), self.__startTRPreviewer)
        self.__menu.addAction(UI.PixmapCache.getIcon("unittest.png"),
            self.trUtf8("Unittest"), self.__startUnittest)
        self.__menu.addAction(UI.PixmapCache.getIcon("ericWeb.png"),
            self.trUtf8("eric5 Web Browser"), self.__startHelpViewer)
        self.__menu.addSeparator()
        
        self.__menu.addAction(UI.PixmapCache.getIcon("diffFiles.png"),
            self.trUtf8("Compare Files"), self.__startDiff)
        self.__menu.addAction(UI.PixmapCache.getIcon("compareFiles.png"),
            self.trUtf8("Compare Files side by side"), self.__startCompare)
        self.__menu.addSeparator()
        
        self.__menu.addAction(UI.PixmapCache.getIcon("sqlBrowser.png"),
            self.trUtf8("SQL Browser"), self.__startSqlBrowser)
        self.__menu.addSeparator()
        
        self.__menu.addAction(UI.PixmapCache.getIcon("iconEditor.png"),
            self.trUtf8("Icon Editor"), self.__startIconEditor)
        self.__menu.addSeparator()
        
        self.__menu.addAction(UI.PixmapCache.getIcon("pluginInstall.png"),
            self.trUtf8("Install Plugin"), self.__startPluginInstall)
        self.__menu.addAction(UI.PixmapCache.getIcon("pluginUninstall.png"),
            self.trUtf8("Uninstall Plugin"), self.__startPluginUninstall)
        self.__menu.addAction(UI.PixmapCache.getIcon("pluginRepository.png"),
            self.trUtf8("Plugin Repository"), self.__startPluginRepository)
        self.__menu.addSeparator()
        
        self.__menu.addAction(UI.PixmapCache.getIcon("configure.png"),
            self.trUtf8('Preferences'), self.__startPreferences)
        self.__menu.addAction(UI.PixmapCache.getIcon("erict.png"),
            self.trUtf8("eric5 IDE"), self.__startEric)
        self.__menu.addAction(UI.PixmapCache.getIcon("editor.png"),
            self.trUtf8("eric5 Mini Editor"), self.__startMiniEditor)
        self.__menu.addSeparator()
        
        self.__menu.addAction(UI.PixmapCache.getIcon("configure.png"),
            self.trUtf8('Preferences (tray starter)'), self.__showPreferences)
        self.__menu.addSeparator()
        
        # recent files
        self.menuRecentFilesAct = self.__menu.addMenu(self.recentFilesMenu)
        # recent multi projects
        self.menuRecentMultiProjectsAct = \
            self.__menu.addMenu(self.recentMultiProjectsMenu)
        # recent projects
        self.menuRecentProjectsAct = self.__menu.addMenu(self.recentProjectsMenu)
        self.__menu.addSeparator()
        
        self.__menu.addAction(UI.PixmapCache.getIcon("exit.png"),
            self.trUtf8('Quit'), qApp.quit)
    
    def __loadRecentProjects(self):
        """
        Private method to load the recently opened project filenames.
        """
        rp = self.rsettings.value(Globals.recentNameProject)
        if rp is not None:
            for f in rp:
                if QFileInfo(f).exists():
                    self.recentProjects.append(f)
    
    def __loadRecentMultiProjects(self):
        """
        Private method to load the recently opened multi project filenames.
        """
        rmp = self.rsettings.value(Globals.recentNameMultiProject)
        if rmp is not None:
            for f in rmp:
                if QFileInfo(f).exists():
                    self.recentMultiProjects.append(f)
    
    def __loadRecentFiles(self):
        """
        Private method to load the recently opened filenames.
        """
        rf = self.rsettings.value(Globals.recentNameFiles)
        if rf is not None:
            for f in rf:
                if QFileInfo(f).exists():
                    self.recentFiles.append(f)
    
    def __activated(self, reason):
        """
        Private slot to handle the activated signal.
        
        @param reason reason code of the signal (QSystemTrayIcon.ActivationReason)
        """
        if reason == QSystemTrayIcon.Context or \
           reason == QSystemTrayIcon.MiddleClick:
            self.__showContextMenu()
        elif reason == QSystemTrayIcon.DoubleClick:
            self.__startEric()
    
    def __showContextMenu(self):
        """
        Private slot to show the context menu.
        """
        self.menuRecentProjectsAct.setEnabled(len(self.recentProjects) > 0)
        self.menuRecentMultiProjectsAct.setEnabled(len(self.recentMultiProjects) > 0)
        self.menuRecentFilesAct.setEnabled(len(self.recentFiles) > 0)
        
        pos = QCursor.pos()
        x = pos.x() - self.__menu.sizeHint().width()
        pos.setX(x > 0 and x or 0)
        y = pos.y() - self.__menu.sizeHint().height()
        pos.setY(y > 0 and y or 0)
        self.__menu.popup(pos)
    
    def __startProc(self, applName, *applArgs):
        """
        Private method to start an eric5 application.
        
        @param applName name of the eric5 application script (string)
        @param *applArgs variable list of application arguments
        """
        proc = QProcess()
        applPath = os.path.join(getConfig("ericDir"), applName)
        
        args = []
        args.append(applPath)
        for arg in applArgs:
            args.append(arg)
        
        if not os.path.isfile(applPath) or not proc.startDetached(sys.executable, args):
            E5MessageBox.critical(self,
                self.trUtf8('Process Generation Error'),
                self.trUtf8(
                    '<p>Could not start the process.<br>'
                    'Ensure that it is available as <b>{0}</b>.</p>'
                ).format(applPath),
                self.trUtf8('OK'))
    
    def __startMiniEditor(self):
        """
        Private slot to start the eric5 Mini Editor.
        """
        self.__startProc("eric5_editor.py", "--config={0}".format(
            Utilities.getConfigDir()))
    
    def __startEric(self):
        """
        Private slot to start the eric5 IDE.
        """
        self.__startProc("eric5.py", "--config={0}".format(
            Utilities.getConfigDir()))

    def __startPreferences(self):
        """
        Private slot to start the eric5 configuration dialog.
        """
        self.__startProc("eric5_configure.py", "--config={0}".format(
            Utilities.getConfigDir()))

    def __startPluginInstall(self):
        """
        Private slot to start the eric5 plugin installation dialog.
        """
        self.__startProc("eric5_plugininstall.py", "--config={0}".format(
            Utilities.getConfigDir()))

    def __startPluginUninstall(self):
        """
        Private slot to start the eric5 plugin uninstallation dialog.
        """
        self.__startProc("eric5_pluginuninstall.py", "--config={0}".format(
            Utilities.getConfigDir()))

    def __startPluginRepository(self):
        """
        Private slot to start the eric5 plugin repository dialog.
        """
        self.__startProc("eric5_pluginrepository.py", "--config={0}".format(
            Utilities.getConfigDir()))

    def __startHelpViewer(self):
        """
        Private slot to start the eric5 web browser.
        """
        self.__startProc("eric5_webbrowser.py", "--config={0}".format(
            Utilities.getConfigDir()))

    def __startUIPreviewer(self):
        """
        Private slot to start the eric5 UI previewer.
        """
        self.__startProc("eric5_uipreviewer.py", "--config={0}".format(
            Utilities.getConfigDir()))

    def __startTRPreviewer(self):
        """
        Private slot to start the eric5 translations previewer.
        """
        self.__startProc("eric5_trpreviewer.py", "--config={0}".format(
            Utilities.getConfigDir()))

    def __startUnittest(self):
        """
        Private slot to start the eric5 unittest dialog.
        """
        self.__startProc("eric5_unittest.py", "--config={0}".format(
            Utilities.getConfigDir()))

    def __startDiff(self):
        """
        Private slot to start the eric5 diff dialog.
        """
        self.__startProc("eric5_diff.py", "--config={0}".format(
            Utilities.getConfigDir()))

    def __startCompare(self):
        """
        Private slot to start the eric5 compare dialog.
        """
        self.__startProc("eric5_compare.py", "--config={0}".format(
            Utilities.getConfigDir()))
    
    def __startSqlBrowser(self):
        """
        Private slot to start the eric5 sql browser dialog.
        """
        self.__startProc("eric5_sqlbrowser.py", "--config={0}".format(
            Utilities.getConfigDir()))

    def __startIconEditor(self):
        """
        Private slot to start the eric5 icon editor dialog.
        """
        self.__startProc("eric5_iconeditor.py", "--config={0}".format(
            Utilities.getConfigDir()))

    def __startQRegExp(self):
        """
        Private slot to start the eric5 QRegExp editor dialog.
        """
        self.__startProc("eric5_qregexp.py", "--config={0}".format(
            Utilities.getConfigDir()))

    def __startPyRe(self):
        """
        Private slot to start the eric5 Python re editor dialog.
        """
        self.__startProc("eric5_re.py", "--config={0}".format(
            Utilities.getConfigDir()))

    def __showRecentProjectsMenu(self):
        """
        Private method to set up the recent projects menu.
        """
        self.recentProjects = []
        self.rsettings.sync()
        self.__loadRecentProjects()
        
        self.recentProjectsMenu.clear()
        
        idx = 1
        for rp in self.recentProjects:
            if idx < 10:
                formatStr = '&{0:d}. {1}'
            else:
                formatStr = '{0:d}. {1}'
            act = self.recentProjectsMenu.addAction(
                formatStr.format(idx,
                    Utilities.compactPath(rp, self.maxMenuFilePathLen)))
            act.setData(rp)
            idx += 1
    
    def __showRecentMultiProjectsMenu(self):
        """
        Private method to set up the recent multi projects menu.
        """
        self.recentMultiProjects = []
        self.rsettings.sync()
        self.__loadRecentMultiProjects()
        
        self.recentMultiProjectsMenu.clear()
        
        idx = 1
        for rmp in self.recentMultiProjects:
            if idx < 10:
                formatStr = '&{0:d}. {1}'
            else:
                formatStr = '{0:d}. {1}'
            act = self.recentMultiProjectsMenu.addAction(
                formatStr.format(idx,
                    Utilities.compactPath(rmp, self.maxMenuFilePathLen)))
            act.setData(rmp)
            idx += 1
    
    def __showRecentFilesMenu(self):
        """
        Private method to set up the recent files menu.
        """
        self.recentFiles = []
        self.rsettings.sync()
        self.__loadRecentFiles()
        
        self.recentFilesMenu.clear()
        
        idx = 1
        for rf in self.recentFiles:
            if idx < 10:
                formatStr = '&{0:d}. {1}'
            else:
                formatStr = '{0:d}. {1}'
            act = self.recentFilesMenu.addAction(
                formatStr.format(idx,
                    Utilities.compactPath(rf, self.maxMenuFilePathLen)))
            act.setData(rf)
            idx += 1
    
    def __openRecent(self, act):
        """
        Private method to open a project or file from the list of rencently opened
        projects or files.
        
        @param act reference to the action that triggered (QAction)
        """
        filename = act.data()
        if filename:
            self.__startProc("eric5.py", filename)
    
    def __showPreferences(self):
        """
        Private slot to set the preferences.
        """
        from Preferences.ConfigurationDialog import ConfigurationDialog
        dlg = ConfigurationDialog(None, 'Configuration', True,
                                  fromEric=True,
                                  displayMode=ConfigurationDialog.TrayStarterMode)
        dlg.preferencesChanged.connect(self.preferencesChanged)
        dlg.show()
        dlg.showConfigurationPageByName("trayStarterPage")
        dlg.exec_()
        QApplication.processEvents()
        if dlg.result() == QDialog.Accepted:
            dlg.setPreferences()
            Preferences.syncPreferences()
            self.preferencesChanged()
    
    def preferencesChanged(self):
        """
        Public slot to handle a change of preferences.
        """
        self.setIcon(
            UI.PixmapCache.getIcon(Preferences.getTrayStarter("TrayStarterIcon")))

    def __about(self):
        """
        Private slot to handle the About dialog.
        """
        from Plugins.AboutPlugin.AboutDialog import AboutDialog
        dlg = AboutDialog()
        dlg.exec_()
