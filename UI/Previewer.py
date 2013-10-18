# -*- coding: utf-8 -*-

# Copyright (c) 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a previewer widget for HTML, Markdown and ReST files.
"""

from __future__ import unicode_literals    # __IGNORE_WARNING__

import os
import threading
import re

from PyQt4.QtCore import pyqtSlot, pyqtSignal, Qt, QTimer, QSize, QUrl, QThread
from PyQt4.QtGui import QWidget
from PyQt4.QtWebKit import QWebPage

from E5Gui.E5Application import e5App

from .Ui_Previewer import Ui_Previewer

import Preferences
import Utilities


class Previewer(QWidget, Ui_Previewer):
    """
    Class implementing a previewer widget for HTML, Markdown and ReST files.
    """
    def __init__(self, viewmanager, splitter, parent=None):
        """
        Constructor
        
        @param viewmanager reference to the viewmanager object (ViewManager)
        @param splitter reference to the embedding splitter (QSplitter)
        @param parent reference to the parent widget (QWidget)
        """
        super(Previewer, self).__init__(parent)
        self.setupUi(self)
        
        self.__vm = viewmanager
        self.__splitter = splitter
        
        self.__firstShow = True
        
        self.previewView.page().setLinkDelegationPolicy(
            QWebPage.DelegateAllLinks)
        
        # Don't update too often because the UI might become sluggish
        self.__typingTimer = QTimer()
        self.__typingTimer.setInterval(500)     # 500ms
        self.__typingTimer.timeout.connect(self.__runProcessingThread)
        
        self.__scrollBarPositions = {}
        self.__vScrollBarAtEnd = {}
        self.__hScrollBarAtEnd = {}
        
        self.__processingThread = PreviewProcessingThread()
        self.__processingThread.htmlReady.connect(self.__setHtml)

        self.__previewedPath = None
        
        self.__vm.editorChangedEd.connect(self.__editorChanged)
        self.__vm.editorLanguageChanged.connect(self.__editorLanguageChanged)
        self.__vm.editorTextChanged.connect(self.__editorTextChanged)

        self.__vm.previewStateChanged.connect(self.__previewStateChanged)
        
        self.__splitter.splitterMoved.connect(self.__splitterMoved)
        
        self.hide()
    
    def show(self):
        """
        Public method to show the preview widget.
        """
        super(Previewer, self).show()
        if self.__firstShow:
            self.__splitter.restoreState(
                Preferences.getUI("PreviewSplitterState"))
            self.jsCheckBox.setChecked(
                Preferences.getUI("ShowFilePreviewJS"))
            self.ssiCheckBox.setChecked(
                Preferences.getUI("ShowFilePreviewSSI"))
            self.__firstShow = False
        self.__typingTimer.start()
    
    def hide(self):
        """
        Public method to hide the preview widget.
        """
        super(Previewer, self).hide()
        self.__typingTimer.stop()
    
    def shutdown(self):
        """
        Public method to perform shutdown actions.
        """
        self.__typingTimer.stop()
        self.__processingThread.wait()
    
    def __splitterMoved(self):
        """
        Private slot to handle the movement of the embedding splitter's handle.
        """
        state = self.__splitter.saveState()
        Preferences.setUI("PreviewSplitterState", state)
    
    @pyqtSlot(bool)
    def on_jsCheckBox_clicked(self, checked):
        """
        Private slot to enable/disable JavaScript.
        
        @param checked state of the checkbox (boolean)
        """
        Preferences.setUI("ShowFilePreviewJS", checked)
        self.__setJavaScriptEnabled(checked)
    
    def __setJavaScriptEnabled(self, enable):
        """
        Private method to enable/disable JavaScript.
        
        @param enable flag indicating the enable state (boolean)
        """
        self.jsCheckBox.setChecked(enable)
        
        settings = self.previewView.settings()
        settings.setAttribute(settings.JavascriptEnabled, enable)
        
        self.__runProcessingThread()
    
    @pyqtSlot(bool)
    def on_ssiCheckBox_clicked(self, checked):
        """
        Private slot to enable/disable SSI.
        
        @param checked state of the checkbox (boolean)
        """
        Preferences.setUI("ShowFilePreviewSSI", checked)
        self.__runProcessingThread()
    
    def __editorChanged(self, editor):
        """
        Private slot to handle a change of the current editor.
        
        @param editor reference to the editor (Editor)
        """
        if editor is None:
            self.hide()
            return
        
        if Preferences.getUI("ShowFilePreview") and \
                self.__isPreviewable(editor):
            self.show()
            self.__runProcessingThread()
        else:
            self.hide()
    
    def __editorLanguageChanged(self, editor):
        """
        Private slot to handle a change of the current editor's language.
        
        @param editor reference to the editor (Editor)
        """
        self.__editorChanged(editor)
    
    def __editorTextChanged(self, editor):
        """
        Private slot to handle changes of an editor's text.
        
        @param editor reference to the editor (Editor)
        """
        if self.isVisible():
            self.__typingTimer.stop()
            self.__typingTimer.start()
    
    def __previewStateChanged(self, on):
        """
        Public slot to toggle the display of the preview.
        
        @param on flag indicating to show a preview (boolean)
        """
        editor = self.__vm.activeWindow()
        if on and editor and self.__isPreviewable(editor):
            self.show()
        else:
            self.hide()
    
    def __isPreviewable(self, editor):
        """
        Private method to check, if a preview can be shown for the given
        editor.
        
        @param editor reference to an editor (Editor)
        @return flag indicating if a preview can be shown (boolean)
        """
        if editor:
            if editor.getFileName() is not None:
                extension = os.path.normcase(
                    os.path.splitext(editor.getFileName())[1][1:])
                return extension in \
                    Preferences.getEditor("PreviewHtmlFileNameExtensions") + \
                    Preferences.getEditor(
                        "PreviewMarkdownFileNameExtensions") + \
                    Preferences.getEditor("PreviewRestFileNameExtensions")
            elif editor.getLanguage() == "HTML":
                return True
        
        return False
    
    def __runProcessingThread(self):
        """
        Private slot to schedule the processing of the current editor's text.
        """
        self.__typingTimer.stop()
        
        editor = self.__vm.activeWindow()
        if editor is not None:
            fn = editor.getFileName()
            
            if fn:
                extension = os.path.normcase(os.path.splitext(fn)[1][1:])
            else:
                extension = ""
            if extension in \
                Preferences.getEditor("PreviewHtmlFileNameExtensions") or \
               editor.getLanguage() == "HTML":
                language = "HTML"
            elif extension in \
                Preferences.getEditor("PreviewMarkdownFileNameExtensions"):
                language = "Markdown"
            elif extension in \
                Preferences.getEditor("PreviewRestFileNameExtensions"):
                language = "ReST"
            else:
                self.__setHtml(fn, self.trUtf8(
                    "<p>No preview available for this type of file.</p>"))
                return
            
            if fn:
                project = e5App().getObject("Project")
                if project.isProjectFile(fn):
                    rootPath = project.getProjectPath()
                else:
                    rootPath = os.path.dirname(os.path.abspath(fn))
            else:
                rootPath = ""
            
            self.__processingThread.process(
                fn, language, editor.text(),
                self.ssiCheckBox.isChecked(), rootPath)

    def __setHtml(self, filePath, html):
        """
        Private method to set the HTML to the view and restore the scroll bars
        positions.
        
        @param filePath file path of the previewed editor (string)
        @param html processed HTML text ready to be shown (string)
        """
        self.__saveScrollBarPositions()
        self.__previewedPath = Utilities.normcasepath(
            Utilities.fromNativeSeparators(filePath))
        self.previewView.page().mainFrame().contentsSizeChanged.connect(
            self.__restoreScrollBarPositions)
        self.previewView.setHtml(html, baseUrl=QUrl.fromLocalFile(filePath))
    
    @pyqtSlot(str)
    def on_previewView_titleChanged(self, title):
        """
        Private slot to handle a change of the title.
        
        @param title new title (string)
        """
        if title:
            self.titleLabel.setText(self.trUtf8("Preview - {0}").format(title))
        else:
            self.titleLabel.setText(self.trUtf8("Preview"))
    
    def __saveScrollBarPositions(self):
        """
        Private method to save scroll bar positions for a previewed editor.
        """
        frame = self.previewView.page().mainFrame()
        if frame.contentsSize() == QSize(0, 0):
            return  # no valid data, nothing to save
        
        pos = frame.scrollPosition()
        self.__scrollBarPositions[self.__previewedPath] = pos
        self.__hScrollBarAtEnd[self.__previewedPath] = \
            frame.scrollBarMaximum(Qt.Horizontal) == pos.x()
        self.__vScrollBarAtEnd[self.__previewedPath] = \
            frame.scrollBarMaximum(Qt.Vertical) == pos.y()

    def __restoreScrollBarPositions(self):
        """
        Private method to restore scroll bar positions for a previewed editor.
        """
        try:
            self.previewView.page().mainFrame().contentsSizeChanged.disconnect(
                self.__restoreScrollBarPositions)
        except TypeError:
            # not connected, simply ignore it
            pass
        
        if self.__previewedPath not in self.__scrollBarPositions:
            return
        
        frame = self.previewView.page().mainFrame()
        frame.setScrollPosition(
            self.__scrollBarPositions[self.__previewedPath])
        
        if self.__hScrollBarAtEnd[self.__previewedPath]:
            frame.setScrollBarValue(
                Qt.Horizontal, frame.scrollBarMaximum(Qt.Horizontal))
        
        if self.__vScrollBarAtEnd[self.__previewedPath]:
            frame.setScrollBarValue(
                Qt.Vertical, frame.scrollBarMaximum(Qt.Vertical))
    
    @pyqtSlot(QUrl)
    def on_previewView_linkClicked(self, url):
        """
        Private slot handling the clicking of a link.
        
        @param url url of the clicked link (QUrl)
        """
        e5App().getObject("UserInterface").launchHelpViewer(url.toString())


class PreviewProcessingThread(QThread):
    """
    Class implementing a thread to process some text into HTML usable by the
    previewer view.
    
    @signal htmlReady(str,str) emitted with the file name and processed HTML
        to signal the availability of the processed HTML
    """
    htmlReady = pyqtSignal(str, str)
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        super(PreviewProcessingThread, self).__init__()
        
        self.__lock = threading.Lock()
    
    def process(self, filePath, language, text, ssiEnabled, rootPath):
        """
        Convert the given text to HTML.
        
        @param filePath file path of the text (string)
        @param language language of the text (string)
        @param text text to be processed (string)
        @param ssiEnabled flag indicating to do some (limited) SSI processing
            (boolean)
        @param rootPath root path to be used for SSI processing (str)
        """
        with self.__lock:
            self.__filePath = filePath
            self.__language = language
            self.__text = text
            self.__ssiEnabled = ssiEnabled
            self.__rootPath = rootPath
            self.__haveData = True
            if not self.isRunning():
                self.start(QThread.LowPriority)
    
    def run(self):
        """
        Thread function to convert the stored data.
        """
        while True:
            # exits with break
            with self.__lock:
                filePath = self.__filePath
                language = self.__language
                text = self.__text
                ssiEnabled = self.__ssiEnabled
                rootPath = self.__rootPath
                self.__haveData = False
            
            html = self.__getHtml(language, text, ssiEnabled, filePath,
                                  rootPath)
            
            with self.__lock:
                if not self.__haveData:
                    self.htmlReady.emit(filePath, html)
                    break
                # else - next iteration
    
    def __getHtml(self, language, text, ssiEnabled, filePath, rootPath):
        """
        Private method to process the given text depending upon the given
        language.
        
        @param language language of the text (string)
        @param text to be processed (string)
        @param ssiEnabled flag indicating to do some (limited) SSI processing
            (boolean)
        @param filePath file path of the text (string)
        @param rootPath root path to be used for SSI processing (str)
        @return processed HTML text (string)
        """
        if language == "HTML":
            if ssiEnabled:
                return self.__processSSI(text, filePath, rootPath)
            else:
                return text
        elif language == "Markdown":
            return self.__convertMarkdown(text)
        elif language == "ReST":
            return self.__convertReST(text)
        else:
            return self.trUtf8(
                "<p>No preview available for this type of file.</p>")
    
    def __processSSI(self, txt, filename, root):
        """
        Private method to process the given text for SSI statements.
        
        Note: Only a limited subset of SSI statements are supported.
        
        @param txt text to be processed (string)
        @param filename name of the file associated with the given text
            (string)
        @param root directory of the document root (string)
        @return processed HTML (string)
        """
        if not filename:
            return txt
        
        # SSI include
        incRe = re.compile(
            r"""<!--#include[ \t]+(virtual|file)=[\"']([^\"']+)[\"']\s*-->""",
            re.IGNORECASE)
        baseDir = os.path.dirname(os.path.abspath(filename))
        docRoot = root if root != "" else baseDir
        while True:
            incMatch = incRe.search(txt)
            if incMatch is None:
                break
            
            if incMatch.group(1) == "virtual":
                incFile = Utilities.normjoinpath(docRoot, incMatch.group(2))
            elif incMatch.group(1) == "file":
                incFile = Utilities.normjoinpath(baseDir, incMatch.group(2))
            else:
                incFile = ""
            if os.path.exists(incFile):
                try:
                    f = open(incFile, "r")
                    incTxt = f.read()
                    f.close()
                except (IOError, OSError):
                    # remove SSI include
                    incTxt = ""
            else:
                # remove SSI include
                incTxt = ""
            txt = txt[:incMatch.start(0)] + incTxt + txt[incMatch.end(0):]
        
        return txt
    
    def __convertReST(self, text):
        """
        Private method to convert ReST text into HTML.
        
        @param text text to be processed (string)
        @return processed HTML (string)
        """
        try:
            import docutils.core    # __IGNORE_EXCEPTION__ __IGNORE_WARNING__
        except ImportError:
            return self.trUtf8(
                """<p>ReStructuredText preview requires the"""
                """ <b>python-docutils</b> package.<br/>Install it with"""
                """ your package manager or see"""
                """ <a href="http://pypi.python.org/pypi/docutils">"""
                """this page.</a></p>""")
        
        return docutils.core.publish_string(text, writer_name='html')\
            .decode("utf-8")
    
    def __convertMarkdown(self, text):
        """
        Private method to convert Markdown text into HTML.
        
        @param text text to be processed (string)
        @return processed HTML (string)
        """
        try:
            import markdown     # __IGNORE_EXCEPTION__ __IGNORE_WARNING__
        except ImportError:
            return self.trUtf8(
                """<p>Markdown preview requires the <b>python-markdown</b> """
                """package.<br/>Install it with your package manager or see """
                """<a href="http://pythonhosted.org/Markdown/install.html">"""
                """installation instructions.</a></p>""")
        
        try:
            import mdx_mathjax  # __IGNORE_EXCEPTION__ __IGNORE_WARNING__
        except ImportError:
            #mathjax doesn't require import statement if installed as extension
            pass

        extensions = ['fenced_code', 'nl2br', 'extra']
        
        # version 2.0 supports only extension names, not instances
        if markdown.version_info[0] > 2 or \
                (markdown.version_info[0] == 2 and 
                 markdown.version_info[1] > 0):
            class _StrikeThroughExtension(markdown.Extension):
                """
                Class is placed here, because it depends on imported markdown,
                and markdown import is lazy.
                
                (see http://achinghead.com/
                python-markdown-adding-insert-delete.html this page for
                details)
                """
                DEL_RE = r'(~~)(.*?)~~'

                def extendMarkdown(self, md, md_globals):
                    # Create the del pattern
                    del_tag = markdown.inlinepatterns.SimpleTagPattern(
                        self.DEL_RE, 'del')
                    # Insert del pattern into markdown parser
                    md.inlinePatterns.add('del', del_tag, '>not_strong')
            
            extensions.append(_StrikeThroughExtension())

        try:
            return markdown.markdown(text,  extensions + ['mathjax'])
        except (ImportError, ValueError):
            # markdown raises ValueError or ImportError, depends on version
            # It is not clear, how to distinguish missing mathjax from other
            # errors. So keep going without mathjax.
            return markdown.markdown(text, extensions)
