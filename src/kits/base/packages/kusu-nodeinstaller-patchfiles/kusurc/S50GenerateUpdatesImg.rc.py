#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

"""kusurc wrapper around /opt/kusu/sbin/genupdatesimg"""

from kusu.core import rcplugin

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'nodeinstaller-patchfiles'
        self.desc = 'Generating nodeinstaller patchfiles'
        self.ngtypes = ['installer']
        self.delete = True

    def run(self):
        """Generate nodeinstaller patchfiles"""

        self.runCommand('$KUSU_ROOT/sbin/genupdatesimg')

        return True
