#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
# This testsuite exercises the NodeInstaller class. Requires ksvalidator from the pykickstart
# package for the full test run.
#

from kusu.nodeinstaller import NodeInstaller, KickstartFromNIIProfile, adaptNIIPartition, translatePartitionOptions
from cStringIO import StringIO
from nose import SkipTest
import subprocess
import tempfile
from path import path
import os
from kusu.partitiontool import DiskProfile

def checkToolExists(tool):
    """ Check if the current tool exists in the system path. """
    cmd = 'which %s > /dev/null 2>&1' % tool
    whichP = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
    whichP.communicate()
    
    if whichP.returncode == 0:
        return True
    else:
        return False

def ksvalidator(ksfile):
    """ Wrapper around pykickstart's ksvalidator """
    cmd = 'ksvalidator %s' % ksfile
    ksP = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
    out,err = ksP.communicate()
    
    print 'output: ', out
    print 'error: ', err

class TestNII:

    def setUp(self):
        
        self.tmpdir = path(tempfile.mkdtemp(dir='/tmp'))
        
        niidata = """\
<?xml version="1.0"?>
<nii>
<debug>
Dump NII: 1 
State:  
Dump CFM: 0 
Node: node0000 
</debug>
<nodeinfo name="node0000" installers="10.1.10.1" repo="/mirror/fc6/i386/os" ostype="fedora" installtype="package" nodegrpid="2" ngtype="installer" repoid="1000">
    <nicinfo device="eth0" ip="10.1.10.10" subnet="255.255.255.0" network="10.1.10.0" suffix="" gateway="10.1.10.1" dhcp="0" options="" boot="1"/>
    <partition device="1" mntpnt="/boot" fstype="ext3" size="100" options="" partition="1" preserve="0"/>
    <partition device="1" mntpnt="" fstype="linux-swap" size="1000" options="" partition="2" preserve="0"/>
    <partition device="1" mntpnt="/" fstype="ext3" size="6000" options="fill" partition="3" preserve="0"/>
    <component>component-base-node</component>
    <optpackage>vim-enhanced</optpackage>
    <appglobals name="ClusterName" value="BadBoy"/>
    <appglobals name="DNSZone" value="myzone.company.com"/>
    <appglobals name="DNSForwarders" value="172.16.1.5,172.16.1.8"/>
    <appglobals name="DNSSearch" value="myzone.company.com company.com corp.company.com"/>
    <appglobals name="NASServer" value="172.25.243.2"/>
    <appglobals name="Timezone_zone" value="Asia/Singapore"/>
    <appglobals name="Timezone_utc" value="1"/>
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
        
        # additional partitioning profiles from nii
        self.niipartition1 = {
                # /boot - 100M, ext3, disk 1 part 1
                0: {'preserve': u'0', 'fstype': u'ext3', 'device': u'1', 'mntpnt': u'/boot', 'options': u'', 'size': u'100', 'partition':'1'},
                # swap - 1000M, linux-swap, disk 1 part 2
                1: {'preserve': u'0', 'fstype': u'linux-swap', 'device': u'1', 'mntpnt': u'', 'options': u'', 'size': u'1000', 'partition':'2'},
                # / - 6000M(fill), ext3, disk 1 part 3
                2: {'preserve': u'0', 'fstype': u'ext3', 'device': u'1', 'mntpnt': u'/', 'options': u'fill', 'size': u'6000', 'partition':'3'}}

        self.niipartition2 = {
                # /boot - 100M, ext3, disk 1 part 1
                0: {'preserve': u'0', 'fstype': u'ext3', 'device': u'1', 'mntpnt': u'/boot', 'options': u'', 
                'size': u'100', 'partition':'1'},
                # swap - 1000M, linux-swap, disk 1 part 2
                1: {'preserve': u'0', 'fstype': u'linux-swap', 'device': u'1', 'mntpnt': u'', 'options': u'', 
                'size': u'1000','partition':'2'},
                # pv - 6000M(fill), vg=VolGroup00, disk 1 part 3
                2: {'preserve': u'0', 'fstype': u'physical volume', 'device': u'1', 'mntpnt': u'', 'options': u'fill;pv;vg=VolGroup00', 
                'size': u'6000', 'partition':'3'},
                # VolGroup00 - extent=32M
                3: {'preserve': u'0', 'fstype': u'', 'device': u'VolGroup00', 'mntpnt': u'', 'options': u'vg;extent=32M', 
                'size': u'0', 'partition':''},
                # ROOT lv - 2000M, ext3, vg=VolGroup00
                4: {'preserve': u'0', 'fstype': u'ext3', 'device': u'ROOT', 'mntpnt': u'/', 'options': u'lv;vg=VolGroup00', 
                'size': u'2000', 'partition':''},
                # DEPOT lv - 4000M(fill), ext3, vg=VolGroup00
                5: {'preserve': u'0', 'fstype': u'ext3', 'device': u'DEPOT', 'mntpnt': u'/depot', 'options': u'lv;vg=VolGroup00;fill', 
                'size': u'4000', 'partition':''},    
                }

        self.niipartition3 = {# /boot - 100M, ext3, disk 1 part 1
                              0: {'preserve': u'0', 'fstype': u'ext3', 'device': u'1',
                                  'mntpnt': u'/boot', 'options': u'', 'size': u'100', 'partition':'1'},
                              # swap - 1000M, linux-swap, disk 1 part 2
                              1: {'preserve': u'0', 'fstype': u'linux-swap', 'device': u'1',
                                  'mntpnt': u'', 'options': u'', 'size': u'1000', 'partition':'2'},
                              # pv - 2000M, vg=VolGroup00, disk 1 part 3
                              2: {'preserve': u'0', 'fstype': u'physical volume', 'device': u'1',
                                  'mntpnt': u'', 'options': u'pv;vg=VolGroup00', 'size': u'2000', 'partition':'3'},
                              # pv - 4000M(fill), vg=VolGroup01, multi-disk
                              3: {'preserve': u'0', 'fstype': u'physical volume', 'device': u'N',
                                  'mntpnt': u'', 'options': u'fill;pv;vg=VolGroup01', 'size': u'4000', 'partition':'N'},
                              # VolGroup00 - extent=32M
                              4: {'preserve': u'0', 'fstype': u'', 'device': u'VolGroup00',
                                  'mntpnt': u'', 'options': u'vg;extent=32M', 'size': u'', 'partition': u''},
                              # VolGroup01 - extent=32M
                              5: {'preserve': u'0', 'fstype': u'', 'device': u'VolGroup01',
                                  'mntpnt': u'', 'options': u'vg;extent=32M', 'size': u'', 'partition': u''},
                              # ROOT lv - 2000M, ext3, vg=VolGroup00
                              6: {'preserve': u'0', 'fstype': u'ext3', 'device': u'ROOT',
                                  'mntpnt': u'/', 'options': u'lv;vg=VolGroup00', 'size': u'2000', 'partition': u''},
                              # DEPOT lv - 4000M(fill), ext3, vg=VolGroup01
                              7: {'preserve': u'0', 'fstype': u'ext3', 'device': u'DEPOT',
                                  'mntpnt': u'/depot', 'options': u'lv;vg=VolGroup01;fill', 'size':u'4000', 'partition': u''}
                             }

        # additional partitioning schemas
        self.expectedSchema1 = {'disk_dict': {1: {'partition_dict': {1: {'fill': False,
                                                                         'fs': u'ext3',
                                                                         'mountpoint': u'/boot',
                                                                         'size_MB': 100},
                                                                     2: {'fill': False,
                                                                         'fs': u'linux-swap',
                                                                         'mountpoint': None,
                                                                         'size_MB': 1000},
                                                                     3: {'fill': True,
                                                                         'fs': u'ext3',
                                                                         'mountpoint': u'/',
                                                                         'size_MB': 6000}}}},
                                'vg_dict': {}}
                                
        self.expectedSchema2 = {'disk_dict': {1: {'partition_dict': {1: {'fill': False,
                                                                         'fs': u'ext3',
                                                                         'mountpoint': u'/boot',
                                                                         'size_MB': 100},
                                                                     2: {'fill': False,
                                                                         'fs': u'linux-swap',
                                                                         'mountpoint': None,
                                                                         'size_MB': 1000},
                                                                     3: {'fill': True,
                                                                         'fs': u'physical volume',
                                                                         'mountpoint': None,
                                                                         'size_MB': 6000}}}},
                                'vg_dict': {u'VolGroup00': {'extent_size': u'32M',
                                                            'lv_dict': {u'DEPOT': {'fill': True,
                                                                                   'fs': u'ext3',
                                                                                   'mountpoint': u'/depot',
                                                                                   'size_MB': 4000},
                                                                        u'ROOT': {'fill': False,
                                                                                  'fs': u'ext3',
                                                                                  'mountpoint': u'/',
                                                                                  'size_MB': 2000}},
                                                            'pv_list': [{'disk': 1, 'partition': 3}]}}}


        self.expectedSchema3 = {'disk_dict': {1:{'partition_dict': {}}}, 'vg_dict': {}}
        disk1part_dict = self.expectedSchema3['disk_dict'][1]['partition_dict']
        disk1part_dict[1] = {'fill': False,
                             'fs': u'ext3',
                             'mountpoint': u'/boot',
                             'size_MB': 100}

        disk1part_dict[2] = {'fill': False,
                             'fs': u'linux-swap',
                             'mountpoint': None,
                             'size_MB': 1000}

        disk1part_dict[3] = {'fill': False,
                             'fs': u'physical volume',
                             'mountpoint': None,
                             'size_MB': 2000}

        disk1part_dict[4] = {'fill': True,
                             'fs': u'physical volume',
                             'mountpoint': None,
                             'size_MB': 4000}

        self.expectedSchema3['vg_dict'][u'VolGroup00'] = {'extent_size': u'32M'}
        self.expectedSchema3['vg_dict'][u'VolGroup00']['pv_list'] = [{'disk': 1, 'partition': 3}]
        root_lv = {'fill': False, 'fs': u'ext3', 'mountpoint': u'/', 'size_MB': 2000}
        self.expectedSchema3['vg_dict'][u'VolGroup00']['lv_dict'] = {u'ROOT': root_lv}

        self.expectedSchema3['vg_dict'][u'VolGroup01'] = {'extent_size': u'32M'}
        self.expectedSchema3['vg_dict'][u'VolGroup01']['pv_list'] = [{'disk': 'N', 'partition': 'N'}]
        self.expectedSchema3['vg_dict'][u'VolGroup01']['pv_span'] = True
        depot_lv = {'fill': True, 'fs': u'ext3', 'mountpoint': u'/depot', 'size_MB': 4000}
        self.expectedSchema3['vg_dict'][u'VolGroup01']['lv_dict'] = {u'DEPOT': depot_lv}
       
        
    def tearDown(self):
        self.niisource = None
        if self.tmpdir.exists(): self.tmpdir.rmtree()

        
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
        # if not root, skip this test
        if os.getuid() <> 0:
            raise SkipTest
        # if pykickstart is not available, skip this test
        try:
            from pykickstart.data import KickstartData
            from pykickstart.parser import KickstartParser, KickstartHandlers, KickstartParseError, KickstartValueError, KickstartError
            import warnings
        except ImportError:
            raise SkipTest
        warnings.filterwarnings('error')
        ksfile = self.tmpdir / 'ks.cfg'
        ni = NodeInstaller(self.niisource)
        ni.setup(ksfile)
        ksdata = KickstartData()
        kshandlers = KickstartHandlers(ksdata)
        ksparser = KickstartParser(ksdata, kshandlers)
        try:
            ksparser.readKickstart(ksfile)
            assert True
        except (KickstartParseError, KickstartValueError, KickstartError):
            assert False
        except DeprecationWarning:
            assert False

        
    def testTranslatePartitionOptions(self):
        """ Test to validate translatePartitionOptions. """
        
        options0 = ''
        options1 = 'fill;label=My Volume'
        options2 = 'fill'
        options3 = 'vg;extent=32M'
        options4 = 'pv;vg=VolGroup00'
        options5 = 'lv;vg=VolGroup00'
        
        # blank options
        assert translatePartitionOptions(options0,'fill')[0] is False
        
        # check for preserve option
#        assert translatePartitionOptions(options0,'preserve')[0] is False
#        assert translatePartitionOptions(options1,'preserve')[0] is True        
        
        # check for fill is true
        assert translatePartitionOptions(options1,'fill')[0] is True
        assert translatePartitionOptions(options2,'fill')[0] is True
        
        # check for label
        assert translatePartitionOptions(options1,'label')[0] is True
        assert translatePartitionOptions(options1,'label')[1] == 'My Volume'
        assert translatePartitionOptions(options2,'label')[0] is False
        
        # check for vg
        assert translatePartitionOptions(options3,'extent')[0] is True
        assert translatePartitionOptions(options3,'extent')[1] == '32M'        
        assert translatePartitionOptions(options1,'extent')[0] is False
        
        # check for pv
        assert translatePartitionOptions(options4,'pv')[0] is True
        assert translatePartitionOptions(options4,'pv')[1] == 'VolGroup00'
        assert translatePartitionOptions(options1,'pv')[0] is False
        
        # check for lv
        assert translatePartitionOptions(options5,'lv')[0] is True
        assert translatePartitionOptions(options5,'lv')[1] == 'VolGroup00'
        assert translatePartitionOptions(options1,'lv')[0] is False      
        
    
    def testKickstartFromNIIProfile(self):
        """ Test to validate ksprofile.  
        """
        
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
        assert ksprofile.networkprofile['fqhn'] == 'node0000.myzone.company.com'
        assert ksprofile.networkprofile['interfaces']['eth0']['ip_address'] == '10.1.10.10'            
        assert ksprofile.networkprofile['interfaces']['eth0']['netmask'] == '255.255.255.0'                
        assert ksprofile.networkprofile['interfaces']['eth0']['active_on_boot'] == True
        
        # validate package profile
        ksprofile.prepareKickstartPackageProfile(ni)
        packages = ['component-base-node','vim-enhanced']
        for p in packages:
            assert p in ksprofile.packageprofile

        
        # validate disk schema
        dp = DiskProfile(fresh=True)
        #adaptedSchema = adaptNIIPartition(ni.partitions, dp)
        #schema = {'disk_dict': {1: {'partition_dict': {1: {'fill': False,
        #                                          'fs': u'ext3',
        #                                          'mountpoint': u'/boot',
        #                                          'size_MB': 100},
        #                                      2: {'fill': False,
        #                                          'fs': u'linux-swap',
        #                                          'mountpoint': None,
        #                                          'size_MB': 1000},
        #                                      3: {'fill': True,
        #                                          'fs': u'ext3',
        #                                          'mountpoint': u'/',
        #                                          'size_MB': 6000}}}},
        #                        'vg_dict': {}}
        #assert schema['disk_dict'] == adaptedSchema['disk_dict']
        #assert schema['vg_dict'] == adaptedSchema['vg_dict']

        # check a couple of other schemas
        #adaptedSchema = adaptNIIPartition(self.niipartition1, dp)
        #assert self.expectedSchema1['disk_dict'] == adaptedSchema['disk_dict']
        #assert self.expectedSchema1['vg_dict'] == adaptedSchema['vg_dict']

        #adaptedSchema = adaptNIIPartition(self.niipartition2, dp)
        #assert self.expectedSchema2['disk_dict'] == adaptedSchema['disk_dict']
        #assert self.expectedSchema2['vg_dict'] == adaptedSchema['vg_dict']
 
        #adaptedSchema = adaptNIIPartition(self.niipartition3, dp)
        #assert self.expectedSchema3['disk_dict'] == adaptedSchema['disk_dict']
        #assert self.expectedSchema3['vg_dict'] == adaptedSchema['vg_dict']
