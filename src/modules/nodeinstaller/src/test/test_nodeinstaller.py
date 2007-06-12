#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
# This testsuite exercises the NodeInstaller class. Requires ksvalidator from the pykickstart
# package for the full test run.
#

from kusu.nodeinstaller import NodeInstaller, KickstartFromNIIProfile
from cStringIO import StringIO
from nose import SkipTest
import subprocess

def checkToolExists(tool):
    " Check if the current tool exists in the system path. "
    cmd = 'which %s > /dev/null 2>&1' % tool
    whichP = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
    whichP.communicate()
    
    if whichP.returncode == 0:
        return True
    else:
        return False

class TestNII:

    def setUp(self):
        niidata = """\
<?xml version="1.0"?>
<nii>
<debug>
Dump NII: 1 
State:  
Dump CFM: 0 
Node: node0000 
</debug>
<nodeinfo name="node0000" installers="10.1.10.1" repo="/mirror/fc6/i386/os" ostype="fedora" installtype="package" nodegrpid="2">
    <nicinfo device="eth0" ip="10.1.10.10" subnet="255.255.255.0" network="10.1.10.0" suffix="" gateway="10.1.10.1" dhcp="0" options=""/>
    <partition device="1" mntpnt="/boot" fstype="ext3" size="100" options="" preserve="0"/>
    <partition device="2" mntpnt="None" fstype="linux-swap" size="1000" options="None" preserve="0"/>
    <partition device="3" mntpnt="/" fstype="ext3" size="6000" options="fill" preserve="0"/>
    <component>component-base-node</component>
    <appglobals name="ClusterName" value="BadBoy"/>
    <appglobals name="DNSZone" value="myzone.company.com"/>
    <appglobals name="DNSForwarders" value="172.16.1.5,172.16.1.8"/>
    <appglobals name="DNSSearch" value="myzone.company.com company.com corp.company.com"/>
    <appglobals name="NASServer" value="172.25.243.2"/>
    <appglobals name="TimeZone" value="Asia/Singapore"/>
    <appglobals name="NISDomain" value="engineering"/>
    <appglobals name="NISServers" value="172.25.243.4,172.25.243.14"/>
    <appglobals name="CFMSecret" value="GF5SEVTHJ589TNT45NTEYST78GYBG5GVYGT84NTV578TEB46"/>
    <appglobals name="InstallerServeDNS" value="True"/>
    <appglobals name="InstallerServeNIS" value="True"/>
    <appglobals name="InstallerServeNFS" value="True"/>
    <appglobals name="InstallerServeNTP" value="True"/>
    <appglobals name="PrimaryInstaller" value="installer0"/>
    <appglobals name="DHCPLeaseTime" value="2400"/>
    <appglobals name="InstallerServeSMTP" value="False"/>
    <appglobals name="Language" value="en_US.UTF-8"/>
    <appglobals name="Keyboard" value="us"/>        
    <appglobals name="RootPassword" value="badrootpassword"/>    
    <appglobals name="SMTPServer" value="mailserver.myzone.company.com"/>
    <appglobals name="CFMBaseDir" value="/opt/kusu/cfm"/>
</nodeinfo>
</nii>
        """
        
        # make niisource more file-like
        self.niisource = StringIO(niidata)
        
        invalidniidata = """\
        <nii>
        <noodleinfo>
        evil nii data
        </noodleinfo>
        </nii>
        """
        
        self.invalidnii = StringIO(invalidniidata)
        
        
    def tearDown(self):
        self.niisource = None

        
    def testValidateNII(self):
        """ Test to parse a valid and correct NII """

        ni = NodeInstaller(self.niisource)
        ni.parseNII()
        assert ni.nics['eth0']['device'] == 'eth0'
        
    def testValidateInvalidNII(self):
        """ Test to parse invalid NII """

        ni = NodeInstaller(self.invalidnii)
        ni.parseNII()
        assert ni.name == ''
        
    def testValidateEmptyNII(self):
        """ Test to parse empty NII """

        ni = NodeInstaller()
        ni.parseNII()
        assert ni.name == ''
        
    def testValidateKSFile(self):
        """ Test to validate generated kickstart file. """
           
        # if the ksvalidator tool is not available, skip this test
        if not checkToolExists('ksvalidator'):
            raise SkipTest
            
        assert True
        
    
    def testKickstartFromNIIProfile(self):
        """ Test to validate ksprofile. """
        
        ni = NodeInstaller(self.niisource)
        ni.parseNII()
        ksprofile = KickstartFromNIIProfile()

        # validate site-specific profile
        ksprofile.prepareKickstartSiteProfile(ni)
        assert ksprofile.tz == 'Asia/Singapore'
        assert ksprofile.lang == 'en_US.UTF-8'
        assert ksprofile.keyboard == 'us'
        assert ksprofile.installsrc == 'http://10.1.10.1/mirror/fc6/i386/os'
        
        # validate network profile
        ksprofile.prepareKickstartNetworkProfile(ni)
        assert ksprofile.networkprofile['interfaces']['eth0']['configure'] == True
        assert ksprofile.networkprofile['interfaces']['eth0']['use_dhcp'] == False
        assert ksprofile.networkprofile['interfaces']['eth0']['hostname'] == 'node0000'
        assert ksprofile.networkprofile['interfaces']['eth0']['ip_address'] == '10.1.10.10'            
        assert ksprofile.networkprofile['interfaces']['eth0']['netmask'] == '255.255.255.0'                
        assert ksprofile.networkprofile['interfaces']['eth0']['active_on_boot'] == True
        
        # validate disk schema
        #ksprofile.prepareKickstartDiskProfile(ni)
        #assert True



    
