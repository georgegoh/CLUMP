#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id$
#
# Copyright (C) 2010 Platform Computing Inc.

"""
The aim of the script is to:
1. disable unneeded scripts on master/compute nodes
"""

from kusu.core import rcplugin
from primitive.system.software.dispatcher import Dispatcher
import kusu.util.log as kusulog

import os

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'servicemanager'
        self.desc = 'Disabling unneeded services'
        self.ngtypes = ['installer' , 'compute']
        self.delete = True
        self.logger = kusulog.getKusuLog()
        self.logger.addFileHandler('/var/log/kusu/kusurc.log')
        self.serviceslist = ['cups_service', 'gpm_service', 'pcsc_service', \
                             'multi-category_service', 'avahi_service',\
                             'restorecond_service', 'bluetooth_service', \
                             'bluetooth_hid_service', 'os_update_service', \
                             'hardware_detect_service' ]

    def run(self):
        """disable unneeded services on PCM master and compute nodes"""
        # for master
        if not os.path.isfile('/etc/profile.nii'):
            self.serviceslist.remove('gpm_service')

        
        for servicename in self.serviceslist:
            if Dispatcher.get(servicename) and self.service(Dispatcher.get(servicename), 'exists')[0]:
                self.logger.info("kusurc %s: Stopping service %s" %(self.name, Dispatcher.get(servicename)))
                self.service(Dispatcher.get(servicename), 'stop')
                self.logger.info("kusurc %s: Disabling service %s" %(self.name, Dispatcher.get(servicename)))
                self.service(Dispatcher.get(servicename), 'disable')

        return True

