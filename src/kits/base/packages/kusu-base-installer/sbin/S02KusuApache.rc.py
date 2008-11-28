#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from path import path
from kusu.core import rcplugin

from primitive.system.software.dispatcher import Dispatcher 

import os
import pwd

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'httpd'
        self.desc = 'Setting up httpd'
        self.ngtypes = ['installer']
        self.delete = True

    def run(self):
        """Setup Apache"""

        wwwroot = path(Dispatcher.get('webserver_docroot'))

        apache = Dispatcher.get('webserver_usergroup')[0]
        apache = pwd.getpwnam(apache)
        uid = apache[2]
        gid = apache[3]

        nodeboot = path('/depot/repos/nodeboot.cgi')
        nodeboot.chown(uid, gid)
        nodeboot.chmod(0770)

        # Set kusu.log permission
        filename = path(os.environ["KUSU_LOGFILE"])
        filename.chown(uid, gid)
        filename.chmod(0644)

        # kusu KUSU_LOGFILE path permission
        parent_path = filename.splitpath()[0].abspath()
        parent_path.chown(uid, gid)
        parent_path.chmod(0755)

        kusu_root = path(os.environ.get('KUSU_ROOT', '/opt/kusu'))

        if wwwroot.exists():
            if not (wwwroot / 'cfm').exists():
                path(kusu_root / 'cfm').symlink(wwwroot / 'cfm')

            if not (wwwroot / 'repos').exists():
                path('/depot/repos').symlink(wwwroot / 'repos')

            if not (wwwroot / 'images').exists():
                path('/depot/images').symlink(wwwroot / 'images')

            if not (wwwroot / 'kits').exists():
                path('/depot/www/kits').symlink(wwwroot / 'kits')

            success, (out,retcode,err) = self.service('webserver', 'enable')
            if not success:
                raise Exception, err
    	    
            webserver_confdir = path(Dispatcher.get('webserver_confdir'))
            kusu_conf =  webserver_confdir / 'kusu.conf'
            retval = self.runCommand('$KUSU_ROOT/bin/genconfig apache_conf > ' + kusu_conf)[0]
            if retval != 0: return False

            success, (out,retcode,err) = self.service('webserver', 'restart')
            if not success:
                raise Exception, err

            return True
        else:
            return False
