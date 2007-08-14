#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import kusu.util.log as kusulog
from path import path
import os
import socket
import sys

try:
    import subprocess
except:
    from popen5 import subprocess

kl = kusulog.getKusuLog()
kl.addFileHandler()

class Plugin: 
    nodename = None
    niihost = None
    os_name = None
    os_version = None
    os_arch = None
    dbs = None
    repoid = None

    def __init__(self):
        self.hostname = socket.gethostname()
      
         # plugin specific settings
        self.name = None # name of the plugin
        self.desc = None # description of the plugin. Used to display during init
        self.disable = False # Whether this plugin is disabled
        self.delete = False # Wheter to delete this plugin after running
        self.ngtypes = ['installer', 'compute'] # types of nodegroups that this plugin should run

    def runCommand(self, cmd):
        p = subprocess.Popen(cmd,
                             shell=True,
                             stdout = subprocess.PIPE,
                             stderr = subprocess.PIPE)
        out, err = p.communicate()
        retval = p.returncode

        return retval, out, err

class PluginRunner:
    def __init__(self, classname, dir, dbs, debug=False):
        self.classname = classname
        self.dir = path(dir)
        self.plugins = {}
        self.dbs = dbs
        self.ngtype = self.getNodeGroupInfo()

        self.initPlugin()
        self.loadPlugins()

    def display(self, desc):
        print '%s%s:' % (' '*3, desc or ''),
        sys.stdout.flush()

    def failure(self):
        cmd = 'source /etc/init.d/functions && failure'
        failureP = subprocess.Popen(cmd,
                                    shell=True)
        failureP.communicate()
        print
        sys.stdout.flush()

    def success(self):
        cmd = 'source /etc/init.d/functions && success'
        successP = subprocess.Popen(cmd,
                                    shell=True)
        successP.communicate()
        print
        sys.stdout.flush()

    def run(self):
        results = []

        for fname in sorted(self.plugins.keys()):
            try:
                plugin = self.plugins[fname]
                self.display(plugin.desc)
                retval = plugin.run()
                if retval:
                    self.success()
                    kl.info('Plugin: %s ran successfully' % plugin.name)
                else:
                    self.failure()
                    kl.error('Plugin: %s failed to run successfully' % plugin.name)
            
                results.append( (plugin.name, retval, None) )

            except Exception, e:
                self.failure()
                results.append( (plugin.name, False, e) )
                kl.error('Plugin: %s failed to run successfully. Reason: %s' % (plugin.name,e))
                   
            if plugin.delete and (self.dir / fname).exists():
                (self.dir / fname).remove()

        return results

    def initPlugin(self):
        from rcplugin import Plugin
    
        Plugin.nodename = self.getNodeName()
        Plugin.niihost = self.getNIIHost()
        Plugin.os_name, Plugin.os_version, Plugin.os_arch = self.getOS()
        Plugin.repoid = self.getRepoID()
        Plugin.dbs = self.dbs
       
        logstr = 'Init plugin wth variables: nodename=%s, niihost=%s, '\
                 'os_name=%s, os_version=%s, os_arch=%s, '\
                 'repoid=%s' % (Plugin.nodename, Plugin.niihost, \
                  Plugin.os_name, Plugin.os_version, Plugin.os_arch,\
                  Plugin.repoid)

        kl.debug(logstr)

    def loadPlugins(self):
        for plugin in self.dir.listdir('*.py'): 

            if plugin in ['__init__.py']:
                continue

            ns = {}
            try:
                execfile(plugin, ns)
            except Exception, e:   
                kl.error('Unable to load plugin: %s Reason: %s' % (plugin.basename(), e))
                continue

            if ns.has_key(self.classname):
                try:
                    m = ns[self.classname]()
                except Exception, e:   
                    kl.error('Unable to instatiate plugin: %s Reason: %s' % (plugin.basename(), e))
                    continue
            
                if m.disable:
                    kl.info('Ignoring plugin: ' + m.name)
                    continue

                if self.ngtype not in m.ngtypes:
                    if m.delete and plugin.exists():
                        plugin.remove()

                    continue

                self.plugins[plugin.basename()] = m
                kl.info('Loaded plugin: ' + m.name)

    def getNodeGroupInfo(self):
        """Returns the node name, nodegroup name, nodegroup type"""

        node_name = None
        nodegroup_name = None
        nodegroup_type = None

        if path('/etc/profile.nii').exists():
            # On compute node
            nodegroup_type = self.parseNII('/etc/profile.nii', 'NII_NGTYPE')
 
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
            os_name, os_version, os_arch = self.parseNII('/etc/profile.nii', 'NII_OSTYPE').split('-')
        else:
            os_name = os.environ['KUSU_DIST']
            os_version = os.environ['KUSU_DISTVER']
            os_arch = os.environ['KUSU_DIST_ARCH']

        return os_name, os_version, os_arch

    def getNIIHost(self):
        nii_host = []

        if path('/etc/profile.nii').exists():
            # On compute node
            nii_host = [self.parseNII('/etc/profile.nii', 'NII_INSTALLERS')]

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
            node_name = self.parseNII('/etc/profile.nii', 'NII_HOSTNAME')
 
        else:
            row = self.dbs.AppGlobals.select_by(kname = 'PrimaryInstaller')[0]
            node_name = row.kvalue

        return node_name

    def getRepoID(self):
        repoid = None

        if path('/etc/profile.nii').exists():
            # On compute node
            repoid = int(self.parseNII('/etc/profile.nii', 'NII_REPOID'))
 
        else:
            row = self.dbs.AppGlobals.select_by(kname = 'PrimaryInstaller')[0]
            node_name = row.kvalue

            ng = self.dbs.NodeGroups.select_by(self.dbs.NodeGroups.c.ngid == self.dbs.Nodes.c.ngid,
                                               self.dbs.Nodes.c.name == node_name)
            if ng:
                repoid = ng[0].repoid

        return repoid

    def parseNII(self, nii, key):
        f = open(nii, 'r')
        lines = f.readlines()
        f.close()

        for line in lines:
            lst = line.split('=')

            if len(lst) >= 2:
                value = lst[1].strip()

            lst = lst[0].split()
            if len(lst) == 2:
                if key == lst[1].strip():
                    return value.strip('"')
           
        return None 
