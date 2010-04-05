#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id$
#
# Copyright 2010 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import os
import sys

try:
    import subprocess
except:
    from popen5 import subprocess

from path import path

from primitive.system.software.dispatcher import Dispatcher
from primitive.svctool.commands import SvcStartCommand
from primitive.support.util import runCommand
from primitive.core.errors import ModuleException
from kusu.core import rcplugin
import kusu.util.log as kusulog

class SecureMySQLApp(object):
    def run():
        mysql_service = Dispatcher.get("mysql_server")
        if not path(Dispatcher.get("service_exists") % mysql_service).isfile():
            kl.info("MySQL doesn't seem to be installed. Exiting.")
            return 0

        SvcStartCommand(service=mysql_service).execute()
        cmd = ['mysqladmin', '-u', 'root', 'password', '`cat /opt/kusu/etc/db.passwd`']
        try:
            runCommand(' '.join(cmd))
        except ModuleException, e:
            kl.warn('Setting mysql root password failed; it may already be set.')
            kl.warn(e.args[0])
            return 0
        kl.info('MySQL root password set')
        return 0
    run = staticmethod(run)

if __name__ == "__main__":
    if os.getuid() != 0:
        print 'You must be root to run this tool'
        sys.exit(1)

    kl = kusulog.getKusuLog()

    sys.exit(SecureMySQLApp.run())
