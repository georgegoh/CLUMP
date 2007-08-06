#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from path import path
import os
import socket

try:
    import subprocess
except:
    from popen5 import subprocess

 
class Plugin: 
    nodename = None
    niihost = None
    os_name = None
    os_version = None
    os_arch = None
 
    def __init__(self):
        self.hostname = socket.gethostname()
      
         # plugin specific settings
        self.name = None # name of the plugin
        self.desc = None # description of the plugin. Used to display during init
        self.disable = False # Whether this plugin is disabled
        self.ngtypes = ['installer', 'compute'] # types of nodegroups that this plugin should run

class PluginRunner:
    def __init__(self, classname, dirs, dbs, debug=False):
        self.classname = classname
        self.dirs = path(dirs)
        self.plugins = {}
        self.dbs = dbs
        self.ngtype = self.getNodeGroupInfo()

        self.initPlugin()
        self.loadPlugins()

    def failure(self, desc):
        print ' '*3,  desc,
     
        cmd = 'source /etc/init.d/functions && failure'
        failureP = subprocess.Popen(cmd,
                                    shell=True)
        failureP.communicate()
        print

    def success(self, desc):
        print ' '*3, desc,

        cmd = 'source /etc/init.d/functions && success'
        successP = subprocess.Popen(cmd,
                                    shell=True)
        successP.communicate()
        print

    def run(self):
        results = []

        for plugin in self.plugins.values():
            try:
                retval = plugin.run()
                if retval:
                    self.success(plugin.desc)
                else:
                    self.failure(plugin.desc)
            
                results.append( (plugin.name, retval, None) )

            except Exception, e:
                self.failure(plugin.desc)
                results.append( (plugin.name, False, e) )
                    
        return results

    def initPlugin(self):
        from plugin import Plugin

        Plugin.nodename = self.getNodeName()
        Plugin.niihost = self.getNIIHost()
        Plugin.os_name, Plugin.os_version, Plugin.os_arch = self.getOS()

    def loadPlugins(self):
        for plugin in self.dirs.listdir('*.py'): 

            if plugin in ['__init__.py']:
                continue

            ns = {}
            try:
                execfile(plugin, ns)
            except Exception, e:   
                continue

            if ns.has_key(self.classname):
                try:
                    m = ns[self.classname]()
                except Exception, e:   
                    continue
            
                if m.disable:
                    continue

                if self.ngtype not in m.ngtypes:
                    continue

                self.plugins[m.name] = m

    def getNodeGroupInfo(self):
        """Returns the node name, nodegroup name, nodegroup type"""

        node_name = None
        nodegroup_name = None
        nodegroup_type = None

        if path('/etc/profile.nii').exists():
            # On compute node
            nodegroup_type = None
 
        else:
            row = self.dbs.AppGlobals.select_by(kname = 'PrimaryInstaller')[0]
            masterName = row.kvalue

            node = self.dbs.Nodes.select_by(name = masterName)[0]

            ng = self.dbs.NodeGroups.select_by(self.dbs.Nodes.c.name == masterName,
                                               self.dbs.NodeGroups.c.ngid == self.dbs.Nodes.c.ngid)[0]

            nodegroup_name = ng.ngname
            nodegroup_type = ng.type

        return nodegroup_type
 
    def getOS(self):
        os_name = None
        os_version = None
        os_arch = None

        if path('/etc/profile.nii').exists():
            return os_name, os_version, os_arch
        else:
            os_name = os.environ['KUSU_DIST']
            os_version = os.environ['KUSU_DISTVER']
            os_arch = os.environ['KUSU_DIST_ARCH']

        return os_name, os_version, os_arch

    def getNIIHost(self):
        nii_host = []

        if path('/etc/profile.nii').exists():
            # On compute node
            nii_host = []
 
        else:
            row = self.dbs.AppGlobals.select_by(kname = 'PrimaryInstaller')[0]
            node_name = row.kvalue

            nics = self.dbs.Nics.select_by(self.dbs.Nodes.c.nid == self.dbs.Nics.c.nid,
                                           self.dbs.Nics.c.netid == self.dbs.Networks.c.netid,
                                           self.dbs.Networks.c.type == 'provision',
                                           self.dbs.Nodes.c.name == node_name)

            nii_host = [ nic.ip for nic in nics if nic.ip ]

        return nii_host

    def getNodeName(self):
        node_name = None

        if path('/etc/profile.nii').exists():
            # On compute node
            node_name = None
 
        else:
            row = self.dbs.AppGlobals.select_by(kname = 'PrimaryInstaller')[0]
            node_name = row.kvalue

        return node_name


