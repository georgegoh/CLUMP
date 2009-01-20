#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

from modules import Redhat5InitrdModule, SLES10InitrdModule

class InitrdModulesFactory(object):
    class_dict = {'rhel' : {'5': Redhat5InitrdModule},
                  'sles'   : {'10': SLES10InitrdModule}}
    
    def getModuleHandler(self, os_name, os_version):
        if os_name in ['rhel', 'centos']:
            os_name = 'rhel'

        return self.class_dict[os_name][os_version]
