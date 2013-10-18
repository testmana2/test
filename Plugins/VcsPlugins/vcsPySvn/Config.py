# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module defining configuration variables for the subversion package.
"""

# Available protocols for the repository URL
ConfigSvnProtocols = [
    'file://',
    'http://',
    'https://',
    'svn://',
    'svn+ssh://',
]


DefaultConfig = "\n".join([
    "### This file configures various client-side behaviors.",
    "###",
    "### The commented-out examples below are intended to demonstrate",
    "### how to use this file.",
    "",
    "### Section for authentication and authorization customizations.",
    "[auth]",
    "### Set password stores used by Subversion. They should be",
    "### delimited by spaces or commas. The order of values determines",
    "### the order in which password stores are used.",
    "### Valid password stores:",
    "###   gnome-keyring        (Unix-like systems)",
    "###   kwallet              (Unix-like systems)",
    "###   keychain             (Mac OS X)",
    "###   windows-cryptoapi    (Windows)",
    "# password-stores = keychain",
    "# password-stores = windows-cryptoapi",
    "# password-stores = gnome-keyring,kwallet",
    "### To disable all password stores, use an empty list:",
    "# password-stores =",
    "###",
    "### Set KWallet wallet used by Subversion. If empty or unset,",
    "### then the default network wallet will be used.",
    "# kwallet-wallet =",
    "###",
    "### Include PID (Process ID) in Subversion application name when",
    "### using KWallet. It defaults to 'no'.",
    "# kwallet-svn-application-name-with-pid = yes",
    "###",
    "### The rest of the [auth] section in this file has been deprecated.",
    "### Both 'store-passwords' and 'store-auth-creds' can now be",
    "### specified in the 'servers' file in your config directory",
    "### and are documented there. Anything specified in this section ",
    "### is overridden by settings specified in the 'servers' file.",
    "# store-passwords = no",
    "# store-auth-creds = no",
    "",
    "### Section for configuring external helper applications.",
    "[helpers]",
    "### Set editor-cmd to the command used to invoke your text editor.",
    "###   This will override the environment variables that Subversion",
    "###   examines by default to find this information ($EDITOR, ",
    "###   et al).",
    "# editor-cmd = editor (vi, emacs, notepad, etc.)",
    "### Set diff-cmd to the absolute path of your 'diff' program.",
    "###   This will override the compile-time default, which is to use",
    "###   Subversion's internal diff implementation.",
    "# diff-cmd = diff_program (diff, gdiff, etc.)",
    "### Diff-extensions are arguments passed to an external diff",
    "### program or to Subversion's internal diff implementation.",
    "### Set diff-extensions to override the default arguments ('-u').",
    "# diff-extensions = -u -p",
    "### Set diff3-cmd to the absolute path of your 'diff3' program.",
    "###   This will override the compile-time default, which is to use",
    "###   Subversion's internal diff3 implementation.",
    "# diff3-cmd = diff3_program (diff3, gdiff3, etc.)",
    "### Set diff3-has-program-arg to 'yes' if your 'diff3' program",
    "###   accepts the '--diff-program' option.",
    "# diff3-has-program-arg = [yes | no]",
    "### Set merge-tool-cmd to the command used to invoke your external",
    "### merging tool of choice. Subversion will pass 5 arguments to",
    "### the specified command: base theirs mine merged wcfile",
    "# merge-tool-cmd = merge_command",
    "",
    "### Section for configuring tunnel agents.",
    "[tunnels]",
    "### Configure svn protocol tunnel schemes here.  By default, only",
    "### the 'ssh' scheme is defined.  You can define other schemes to",
    "### be used with 'svn+scheme://hostname/path' URLs.  A scheme",
    "### definition is simply a command, optionally prefixed by an",
    "### environment variable name which can override the command if it",
    "### is defined.  The command (or environment variable) may contain",
    "### arguments, using standard shell quoting for arguments with",
    "### spaces.  The command will be invoked as:",
    "###   <command> <hostname> svnserve -t",
    "### (If the URL includes a username, then the hostname will be",
    "### passed to the tunnel agent as <user>@<hostname>.)  If the",
    "### built-in ssh scheme were not predefined, it could be defined",
    "### as:",
    "# ssh = $SVN_SSH ssh -q",
    "### If you wanted to define a new 'rsh' scheme, to be used with",
    "### 'svn+rsh:' URLs, you could do so as follows:",
    "# rsh = rsh",
    "### Or, if you wanted to specify a full path and arguments:",
    "# rsh = /path/to/rsh -l myusername",
    "### On Windows, if you are specifying a full path to a command,",
    "### use a forward slash (/) or a paired backslash (\\\\) as the",
    "### path separator.  A single backslash will be treated as an",
    "### escape for the following character.",
    "",
    "### Section for configuring miscelleneous Subversion options.",
    "[miscellany]",
    "### Set global-ignores to a set of whitespace-delimited globs",
    "### which Subversion will ignore in its 'status' output, and",
    "### while importing or adding files and directories.",
    "### '*' matches leading dots, e.g. '*.rej' matches '.foo.rej'.",
    "global-ignores = *.o *.lo *.la *.al .libs *.so *.so.[0-9]* *.a *.pyc",
    "  *.pyo .*.rej *.rej .*~ *~ #*# .#* .*.swp .DS_Store",
    "  *.orig *.bak cur tmp __pycache__ .directory",
    "  .ropeproject .eric4project .eric5project",
    "  _ropeproject _eric4project _eric5project",
    "### Set log-encoding to the default encoding for log messages",
    "# log-encoding = latin1",
    "### Set use-commit-times to make checkout/update/switch/revert",
    "### put last-committed timestamps on every file touched.",
    "# use-commit-times = yes",
    "### Set no-unlock to prevent 'svn commit' from automatically",
    "### releasing locks on files.",
    "# no-unlock = yes",
    "### Set mime-types-file to a MIME type registry file, used to",
    "### provide hints to Subversion's MIME type auto-detection",
    "### algorithm.",
    "# mime-types-file = /path/to/mime.types",
    "### Set preserved-conflict-file-exts to a whitespace-delimited",
    "### list of patterns matching file extensions which should be",
    "### preserved in generated conflict file names.  By default,",
    "### conflict files use custom extensions.",
    "# preserved-conflict-file-exts = doc ppt xls od?",
    "### Set enable-auto-props to 'yes' to enable automatic properties",
    "### for 'svn add' and 'svn import', it defaults to 'no'.",
    "### Automatic properties are defined in the section 'auto-props'.",
    "# enable-auto-props = yes",
    "### Set interactive-conflicts to 'no' to disable interactive",
    "### conflict resolution prompting.  It defaults to 'yes'.",
    "# interactive-conflicts = no",
    "### Set memory-cache-size to define the size of the memory cache",
    "### used by the client when accessing a FSFS repository via",
    "### ra_local (the file:// scheme). The value represents the number",
    "### of MB used by the cache.",
    "# memory-cache-size = 16",
    "",
    "### Section for configuring automatic properties.",
    "[auto-props]",
    "### The format of the entries is:",
    "###   file-name-pattern = propname[=value][;propname[=value]...]",
    "### The file-name-pattern can contain wildcards (such as '*' and",
    "### '?').  All entries which match (case-insensitively) will be",
    "### applied to the file.  Note that auto-props functionality",
    "### must be enabled, which is typically done by setting the",
    "### 'enable-auto-props' option.",
    "# *.c = svn:eol-style=native",
    "# *.cpp = svn:eol-style=native",
    "# *.h = svn:keywords=Author Date Id Rev URL;svn:eol-style=native",
    "# *.dsp = svn:eol-style=CRLF",
    "# *.dsw = svn:eol-style=CRLF",
    "# *.sh = svn:eol-style=native;svn:executable",
    "# *.txt = svn:eol-style=native;svn:keywords=Author Date Id Rev URL;",
    "# *.png = svn:mime-type=image/png",
    "# *.jpg = svn:mime-type=image/jpeg",
    "# Makefile = svn:eol-style=native",
    "",
])


DefaultIgnores = [
    "*.orig",
    "*.bak",
    "cur",
    "tmp",
    "__pycache__",
    ".directory",
    ".ropeproject",
    ".eric4project",
    ".eric5project",
    "_ropeproject",
    "_eric4project",
    "_eric5project",
]
