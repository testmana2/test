# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing templates for the documentation generator (lists style).
"""

#################################################
##  Common templates for index and docu files  ##
#################################################

headerTemplate = \
'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC '-//W3C//DTD XHTML 1.0 Strict//EN'
'http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd'>
<html><head>
<title>{Title}</title>
<style>
{Style}
</style>
</head>
<body>'''

footerTemplate = '''
</body></html>'''

#########################################
##  Templates for documentation files  ##
#########################################

moduleTemplate = \
'''<a NAME="top" ID="top"></a>
<h1>{Module}</h1>
{ModuleDescription}
<h3>Global Attributes</h3>
{GlobalsList}
<h3>Classes</h3>
{ClassList}
<h3>Functions</h3>
{FunctionList}
<hr />'''

rbFileTemplate = \
'''<a NAME="top" ID="top"></a>
<h1>{Module}</h1>
{ModuleDescription}
<h3>Global Attributes</h3>
{GlobalsList}
<h3>Classes</h3>
{ClassList}
<h3>Modules</h3>
{RbModulesList}
<h3>Functions</h3>
{FunctionList}
<hr />'''

classTemplate = \
'''<hr />
<a NAME="{Anchor}" ID="{Anchor}"></a>
<h2>{Class}</h2>
{ClassDescription}
<h3>Derived from</h3>
{ClassSuper}
<h3>Class Attributes</h3>
{GlobalsList}
<h3>Methods</h3>
{MethodList}
{MethodDetails}
<div align="right"><a href="#top">Up</a></div>
<hr />'''

methodTemplate = \
'''<a NAME="{Anchor}.{Method}" ID="{Anchor}.{Method}"></a>
<h4>{Class}.{Method}</h4>
<b>{Method}</b>(<i>{Params}</i>)
{MethodDescription}'''

constructorTemplate = \
'''<a NAME="{Anchor}.{Method}" ID="{Anchor}.{Method}"></a>
<h4>{Class} (Constructor)</h4>
<b>{Class}</b>(<i>{Params}</i>)
{MethodDescription}'''

rbModuleTemplate = \
'''<hr />
<a NAME="{Anchor}" ID="{Anchor}"></a>
<h2>{Module}</h2>
{ModuleDescription}
<h3>Module Attributes</h3>
{GlobalsList}
<h3>Classes</h3>
{ClassesList}
<h3>Functions</h3>
{FunctionsList}
<hr />
{ClassesDetails}
{FunctionsDetails}
<div align="right"><a href="#top">Up</a></div>
<hr />'''

rbModulesClassTemplate = \
'''<a NAME="{Anchor}" ID="{Anchor}"></a>
<h2>{Class}</h2>
{ClassDescription}
<h3>Derived from</h3>
{ClassSuper}
<h3>Methods</h3>
{MethodList}
{MethodDetails}
<div align="right"><a href="#top">Up</a></div>
<hr />'''

functionTemplate = \
'''<hr />
<a NAME="{Anchor}" ID="{Anchor}"></a>
<h2>{Function}</h2>
<b>{Function}</b>(<i>{Params}</i>)
{FunctionDescription}
<div align="right"><a href="#top">Up</a></div>
<hr />'''

listTemplate = \
'''<table>
{Entries}
</table>'''

listEntryTemplate = \
'''<tr>
<td><a href="#{Link}">{Name}</a></td>
<td>{Deprecated}{Description}</td>
</tr>'''

listEntryNoneTemplate = \
'''<tr><td>None</td></tr>'''

listEntryDeprecatedTemplate = \
'''<b>Deprecated.</b>'''

listEntrySimpleTemplate = \
'''<tr><td>{Name}</td></tr>'''

paragraphTemplate = \
'''<p>
{Lines}
</p>'''

parametersListTemplate = \
'''<dl>
{Parameters}
</dl>'''

parametersListEntryTemplate = \
'''<dt><i>{Name}</i></dt>
<dd>
{Description}
</dd>'''

returnsTemplate = \
'''<dl>
<dt>Returns:</dt>
<dd>
{0}
</dd>
</dl>'''

exceptionsListTemplate = \
'''<dl>
{Exceptions}
</dl>'''

exceptionsListEntryTemplate = \
'''<dt>Raises <b>{Name}</b>:</dt>
<dd>
{Description}
</dd>'''

signalsListTemplate = \
'''<h4>Signals</h4>
<dl>
{Signals}
</dl>'''

signalsListEntryTemplate = \
'''<dt>{Name}</dt>
<dd>
{Description}
</dd>'''

eventsListTemplate = \
'''<h4>Events</h4>
<dl>
{Events}
</dl>'''

eventsListEntryTemplate = \
'''<dt>{Name}</dt>
<dd>
{Description}
</dd>'''

deprecatedTemplate = \
'''<p>
<b>Deprecated.</b>
{Lines}
</p>'''

authorInfoTemplate = \
'''<p>
<i>Author(s)</i>:
{Authors}
</p>'''

seeListTemplate = \
'''<dl>
<dt><b>See Also:</b></dt>
{Links}
</dl>'''

seeListEntryTemplate = \
'''<dd>
{Link}
</dd>'''

seeLinkTemplate = \
'''<a {Link}'''

sinceInfoTemplate = \
'''<p>
<b>since</b> {Info}
</p>'''

#################################
##  Templates for index files  ##
#################################

indexBodyTemplate = '''
<h1>{Title}</h1>
{Description}
{Subpackages}
{Modules}'''

indexListPackagesTemplate = '''
<h3>Packages</h3>
<table>
{Entries}
</table>'''

indexListModulesTemplate = '''
<h3>Modules</h3>
<table>
{Entries}
</table>'''

indexListEntryTemplate = \
'''<tr>
<td><a href="{Link}">{Name}</a></td>
<td>{Description}</td>
</tr>'''
