#!/usr/bin/env python
# $Id: S99KusuXorg.rc.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Copyright 2008 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from kusu.core import rcplugin 
from path import path

class KusuRC(rcplugin.Plugin):

    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'Setting up Xorg'
        self.desc = 'Setting up Xorg'
        self.ngtypes = ['installer']
        self.delete = True

        if self.os_name not in ['sles', 'opensuse' 'suse']:
            self.disable = True

    def run(self):

        xorg = path('/etc/X11/xorg.conf')

        if xorg.exists():
            xorg.remove()

        return True
