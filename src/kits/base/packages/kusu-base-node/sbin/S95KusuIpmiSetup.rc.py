#!/usr/bin/env python
#
# $Id: S95KusuIpmiSetup.rc.py 3513 2010-02-12 08:24:35Z ggoh $
#
# Copyright (C) 2010 Platform Computing Inc.

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

import re
import os
import pwd
import subprocess
import time
from path import path
from kusu.core import rcplugin
import kusu.util.log as kusulog
from primitive.support.util import runCommand, pollCommand
from primitive.system.software.dispatcher import Dispatcher


logger = kusulog.getKusuLog()

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'ipmiSetup'
        self.desc = 'Setting up IPMI network interface'
        self.ngtypes = ['installer', 'compute', 'compute-imaged', 'compute-diskless']
        self.delete = True
        self.ipmiUserName = 'kusu-ipmi'
        self.ipmiPasswordFile = ''
        self.ipAddress = ''
        self.netmask = ''
        self.gatewayIpAddress = ''
        self.ipmiPassword = ''
        self.ipmiPasswordFile = path(os.environ.get('KUSU_ROOT', '/opt/kusu')) / "etc" / ".ipmi.passwd"
        # Disable this plugin if there is no configuration for BMC.
        self.isMaster = self.dbs is not None
        self.determineConfiguration()
        if not self.ipAddress:
            if self.isMaster: self.establishIpmiPassword()
            self.disable = True

    def run(self):
        """
        Setting up IPMI network interface
        
        This either uses the values found in profile.nii or,
        if the file isn't present, queries the database for
        the necessary information.
        """
        print

        if not self.establishIpmiPassword():
            return False

        if self.determineConfiguration():
            (ipmiServiceStarted, ipmiWasRunning) = self.startIpmiService()        

            if not ipmiServiceStarted:
                print "Failed to start IPMI service."
                logger.error("%s: Failed to start IPMI service." % self.name)
                return False

            if not self.setupIpmi():
                self.service(Dispatcher.get('ipmi_service'), 'stop')
                return False
            logger.info("%s: Found configuration:" % self.name)
            logger.info("   IP Address: %s" % self.ipAddress)
            logger.info("   Subnet Mask: %s" % self.netmask)
            logger.info("   Default Gateway: %s" % self.gatewayIpAddress)
            logger.info("   IPMI password file: %s" % self.ipmiPasswordFile)
            if self.isMaster: # add the IPMI daemon to the default runlevel on the master node
                success, (stdOut,returnCode,stdErr) = self.service(Dispatcher.get('ipmi_service'), 'enable')
                ipmiWasRunning = True
                if not success:
                    print "Failed to add the IPMI daemon to the default runlevel."
                    logger.error("%s: Failed to add the IPMI daemon to the default runlevel." % self.name)
                    return False
        else:
            print "Failed to determine configuration values."
            logger.error("%s: Failed to determine configuration values." % self.name)
            return False

        if not ipmiWasRunning:
            self.service(Dispatcher.get('ipmi_service'), 'stop')

        return True


    def establishIpmiPassword(self):
        """ Reads or creates the password for IPMI """
        if not self.ipmiPasswordFile.exists() and self.isMaster:
            if not self.generatePasswordFile():
                print "Failed to create password file at %s." % self.ipmiPasswordFile
                logger.error("%s: Failed to create password file at %s." % (self.name, self.ipmiPasswordFile))
                return False
        else:
            if not self.readIpmiPasswordFile():
                print "Failed to read password file at %s." % self.ipmiPasswordFile
                logger.error("%s: Failed to read password file at %s." % (self.name, self.ipmiPasswordFile))
                return False
        return True


    def generatePasswordFile(self):
        """ Generates a password and writes it to a file """
        try:
            f = open(self.ipmiPasswordFile, 'w')
            self.ipmiPassword = self.generatePassword()
            f.write(self.ipmiPassword)
            f.close()
            wwwUser = Dispatcher.get('webserver_usergroup')[0]
            userinfo = pwd.getpwnam(wwwUser)
            if not userinfo:
                return False
            userId = userinfo[2]
            groupId = userinfo[3]
            os.chmod(self.ipmiPasswordFile, 0400)
            os.chown(self.ipmiPasswordFile, userId, groupId)
        except:
            return False
        return True


    def generatePassword(self):
        """ Generate a password """
        import random
        r = random.Random(time.time())
        chars = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        password = ''.join([r.choice(chars) for i in xrange(8)])
        return password

    
    def readIpmiPasswordFile(self):
        """ Reads the IPMI password file """
        try:
            f = open(self.ipmiPasswordFile, 'r')
            self.ipmiPassword = f.read().strip()
            f.close()
        except:
            return False
        return True


    def startIpmiService(self):
        """ Starts the IPMI service and checks whether it successfully started or was already running """
        ipmiWasRunning = False
        ipmiService = Dispatcher.get('ipmi_service')
        success, (stdOut,returnCode,stdErr) = self.service(ipmiService, 'status')

        if not success:
            return (False, ipmiWasRunning)
        elif returnCode != 0:
            success, (stdOut,returnCode,stdErr) = self.service(ipmiService, 'start')
            if not success or returnCode != 0:
                return (False, ipmiWasRunning)
        else:
            ipmiWasRunning = True

        return (True, ipmiWasRunning)


    def determineConfiguration(self):
        """ Attempts to determine the IPMI configuration values
            by either parsing profile.nii or checking the database. """

        if self.isMaster:
            self.getValuesFromDatabase()
        else:
            self.getValuesFromNiiFile(path('/etc/profile.nii'))

        return self.ipAddress and self.gatewayIpAddress and self.netmask


    def getValuesFromNiiFile(self, profileFile):
        """ Attempts to determine the IPMI configuration values by parsing profile.nii """
        nicDefinitionCount = 0
        while True:
            nicDefinition = self.parseNii(profileFile, 'NII_NICDEF%s' % nicDefinitionCount)
            nicDefinitionCount += 1
            if not nicDefinition or nicDefinition.startswith('bmc'):
                break

        if nicDefinition:
            bmcConfiguration = nicDefinition.split('|')
            self.ipAddress = bmcConfiguration[1]
            self.netmask = bmcConfiguration[2]
            self.gatewayIpAddress = bmcConfiguration[5]
        
        return self.ipAddress and self.gatewayIpAddress and self.netmask


    def getValuesFromDatabase(self):
        """ Attempts to determine the IPMI configuration values by checking the database """
        installerName = self.dbs.AppGlobals.selectfirst_by(kname='PrimaryInstaller').kvalue
        nodeId = self.dbs.Nodes.selectfirst_by(name=installerName).nid
        bmcNetwork = self.dbs.Networks.selectfirst_by(device='bmc')
        
        if not bmcNetwork:
            return False
        
        nics = self.dbs.Nics.selectfirst_by(nid=nodeId, netid=bmcNetwork.netid)
        if not nics:
            return False
        
        self.ipAddress = nics.ip
        self.gatewayIpAddress = bmcNetwork.gateway
        self.netmask = bmcNetwork.subnet


    def setupIpmi(self):
        """ Configures IPMI using either vendor scripts,
            should any be provided, or a default method. """
        ipmiVendorPath = path('/opt/kusu/etc/ipmi-vendor')
        if ipmiVendorPath.exists() and ipmiVendorPath.files():
            return self.setupIpmiVendor(ipmiVendorPath)
        else:
            return self.setupIpmiDefault()


    def setupIpmiVendor(self, ipmiVendorPath):
        """ Configures IPMI using vendor scripts, if found to be available """
        vendorScripts = False
        for script in ipmiVendorPath.files():
            ipmiParameters = os.environ.copy()
            try:
                ipmiParameters['BMC_IPADDR'] = self.ipAddress
                ipmiParameters['BMC_NETMASK'] = self.netmask
                ipmiParameters['BMC_GATEWAY_IPADDR'] = self.gatewayIpAddress
                ipmiParameters['BMC_USER_NAME'] = self.ipmiUserName
                ipmiParameters['BMC_PASSWORD_FILE'] = self.ipmiPasswordFile
                scriptExecution = subprocess.Popen('%s %s %s %s %s %s' % (script,
                                                                    self.ipAddress,
                                                                    self.netmask,
                                                                    self.gatewayIpAddress,
                                                                    self.ipmiUserName,
                                                                    self.ipmiPasswordFile),
                                                    shell=True,
                                                    env=ipmiParameters,
                                                    stdout=subprocess.PIPE,
                                                    stderr=subprocess.PIPE)
                scriptExecution.wait()
                if scriptExecution.returncode:
                    stdError = scriptExecution.stderr.read()
                    print "Script '%s' failed: %s" % (script, stdError)
                    logger.error("%s: Script %s failed: %s" % (self.name, script, stdError))
                    return False
            except OSError, osException:
                print "Script '%s' failed: %s" % (script, osException)
                logger.error("%s: Script %s failed: %s" % (self.name, script, osException))
                return False
        return True


    def setupIpmiDefault(self):
        """ Configures IPMI using the default method """
        (userExists, emtpyId) = self.checkIpmiUsers()
        if not emtpyId:
            print "Unable to find a valid ID for a new IPMI user."
            logger.error("%s: Unable to find a valid ID for a new IPMI user." % self.name)
            return False
        try:
            pollCommand('/usr/bin/ipmitool -I open lan set 1 ipaddr %s' % self.ipAddress)
            pollCommand('/usr/bin/ipmitool -I open lan set 1 defgw ipaddr %s' % self.gatewayIpAddress)
            pollCommand('/usr/bin/ipmitool -I open lan set 1 netmask %s' % self.netmask)
            pollCommand('/usr/bin/ipmitool -I open lan set 1 access on')
            if not userExists and emtpyId:
                pollCommand('/usr/bin/ipmitool -I open user set name %s %s' % (emtpyId, self.ipmiUserName))
                pollCommand('/usr/bin/ipmitool -I open user enable %s' % emtpyId)
                pollCommand('/usr/bin/ipmitool -I open user priv %s 4 1' % emtpyId) # set the privilege level of the user to "Administrator"
            pollCommand('/usr/bin/ipmitool -I open user set password %s %s' % (emtpyId, self.ipmiPassword))
        except OSError, osException:
            print "ipmitool failed: %s" % osException
            logger.error("%s: ipmitool failed: %s" % (self.name, osException))
            return False
        return True


    def checkIpmiUsers(self):
        (data, error) = runCommand('/usr/bin/ipmitool -I open user list 1')
        rows = data.split("\n")

        # remove the first element from the list
        rows.reverse()
        rows.pop()
        
        userDict = {}
        userIDList = []
        
        for row in rows:
            elements = row.split()
            if not elements:
                continue
            
            # name:id 
            userDict[elements[1]] = elements[0]
            userIDList.append(int(elements[0]))    
        
        # look up user ID if the "kusu-ipmi" user was found    
        if self.ipmiUserName in userDict.keys():
            return (True, userDict[self.ipmiUserName])
    
        # IPMI user list has a possible max of 10 user ids, starting from 2
        for emptyId in range(2,11):
            if emptyId not in userIDList:
                return (False, emptyId)
        
        return (False, 0)
        

    def parseNii(self, nii, key):
        """ Parses the given NII file returning the value for the key provided """
        # This function was first defined as PluginRunner.parseNII() within rcplugin.py.
        # A method should be determined to merge both functions together again.
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
