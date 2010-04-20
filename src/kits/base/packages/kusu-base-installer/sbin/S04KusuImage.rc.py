#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from kusu.core import rcplugin 

class KusuRC(rcplugin.Plugin):

    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'image'

        self.ngs = self.dbs.NodeGroups.select(
                self.dbs.NodeGroups.c.installtype.in_('diskless', 'disked'))
        diskless = imaged = False
        for ng in self.ngs:
            if ng.installtype == 'disked':
                imaged = True
            if ng.installtype == 'diskless':
                diskless = True
        ng_types = ''
        if imaged:
            ng_types = 'imaged'
        if diskless:
            if ng_types:
                ng_types = ng_types + ' and diskless'
            else:
                ng_types = 'diskless'
        self.desc = 'Creating images for %s nodes\n      This will take some time.  Please wait' % ng_types

        self.ngtypes = ['installer']
        self.delete = True

        # Bypass this rc script for opensuse
        if self.os_name in ['opensuse', 'suse']:
            self.disable = True

    def run(self):
        """Creating images for imaged and diskless nodes"""
        for ng in self.ngs:
            cmd = 'kusu-buildinitrd -n "%s"' % ng.ngname
            retval = self.runCommand(cmd)[0]
            if retval != 0:
                return False
  
            cmd = 'kusu-buildimage -n "%s"' % ng.ngname
            retval = self.runCommand(cmd)[0]
            if retval != 0:
                return False

        return True
