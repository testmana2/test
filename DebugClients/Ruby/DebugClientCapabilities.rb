# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

=begin edoc
File defining the debug clients capabilities.
=end

HasDebugger      = 0x0001
HasInterpreter   = 0x0002
HasProfiler      = 0x0004
HasCoverage      = 0x0008
HasCompleter     = 0x0010
HasUnittest      = 0x0020
HasShell         = 0x0040

HasAll = HasDebugger | HasInterpreter | HasProfiler | \
         HasCoverage | HasCompleter | HasUnittest | HasShell
