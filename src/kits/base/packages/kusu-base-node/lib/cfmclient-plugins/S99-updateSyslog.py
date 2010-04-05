#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id$
#
# Copyright (C) 2010 Platform Computing Inc.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of version 2 of the GNU General Public License as published by the
# Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

from Cheetah.Template import Template
import sys
import os

sys.path.append('/opt/primitive/lib64/python2.4/site-packages')
sys.path.append('/opt/primitive/lib/python2.4/site-packages')

import kusu.util.log as kusulog
from primitive.system.software.dispatcher import Dispatcher
from path import path
from primitive.svctool.commands import SvcRestartCommand
from primitive.system.hardware.net import getPhysicalInterfaces
from primitive.system.software.probe import OS
from primitive.support.osfamily import getOSNames
try:
    import subprocess
except:
    from popen5 import subprocess

scriptname = 'syslog'
logger = kusulog.getKusuLog()
logger.addFileHandler('/var/log/cfmclient.log')
logserverfile = '/opt/kusu/etc/logserver.addr'
logconftmpl = Dispatcher.get('syslog_conf_tmpl')
logconf = Dispatcher.get('syslog_conf')
syslogservice = Dispatcher.get('logging_service')

def log_error(msg):
    logger.error("cfmclient plugin: %s: %s" % (scriptname, msg))

def log_info(msg):
    logger.info("cfmclient plugin: %s: %s" % (scriptname, msg))

# check syslog config files
if not path(logconf).exists():
    log_error("Could not find syslog configuration file.")
    sys.exit(1)

# check syslog config template files
if not path(logconftmpl).exists():
    log_error("Could not find syslog configuration template file.")
    sys.exit(1)

# check if CFM file is there.
if not path(logserverfile).exists():
    log_info("Could not find logging server address file.")
    sys.exit(0)

log_info("Parsing log server address.")
logserverfp = open(logserverfile)
logserver = logserverfp.read().strip()
logserverfp.close()

# if I am the logging server? avoid infinite forwarding.
# get my ips.
log_info("Get my ethernet interfaces.")
myifs = getPhysicalInterfaces().values()
myips = [ifentry['ip'] for ifentry in myifs]

# parse hostname
log_info("Parsing hostname.")
hostsfp = open('/etc/hosts', 'r')
hostcfglines = [line.strip() for line in hostsfp if ( len(line.strip()) > 0 and not line.startswith('#'))]
hostsfp.close()
for hostcfgline in hostcfglines:
    if logserver in hostcfgline.split() and hostcfgline.split()[0] in myips:
        # I am the log server. don't forward to self.
        logserver = ''
        break

ns = {'syslogserver' : logserver}

osname, osver, osarch = OS()
if osname.lower() in getOSNames('rhelfamily') or osname.lower() == 'fedora' : 
    cmd = 'rpm -q --qf=%{VERSION} rsyslog'
    p = subprocess.Popen(cmd,
                        shell=True,
                        stdout = subprocess.PIPE,
                        stderr = subprocess.PIPE)
    out, err = p.communicate()

    if p.returncode:
        log_info("Error: rsyslog is not installed. Exiting") 
        sys.exit(1)

    head_version = out.strip().split('.')[0]
    head_version = head_version.split('-')[0]

    # check if there are some changes in configuration file.
    ns['version'] = int(head_version)

tpl = Template(file=logconftmpl, searchList=[ns])

logconffp = open(logconf, 'r')
logconflines = logconffp.read()
logconffp.close()

log_info("Reading syslog configuration template.")
if str(tpl).strip() == logconflines.strip():
    log_info("No change to syslog server. Exiting")
    sys.exit(0)

# generate configuration files
log_info("Regenerating syslog configuration file.")
logconffpw = open(logconf, 'w')
logconflines = logconffpw.write(str(tpl))
logconffpw.close()

# re-generate real configuration file if necessary (currently for SLES)
if Dispatcher.get('syslog_reconfig_cmd'):
    log_info("Reconfiguring syslog.")
    os.system("%s >> /va/log/cfmclient.log 2>&1" % Dispatcher.get('syslog_recnfig_cmd'))

# restart syslog service.
log_info("Restarting syslog service.")
svc = SvcRestartCommand(service=syslogservice)
svc.execute()
