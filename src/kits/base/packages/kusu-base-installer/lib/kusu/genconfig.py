# $Id$
#
#   Copyright 2007 Platform Computing Inc
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.
# 	
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
#
#

import os
import sys
import string

from kusu.core.app import KusuApp
from kusu.core.db import KusuDB


class Report:
    """This class will be used to generate various configuration files
    for applications and services on the installer and on other nodes."""
    
    def __init__(self, gettext):
        """__init__  - Initializer for the Report class.  For internationalization
        it must be passed the gettext object"""
        self.user     = 'nobody'
        self.database = 'kusudb'
        self.password = ''
        self.gettext  = gettext 
        self.plugins  = []

        query=('select distinct kits.kid '
               'from nodes, nodegroups, repos, repos_have_kits, kits, appglobals '
               'where kits.kid = repos_have_kits.kid and '
               'repos.repoid = repos_have_kits.repoid and '
               'nodegroups.repoid = repos.repoid and '
               'nodegroups.ngid = nodes.ngid and '
               'nodes.name = appglobals.kvalue and '
               'appglobals.kname = \'PrimaryInstaller\'')
        db = KusuDB()
        db.connect(self.database, self.user, self.password)
        db.execute(query)
        kitslist = db.fetchall()
        for kit in kitslist:
            plug='/depot/kits/%s/plugins/genconfig' % str(kit[0])
            if os.path.isdir(plug):
                self.plugins.append(plug)

    def setRepoPlugins(self, repo):
        query=('select distinct kits.kid '
               'from repos, repos_have_kits, kits '
               'where kits.kid = repos_have_kits.kid and '
               'repos.repoid = repos_have_kits.repoid and '
               'repos.reponame = \'%s\'' % repo)
        db = KusuDB()
        db.connect(self.database, self.user, self.password)
        db.execute(query)
        kitslist = db.fetchall()
        self.plugins = []

        if not kitslist:
            print "Repository %s does not exist." % repo
        else:
            for kit in kitslist:
                plug='/depot/kits/%s/plugins/genconfig' % str(kit[0])
                if os.path.isdir(plug):
                    self.plugins.append(plug)

        
    def setNGPlugins(self, ngroup):
        query=('select distinct kits.kid '
               'from repos, repos_have_kits, kits, nodegroups '
               'where kits.kid = repos_have_kits.kid and '
               'repos.repoid = repos_have_kits.repoid and '
               'repos.repoid = nodegroups.repoid and '
               'nodegroups.ngname = \'%s\'' % ngroup)
        db = KusuDB()
        db.connect(self.database, self.user, self.password)
        db.execute(query)
        kitslist = db.fetchall()
        self.plugins = []

        if not kitslist:
            print "Nodegroup name %s does not exist." % ngroup
        else:
            for kit in kitslist:
                plug='/depot/kits/%s/plugins/genconfig' % str(kit[0])
                if os.path.isdir(plug):
                    self.plugins.append(plug)


    def toolHelp(self):
        """toolHelp - This method will provide the help for each of the
        plugins.  Each plugin must override this method."""
        msg = self.gettext("genconfig_Help")
        print msg
        
        for plugin in self.plugins:
            dirlist = os.listdir(plugin)
            for file in dirlist:
                if file[-3:] == '.py' and file[0:2] != '__':
                    print "%s\t" % file[:-3],
            
        sys.exit(0)


    def runPlugin(self, pluginargs):
        """runPlugin - Each plugin will impliment this method.  This is what does
        the real work"""
        pass


    def run(self, plugin, action, pargs):
        """run - This method is responsible for calling the appropriate interface
        from the plugin"""
        
        if self.plugins: 
            exec "from " + plugin + " import *"
            pinst = thisReport(self.gettext)
            if action == 'help':
                pinst.toolHelp()
            else:
                # Get a database connection for the plugin to use
                pinst.db = KusuDB()
                pinst.db.connect(self.database, self.user, self.password)       

                # Run the plugin
                pinst.runPlugin(pargs)  
         

    def altDb(self, database, user, password):
        """altDb - Change the database user, password and database"""
        self.database = database
        self.user = user
        self.password = password
    
