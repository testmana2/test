# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the multithreaded version of the debug client.
"""

import _thread
import sys

from AsyncIO import AsyncIO
from DebugThread import DebugThread
import DebugClientBase


def _debugclient_start_new_thread(target, args, kwargs={}):
    """
    Module function used to allow for debugging of multiple threads.
    
    The way it works is that below, we reset _thread._start_new_thread to
    this function object. Thus, providing a hook for us to see when
    threads are started. From here we forward the request onto the
    DebugClient which will create a DebugThread object to allow tracing
    of the thread then start up the thread. These actions are always
    performed in order to allow dropping into debug mode.
    
    See DebugClientThreads.attachThread and DebugThread.DebugThread in
    DebugThread.py
    
    @param target the start function of the target thread (i.e. the user code)
    @param args arguments to pass to target
    @param kwargs keyword arguments to pass to target
    @return The identifier of the created thread
    """
    if DebugClientBase.DebugClientInstance is not None:
        return DebugClientBase.DebugClientInstance.attachThread(
            target, args, kwargs)
    else:
        return _original_start_thread(target, args, kwargs)
    
# make _thread hooks available to system
_original_start_thread = _thread.start_new_thread
_thread.start_new_thread = _debugclient_start_new_thread

# Note: import threading here AFTER above hook, as threading cache's
#       thread._start_new_thread.
from threading import RLock


class DebugClientThreads(DebugClientBase.DebugClientBase, AsyncIO):
    """
    Class implementing the client side of the debugger.

    This variant of the debugger implements a threaded debugger client
    by subclassing all relevant base classes.
    """
    def __init__(self):
        """
        Constructor
        """
        AsyncIO.__init__(self)
        
        DebugClientBase.DebugClientBase.__init__(self)
        
        # protection lock for synchronization
        self.clientLock = RLock()
        
        # the "current" thread, basically the thread we are at a breakpoint
        # for.
        self.currentThread = None
        
        # special objects representing the main scripts thread and frame
        self.mainThread = None
        self.mainFrame = None
        
        self.variant = 'Threaded'

    def attachThread(self, target=None, args=None, kwargs=None,
                     mainThread=False):
        """
        Public method to setup a thread for DebugClient to debug.
        
        If mainThread is non-zero, then we are attaching to the already
        started mainthread of the app and the rest of the args are ignored.
        
        @param target the start function of the target thread (i.e. the
            user code)
        @param args arguments to pass to target
        @param kwargs keyword arguments to pass to target
        @param mainThread True, if we are attaching to the already
              started mainthread of the app
        @return identifier of the created thread
        """
        try:
            self.lockClient()
            newThread = DebugThread(self, target, args, kwargs, mainThread)
            ident = -1
            if mainThread:
                ident = _thread.get_ident()
                self.mainThread = newThread
                if self.debugging:
                    sys.setprofile(newThread.profile)
            else:
                ident = _original_start_thread(newThread.bootstrap, ())
            newThread.set_ident(ident)
            self.threads[newThread.get_ident()] = newThread
        finally:
            self.unlockClient()
        return ident
    
    def threadTerminated(self, dbgThread):
        """
        Public method called when a DebugThread has exited.
        
        @param dbgThread the DebugThread that has exited
        """
        self.lockClient()
        try:
            del self.threads[dbgThread.get_ident()]
        except KeyError:
            pass
        finally:
            self.unlockClient()
    
    def lockClient(self, blocking=True):
        """
        Public method to acquire the lock for this client.
        
        @param blocking flag to indicating a blocking lock
        @return flag indicating successful locking
        """
        if blocking:
            self.clientLock.acquire()
        else:
            return self.clientLock.acquire(blocking)
    
    def unlockClient(self):
        """
        Public method to release the lock for this client.
        """
        try:
            self.clientLock.release()
        except AssertionError:
            pass
    
    def setCurrentThread(self, id):
        """
        Public method to set the current thread.

        @param id the id the current thread should be set to.
        """
        try:
            self.lockClient()
            if id is None:
                self.currentThread = None
            else:
                self.currentThread = self.threads[id]
        finally:
            self.unlockClient()
    
    def eventLoop(self, disablePolling=False):
        """
        Public method implementing our event loop.
        
        @param disablePolling flag indicating to enter an event loop with
            polling disabled (boolean)
        """
        # make sure we set the current thread appropriately
        threadid = _thread.get_ident()
        self.setCurrentThread(threadid)
        
        DebugClientBase.DebugClientBase.eventLoop(self, disablePolling)
        
        self.setCurrentThread(None)

    def set_quit(self):
        """
        Public method to do a 'set quit' on all threads.
        """
        try:
            locked = self.lockClient(False)
            try:
                for key in self.threads:
                    self.threads[key].set_quit()
            except:
                pass
        finally:
            if locked:
                self.unlockClient()

# We are normally called by the debugger to execute directly.

if __name__ == '__main__':
    debugClient = DebugClientThreads()
    debugClient.main()
