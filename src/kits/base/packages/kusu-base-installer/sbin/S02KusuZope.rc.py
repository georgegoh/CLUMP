#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from path import path
from kusu.core import rcplugin

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'initialize-zope'
        self.desc = 'Setting up zope'
        self.ngtypes = ['installer']
        self.delete = True

    def run(self):
        """Setup kusuadmin zope user"""
        zinstancehome = path('/opt/Plone-3.0.3/zinstance')
        dbpasswd = path('/opt/kusu/etc/db.passwd')
        initscript = path('/etc/init.d/zinstance.sh')

        if not zinstance.exists():
            return False

        if not dbpasswd.exists():
            return False

        f = open(dbpasswd,'r')
        password = f.read()
        f.close()

        cmd = "%s/bin/zopectl adduser kusuadmin %s" % (zinstancehome,password)
        retcode, out, err = self.runCommand(cmd)

        if retcode != 0:
            return False

        if not initscript.exists():
            return False

        retcode, out, err = self.runCommand('/sbin/chkconfig zinstance on')
        retcode, out, err = self.runCommand('/etc/init.d/zinstance restart')

        if retcode != 0:
            return False

        return True

