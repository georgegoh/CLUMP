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
import sys
import traceback
import time
import re

sys.path.append("/opt/kusu/lib")
import platform
if platform.machine() == "x86_64":
    sys.path.append("/opt/kusu/lib64/python")
sys.path.append("/opt/kusu/lib/python")
sys.path.append('/opt/primitive/lib/python2.4/site-packages')

import kusu.util.log as kusulog
from kusu.util.errors import CommandFailedToRunError
from kusu.util.tools import service
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
                             stderr = subprocess.STDOUT)

        # Also with S99RunCFMSync script to redirect output to a file
        #  cfmsync -p >> /var/log/kusu/kusurc.log 2>&1
        fptr = open('/var/log/kusu/kusurc.log', 'a')
        fptr.write('Running: %s\n' % cmd)
        retval = None
        while retval == None:
            retval = p.poll()
            dump = p.stdout.readlines()
            if len(dump):
                fptr.writelines(dump)
            else:
                time.sleep(.05)
        fptr.close()

        return retval, '', ''

    service = staticmethod(service)


def getInteger(string):
    """ Find and return the first occurence of integers in a string.
        Returns None if no integers are found.
    """
    occurences = re.findall(r'\d+',string)
    if occurences:
        return int(occurences[0])
    return None


def rcCompare(scriptName, comparedName):
    """ Compare the integers of 2 filenames using getInteger method.
        Do simple string comparison if:
        - any of them have no integers, or
        - both have the same integer.
    """
    scriptInteger = getInteger(scriptName)
    comparedInteger = getInteger(comparedName)
    cmpResult = 0

    # Make sure that both have a valid integer before doing a comparison.
    if (scriptInteger is not None and comparedInteger is not None):
        cmpResult = cmp(scriptInteger, comparedInteger)

    # If they have no difference so far, then do a string comp.
    if cmpResult == 0:
        cmpResult = cmp(scriptName, comparedName)

    return cmpResult


class PluginRunner:
    def __init__(self, classname, p, dbs, debug=False):
        self.classname = classname
        self.plugins = {}
        self.dbs = dbs
        self.ngtype, self.ngid = self.getNodeGroupInfo()

        self.initPlugin()
        self.pluginPath = p

    def display(self, desc):
        print '%s%s:' % (' '*3, desc or ''),
        sys.stdout.flush()

    def failure(self):
        cmd = 'source /lib/lsb/init-functions && log_failure_msg "$@"'
        failureP = subprocess.Popen(cmd,
                                    shell=True)
        failureP.communicate()
        sys.stdout.flush()

    def success(self):
        cmd = 'source /lib/lsb/init-functions && log_success_msg "$@"'
        successP = subprocess.Popen(cmd,
                                    shell=True)
        successP.communicate()
        sys.stdout.flush()

    def run(self, ignoreFiles=[]):
        results = []

        kusuenv = os.environ.copy()
        kusuenv['KUSU_NODE_NAME'] = Plugin.nodename
        kusuenv['KUSU_NII_HOST'] = ' '.join(Plugin.niihost)
        kusuenv['KUSU_OS_NAME'] = Plugin.os_name
        kusuenv['KUSU_OS_VERSION'] = Plugin.os_version
        kusuenv['KUSU_OS_ARCH'] = Plugin.os_arch
        kusuenv['KUSU_REPOID'] = str(Plugin.repoid)
        kusuenv['KUSU_NGTYPE'] = self.ngtype

        plugins = self.loadPlugins(self.pluginPath)

        for fname in sorted(plugins.keys(), rcCompare):
            if fname.exists() and not fname in ignoreFiles:
                if type(plugins[fname]) == str:
                    fbasename = fname.basename()
                    self.display('Running ' + fbasename)

                    try:
                        p = subprocess.Popen(plugins[fname],
                                             env = kusuenv,
                                             shell=True,
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.STDOUT)

                        fptr = open('/var/log/kusu/kusurc.log', 'a')
                        fptr.write('Calling: %s \n' % plugins[fname])
                        retval = None
                        while retval == None:
                            retval = p.poll()
                            dump = p.stdout.readlines()
                            if len(dump):
                                fptr.writelines(dump)
                            else:
                                time.sleep(.05)

                        fptr.close()

                        if retval == 0:
                            retval = True
                            self.success()
                            kl.info('Plugin: %s ran successfully' % fbasename)
                        else:
                            retval = False
                            self.failure()
                            kl.error('Plugin: %s failed to run successfully' % fbasename)

                        results.append( (fbasename, fname, retval, None) )

                    except Exception, e:
                        self.failure()
                        results.append( (fbasename, fname, 0, e) )
                        kl.error('Plugin: %s failed to run successfully. Reason: %s' % (fbasename,e))

                else:
                    try:
                        plugin = plugins[fname]
                        self.display(plugin.desc)
                        retval = plugin.run()
                        if retval:
                            self.success()
                            kl.info('Plugin: %s ran successfully' % plugin.name)
                        else:
                            self.failure()
                            kl.error('Plugin: %s failed to run successfully' % plugin.name)

                        results.append( (plugin.name, fname, retval, None) )

                    except CommandFailedToRunError, e:
                        self.failure()
                        kl.error('Plugin: %s failed to run successfully. Reason: %s' % (plugin.name, e))
                        kl.error('Plugin traceback:\n%s', traceback.format_exc())
                        kl.error('No more plugins will be executed.')
                        raise
                    except Exception, e:
                        self.failure()
                        results.append( (plugin.name, fname, 0, e) )
                        kl.error('Plugin: %s failed to run successfully. Reason: %s' % (plugin.name,e))
                        kl.error('Plugin traceback:\n%s', traceback.format_exc())

                    if plugin.delete and fname.exists():
                        self.removeByteCompiledFiles(fname)

                        firstrun = path('/etc/rc.kusu.d/firstrun')
                        if not firstrun.exists():
                            firstrun.makedirs()
                        fname.move(firstrun / fname.basename())

        return results

    def initPlugin(self):
        from rcplugin import Plugin

        Plugin.nodename = self.getNodeName()
        Plugin.niihost = self.getNIIHost()
        Plugin.os_name, Plugin.os_version, Plugin.os_arch = self.getOS()
        Plugin.repoid = self.getRepoID()
        Plugin.dbs = self.dbs
        Plugin.appglobals = self.getAppGlobals()

        logstr = 'Init plugin wth variables: nodename=%s, niihost=%s, '\
                 'os_name=%s, os_version=%s, os_arch=%s, '\
                 'repoid=%s' % (Plugin.nodename, Plugin.niihost, \
                  Plugin.os_name, Plugin.os_version, Plugin.os_arch,\
                  Plugin.repoid)

        kl.debug(logstr)

    def loadPlugins(self, pluginPath):
        if pluginPath.isdir():
            plugins = pluginPath.listdir()
        else:
            plugins = [pluginPath]

        pluginsData = {}
        for plugin in plugins:

            if not plugin.isfile():
                continue

            if plugin.endswith('.pyc') or plugin.endswith('.pyo'):
                continue

            if plugin.endswith('.rc.py'):
                ns = {}
                try:
                    execfile(plugin, ns)
                except Exception, e:
                    kl.error('Unable to load plugin: %s Reason: %s' % (plugin.basename(), e))
                    kl.error('Plugin traceback:\n%s', traceback.format_exc())
                    continue

                if ns.has_key(self.classname):
                    try:
                        m = ns[self.classname]()
                    except Exception, e:
                        kl.error('Unable to instatiate plugin: %s Reason: %s' % (plugin.basename(), e))
                        kl.error('Plugin traceback:\n%s', traceback.format_exc())
                        continue

                    if m.disable:
                        kl.info('Ignoring plugin: ' + m.name)
                        continue

                    if self.ngtype not in m.ngtypes:
                        if m.delete and plugin.exists():
                            self.removeByteCompiledFiles(plugin)
                            plugin.remove()
                        continue

                    pluginsData[plugin] = m
                    kl.info('Loaded plugin: ' + m.name)

            else:
                pluginsData[plugin] = str(plugin)
                kl.info('Loaded plugin: ' + plugin.basename())

        return pluginsData

    def getNodeGroupInfo(self):
        """Returns nodegroup type, nodegroup ID"""

        nodegroup_type = None
        nodegroup_id = None

        if path('/etc/profile.nii').exists():
            # On compute node
            nodegroup_type = self.parseNII('/etc/profile.nii', 'NII_NGTYPE')
            nodegroup_id = self.parseNII('/etc/profile.nii', 'NII_NGID')

        else:
            row = self.dbs.AppGlobals.select_by(kname = 'PrimaryInstaller')[0]
            masterName = row.kvalue

            node = self.dbs.Nodes.select_by(name = masterName)[0]

            ng = self.dbs.NodeGroups.select_by(self.dbs.Nodes.c.name == masterName,
                                               self.dbs.NodeGroups.c.ngid == self.dbs.Nodes.c.ngid)[0]

            nodegroup_id = ng.ngid
            nodegroup_type = ng.type

        return (nodegroup_type, nodegroup_id)

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

            # Keep this import statement here since we don't need
            # (and don't want to) to install sqlalchemy on compute nodes.
            import sqlalchemy

            nics = self.dbs.Nics.select_by(self.dbs.Nodes.c.nid == self.dbs.Nics.c.nid,
                                           self.dbs.Nics.c.netid == self.dbs.Networks.c.netid,
                                           self.dbs.Networks.c.type == 'provision',
                                           self.dbs.Nodes.c.name == node_name,
                                           sqlalchemy.func.lower(self.dbs.Networks.c.device) != 'bmc')

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

    def parseNIIAll(self, nii):
        """
        parse nii file and return a dictionary containing all appglobal variables.
        """
        appglobal_map = {}
        if not path(nii).exists():
            return appglobal_map

        confp = open(nii, 'r')
        lines = confp.readlines()
        confp.close()
        
        for line in lines:
            # ignore empty line and comment line
            if line.isspace():
                continue
            if line.strip().startswith('#'):
                continue

            assignstr = line.split()
            if len(assignstr) != 2:
                continue
            couple = assignstr[1].split('=')
            if len(couple) == 2:
                key = couple[0].strip()
                value = couple[1].strip().strip('"\'')
                appglobal_map[key] = value

        return appglobal_map

    def getAppGlobalsFromDB(self):
        """
        dump appglobals from DB and return as a dictionary.
        """
        appglobal_map = {}
        rows = self.dbs.AppGlobals.select_by('ngid is NULL or ngid = %s' % self.ngid)
        for row in rows:
            kname = (row.kname or '').strip()
            if kname: 
                 appglobal_map[kname] = (row.kvalue or '').strip()
        return appglobal_map

    def getAppGlobals(self):
        """
        Get all appglobal variables and return as a dictionary.
        If ngid is specified for an appglobals variable, won't include it in the 
            dictionary if the ngid not same with node's ngid.
        Include all appglobals with NULL ngid column.
        """
        # compute nodes.
        if path('/etc/profile.nii').exists():
            return self.parseNIIAll('/etc/profile.nii')
        # master
        return self.getAppGlobalsFromDB()

    def removeByteCompiledFiles(self, fname):
        bcFiles = [ path("%sc" % fname), path("%so" % fname) ]
        for file in bcFiles:
            if file.exists():
                file.remove()
