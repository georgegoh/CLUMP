#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from path import path
from kusu.core.plugin import Plugin

import os

class KusuRC(Plugin):
    def __init__(self):
        Plugin.__init__(self)
        self.name = 'httpd'
        self.desc = 'Setting up httpd'
        self.ngtypes = ['installer']
        self.delete = True

    def run(self):
        """Setup Apache"""

        kusu_root = path(os.environ.get('KUSU_ROOT', '/opt/kusu'))

        if path('/var/www/html').exists():

            if not path('/var/www/html/cfm').exists():
                path(kusu_root / 'cfm').symlink('/var/www/html/cfm')

            if not path('/var/www/html/repos').exists():
                path('/depot/repos').symlink('/var/www/html/repos')

            if not path('/var/www/html/images').exists():
                path('/depot/images').symlink('/var/www/html/images')

            self.runCommand('/sbin/chkconfig httpd on')
    	    
            retval = self.runCommand('$KUSU_ROOT/bin/genconfig apache_conf > /etc/httpd/conf.d/kusu.conf')[0]
            if retval != 0: return False

            retval = self.runCommand('/etc/init.d/httpd restart')[0]
            if retval != 0: return False

            return True
        else:
            return False
