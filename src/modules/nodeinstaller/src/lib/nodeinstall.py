#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

from kusu.autoinstall.scriptfactory import KickstartFactory, RHEL5KickstartFactory
from kusu.autoinstall.autoinstall import Script
from kusu.partitiontool import DiskProfile
from kusu.installer.defaults import setupDiskProfile
from kusu.nodeinstaller import NodeInstInfoHandler
from kusu.util.errors import EmptyNIISource, InvalidPartitionSchema
from kusu.hardware import probe
from random import choice
from cStringIO import StringIO
import string
import urllib2
import os
import kusu.util.log as kusulog
from xml.sax import make_parser, SAXParseException
from path import path

try:
    import subprocess
except:
    from popen5 import subprocess

logger = kusulog.getKusuLog('nodeinstaller.NodeInstaller')

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
        retVal = int(value)
    except ValueError:
        if value.strip().lower() == 'n':
            retVal = 'N'
        retVal = 0
    return retVal

def translatePartitionSize(value):
    """ Translate NII partition size which is a string into
        partitiontool partition size which is an integer
    """
    return int(value)

def translateMntPnt(value):
    """ Check if mountpoint is an empty string - translate into None if yes. """
    if value.strip():
        return value
    else:
        return None

def translateFSTypes(fstype):
    """ Translates fstype to something partitiontool can understand. Right now
        only swap fstypes needs to be translated, the rest can be passed through.
    """

    if fstype == 'swap':
        return 'linux-swap'
    elif fstype.strip() == '':
        return None
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
    if opt == 'vg':
        if 'vg' in opt_dict.keys()  and 'extent' in opt_dict.keys():
            return (True, opt_dict['extent'])
        else:
            return (False, None)

    # pv
    if opt == 'pv':
        if 'pv' in opt_dict.keys() and 'vg' in opt_dict.keys():
            return (True, opt_dict['vg'])
        else:
            return (False,None)
        
    # lv
    if opt == 'lv':
        if 'lv' in opt_dict.keys() and 'vg' in opt_dict.keys():
            return (True, opt_dict['vg'])
        else:
            return (False, None)

def adaptNIIPartition(niipartition):
    """ Adapt niipartition into a partitiontool schema. This schema can
        be passed along with a partitiontool diskprofile to setupDiskProfile
        method.

    """

    schema = {'disk_dict':{},'vg_dict':None}

    # filter out the values into normal volumes and volume groups and logical volumes.
    part_list, vg_list, lv_list = filterPartitionEntries(niipartition.values())

    if vg_list:
        schema['vg_dict'] = {}
    # create the volume groups first.
    try:
        for vginfo in vg_list:
            vgname = vginfo['device']
            vg_extent_size = translatePartitionOptions(vginfo['options'], 'vg')[1]
            schema['vg_dict'][vgname] = {'pv_list':[], 'lv_dict':{},
                                         'extent_size':vg_extent_size}

        # create the normal volumes.
        for partinfo in part_list:
            createPartition(partinfo, schema['disk_dict'], schema['vg_dict'])
            pv, vg_name = translatePartitionOptions(partinfo['options'], 'pv')
            if pv: handlePV(partinfo, vg_name, schema['vg_dict'])
        # renumber spanning partitions
        for disk in schema['disk_dict'].itervalues():
            part_dict = disk['partition_dict']
            if part_dict.has_key('N'):
                partition = part_dict['N']
                part_dict[len(part_dict)] = partition
                del part_dict['N']

        # create the logical volumes.
        for lvinfo in lv_list:
            lv, vg_name = translatePartitionOptions(lvinfo['options'],'lv')
            if lv: handleLV(lvinfo, vg_name, schema['vg_dict'])

    except ValueError:
        raise InvalidPartitionSchema, "Couldn't parse one of the Volume Group fields."

    return schema

def filterPartitionEntries(partition_entries):
    """ Filter out the values into normal volumes and volume
        groups and logical volumes.
    """
    part_list = []
    vg_list = []
    lv_list = []
    for partinfo in partition_entries:
        try:
            disknum = int(partinfo['device'])
            part_list.append(partinfo)
        except ValueError:
            if translatePartitionOptions(partinfo['options'],'lv')[0]:
                lv_list.append(partinfo)
            elif translatePartitionOptions(partinfo['options'],'vg')[0]:
                vg_list.append(partinfo)
            elif partinfo['device'].lower() == 'n':
                part_list.append(partinfo)
            else:
                raise InvalidPartitionSchema, \
                 "Don't know what this entry is(not a partition, pv, vg or lv):\n%s" % partinfo
    return part_list, vg_list, lv_list

def createPartition(partinfo, disk_dict, vg_dict):
    """ Create a new partition and add it to the supplied disk dictionary."""
    try:
        disknum = int(partinfo['device'])
        part_no = translatePartitionNumber(partinfo['partition'])
    except ValueError:
        if partinfo['device'].lower() == 'n':
            handleSpanningPartition(partinfo, disk_dict, vg_dict)
            disknum = 1
            part_no = 'N'
        else:
            raise InvalidPartitionSchema, "Couldn't translate the disknum/partition number."
    try:
        size = translatePartitionSize(partinfo['size'])
        fs = translateFSTypes(partinfo['fstype'])
        mountpoint = translateMntPnt(partinfo['mntpnt'])
        fill = translatePartitionOptions(partinfo['options'], 'fill')[0]
    except ValueError:
        raise InvalidPartitionSchema, "Couldn't parse one of the Partition fields. " + \
                                      "disknum=%s, size=%s, fs=%s, mntpnt=%s, fill=%s, " + \
                                      "part_no=%s" % (partinfo['device'], partinfo['size'], \
                                      partinfo['fstype'], partinfo['mntpnt'], \
                                      partinfo['options'], partinfo['partition'])
 
    if part_no != 'N' and part_no <= 0:
        raise InvalidPartitionSchema, "Partition number cannot be less than 1."
    partition = {'size_MB': size, 'fill': fill,
                 'fs': fs, 'mountpoint': mountpoint}

    if disk_dict.has_key(disknum): disk = disk_dict[disknum]
    else: disk = {'partition_dict': {}}
    disk['partition_dict'][part_no] = partition
    disk_dict[disknum] = disk

def handleSpanningPartition(partinfo, disk_dict, vg_dict):
    is_pv, vg_name = translatePartitionOptions(partinfo['options'], 'pv')
    if not is_pv:
        raise InvalidPartitionSchema, "Partition marked as spanning multiple disks, but not as physical volumes."
    vg_dict[vg_name]['pv_span'] = True

def handlePV(partinfo, vg_name, vg_dict):
    if not vg_name.strip(): raise InvalidPartitionSchema, 'No Volume Group given for Physical Volume.'
    if vg_dict.has_key(vg_name): vg = vg_dict[vg_name]
    else: raise InvalidPartitionSchema, 'Physical Volume belongs to an unspecified Volume Group.'
    try:
        disknum = int(partinfo['device'])
        part_no = translatePartitionNumber(partinfo['partition'])
    except ValueError:
        if partinfo['device'].lower() == 'n':
            disknum = 'N'
            part_no = 'N'
        else:
            raise InvalidPartitionSchema, "Couldn't parse one of the LVM physical volume fields. " + \
                                          "disknum=%s, part_no=%s" % \
                                          (partinfo['device'], partinfo['partition'])

    vg['pv_list'].append({'disk': disknum, 'partition': part_no})

def handleLV(lvinfo, vg_name, vg_dict):
    if not vg_name.strip(): raise InvalidPartitionSchema, 'No Volume Group given for Logical Volume.'
    if vg_dict.has_key(vg_name): vg = vg_dict[vg_name]
    else: raise InvalidPartitionSchema, 'Logical Volume belongs to an unspecified Volume Group.'
    try:
        name = lvinfo['device']
        size_MB = translatePartitionSize(lvinfo['size'])
        fill = translatePartitionOptions(lvinfo['options'], 'fill')[0]
        fs = translateFSTypes(lvinfo['fstype'])
        mountpoint = translateMntPnt(lvinfo['mntpnt'])
    except ValueError:
        raise InvalidPartitionSchema, "Couldn't parse one of the LVM logical volume fields."

    vg['lv_dict'][name] = {'size_MB': size_MB, 'fill': fill,
                           'fs': fs, 'mountpoint': mountpoint}

def retrieveNII(niihost):
    """ Downloads the NII from the niihost.
    """
    url = 'http://%s/repos/nodeboot.cgi?dump=1&getindex=1' % niihost
    try:
        logger.debug('Fetching %s' % url)
        f = urllib2.urlopen(url)
        logger.debug('urlopen returned object: %r' % f)
        data = f.read()
        logger.debug('urlopen data: %s' % data)
        return StringIO(data)
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
                     'tz_utc': None,
                     'installsrc': None,
                     'lang': None,
                     'keyboard' : None}
    
    
    def __init__(self):
        """ ni is an instance of the NodeInstaller class. """
        super(KickstartFromNIIProfile, self).__init__()
        

    def prepareKickstartSiteProfile(self,ni):
        """ Reads in the NII instance and fills up the site-specific
            profile.
        """
        
        # rootpw is a randomly generated string since cfm will refresh /etc/passwd and /etc/shadow files
        #self.rootpw = getRandomSeq()
        self.rootpw = 'system'
        self.tz = ni.appglobal['Timezone_zone']
        self.tz_utc = translateBoolean(ni.appglobal['Timezone_utc'])
        self.lang = ni.appglobal['Language']
        self.keyboard = ni.appglobal['Keyboard']
        self.installsrc = 'http://' + ni.installers + ni.repo

        kusu_dist = os.environ['KUSU_DIST']
        kusu_distver = os.environ['KUSU_DISTVER']

        if kusu_dist == 'rhel' and kusu_distver == '5':
            self.getattr_dict['instnum'] = None

            if ni.appglobal.has_key('InstNum'):
                self.instnum = ni.appglobal['InstNum']

    def prepareKickstartNetworkProfile(self,ni):
        """ Reads in the NII instance and fills up the networkprofile. """
        
        logger.debug('Preparing network profile')
        nw = {}
        # network profile dict
        nw['interfaces'] = probe.getPhysicalInterfaces()
        unused_nics = []
        default_gateway = ''
        for nic in nw['interfaces']:
            if nic not in ni.nics:
                logger.debug('ni.nics does not contain nic %s', nic)
                # remember this nic for removal outside this for-loop
                unused_nics.append(nic)
                continue

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
                       'active_on_boot': translateBoolean(ni.nics[nic]['boot'])
                       }
                    
            if ni.nics[nic]['gateway']:
                default_gateway = ni.nics[nic]['gateway']

            nw['interfaces'][nic].update(nicinfo)


        for nic in unused_nics:
            # remove unused nics, configuring these will raise KeyErrors
            nw['interfaces'].pop(nic)

        nw['fqhn_use_dhcp'] = False     # always static hostnames
        nw['fqhn'] = '.'.join([ni.name, ni.appglobal['DNSZone']])

        if default_gateway:
            nw['gw_dns_use_dhcp'] = False
            nw['default_gw'] = default_gateway
        else:
            nw['gw_dns_use_dhcp'] = True

        nw['dns1'] = ni.appglobal.get('dns1', '')
        nw['dns2'] = ni.appglobal.get('dns2', '')
        nw['dns3'] = ni.appglobal.get('dns3', '')

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

        kusu_dist = os.environ['KUSU_DIST']
        kusu_distver = os.environ['KUSU_DISTVER']

        if kusu_dist == 'rhel' and kusu_distver == '5':
            autoscript = Script(RHEL5KickstartFactory(self.ksprofile))
        else:
            autoscript = Script(KickstartFactory(self.ksprofile))

        autoscript.write(self.autoinstallfile)
        
    def commit(self):
        """ This starts the automatic provisioning """

        logger.debug('Committing changes and formatting disk..')
        self.ksprofile.diskprofile.commit()
        self.ksprofile.diskprofile.formatAll()

    def setTimezone(self):
        tzfile = path('/usr/share/zoneinfo') / self.ksprofile.tz
        tzfile.copy('/etc/localtime')

        hwclock_args = '--hctosys'
        if self.ksprofile.tz_utc:
            hwclock_args += ' -u'

        hwclockP = subprocess.Popen('hwclock %s' % hwclock_args, shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        hwclockP.communicate()
        logger.debug('Setting timezone hwclock args: %s, return code: %s',
                     hwclock_args, hwclockP.returncode)

