#!/usr/bin/env python
# $Id: S03KusuImage.rc.py 2101 2007-08-22 10:18:52Z ltsai $
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
        self.desc = 'Creating images for imaged and diskless nodes\n      This will take some time.  Please wait'
        self.ngtypes = ['installer']
        self.delete = True

    def run(self):
        """Creating images for imaged and diskless nodes"""

        ngs = self.dbs.NodeGroups.select(
                self.dbs.NodeGroups.c.installtype.in_('diskless', 'disked'))

        for ng in ngs:
            cmd = 'buildinitrd -n "%s"' % ng.ngname
            retval = self.runCommand(cmd)[0]
            if retval != 0:
                return False
  
            cmd = 'buildimage -n "%s"' % ng.ngname
            retval = self.runCommand(cmd)[0]
            if retval != 0:
                return False

        return True
