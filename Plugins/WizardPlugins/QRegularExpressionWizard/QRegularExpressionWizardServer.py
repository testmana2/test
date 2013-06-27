# -*- coding: utf-8 -*-

# Copyright (c) 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

import json
import sys

def printerr(string):
    sys.stderr.write(string)
    sys.stderr.flush()

def rxValidate(regexp, options):
    """
    Function to validate the given regular expression.
    
    @param regexp regular expression to validate (string)
    @param options list of options (list of string)
    @return tuple of flag indicating validity (boolean), error
        string (string) and error offset (integer)
    """
    try:
        from PyQt5.QtCore import QRegularExpression
        rxOptions = QRegularExpression.NoPatternOption
        if "CaseInsensitiveOption" in options:
            rxOptions |= QRegularExpression.CaseInsensitiveOption
        if "MultilineOption" in options:
            rxOptions |= QRegularExpression.MultilineOption
        if "DotMatchesEverythingOption" in options:
            rxOptions |= QRegularExpression.DotMatchesEverythingOption
        if "ExtendedPatternSyntaxOption" in options:
            rxOptions |= QRegularExpression.ExtendedPatternSyntaxOption
        if "InvertedGreedinessOption" in options:
            rxOptions |= QRegularExpression.InvertedGreedinessOption
        if "UseUnicodePropertiesOption" in options:
            rxOptions |= QRegularExpression.UseUnicodePropertiesOption
        if "DontCaptureOption" in options:
            rxOptions |= QRegularExpression.DontCaptureOption
        
        error = ""
        errorOffset = -1
        re = QRegularExpression(regexp, rxOptions)
        valid = re.isValid()
        if not valid:
            error = re.errorString()
            errorOffset = re.patternErrorOffset()
    except ImportError:
        valid = False
        error = "ImportError"
        errorOffset = 0
    
    return valid, error, errorOffset


if __name__ == "__main__":
    while True:
        commandStr = sys.stdin.readline()
        try:
            commandDict = json.loads(commandStr)
            responseDict = {"error": ""}
            printerr(str(commandDict))
            if "command" in commandDict:
                command = commandDict["command"]
                if command == "exit":
                    break
                elif command == "available":
                    try:
                        import PyQt5    # __IGNORE_WARNING__
                        responseDict["available"] = True
                    except ImportError:
                        responseDict["available"] = False
                elif command == "validate":
                    valid, error, errorOffset = rxValidate(commandDict["regexp"],
                                                           commandDict["options"])
                    responseDict["valid"] = valid
                    responseDict["errorMessage"] = error
                    responseDict["errorOffset"] = errorOffset
        except ValueError as err:
            responseDict = {"error": str(err)}
        except Exception as err:
            responseDict = {"error": str(err)}
        responseStr = json.dumps(responseDict)
        sys.stdout.write(responseStr)
        sys.stdout.flush()
    
    sys.exit(0)
