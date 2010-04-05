#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

from primitive.support import osfamily
from modules import Redhat5InitrdModule, SLES10InitrdModule, OpenSUSE103InitrdModule

class InitrdModulesFactory(object):
    class_dict = {'rhel' : {'5': Redhat5InitrdModule},
                  'sles'   : {'10': SLES10InitrdModule},
                  'opensuse'   : {'10.3': OpenSUSE103InitrdModule}}
    
    def getModuleHandler(self, os_name, os_version):
        if os_name in osfamily.getOSNames('rhelfamily'):
            os_name = 'rhel'

        return self.class_dict[os_name][os_version]

