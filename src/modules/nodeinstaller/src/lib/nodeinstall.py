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
from kusu.util.errors import EmptyNIISource, InvalidPartitionSchema
from whrandom import choice
import string
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
        
def translatePartitionNumber(value):
    """ Translate NII partition number which is a string into
        partitiontool partition number which is an integer
    """
    try:
        return int(value)
    except ValueError:
        return 0
    
def translatePartitionSize(value):
    """ Translate NII partition size which is a string into
        partitiontool partition size which is an integer
    """
    return int(value)

def translateFSTypes(fstype):
    """ Translates fstype to something partitiontool can understand. Right now
        only swap fstypes needs to be translated, the rest can be passed through.
    """

    if fstype == 'swap':
        return 'linux-swap'
    else:
        return fstype
        
def translatePartitionOptions(options, opt):
    """ Translate the options line for the opt value. This method returns
        a tuple (x,y). The first tuple element is a boolean, True if the 
        opt value exists, False if otherwise. The second element is data 
        that is specific to the opt value.

        PARTITION_OPTIONS = [ 'fill', 'pv', 'vg', 'lv', 'label', 
                            'preserve', 'extent']

        An example partitionopts line looks like the following:
            fill;label='My Volume';preserve

        An example partitionopts line for a LVM Volume Group can be defined
        as follows, note that the name of the Volume Group should be defined
        in the device column in the partitions table:
            vg;extent=32M

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
    optionlist = options.split(';')
    opt_dict = {}
    if optionlist:
        for i in optionlist:
            try:
                opt_dict[i.split('=')[0]] = i.split('=')[1]
            except IndexError:
                opt_dict[i.split('=')[0]] = None

    # fill
    if opt == 'fill' and opt not in opt_dict.keys():
        return (False,None)
        
    if opt == 'fill' and opt in opt_dict.keys():
        return (True,None)

    # preserve
    if opt == 'preserve' and opt not in opt_dict.keys():
        return (False,None)

    if opt == 'preserve' and opt in opt_dict.keys():
        return (True,None)
        
    # extent
    if opt == 'extent' and opt not in opt_dict.keys():
        return (False,None)
        
    if opt == 'extent' and opt in opt_dict.keys():
        return (True,opt_dict[opt])
        
    # label
    if opt == 'label' and opt not in opt_dict.keys():
        return (False,None)

    if opt == 'label' and opt in opt_dict.keys():
        return (True,opt_dict[opt])
        
    # vg
    if opt == 'vg' and 'extent' not in opt_dict.keys():
        return (False,None)

    if opt == 'vg' and 'extent' in opt_dict.keys():
        return (True,opt_dict['extent'])
        
    # pv
    if opt == 'pv' and 'vg' not in opt_dict.keys():
        return (False,None)
        
    if opt == 'pv' and 'vg' in opt_dict.keys():
        return (True,opt_dict['vg'])
        
    # lv
    if opt == 'lv' and 'vg' not in opt_dict.keys():
        return (False,None)

    if opt == 'lv' and 'vg' in opt_dict.keys():
        return (True,opt_dict['vg'])

def adaptNIIPartition(niipartition):
    """ Adapt niipartition into a partitiontool schema. This schema can
        be passed along with a partitiontool diskprofile to setupDiskProfile
        method.

    """

    schema = {'disk_dict':{},'vg_dict':{}}
    disk_dict = {}
    partition_dict = {}
    vg_dict = {}
    vg_extent_size = ''
    vgname = None
    pv_dict = {}
    lv_dict = {}
    for partnum, partinfo in niipartition.items():
        # check device
        try:
            disknum = int(partinfo['device'])
        except ValueError:
            disknum = 0
        # handling physical partitioning
        if disknum:
            try:
                size = translatePartitionSize(partinfo['size'])
                fs = translateFSTypes(partinfo['fstype'])
                mountpoint = partinfo['mntpnt']
                fill = translatePartitionOptions(partinfo['options'],'fill')[0]

                # also check if this is a physical volume
                pv = translatePartitionOptions(partinfo['options'],'pv')
                partition = translatePartitionNumber(partinfo['partition'])
                if pv[0] and partition > 0:
                    pv_dict.update({disknum:{'disk':disknum,
                                            'partition':partition}})
                disk_part_dict = {'size_MB':size,'fs':fs,
                                'mountpoint':mountpoint,'fill' : fill}
            except ValueError:
                raise InvalidPartitionSchema
                
            partition_dict.update({partition:disk_part_dict})
            disk_dict.update({disknum:{'partition_dict':partition_dict}})
            schema['disk_dict'].update(disk_dict)
        else:
            # handle LVM
            try:
                # FIXME: we are only supporting a single volume group for now!
                if partinfo['device']: vgname = partinfo['device']
                size = translatePartitionSize(partinfo['size'])
                fs = translateFSTypes(partinfo['fstype'])
                mountpoint = partinfo['mntpnt']
                fill = translatePartitionOptions(partinfo['options'],'fill')[0]
                
                # is this a volume group?
                vg = translatePartitionOptions(partinfo['options'],'vg')
                if vg[0]:
                    # get the extent size
                    vg_extent_size = vg[1]
                    vg_dict.update({vgname:{'pv_dict':pv_dict,
                                        'lv_dict':lv_dict,
                                        'extent_size':vg_extent_size}})
                                    
                # or it could be a logical volume
                lv = translatePartitionOptions(partinfo['options'],'lv')
                if lv[0]:
                    # FIXME: please ensure that the vgname defined here corresponds to the devname!
                    size = translatePartitionSize(partinfo['size'])
                    fs = translateFSTypes(partinfo['fstype'])
                    mountpoint = partinfo['mntpnt']
                    if mountpoint == '/':
                        lvroot = 'ROOT'
                    else:
                        lvroot = mountpoint[1:].upper()
                    fill = translatePartitionOptions(partinfo['options'],'fill')[0]                
                
                    disk_part_dict = {'size_MB':size,'fs':fs,
                                    'mountpoint':mountpoint,'fill' : fill}
                    if lvroot: lv_dict.update({lvroot:disk_part_dict})
                    vg_dict.update({vgname:{'pv_dict':pv_dict,
                                        'lv_dict':lv_dict,
                                        'extent_size':vg_extent_size}})
            except ValueError:
                raise InvalidPartitionSchema
            
            schema['vg_dict'].update(vg_dict)
    return schema

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

def getRandomSeq(length=8, chars=string.letters + string.digits):
    """Return a random sequence length chars long."""

    return ''.join([choice(chars) for i in range(length)])

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
        
        if '@Base' not in self.packageprofile: self.packageprofile.append('@Base')
        
    def prepareKickstartSiteProfile(self,ni):
        """ Reads in the NII instance and fills up the site-specific
            profile.
        """
        
        # rootpw is a randomly generated string since cfm will refresh /etc/passwd and /etc/shadow files
        self.rootpw = getRandomSeq()
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
                    'ip_address': ni.nics[nic]['ip'],
                    'netmask': ni.nics[nic]['subnet'],
                    'active_on_boot': True, # FIXME: this needs to be figured out from somewhere!
                    }
                    
            nw['interfaces'][nic] = nicinfo
            nw['default_gw'] = ''
            nw['dns1'] = ''
            nw['gw_dns_use_dhcp'] = True # FIXME: this needs to be figured out from somewhere!
            nw['fqhn_use_dhcp'] = False # FIXME: this needs to be figured out from somewhere!
            nw['fqhn'] = ni.name + ni.nics[nic]['suffix'] # FIXME: suffix may be empty and there may be multiple fqhn with same names!
        logger.debug('network profile constructed: %r' % nw)
        
        self.networkprofile = nw
        
    def prepareKickstartDiskProfile(self,ni, testmode=False, diskimg=None):
        """ Reads in the NII instance and fills up the diskprofile. """

        logger.debug('Preparing disk profile')
        
        try:
            # adapt the NII into a schema
            logger.debug('Adapting ni.partitions: %r' % ni.partitions)
            schema = adaptNIIPartition(ni.partitions)
            logger.debug('Adapted schema from the ni.partitions: %r' % schema)
            if testmode:
                self.diskprofile = DiskProfile(True,diskimg)
            else:
                self.diskprofile = DiskProfile(True)
            logger.debug('Calling setupDiskProfile to apply schema to the diskprofile..')    
            setupDiskProfile(self.diskprofile, schema)
        except InvalidPartitionSchema, e:
            logger.debug('Invalid partition schema! schema: %r' % schema)
            raise e
       
    def prepareKickstartPackageProfile(self,ni):
        """ Reads in the NII instance and fills up the packageprofile. """
        
        logger.debug('Preparing package profile')
        for p in ni.packages:
            logger.debug('Adding package %s to packageprofile..' % p)
            if p not in self.packageprofile:
                self.packageprofile.append(p)
       
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
    'installers':[],    # List of available installers
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
        self.ksprofile = KickstartFromNIIProfile()
        self.ksprofile.prepareKickstartSiteProfile(self)
        self.ksprofile.prepareKickstartNetworkProfile(self)
        self.ksprofile.prepareKickstartDiskProfile(self)
        self.ksprofile.prepareKickstartPackageProfile(self)
        self.generateAutoinstall()
        
    def generateAutoinstall(self):
        """ Generates a distro-specific autoinstallation configuration file.
            FIXME: Except that it doesnt.. this needs to be handled per
            distro-specific!
        """
        autoscript = Script(KickstartFactory(self.ksprofile))
        autoscript.write(self.autoinstallfile)
        
    def commit(self):
        """ This starts the automatic provisioning """

        logger.debug('Committing changes and formatting disk..')
        self.diskprofile.commit()
        self.diskprofile.format()
