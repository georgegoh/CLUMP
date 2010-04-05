#!/usr/bin/env python
# $Id: test_datamodel.py 476 2008-01-25 12:36:55Z hirwan $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

from kusu.util import tools
from kusu.core import database as db
from kusu.driverpatch.control import DataModel
from path import path



class TestDataModel(object):
    """ Test for driverpatch datamodel class. 
    """
    
    def setUp(self):

        self.scratchdir = path(tools.mkdtemp(prefix='driverpatch-datamodel-'))
        self.kusudb = self.scratchdir / 'kusu.db'
        self.dbinst = db.DB('sqlite', self.kusudb)

        self.dbinst.createTables()

        # Network
        network1 = self.dbinst.Networks()
        network1.network = '10.0.0.0'
        network1.subnet = '255.0.0.0'
        network1.device = 'eth0'
        network1.type = 'public'
        network1.save()
        network1.flush()

        network2 = self.dbinst.Networks()
        network2.network = '192.168.1.0'
        network2.subnet = '255.255.255.0'
        network2.device = 'eth1'
        network2.type = 'provision'
        network2.save()
        network2.flush()

        # nodegroup
        node = self.dbinst.Nodes(name='master-0')
        masterIP1 = '10.1.1.1'
        masterIP2 = '192.168.1.1'
        node.nics.append(self.dbinst.Nics(ip=masterIP1, netid=network1.netid))
        node.nics.append(self.dbinst.Nics(ip=masterIP2, netid=network2.netid))

        # installer nodegroup
        installer = self.dbinst.NodeGroups(ngname='installer nodegroup',
                                  type='installer',installtype='package') 
        installer.nodes.append(node)
        installer.save()
        installer.flush()
        
        # compute nodegroup
        compute = self.dbinst.NodeGroups(ngname='compute nodegroup',type='compute',installtype='package')
        compute.save()
        compute.flush()
        
        # compute-imaged nodegroup
        computeimg = self.dbinst.NodeGroups(ngname='compute-imaged nodegroup',
            type='compute',installtype='disked')
            
        # compute-diskless nodegroup
        computediskless = self.dbinst.NodeGroups(ngname='compute-diskless nodegroup',
            type='compute',installtype='diskless')
        computediskless.save()
        computediskless.flush()

        # Kits + components
        osKit = self.dbinst.Kits()
        osKit.rname = 'fedora'
        osKit.version = '6'
        osKit.arch = 'i386'
        osKit.isOS = True
        osComp = self.dbinst.Components(cname='fedora-6-i386')
        dpack = self.dbinst.DriverPacks()
        dpack.dpname = 'kernel-2.6.18-1.2798.fc6.i686.rpm'
        dpack.dpdesc = 'Fedora Core 6 Kernel Package (i686)'
        osComp.driverpacks.append(dpack)
        dpack = self.dbinst.DriverPacks()
        dpack.dpname = 'kernel-2.6.18-1.2798.fc6.i586.rpm'
        dpack.dpdesc = 'Fedora Core 6 Kernel Package (i586)'
        osComp.driverpacks.append(dpack)        
        osKit.components.append(osComp)
        osKit.save()
        osKit.flush()

        baseKit = self.dbinst.Kits()
        baseKit.rname = 'base'
        baseKit.version = '0.1'
        baseKit.arch = 'noarch'
        baseKit.isOS = False
        baseComp = self.dbinst.Components(cname='base-installer')
        baseNodeComp = self.dbinst.Components(cname='base-node')
        baseKit.components.append(baseComp)
        baseKit.components.append(baseNodeComp)
        baseKit.save()
        baseKit.flush()
        
        driverKit = self.dbinst.Kits()
        driverKit.rname = 'dvendor'
        driverKit.version = '0.1'
        driverKit.arch = 'noarch'
        driverKit.isOS = False
        driverComp = self.dbinst.Components(cname='dvendor')
        dpack = self.dbinst.DriverPacks()
        dpack.dpname = 'e1000-7.3.15.3-sv_dkms.noarch.rpm'
        dpack.dpdesc = 'D Vendor e1000 Driver update'
        driverComp.driverpacks.append(dpack)
        driverKit.components.append(driverComp)
        driverKit.save()
        driverKit.flush()

        installer.components.append(osComp)
        installer.components.append(baseComp)
        installer.components.append(baseNodeComp)
        installer.components.append(driverComp)
        installer.save() 
        installer.flush()

        compute.components.append(osComp)
        compute.components.append(baseNodeComp)
        compute.components.append(driverComp)
        compute.save()
        compute.flush()
        
        computeimg.components.append(osComp)
        computeimg.components.append(baseNodeComp)
        computeimg.components.append(driverComp)
        computeimg.save()
        computeimg.flush()
        
        computediskless.components.append(osComp)
        computediskless.components.append(baseNodeComp)
        computediskless.components.append(driverComp)
        computediskless.save()
        computediskless.flush()

        appglobals = self.dbinst.AppGlobals(kname='PrimaryInstaller', kvalue='master-0')
        appglobals.save()
        appglobals.flush()
        
    def tearDown(self):
        if self.scratchdir.exists(): self.scratchdir.rmtree()
        
    def testGetDriverPacksEntries(self):

        names = ['kernel-2.6.18-1.2798.fc6.i686.rpm',
            'kernel-2.6.18-1.2798.fc6.i586.rpm',
            'e1000-7.3.15.3-sv_dkms.noarch.rpm']
        names.sort()

        dm = DataModel(self.dbinst)
        dpacks = dm.getDriverPacks(id='2')
        # get the list of names
        li = [dpack.dpname for dpack in dpacks]
        li.sort()
        
        assert li == names

        # nothing should be returned since the installtype is diskless
        dpacks = dm.getDriverPacks(name='compute-diskless')
        assert not dpacks

        dpacks = dm.getDriverPacks(id='1')
        li = [dpack.dpname for dpack in dpacks]
        li.sort()
        assert li == names


        

