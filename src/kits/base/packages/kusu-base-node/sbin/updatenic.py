#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id$
#
# Copyright 2010 Platform Computing Inc
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


# This script has the following functions:
#   1. Determine the IP address of the Installer node
#   2. Retrieve the NII and set the state to installed
#   3. Create/update the CFM shared secret
#   4. Create/update the profile.nii
#   5. Call the script to generate the network config
#
# It should be run only after the network is up, but before other
# services have started.
# It should not run on the installer.

import os
import sys
import string
import gettext
import shutil
import time
import glob

try:
    import subprocess
except:
    from popen5 import subprocess

from kusu.ipfun import *
from primitive.nodeinstall.niifun import *

LOGFILE = '/var/log/kusu/updatenic.log'

class App:
    def __init__(self):
        """ Initialize Class variables.  Extend as needed (if needed) """
        self.args        = sys.argv
        self.installerIP = ''    # The IP address of the installer
        self.ostype      = ''

        langdomain       = 'kusunodeapps'
        localedir        = '/opt/kusu/share/locale'

        if not os.path.exists(localedir):
            # Try the system path
            localedir = '/usr/share/locale'

        gettext.bindtextdomain(langdomain, localedir)
        gettext.textdomain(langdomain)
        self.gettext = gettext.gettext
        self._ = self.gettext

    def err(self, message, *args):
        """Output messages to STDERR with Internationalization.
        Additional arguments will be used to substitute variables in the
        message output"""
        if len(args) > 0:
            mesg = self.gettext(message) % args
        else:
            mesg = self.gettext(message)
        sys.stderr.write(mesg)
        try:
            fp = open(LOGFILE, 'a')
            fp.write(mesg)
            fp.close()
        except:
            pass

    def out(self, message, *args):
        """Output messages to STDOUT with Internationalization.
        Additional arguments will be used to substitute variables in the
        message output"""
        if len(args) > 0:
            mesg = self.gettext(message) % args
        else:
            mesg = self.gettext(message)
        sys.stdout.write(mesg)
        try:
            fp = open(LOGFILE, 'a')
            fp.write(mesg)
            fp.close()
        except:
            pass

    def getInstallerIP(self):
        """Get the installer's IP address"""
        self.installerIP = self.getProfileVal('NII_INSTALLERS')
        if self.installerIP == '':
            self.err("ERROR:  Failed to determine the IP address of the Installer.\n")
            self.err("ERROR:  Do not run this tool on the installer.\n")
            sys.exit(-1)
        self.out("Installer IP is: %s\n", self.installerIP)

    def getProfileVal(self, name):
        """Returns the value of the NII property from
        /etc/profile.nii with any quotes removed."""
        cmd = "grep %s /etc/profile.nii 2>/dev/null" % name
        val = ''
        proc = os.popen(cmd)
        for line in proc.readlines():
            loc = string.find(line, name)
            if loc < 0:
                continue

            t2 = string.split(line[string.find(line, '=')+1:])[0]
            val = string.strip(t2, '"')
            break
        proc.close()
        return val

    def getHaddrForNic(self, nic):
        """Extracts the HWADDR field from a NIC configuration
        script.  It looks like:  HWADDR=00:16:29:F7:99:99 """

        filename = '/etc/sysconfig/network-scripts/ifcfg-%s' % nic
        if not os.path.exists(filename):
            # MAC address not really needed for other OSes.
            return ''

        try:
            fin = open(filename, 'r')
        except:
            return ''
        lines = fin.readlines()
        fin.close()

        for line in lines:
            if line[0] == "#" or line.isspace():
                continue
            try:
                key,val = string.split(line, '=', 1)
                key = string.strip(key)
            except:
                continue
            if key == 'HWADDR':
                val = string.strip(val)
                return val

    def getNii(self):
        url = 'http://%s/repos/nodeboot.cgi?dump=1' % self.installerIP
        goturl = False
        for i in [1, 2, 3, 4, 5, 6]:
            try:
                (niidata, header) = urllib.urlretrieve(url)
                goturl = True
            except:
                self.err("WARNING:  Failed to download NII.  Try: %i\n", i)
                time.sleep(5)

        if not goturl:
            self.err("ERROR:  Failed to download NII using: %s\n", url)
            sys.exit(-1)

        parser = make_parser()
        self.niihandler = NodeInstInfoHandler()
        parser.setContentHandler(self.niihandler)
        try:
            parser.parse(open(niidata))
        except:
            self.err("ERROR:  Error parsing NII got:\n")
            fp = open(niidata)
            print fp.readlines()
            fp.close()
            sys.exit(-1)

        if self.niihandler.name == '':
            self.err("ERROR:  Failed to get good NII\n")
            fp = open(niidata)
            data = fp.readlines()
            fp.close()
            for line in data:
                self.err(line)
            sys.exit(-1)

        os.unlink(niidata)
        self.ostype = string.split(self.niihandler.ostype, '-', 1)[0]
        return self.niihandler

    def updateHostname(self, niihandler):
        '''Update the host's name in the configuration and set it'''
        dnszone = ''
        if niihandler.appglobal.has_key('DNSZone'):
            fqhn = "%s.%s" % (niihandler.name, niihandler.appglobal['DNSZone'])
        else:
            fqhn = niihandler.name

        if self.ostype in ['rhel', 'centos', 'fedora']:
            if os.path.exists('/etc/sysconfig/network'):
                fp = open('/etc/sysconfig/network', 'r')
                lines = fp.readlines()
                fp.close()
                fp = open('/etc/sysconfig/network', 'w')
                for line in lines:
                    try:
                        key,val = string.split(line, '=', 1)
                    except:
                        key = 'none'
                    if key == 'HOSTNAME':
                        line = "HOSTNAME=%s\n" % fqhn
                    fp.write(line)
                fp.close()
            else:
                self.err("WARNING:  Failed to update NOSTNAME in network file")

        elif self.ostype in ['sles', 'suse', 'opensuse']:
            fp = open('/etc/HOSTNAME', 'w')
            fp.write('%s\n' % fqhn)
            fp.close()

        cmd = '/bin/hostname %s' % fqhn
        os.system(cmd)

    def delOldNics(self, niihandler):

        # Get list of existing configs, and build a list of current NICs
        delNics = []
        if self.ostype in ['rhel', 'centos', 'fedora']:
            pattern = '/etc/sysconfig/network-scripts/ifcfg-*'
        elif self.ostype in ['sles', 'suse', 'opensuse']:
            pattern = '/etc/sysconfig/network/ifcfg-*'

        flist = glob.glob(pattern)
        for i in flist:
            n = i[len(pattern)-1:]
            if n == 'lo':
                continue
            delNics.append(n)

        # Determine which NICS need to be removed
        if delNics:
            for i in niihandler.nics.keys():
                dev = niihandler.nics[i]['device']
                if niihandler.nics[i]['device'] in delNics:
                    delNics.remove(dev)

                # SLES names its ifcfg file like this:
                #   ifcfg-eth-id-00:0c:29:36:16:24
                # So we check for that pattern in delNics.
                mac = niihandler.nics[i]['mac']
                if mac:
                    sles_ifcfg_file = "eth-id-%s" % mac
                    if sles_ifcfg_file in delNics:
                        delNics.remove(sles_ifcfg_file)

        # delNics should only contain NICS that need to be deleted
        for i in delNics:
            self.out("Deconfiguring NIC %s\n", i)

            # This works for both RHEL and SLES because
            #   /sbin/ifdown eth-id-<MAC>
            # actually works on SLES. See 'man 8 ifdown' on SLES
            # for more info.
            cmd = '/sbin/ifdown %s' % i
            os.system(cmd)

            if self.ostype in ['rhel', 'centos', 'fedora']:
                mac = ''
                ifcfg = '/etc/sysconfig/network-scripts/ifcfg-%s' % i
                if os.path.exists(ifcfg):
                    # Back it up and extract the MAC
                    shutil.copy(ifcfg, "/tmp/ifcfg-%s.ORIG" % i)
                    mac = self.getHaddrForNic(i)

                # Write back the file
                fp = open("%s" % ifcfg, 'w')
                fp.write('# Updated by PCM/Kusu\n')
                fp.write('DEVICE=%s\n' % i)
                fp.write('ONBOOT=no\n')
                if mac:
                    fp.write('HWADDR=%s\n' % mac)
                fp.close()

            elif self.ostype in ['sles', 'opensuse', 'suse']:
                ifcfg = '/etc/sysconfig/network/ifcfg-%s' % i
                if os.path.exists(ifcfg):
                    # Back it up
                    shutil.copy(ifcfg, "/tmp/ifcfg-%s.ORIG" % i)

                    # Update ifcfg file so that this interface does not start on boot.
                    cmd = """/bin/sed -i -e "/STARTMODE=/cSTARTMODE='manual'" %s""" % ifcfg
                    sed = subprocess.Popen(cmd, shell=True)
                    sed.communicate()
                    if sed.returncode <> 0:
                        self.err("Error: unable to update %s\n", ifcfg)


    def configNics(self, niihandler):
        """Update the NIC config."""
        for i in niihandler.nics.keys():
            self.out("------------------------------ NICS:  Key = %s\n", i)
            self.out("    Device  = %s\n", (niihandler.nics[i]['device']))
            self.out("    IP      = %s\n", (niihandler.nics[i]['ip']))
            self.out("    subnet  = %s\n", (niihandler.nics[i]['subnet']))
            self.out("    network = %s\n", (niihandler.nics[i]['network']))
            self.out("    suffix  = %s\n", (niihandler.nics[i]['suffix']))
            self.out("    gateway = %s\n", (niihandler.nics[i]['gateway']))
            self.out("    dhcp    = %s\n", (niihandler.nics[i]['dhcp']))
            self.out("    options = %s\n", (niihandler.nics[i]['options']))

            # Call external script to handle BMC devices
            if niihandler.nics[i]['device'] == 'bmc':
                self.out("Configuring BMC\n")
                # ---------------------  NEED THE SCRIPT  ---------------------------------------   FIX ME
                if not os.path.exists("/opt/omsa"):
                   os.system("/opt/kusu/bin/kusurc /etc/rc.kusu.d/S99DellBMCSetup")
                continue

            if self.ostype in ['rhel', 'centos', 'fedora']:
                mac = ''
                ifcfg = '/etc/sysconfig/network-scripts/ifcfg-%s' % niihandler.nics[i]['device']
                if os.path.exists(ifcfg):
                    # Back it up and extract the MAC
                    shutil.copy(ifcfg, "/tmp/ifcfg-%s.ORIG" % niihandler.nics[i]['device'])
                    mac = self.getHaddrForNic(niihandler.nics[i]['device'])

                # Write back the file
                fp = open(ifcfg, 'w')
                fp.write('# Updated by PCM/Kusu\n')
                fp.write('DEVICE=%s\n' % niihandler.nics[i]['device'])
                fp.write('ONBOOT=yes\n')
                if niihandler.nics[i]['dhcp'] == '0':
                    fp.write('BOOTPROTO=static\n')
                    fp.write('IPADDR=%s\n' % niihandler.nics[i]['ip'])
                    fp.write('NETWORK=%s\n' % niihandler.nics[i]['network'])
                    fp.write('NETMASK=%s\n' % niihandler.nics[i]['subnet'])
                    # Don't think BROADCAST is needed
                else:
                    fp.write('BOOTPROTO=dhcp\n')

                if mac:
                    fp.write('HWADDR=%s\n' % mac)

                fp.close()

                # Bring up NIC
                cmd = '/sbin/ifdown %s' % niihandler.nics[i]['device']
                os.system(cmd)
                cmd = '/sbin/ifup %s' % niihandler.nics[i]['device']
                os.system(cmd)

            elif self.ostype in ['sles', 'opensuse', 'suse']:
                # 1. opensuse uses 'ifcfg-ethX' and not 'ifcfg-eth-id-<MAC>' for ethX interfaces.
                # 2. For ib interfaces in SLES and opensuse, use 'ifcfg-ibX'.
                interface = niihandler.nics[i]['device']
                if niihandler.nics[i]['device'].startswith('eth') and self.ostype in ['sles', 'suse']:
                    mac = niihandler.nics[i]['mac']
                    # mac address for this interface may not be present in profile.nii
                    # because this is a new interface. PCM only has the mac addresses
                    # of interfaces that were used to perform the provisioning. So
                    # here we only use the 'eth-id-<MAC>' style of naming the interface
                    # if its mac address is provided.
                    if mac:
                        interface = 'eth-id-%s' % mac

                ifcfg = '/etc/sysconfig/network/ifcfg-%s' % interface

                if os.path.exists(ifcfg):
                    # Back it up
                    shutil.copy(ifcfg, "/tmp/ifcfg-%s.ORIG" % interface)

                # Write the file. This over-writes an existing file.
                fp = open(ifcfg, 'w')
                fp.write('# Updated by PCM/Kusu\n')
                fp.write("STARTMODE='onboot'\n")
                if niihandler.nics[i]['dhcp'] == '0':
                    fp.write('BOOTPROTO=static\n')
                    fp.write('IPADDR=%s\n' % niihandler.nics[i]['ip'])
                    fp.write('NETWORK=%s\n' % niihandler.nics[i]['network'])
                    fp.write('NETMASK=%s\n' % niihandler.nics[i]['subnet'])
                else:
                    fp.write('BOOTPROTO=dhcp\n')

                fp.close()

                # Bring up NIC
                cmd = '/sbin/ifdown %s' % interface
                os.system(cmd)
                cmd = '/sbin/ifup %s' % interface
                os.system(cmd)

    def run(self):
        self.getInstallerIP()
        niihandler = self.getNii()

        self.out("Name        = %s\n", niihandler.name)
        self.out("installers  = %s\n", niihandler.installers)
        self.out("repo        = %s\n", niihandler.repo)
        self.out("ostype      = %s\n", niihandler.ostype)
        self.out("installtype = %s\n", niihandler.installtype)
        self.out("nodegrpid   = %s\n", niihandler.nodegrpid)

        if niihandler.nodegrpid == '1':
            self.err("ERROR:  This tool should not be run on the installer\n")
            sys.exit(1)

        self.ostype = string.split(niihandler.ostype, '-', 1)[0]
        niihandler.saveAppGlobalsEnv('/etc/profile.nii')
        self.out("Wrote:  /etc/profile.nii\n")
        niihandler.saveCFMSecret('/etc/cfm/.cfmsecret')
        self.out("Wrote:  /etc/cfm/.cfmsecret\n")
        ipmiPasswordFile = "%s/etc/.ipmi.passwd" % (os.environ.get('KUSU_ROOT', '/opt/kusu'))
        if not niihandler.saveIpmiPassword(ipmiPasswordFile):
            self.err("ERROR:  Failed to write the IPMI password file to %s.\n" % ipmiPasswordFile)
        else:
            self.out("Wrote:  %s\n" % ipmiPasswordFile)
        self.updateHostname(niihandler)
        self.delOldNics(niihandler)
        self.configNics(niihandler)


if __name__ == '__main__':
    # Check if root user
    if os.geteuid():
        print "ERROR:  Only root can run this tool"
        sys.exit(-1)

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '-v':
            print "Updatenic Version ${VERSION_STR}\n"
            sys.exit(0)
        elif args[i] == '-h':
            msg = ("updatenic [-h|-v]\n\n"
                   "The updatenic tool queries the installer for an updated profile.nii.\n"
                   "It also causes the network configuration on the node to be created\n"
                   "or updated, and the hostname to be updated.\n"
                   "This tool is typically invoked by a cfmclient plugin.\n"
                   "It should not be invoked on the installer.\n")
            print msg
            sys.exit(0)
        else:
            sys.stderr.write("ERROR:  Unknown argument\n")
            sys.exit(1)
        i += 1

    app = App()
    app.run()
