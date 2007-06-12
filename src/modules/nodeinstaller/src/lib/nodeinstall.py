#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE for details.

from kusu.autoinstall.scriptfactory import KickstartFactory
from kusu.autoinstall.autoinstall import Script
from kusu.partitiontool.partitiontool import DiskProfile
from kusu.installer.defaults import setupDiskProfile
from kusu.nodeinstaller import NodeInstInfoHandler
from kusu.util.errors import EmptyNIISource, NotPriviledgedUser
import urllib2
import kusu.util.log as kusulog
from xml.sax import make_parser, SAXParseException

logger = kusulog.getKusuLog('nodeinstaller.NodeInstaller')
logger.addFileHandler()

def translateBoolean(value):
    """ Tries to translate value into boolean"""
    if value.lower() == 'true':
        return True
    elif value.lower() == 'false':
        return False
    try:
        if int(value) > 0:
            return True
        else:
            return False
    except ValueError:
        return False
        

def translateFSTypes(fstype):
    """ Translates fstype to something partitiontool can understand. Right now
        only swap fstypes needs to be translated, the rest can be passed through.
    """

    if fstype == 'swap':
        return 'linux-swap'
    else:
        return fstype

def translatePartitionOptions(niipartition, opt=None):
    """ Translate niipartition to something that the 
        partitiontool's schema expects.

        PARTITION_OPTIONS = [ 'fill', 'pv', 'vg', 'lv', 'label', 
                            'preserve', 'extent']

        An example partitionopts line looks like the following:
            fill;label='My Volume';preserve

        An example partitionopts line for a LVM Volume Group can be defined
        as follows, note that the name of the Volume Group should be defined
        in the device column in the partitions table:
            vg;example=32M

        An example partitionopts for a LVM Logical Volume can be defined 
        as follows, it needs to belong to a Volume Group, note that the name 
        of the Volume Group will be matched against the device name of an 
        existing Volume Group definition:
            lv;vg=VolGroup00

        An example partitionopts for a LVM Physical Volume can be defined 
        as follows, note that the name  of the Volume Group will be matched 
        against the device name of an existing Volume Group definition:
            pv;vg=VolGroup00


    """
    PARTITION_OPTIONS = [ 'fill', 'pv', 'vg', 'lv', 'label', 
                        'preserve', 'extent']

    logger.debug('Translating niipartition: %r' % niipartition)
    if opt: logger.debug('Looking for %r' % opt)

    partnum = niipartition.keys()[0]
    device = niipartition[partnum]['device']
    # is this a disk number?
    try:
        disknum = int(device)
    except ValueError:
        disknum = None
    mountpoint = niipartition[partnum]['mntpnt']

    # set up the disk_dict if this has a disknum if no opt is provided
    if not opt and disknum:
        d = {'size_MB' : niipartition[partnum]['size'],
            'fs' : translateFSTypes(niipartition[partnum]['fstype']),
            'mountpoint' : niipartition[partnum]['mntpnt'],
            'fill' : translatePartitionOptions(niipartition,'fill') or False}
        return {disknum:{partnum:d}}        


    # convert niipartition options into a dict
    logger.debug('Converting niipartition options into dict')
    options = niipartition[partnum]['options']
    if options:
        li = niipartition[partnum]['options'].split(';')
        logger.debug('niipartition options list : %r' % li)
        opts_dict = {}
        for l in li:
            if l == 'None': continue
            logger.debug('Converting option : %r' % l)
            if len(l.split('=')) > 1:
                opts_dict[l] = l.split('=')[:-1]
            else:
                opts_dict[l] = {}
        logger.debug('opts_dict : %r' % opts_dict)

    # Volume Group definition
    if opt == 'vg':
        vg = {}
        vg[device]['extent_size'] = translatePartitionOptions(niipartition,'extent')
        vg[device]['pv_dict'] = translatePartitionOptions(niipartition,'pv')
        vg[device]['lv_dict'] = translatePartitionOptions(niipartition,'lv')
        return {device:vg}

    if opt == 'pv':
        try:
            # a device can be a disk number
            devname = int(device)
        except ValueError:
            # or a pvname/vgname
            devname = device
        return {'disk':devname,'partition':partnum}

    if opt == 'lv':
        d = {'size_MB' : niipartition[partnum]['size'],
            'fs' : translateFSTypes(niipartition[partnum]['fstype']),
            'mountpoint' : niipartition[partnum]['mntpnt'],
            'fill' : translatePartitionOptions(niipartition,'fill') or False}
        if d['mountpoint'] == '/':
            return {'ROOT':d}
        else:
            lvroot = d['mountpoint'][1:].upper()
            return {lvroot:d}

    # fill
    if opt == 'fill':
        return True
    else:
        return False

    # preserve
    if opt == 'preserve':
        return True

    # label
    if opt == 'label':
        return opts_dict[opt]

    # extent
    if opt == 'extent':
        return opts_dict[opt]




def retrieveNII(niihost, node):
    """ Downloads the NII from the niihost.
        FIXME: currently a hardcoded url!!
    """
    url = 'http://%s/mirror/fc6/i386/os/nii.xml' % niihost
    try:
        logger.debug('Fetching %s' % url)
        f = urllib2.urlopen(url)
        logger.debug('urlopen returned object: %r' % f)
        data = f.read()
        logger.debug('urlopen data: %s' % data)
        return data
    except urllib2.HTTPError, e:
        logger.debug(str(e))
        return None

class KickstartFromNIIProfile(object):
    """ NII-specific profile class for generating Kickstart objects. """

    getattr_dict = { 'diskprofile' : None,
                     'networkprofile' : None,
                     'packageprofile' : [],
                     'rootpw': None,
                     'tz': None,
                     'installsrc': None,
                     'lang': None,
                     'keyboard' : None}
    
    
    def __init__(self):
        """ ni is an instance of the NodeInstaller class. """
        super(KickstartFromNIIProfile, self).__init__()
                      
        self.packageprofile.append('@Base')
        
    def prepareKickstartSiteProfile(self,ni):
        """ Reads in the NII instance and fills up the site-specific
            profile.
        """
        self.rootpw = ni.appglobal['RootPassword']
        self.tz = ni.appglobal['TimeZone']
        self.lang = ni.appglobal['Language']
        self.keyboard = ni.appglobal['Keyboard']
        self.installsrc = 'http://' + ni.installers + ni.repo

    def prepareKickstartNetworkProfile(self,ni):
        """ Reads in the NII instance and fills up the networkprofile. """
        
        # network profile dict
        logger.debug('Preparing network profile')
        nw = {}
        nw['interfaces'] = {}
        for nic in ni.nics:
            logger.debug('ni.nics info for device: %s' % nic)
            logger.debug('ni.hostname: %s' % ni.name)         
            logger.debug('ni.nics[%s]["suffix"]: %s' % (nic,ni.nics[nic]['suffix']))               
            logger.debug('ni.nics[%s]["dhcp"]: %s' % (nic,ni.nics[nic]['dhcp']))
            logger.debug('ni.nics[%s]["ip"]: %s' % (nic,ni.nics[nic]['ip']))
            logger.debug('ni.nics[%s]["subnet"]: %s' % (nic,ni.nics[nic]['subnet']))            
            nicinfo = {'configure': True,
                    'use_dhcp': translateBoolean(ni.nics[nic]['dhcp']),
                    'hostname': ni.name + ni.nics[nic]['suffix'],
                    'ip_address': ni.nics[nic]['ip'],
                    'netmask': ni.nics[nic]['subnet'],
                    'active_on_boot': True}
                    
            nw['interfaces'][nic] = nicinfo
        logger.debug('network profile constructed: %r' % nw)
        
        self.networkprofile = nw
        
    def prepareKickstartDiskProfile(self,ni, testmode=False, diskimg=None):
        """ Reads in the NII instance and fills up the diskprofile. """

        logger.debug('Preparing disk profile')
        
        # create disk_dict structure
        disks = []
        partitionlist = []
        for k,v in ni.partitions.items():
            try:
                # we only want the physical disks
                d = int(v['device'])
                if d not in disks:  
                    disks.append({d:{'partition_dict':{}}})
            except ValueError:
                    pass
            partitionlist.append({k:v})
                    
        logger.debug('disks structure : %r' % disks)
           
        # create schema structure
        schema = {'disk_dict':{},'vg_dict':{}}

        # handle the physical disks
        for p in partitionlist:
            # get the schema from the partitionline
            d = translatePartitionOptions(p)
            if d:
                for disknum, part_dict in d.items():
                    if disknum in disks:
                        for partnum,v in part_dict.items():
                            disks[disknum]['partition_dict'][partnum] = v
                    
        
        # handle LVM
        vg = {}
        for p in partitionlist:
            d = translatePartitionOptions(p,'vg')
            if d: vg.update(d)
            
        schema['disk_dict'] = disks
        schema['vg_dict'] = vg
        
        logger.debug('diskprofile schema : %r' % schema)
        print 'schema : %r' % schema
        if testmode:
            self.diskprofile = DiskProfile(True,diskimg)
        else:
            self.diskprofile = DiskProfile(True)        
        setupDiskProfile(self.diskprofile, schema)

        
    def prepareKickstartPackageProfile(self,ni):
        """ Reads in the NII instance and fills up the packageprofile. """
        
        self.packageprofile = ni.packages
       
    def _makeRootPw(self, rootpw):
        import md5crypt
        import time

        # Not support unicode in root password
        return md5crypt.md5crypt(str(rootpw), str(time.time()));

    def __getattr__(self, name):
        if name in self.getattr_dict.keys():
            return self.getattr_dict[name]
        else:
            raise AttributeError, "%s instance has no attribute '%s'" % \
                                  (self.__class__, name)

    def __setattr__(self, item, value):
        if item in self.getattr_dict.keys():
            if item == 'rootpw':
                value = self._makeRootPw(value)

            self.getattr_dict[item] = value
        else:
             raise AttributeError, "%s instance has no attribute '%s'" % \
                                  (self.__class__, item)


class NodeInstaller(object):
    """ The model for nodeinstaller. This class provides access to
        the data and methods to perform the operations for automatic
        node provisioning. 
    """

    _niidict = {
    'source' : None,    # The NII source
    'name':'',          # Name of the node
    'installers':[],    # List of avaliable installers
    'repo':'',          # Repo location
    'ostype':'',        # OS type
    'installtype': '',  # Type of install to perform
    'nodegrpid':0 ,     # Node group ID
    'appglobal':{},     # Dictionary of all the appglobal data
    'nics':{},          # Dictionary of all the NIC info
    'partitions':{},    # Dictionary of all the Partition info.  Note key is only a counter
    'packages':[],      # List of packages to install
    'scripts':[],       # List of scripts to run
    'cfm': '',           # The CFM data
    'ksprofile' : None,  # The kickstart profile 
    'partitionschema' : {}, # partition schema
    'autoinstallfile' : None # distro-specific autoinstallation config file
    }

    def __init__(self, niisource=None):
        super(NodeInstaller, self).__init__()
        self.source = niisource


    def __getattr__(self, name):
	""" Convenience method for accessing attributes. Code snippet
	    taken from autoinstall.installprofile. 
	"""
        
        if name in self._niidict.keys():
            return self._niidict[name]
        else:
            raise AttributeError, "%s instance has no attribute '%s'" % \
                                  (self.__class__, name)

    def __setattr__(self, item, value):
    	""" Convenience method for setting attributes. Code snippet
    	    taken from autoinstall.installprofile. 
    	"""        
        if item in self._niidict.keys():
            self._niidict[item] = value
        else:
             raise AttributeError, "%s instance has no attribute '%s'" % \
                                  (self.__class__, item)

    def reset(self):
        """ Resets the NII dict. """

        self.source = None
        self.name = ''
        self.installers = []
        self.repo = ''
        self.ostype = ''
        self.installtype = ''
        self. nodegrpid = 0 
        self.appglobal = {}
        self.nics = {}
        self.partitions = {}
        self.packages = []
        self.scripts = []
        self.cfm = ''
        self.ksprofile = None
        self.partitionschema = {}
        self.autoinstallfile = None
        
        
    def parseNII(self):
        """ Parses the NII and places the resulting data into self.niidata """
        try:
            logger.debug('Parsing NII')
            logger.debug('niisource : %s' % self.source)
        
            if not self.source :
                self.reset()
                raise EmptyNIISource
        
            niidata = NodeInstInfoHandler()
            p = make_parser()
            p.setContentHandler(niidata)
            p.parse(self.source)
            for i in ['name', 'installers', 'repo', 'ostype', 'installtype',
                'nodegrpid', 'appglobal', 'nics', 'partitions', 'packages',
                'scripts', 'cfm']:
                setattr(self,i,getattr(niidata,i))
                logger.debug('%s : %s' % (i,getattr(self,i)))
                # also generate the appglobal source file
                niidata.saveAppGlobalsEnv()
        except SAXParseException:
            logger.debug('Failed parsing NII!')
        except EmptyNIISource:
            logger.debug('NII Source is empty!')
        
    def setup(self, autoinstallfile):
        """ Preparing attributes needed for automatic provisioning.
            A distro-specific autoinstallation configuration filename
            needs to be provided.
            FIXME: This needs to be handled per distro-specific!
        """
        self.parseNII()
        self.autoinstallfile = autoinstallfile
        self.ksprofile = KickstartFromNIIProfile(self)
        self.ksprofile.prepareKickstartSiteProfile()
        self.ksprofile.prepareKickstartNetworkProfile()
        self.ksprofile.prepareKickstartDiskProfile()
        self.ksprofile.prepareKickstartPackageProfile()
        
    def generateAutoinstall(self):
        """ Generates a distro-specific autoinstallation configuration file.
            FIXME: Except that it doesnt.. this needs to be handled per
            distro-specific!
        """
        autoscript = Script(KickstartFactory(self.ksprofile))
        autoscript.write(autoscript)
        
    def commit(self):
        """ This starts the automatic provisioning """

        logger.debug('Committing changes and formatting disk..')
        self.diskprofile.commit()
        self.diskprofile.format()
        self.generateAutoinstall()
    


