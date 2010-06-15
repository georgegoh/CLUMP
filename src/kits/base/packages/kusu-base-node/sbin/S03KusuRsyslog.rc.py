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
This script runs on PCM RHEL master and compute nodes.
It is for following aims:
1. disable syslog
2. configure and start rsyslog
"""

from kusu.core import rcplugin
import kusu.util.log as kusulog
from primitive.system.software.dispatcher import Dispatcher

from Cheetah.Template import Template
import os

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'rsyslog'
        self.desc = 'Setting up rsyslog'
        self.ngtypes = ['installer' , 'compute']
        self.delete = True
        self.logger = kusulog.getKusuLog()
        self.logger.addFileHandler('/var/log/kusu/kusurc.log')
        self.rsyslogsysconfig = '/etc/sysconfig/rsyslog'

    def run(self):
        """disable syslog and enable rsyslog"""
        # Sanity check
        if not os.path.isfile(self.rsyslogsysconfig):
            self.logger.error("kusurc %s: Could not find rsyslog configuration file." % self.name)
            return False

        self.disableSyslog()

        self.generateRsyslogConfig()

        self.enableRsyslog()
        return True

    def generateRsyslogConfig(self):
        """
        configure /etc/sysconfig/rsyslog 
        """
        ns = {}
        tpl = Template(file='/opt/kusu/etc/templates/syslog_rsyslog.tmpl', searchList=[ns])

        rsysfptmp = open(self.rsyslogsysconfig,'w+') 
        rsysfptmp.write(str(tpl))
        rsysfptmp.close()

    def disableSyslog(self):
        """
        Disable syslog.
        """
        # This script will be packaged into RHEL packages only, 
        # so we know the service name which will be disabled.
        if self.service('syslog', 'exists')[0]: 
            self.logger.info("kusurc %s: Stopping service syslog" % self.name )
            self.service('syslog', 'stop')
            self.logger.info("kusurc %s: Disabling service syslog" % self.name )
            self.service('syslog', 'disable')

    def enableRsyslog(self):
        """
        Enable rsyslog
        """
        if self.service('rsyslog', 'exists')[0]:
            self.logger.info("kusurc %s: Starting service rsyslog" % self.name )
            self.service('rsyslog', 'start')
            self.logger.info("kusurc %s: Enabling service rsyslog" % self.name )
            self.service('rsyslog', 'enable')

