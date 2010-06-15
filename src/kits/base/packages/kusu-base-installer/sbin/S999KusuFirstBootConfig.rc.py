#!/usr/bin/env python
#
# Copyright (C) 2007 Platform Computing Inc.

# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

from path import path
from kusu.core import rcplugin
import subprocess

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'firstbootConfig'
        self.desc = 'Starting initial configuration procedure'
        self.ngtypes = ['installer']
        self.delete = False

    def run(self):
        """Run firstboot configuration script on the installer"""
        
        firstbootDirectory = path('/opt/kusu/firstboot')
        
        if not firstbootDirectory.exists():
            firstbootDirectory.mkdir()
        else:
            rcScripts = [ file for file in firstbootDirectory.files()
                          if not (file.lower().endswith('.disable')
                                 or file.lower().endswith('.pyo')
                                 or file.lower().endswith('.pyc')) ]
            for script in rcScripts:
                try:
                    scriptExecution = subprocess.Popen(script)
                    scriptExecution.wait()
                    script.move(script + '.disable' ) 
                except OSError, osException:
                    print "Script '%s' failed: %s" % (script, osException)

        return True