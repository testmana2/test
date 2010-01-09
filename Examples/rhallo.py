#!/usr/bin/env python

import sys

import eric5dbgstub

def main():
    print("Hello World!")
    sys.exit(0)
    
if __name__ == "__main__":
    if eric5dbgstub.initDebugger("standard"):
# or   if eric5dbgstub.initDebugger("threads"):
        eric5dbgstub.debugger.startDebugger()

    main()
