#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
import os
from path import path
from kusu.core import rcplugin

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'firefox-homepage'
        self.desc = 'Setting up default Firefox homepage'
        self.ngtypes = ['installer']
        self.delete = True

    def run(self):
        """Setup firefox default homepage."""
        lib_path_str = '/usr/lib'
        if not self.os_name in ['sles', 'suse']:
            arch = os.getenv('KUSU_DIST_ARCH')
            if arch.endswith('64'):
                lib_path_str += '64'
        lib_path = path(lib_path_str)

        ff_path_list = lib_path.listdir('firefox*')

        if not ff_path_list:
            # Firefox is not installed, so gracefully exit
            return True

        ff_path = ff_path_list[0]

        user_profile = ff_path / 'defaults' / 'profile' / 'user.js'
        if not user_profile.dirname().exists():
            user_profile.dirname().makedirs()

        f = user_profile.open('w')
        f.write('user_pref("browser.startup.homepage", "http://localhost/");\n')
        f.write('user_pref("startup.homepage_override_url", "http://localhost/");')
        f.close()
        return True
