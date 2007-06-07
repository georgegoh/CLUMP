#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from kusu.nodeinstaller import NodeInstaller

class TestNII:

    def setUp(self):
        self.niisource = """\
<?xml version="1.0"?>
<nii>
<debug>
Dump NII: 1 
State:  
Dump CFM: 0 
Node: node0000 
</debug>
<nodeinfo name="node0000" installers="installer0" repo="/mirror/fc6/i386/os" ostype="fedora" installtype="package" nodegrpid="2">
    <nicinfo device="eth0" ip="10.1.10.10" subnet="255.255.255.0" network="10.1.10.0" suffix="" gateway="10.1.10.1" dhcp="0" options=""/>
    <partition device="1" mntpnt="/boot" fstype="ext3" size="100" options="" preserve="0"/>
    <partition device="2" mntpnt="None" fstype="linux-swap" size="1000" options="None" preserve="0"/>
    <partition device="3" mntpnt="/" fstype="ext3" size="6000" options="fillAvailableSpace" preserve="0"/>
    <component>component-base-node</component>
    <appglobals name="ClusterName" value="BadBoy"/>
    <appglobals name="DNSZone" value="myzone.company.com"/>
    <appglobals name="DNSForwarders" value="172.16.1.5,172.16.1.8"/>
    <appglobals name="DNSSearch" value="myzone.company.com company.com corp.company.com"/>
    <appglobals name="NASServer" value="172.25.243.2"/>
    <appglobals name="TimeZone" value="EST/EDT"/>
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
    <appglobals name="SMTPServer" value="mailserver.myzone.company.com"/>
    <appglobals name="CFMBaseDir" value="/opt/kusu/cfm"/>
</nodeinfo>
</nii>
        """
        
    def tearDown(self):
        pass
        
    def testNIIStructure(self):
        assert True
        
    def testGetNII(self):
        assert True
        
    def testFailGetNII(self):
        assert True
        
    def testGetNodeInfoLine(self):
        
        # parse NII
        # get nodeinfo
        # validate nodeinfo
        
        assert True
        
    def testGetNodeInfoLine(self):
        
        # parse NII
        # get nodeinfo
        # validate nodeinfo
        
        assert True

    def testGetNicInfoLine(self):
        
        # parse NII
        # get nicinfo
        # validate nicinfo
        
        assert True

    def testGetPartitionInfoLine(self):
        
        # parse NII
        # get partitioninfo
        # validate partitioninfo
        
        assert True

    def testGetComponentLine(self):
        
        # parse NII
        # get component
        # validate component
        
        assert True

    def testGetPackageLine(self):
        
        # parse NII
        # get package
        # validate package
        
        assert True

    def testGetScriptLine(self):
        
        # parse NII
        # get script
        # validate script
        
        assert True
        
    def testGetAppGlobalsLine(self):

        # parse NII
        # get appglobals
        # validate appglobals
        
        assert True
        
    
        



    