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

"""
This script does following:
1. create cfm symbolic links for /opt/kusu/etc/logserver.addr
2. update /opt/kusu/etc/logserver.addr according to appglobals value.
"""

from kusu.core import rcplugin
from path import path
import kusu.util.log as kusulog
from primitive.system.software.dispatcher import Dispatcher

import os

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'syslog'
        self.desc = 'Setting up syslog on PCM master'
        self.ngtypes = ['installer']
        self.delete = False
        self.logger = kusulog.getKusuLog()
        self.logger.addFileHandler('/var/log/kusu/kusurc.log')
        self.logserverfile = '/opt/kusu/etc/logserver.addr'
        # dispatchers
        self.syslogconf = Dispatcher.get('syslog_conf')
        self.syslogserver = ''

    def run(self):
        """configure rsyslog settings"""
        # Sanity check
        if not path(self.syslogconf).exists():
            self.logger.error("kusurc %s: Could not find syslog configuration file." % self.name)
            return False

        # get current syslog_server configuration from DB
        self.syslogserver = self.appglobals['SYSLOG_SERVER']
        if not self.syslogserver:
            self.logger.error("kusurc %s: Could not get current syslog server address." % self.name)
            return False
 
        # create symbollic links for all NGs if link files aren't there.
        self.createCfmFiles()

        # restart syslog on PCM master.
        self.logger.info("kusurc %s: restart service %s" %(self.name, Dispatcher.get('logging_service')))
        self.service(Dispatcher.get('logging_service'), 'restart')

        return True

    def createCfmFiles(self):
        """
        Create cfm files for all NGs in PCM cluster to sync-up /etc/rsyslog.conf
        """
        conffile = path(self.logserverfile)

        ngs = self.dbs.NodeGroups.select()
        for ng in ngs:
            # ignore unmanaged NGs
            if ng.ngname == 'unmanaged': 
                continue
            # create cfm dirs for all NGs if not exist
            dest = path('/etc') / 'cfm' / ng.ngname
            if not dest.exists(): 
                dest.makedirs()
            # create config file parent dirs under /etc/cfm/NGname
            newDir = dest + conffile.parent
            if not newDir.exists():
                newDir.makedirs()
            # create symlink for config file
            newFile = newDir / conffile.basename()

            # Copy /opt/kusu/etc/logserver.addr to /etc/cfm/NGs/opt/kusu/etc/logserver.addr.
            # We don't create symbol link in /etc/cfm/ points to /opt/kusu/etc/logserver.addr as we
            # want to trigger cfmclient plugins on PCM master too.
            cfmfp = open(newFile, 'w')
            cfmfp.write('%s\n' % self.syslogserver)
            cfmfp.close()

