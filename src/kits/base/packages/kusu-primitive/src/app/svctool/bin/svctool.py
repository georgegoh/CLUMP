#!/usr/bin/env python
# $Id: svctool.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Copyright 2008 Platform Computing Inc.
#
import sys
from optparse import OptionParser
from primitive.svctool.commands import SvcStartCommand
from primitive.svctool.commands import SvcStopCommand
from primitive.svctool.commands import SvcStatusCommand
from primitive.svctool.commands import SvcRestartCommand
from primitive.svctool.commands import SvcReloadCommand
from primitive.svctool.commands import SvcEnableCommand
from primitive.svctool.commands import SvcDisableCommand
from primitive.svctool.commands import SvcListCommand
from primitive.svctool.helper import printOutErr

parser = OptionParser(usage='usage: %prog <service> [action]\n  actions: start|stop|status|restart|enable|disable')

(options, args) = parser.parse_args()

if not args:
    sys.exit('Service name not provided')

service = args[0]

action = 'status'
if len(args) > 1:
    action = args[1]
COMMAND_DICT = { 'start' : SvcStartCommand,
                 'stop' : SvcStopCommand,
                 'status' : SvcStatusCommand,
                 'restart' : SvcRestartCommand,
                 'enable' : SvcEnableCommand,
                 'disable' : SvcDisableCommand }
svcc = COMMAND_DICT[action](service=service, action=action)
ret, stuff = svcc.execute()
printOutErr(stuff)
print '='*30
print '%s' % ret
