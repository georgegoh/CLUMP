#!/bin/sh
# In Kusu Installer mode?
# Do not change the following line!
if [ -e /tmp/kusu/installer_running ]; then exit 0; fi 

# Put any custom stuff after this line
# SQL/Shell/Python code to update the database.. The updates may optionally
# include Node group creation and component association

# sqlrunner may be used to perform sql injections
# ngedit may be used non-interactively to add and copy nodegroups

/bin/cat << 'EOF' > /etc/rc.kusu.d/S02KusuDataFS.rc.py
#!/usr/bin/env python
#

from path import path
from kusu.core import rcplugin
import sys

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'Kusu Documentation sources'
        self.desc = 'Setting up Kusu Documentation sources'
        self.ngtypes = ['installer']
        self.delete = True

    def run(self):
        """Setting up Kusu Documentation sources"""
        
        datafs = path('/opt/kusu/share/doc/kusu/Data.fs')
        olddatafs = path('/opt/Plone-3.0.3/zinstance/var/Data.fs')
        
        if not datafs.exists(): return False
            
        if not olddatafs.exists(): return False
            
        # delete the stock Data.fs
        olddatafs.remove()
        
        # copy our Data.fs into the old path
        datafs.copy('/opt/Plone-3.0.3/zinstance/var')
        
        return True

EOF