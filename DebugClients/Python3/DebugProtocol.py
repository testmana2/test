# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module defining the debug protocol tokens.
"""

# The address used for debugger/client communications.
DebugAddress = '127.0.0.1'

# The protocol "words".
RequestOK = '>OK?<'
RequestEnv = '>Environment<'
RequestCapabilities = '>Capabilities<'
RequestLoad = '>Load<'
RequestRun = '>Run<'
RequestCoverage = '>Coverage<'
RequestProfile = '>Profile<'
RequestContinue = '>Continue<'
RequestStep = '>Step<'
RequestStepOver = '>StepOver<'
RequestStepOut = '>StepOut<'
RequestStepQuit = '>StepQuit<'
RequestBreak = '>Break<'
RequestBreakEnable = '>EnableBreak<'
RequestBreakIgnore = '>IgnoreBreak<'
RequestWatch = '>Watch<'
RequestWatchEnable = '>EnableWatch<'
RequestWatchIgnore = '>IgnoreWatch<'
RequestVariables = '>Variables<'
RequestVariable = '>Variable<'
RequestSetFilter = '>SetFilter<'
RequestThreadList = '>ThreadList<'
RequestThreadSet = '>ThreadSet<'
RequestEval = '>Eval<'
RequestExec = '>Exec<'
RequestShutdown = '>Shutdown<'
RequestBanner = '>Banner<'
RequestCompletion = '>Completion<'
RequestUTPrepare = '>UTPrepare<'
RequestUTRun = '>UTRun<'
RequestUTStop = '>UTStop<'
RequestForkTo = '>ForkTo<'
RequestForkMode = '>ForkMode<'

ResponseOK = '>OK<'
ResponseCapabilities = RequestCapabilities
ResponseContinue = '>Continue<'
ResponseException = '>Exception<'
ResponseSyntax = '>SyntaxError<'
ResponseExit = '>Exit<'
ResponseLine = '>Line<'
ResponseRaw = '>Raw<'
ResponseClearBreak = '>ClearBreak<'
ResponseBPConditionError = '>BPConditionError<'
ResponseClearWatch = '>ClearWatch<'
ResponseWPConditionError = '>WPConditionError<'
ResponseVariables = RequestVariables
ResponseVariable = RequestVariable
ResponseThreadList = RequestThreadList
ResponseThreadSet = RequestThreadSet
ResponseStack = '>CurrentStack<'
ResponseBanner = RequestBanner
ResponseCompletion = RequestCompletion
ResponseUTPrepared = '>UTPrepared<'
ResponseUTStartTest = '>UTStartTest<'
ResponseUTStopTest = '>UTStopTest<'
ResponseUTTestFailed = '>UTTestFailed<'
ResponseUTTestErrored = '>UTTestErrored<'
ResponseUTTestSkipped = '>UTTestSkipped<'
ResponseUTTestFailedExpected = '>UTTestFailedExpected<'
ResponseUTTestSucceededUnexpected = '>UTTestSucceededUnexpected<'
ResponseUTFinished = '>UTFinished<'
ResponseForkTo = RequestForkTo

PassiveStartup = '>PassiveStartup<'

RequestCallTrace = '>CallTrace<'
CallTrace = '>CallTrace<'

EOT = '>EOT<\n'
