#!/usr/bin/env python
# $Id: kitops.py 2412 2007-09-29 03:30:56Z mike $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

try:
    import subprocess
except:
    from popen5 import subprocess

from kusu.addhost import *

class AddHostPlugin(AddHostPluginBase):
    def added(self, nodename, info, prePopulateMode):
        print "Nagios adding nodes:", nodename
        cmds = ['/usr/bin/python', '/opt/nagios/bin/nagiosconfig.py',
                '-a', nodename]
        nagiosconfigP = subprocess.Popen(cmds, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
        out, err = nagiosconfigP.communicate()

    def removed(self, nodename, info):
        print "Nagios removing node:", nodename
        cmds = ['/usr/bin/python', '/opt/nagios/bin/nagiosconfig.py',
                '-r', nodename]
        nagiosconfigP = subprocess.Popen(cmds, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
        out, err = nagiosconfigP.communicate()

    def finished(self, nodelist):
        cmds = ['/etc/init.d/nagios', 'restart']
        nagiosserviceP = subprocess.Popen(cmds, stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE)
        out, err = nagiosserviceP.communicate()
