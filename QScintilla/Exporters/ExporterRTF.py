# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing an exporter for RTF.
"""

from __future__ import unicode_literals

# This code is a port of the C++ code found in SciTE 1.74
# Original code: Copyright 1998-2006 by Neil Hodgson <neilh@scintilla.org>

import time

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QCursor, QFontInfo, QApplication
from PyQt4.Qsci import QsciScintilla

from E5Gui import E5MessageBox

from .ExporterBase import ExporterBase

import Preferences


class ExporterRTF(ExporterBase):
    """
    Class implementing an exporter for RTF.
    """
    RTF_HEADEROPEN = "{\\rtf1\\ansi\\deff0\\deftab720"
    RTF_HEADERCLOSE = "\n"
    RTF_FONTDEFOPEN = "{\\fonttbl"
    RTF_FONTDEF = "{{\\f{0:d}\\fnil\\fcharset{1:d} {2};}}"
    RTF_FONTDEFCLOSE = "}"
    RTF_COLORDEFOPEN = "{\\colortbl"
    RTF_COLORDEF = "\\red{0:d}\\green{1:d}\\blue{2:d};"
    RTF_COLORDEFCLOSE = "}"
    RTF_INFOOPEN = "{\\info "
    RTF_INFOCLOSE = "}"
    RTF_COMMENT = "{\\comment Generated by eric5's RTF export filter.}"
    # to be used by strftime
    RTF_CREATED = "{\creatim\yr%Y\mo%m\dy%d\hr%H\min%M\sec%S}"
    RTF_BODYOPEN = ""
    RTF_BODYCLOSE = "}"

    RTF_SETFONTFACE = "\\f"
    RTF_SETFONTSIZE = "\\fs"
    RTF_SETCOLOR = "\\cf"
    RTF_SETBACKGROUND = "\\highlight"
    RTF_BOLD_ON = "\\b"
    RTF_BOLD_OFF = "\\b0"
    RTF_ITALIC_ON = "\\i"
    RTF_ITALIC_OFF = "\\i0"

    RTF_EOLN = "\\line\n"
    RTF_TAB = "\\tab "

    RTF_COLOR = "#000000"

    def __init__(self, editor, parent=None):
        """
        Constructor
        
        @param editor reference to the editor object (QScintilla.Editor.Editor)
        @param parent parent object of the exporter (QObject)
        """
        ExporterBase.__init__(self, editor, parent)
    
    def __GetRTFNextControl(self, pos, style):
        """
        Private method to extract the next RTF control word from style.
        
        @param pos position to start search (integer)
        @param style style definition to search in (string)
        @return tuple of new start position and control word found
            (integer, string)
        """
        # \f0\fs20\cf0\highlight0\b0\i0
        if pos >= len(style):
            return pos, ""
        
        oldpos = pos
        pos += 1    # implicit skip over leading '\'
        while pos < len(style) and style[pos] != '\\':
            pos += 1
        return pos, style[oldpos:pos]
    
    def __GetRTFStyleChange(self, last, current):
        """
        Private method to extract control words that are different between two
        styles.
        
        @param last least recently used style (string)
        @param current current style (string)
        @return string containing the delta between these styles (string)
        """
        # \f0\fs20\cf0\highlight0\b0\i0
        lastPos = 0
        currentPos = 0
        delta = ''
        i = 0
        while i < 6:
            lastPos, lastControl = self.__GetRTFNextControl(lastPos, last)
            currentPos, currentControl = self.__GetRTFNextControl(currentPos,
                                                                  current)
            if lastControl != currentControl:
                delta += currentControl
            i += 1
        if delta != '':
            delta += ' '
        return delta
    
    def exportSource(self):
        """
        Public method performing the export.
        """
        filename = self._getFileName(self.tr("RTF Files (*.rtf)"))
        if not filename:
            return
        
        try:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            QApplication.processEvents()
            
            self.editor.recolor(0, -1)
            lex = self.editor.getLexer()
            
            tabSize = Preferences.getEditor("TabWidth")
            if tabSize == 0:
                tabSize = 4
            wysiwyg = Preferences.getEditorExporter("RTF/WYSIWYG")
            if wysiwyg:
                if lex:
                    defaultFont = lex.font(QsciScintilla.STYLE_DEFAULT)
                else:
                    defaultFont = Preferences.getEditorOtherFonts(
                        "DefaultFont")
            else:
                defaultFont = Preferences.getEditorExporter("RTF/Font")
            fontface = defaultFont.family()
            fontsize = QFontInfo(defaultFont).pointSize() << 1
            if fontsize == 0:
                fontsize = 10 << 1
            characterset = QsciScintilla.SC_CHARSET_DEFAULT
            tabs = Preferences.getEditorExporter("RTF/UseTabs")
            
            if lex:
                fgColour = lex.color(QsciScintilla.STYLE_DEFAULT)
                bgColour = lex.paper(QsciScintilla.STYLE_DEFAULT)
            else:
                fgColour = self.editor.color()
                bgColour = self.editor.paper()
            
            try:
                f = open(filename, "w", encoding="utf-8")
                
                styles = {}
                fonts = {}
                colors = {}
                lastStyle = ""
                
                f.write(self.RTF_HEADEROPEN + self.RTF_FONTDEFOPEN)
                fonts[0] = fontface
                fontCount = 1
                f.write(self.RTF_FONTDEF.format(0, characterset, fontface))
                colors[0] = fgColour
                colors[1] = bgColour
                colorCount = 2
                
                if lex:
                    istyle = 0
                    while istyle <= QsciScintilla.STYLE_MAX:
                        if (istyle < QsciScintilla.STYLE_DEFAULT or
                                istyle > QsciScintilla.STYLE_LASTPREDEFINED):
                            if lex.description(istyle):
                                font = lex.font(istyle)
                                if wysiwyg:
                                    fontKey = None
                                    for key, value in list(fonts.items()):
                                        if value.lower() == \
                                                font.family().lower():
                                            fontKey = key
                                            break
                                    if fontKey is None:
                                        fonts[fontCount] = font.family()
                                        f.write(self.RTF_FONTDEF.format(
                                            fontCount, characterset,
                                            font.family()))
                                        fontKey = fontCount
                                        fontCount += 1
                                    lastStyle = self.RTF_SETFONTFACE + \
                                        "{0:d}".format(fontKey)
                                else:
                                    lastStyle = self.RTF_SETFONTFACE + "0"
                                
                                if wysiwyg and QFontInfo(font).pointSize():
                                    lastStyle += self.RTF_SETFONTSIZE + \
                                        "{0:d}".format(
                                            QFontInfo(font).pointSize() << 1)
                                else:
                                    lastStyle += self.RTF_SETFONTSIZE + \
                                        "{0:d}".format(fontsize)
                                
                                sColour = lex.color(istyle)
                                sColourKey = None
                                for key, value in list(colors.items()):
                                    if value == sColour:
                                        sColourKey = key
                                        break
                                if sColourKey is None:
                                    colors[colorCount] = sColour
                                    sColourKey = colorCount
                                    colorCount += 1
                                lastStyle += self.RTF_SETCOLOR + \
                                    "{0:d}".format(sColourKey)
                                
                                sColour = lex.paper(istyle)
                                sColourKey = None
                                for key, value in list(colors.items()):
                                    if value == sColour:
                                        sColourKey = key
                                        break
                                if sColourKey is None:
                                    colors[colorCount] = sColour
                                    sColourKey = colorCount
                                    colorCount += 1
                                lastStyle += self.RTF_SETBACKGROUND + \
                                    "{0:d}".format(sColourKey)
                                
                                if font.bold():
                                    lastStyle += self.RTF_BOLD_ON
                                else:
                                    lastStyle += self.RTF_BOLD_OFF
                                if font.italic():
                                    lastStyle += self.RTF_ITALIC_ON
                                else:
                                    lastStyle += self.RTF_ITALIC_OFF
                                styles[istyle] = lastStyle
                            else:
                                styles[istyle] = \
                                    self.RTF_SETFONTFACE + "0" + \
                                    self.RTF_SETFONTSIZE + \
                                    "{0:d}".format(fontsize) + \
                                    self.RTF_SETCOLOR + "0" + \
                                    self.RTF_SETBACKGROUND + "1" + \
                                    self.RTF_BOLD_OFF + self.RTF_ITALIC_OFF
                        
                        istyle += 1
                else:
                    styles[0] = self.RTF_SETFONTFACE + "0" + \
                        self.RTF_SETFONTSIZE + \
                        "{0:d}".format(fontsize) + \
                        self.RTF_SETCOLOR + "0" + \
                        self.RTF_SETBACKGROUND + "1" + \
                        self.RTF_BOLD_OFF + self.RTF_ITALIC_OFF
                
                f.write(self.RTF_FONTDEFCLOSE + self.RTF_COLORDEFOPEN)
                for value in list(colors.values()):
                    f.write(self.RTF_COLORDEF.format(
                            value.red(), value.green(), value.blue()))
                f.write(self.RTF_COLORDEFCLOSE)
                f.write(self.RTF_INFOOPEN + self.RTF_COMMENT)
                f.write(time.strftime(self.RTF_CREATED))
                f.write(self.RTF_INFOCLOSE)
                f.write(self.RTF_HEADERCLOSE +
                        self.RTF_BODYOPEN + self.RTF_SETFONTFACE + "0" +
                        self.RTF_SETFONTSIZE + "{0:d}".format(fontsize) +
                        self.RTF_SETCOLOR + "0 ")
                lastStyle = self.RTF_SETFONTFACE + "0" + \
                    self.RTF_SETFONTSIZE + "{0:d}".format(fontsize) + \
                    self.RTF_SETCOLOR + "0" + \
                    self.RTF_SETBACKGROUND + "1" + \
                    self.RTF_BOLD_OFF + self.RTF_ITALIC_OFF
                
                lengthDoc = self.editor.length()
                prevCR = False
                column = 0
                pos = 0
                deltaStyle = ""
                styleCurrent = -1
                utf8 = self.editor.isUtf8()
                utf8Ch = b""
                utf8Len = 0
                
                while pos < lengthDoc:
                    ch = self.editor.byteAt(pos)
                    style = self.editor.styleAt(pos)
                    if style != styleCurrent:
                        deltaStyle = self.__GetRTFStyleChange(
                            lastStyle, styles[style])
                        if deltaStyle:
                            f.write(deltaStyle)
                        styleCurrent = style
                        lastStyle = styles[style]
                    
                    if ch == b'{':
                        f.write('\\{')
                    elif ch == b'}':
                        f.write('\\}')
                    elif ch == b'\\':
                        f.write('\\\\')
                    elif ch == b'\t':
                        if tabs:
                            f.write(self.RTF_TAB)
                        else:
                            ts = tabSize - (column % tabSize)
                            f.write(' ' * ts)
                            column += ts - 1
                    elif ch == b'\n':
                        if not prevCR:
                            f.write(self.RTF_EOLN)
                            column -= 1
                    elif ch == b'\r':
                        f.write(self.RTF_EOLN)
                        column -= 1
                    else:
                        if ord(ch) > 0x7F and utf8:
                            utf8Ch += ch
                            if utf8Len == 0:
                                if (utf8Ch[0] & 0xF0) == 0xF0:
                                    utf8Len = 4
                                elif (utf8Ch[0] & 0xE0) == 0xE0:
                                    utf8Len = 3
                                elif (utf8Ch[0] & 0xC0) == 0xC0:
                                    utf8Len = 2
                                column -= 1  # will be incremented again later
                            elif len(utf8Ch) == utf8Len:
                                ch = utf8Ch.decode('utf8')
                                if ord(ch) <= 0xff:
                                    f.write("\\'{0:x}".format(ord(ch)))
                                else:
                                    f.write("\\u{0:d}\\'{1:x}".format(
                                            ord(ch), ord(ch) & 0xFF))
                                utf8Ch = b""
                                utf8Len = 0
                            else:
                                column -= 1  # will be incremented again later
                        else:
                            f.write(ch.decode())
                    
                    column += 1
                    prevCR = ch == b'\r'
                    pos += 1
                
                f.write(self.RTF_BODYCLOSE)
                f.close()
            except IOError as err:
                QApplication.restoreOverrideCursor()
                E5MessageBox.critical(
                    self.editor,
                    self.tr("Export source"),
                    self.tr(
                        """<p>The source could not be exported to"""
                        """ <b>{0}</b>.</p><p>Reason: {1}</p>""")
                    .format(filename, str(err)))
        finally:
            QApplication.restoreOverrideCursor()
