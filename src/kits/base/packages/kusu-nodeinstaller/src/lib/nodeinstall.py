#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

from primitive.system.hardware.partitiontool import DiskProfile
from primitive.system.hardware.disk import Partition
from kusu.installer.defaults import *
from kusu.nodeinstaller import NodeInstInfoHandler
from kusu.util.testing import runCommand
from kusu.util.errors import KusuError, NIISourceUnavailableError, ParseNIISourceError, InvalidPartitionSchema, LVMPreservationError, EmptyNIISource
from primitive.system.hardware.errors import *
from primitive.system.hardware import probe
from primitive.system.hardware.net import arrangeOnBoardNicsFirst
from random import choice
from cStringIO import StringIO
import time
import string
import tempfile
import urllib2
import os
import md5crypt
import kusu.util.log as kusulog
from xml.sax import make_parser, SAXParseException
from path import path
from kusu.nodeinstaller.partition import *
from primitive.system.software.dispatcher import Dispatcher
from primitive.installtool.commands import GenerateAutoInstallScriptCommand
from primitive.system.hardware.net import getPhysicalAddressList
from primitive.support.util import convertStrMACAddresstoInt
from primitive.support.errors import InvalidMacAddressException
import sha

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

def getLowestMACAddress():
    """ Returns the lowest integer MAC Address among all physical interfaces."""
    macs = getPhysicalAddressList()

    intMACs = []
    for mac in macs:
        try:
            mac = convertStrMACAddresstoInt(mac)
            intMACs.append(mac)
        except InvalidMacAddressException:
            pass

    return min(intMACs)

def genUID():
    """ Returns a hashed time-invariant Unique ID (string) for the machine."""
    mac = getLowestMACAddress()

    if not mac:
        return ''

    s = sha.new(str(mac))
    hashed = s.hexdigest()
    return hashed
 
def retrieveNII(niihost):
    """ Downloads the NII from the niihost."""
    url = 'http://%s/repos/nodeboot.cgi?dump=1&getindex=1&state=Installing' % niihost

    uid = genUID()
    if uid:
        url += '&uid=%s' % uid

    try:
        logger.debug('Fetching %s' % url)
        f = urllib2.urlopen(url)
        logger.debug('urlopen returned object: %r' % f)
        data = f.read()
        logger.debug('urlopen data: %s' % data)
        return StringIO(data)
    except urllib2.HTTPError, e:
        msg = "nodeboot.cgi unavailable. " + \
              "Return code: %d, message: %s, URL: %s" % (e.code, e.msg, url)
        logger.error(msg)
        raise NIISourceUnavailableError, msg
    except urllib2.URLError, e:
        logger.error('%s', e.reason)
        raise NIISourceUnavailableError, str(e.reason)


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
                     'keyboard' : None,
                     'diskorder' : None}

    def __init__(self):
        """ ni is an instance of the NodeInstaller class. """
        super(KickstartFromNIIProfile, self).__init__()

    def prepareKickstartSiteProfile(self, ni):
        """ Reads in the NII instance and fills up the site-specific
            profile.
        """
        
        # rootpw is a randomly generated string since cfm will
        # refresh /etc/passwd and /etc/shadow files
        self.rootpw = getRandomSeq()
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

    def prepareKickstartNetworkProfile(self,ni,niihost):
        """ Reads in the NII instance and fills up the networkprofile. """
        
        logger.debug('Preparing network profile')
        nw = {}
        # network profile dict
        nw['interfaces'] = arrangeOnBoardNicsFirst(probe.getPhysicalInterfaces())
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
                       # Apparently nics.boot != active_on_boot (KUSU-602).
                       #'active_on_boot': translateBoolean(ni.nics[nic]['boot'])
                       'active_on_boot': True
                       }
                    
            if ni.nics[nic]['gateway']:
                default_gateway = ni.nics[nic]['gateway']

            nw['interfaces'][nic].update(nicinfo)

        for nic in unused_nics:
            # remove unused nics, configuring these will raise KeyErrors
            nw['interfaces'].pop(nic)

        nw['fqhn_use_dhcp'] = False     # always static hostnames
        nw['fqhn_host'] = '.'.join([ni.name, ni.appglobal['DNSZone']])

        if default_gateway:
            nw['gw_dns_use_dhcp'] = False
            nw['default_gw'] = default_gateway
        else:
            nw['gw_dns_use_dhcp'] = True

        if ni.appglobal.get('InstallerServeDNS', '0') == '1':
            nw['dns1'] = niihost
        else:
            nw['dns1'] = ni.appglobal.get('dns1', '')
            nw['dns2'] = ni.appglobal.get('dns2', '')
            nw['dns3'] = ni.appglobal.get('dns3', '')

        logger.debug('network profile constructed: %r' % nw)
        
        self.networkprofile = nw
        
    def prepareKickstartDiskProfile(self,ni, testmode=False, diskimg=None, disk_order=None):
        """ Reads in the NII instance and fills up the diskprofile. """

        logger.debug('Preparing disk profile')
        
        try:
            # adapt the NII into a schema
            logger.debug('Adapting ni.partitions: %r' % ni.partitions)
            if testmode:
                self.diskprofile = DiskProfile(False,diskimg)
            else:
                self.diskprofile = DiskProfile(False)
            for disk in self.diskprofile.disk_dict.values():
                if isDiskFormatted(disk):
                    logger.debug('Re-initialize')
                    runCommand('dd if=/dev/zero of=%s bs=1k count=10' % disk.path)
                    self.diskprofile = DiskProfile(fresh=False, probe_fstab=False)
 
            schema = None
            schema, self.diskprofile = adaptNIIPartition(ni.partitions, self.diskprofile, ni.appglobal)
            logger.debug('Adapted schema from the ni.partitions: %r' % schema)
            if not disk_order:
                logger.debug('Getting order of disks according to the BIOS.')
                disk_order = self.diskprofile.getBIOSDiskOrder()
            logger.debug('Calling setupDiskProfile to apply schema to the diskprofile..')
            setupDiskProfile(self.diskprofile, schema, disk_order=disk_order)
            self.diskorder = disk_order
        except InvalidPartitionSchema, e:
            logger.debug('Invalid partition schema! schema: %r' % schema)
            raise e
        except LVMPreservationError, e:
            logger.debug('LVM Preservation Error: %s' % str(e))
            raise e        
        except OutOfSpaceError, e:
            s = str(e) + '\nPlease remove unwanted partitions/logical volumes, or ' + \
                'modify the partition schema for this nodegroup to reduce the size ' + \
                'of this Logical Volume.'
            raise OutOfSpaceError, s
        return self.diskprofile
       

    def prepareKickstartPackageProfile(self,ni):
        """ Reads in the NII instance and fills up the packageprofile. """
        
        logger.debug('Preparing package profile')

        for c in ni.components:
            logger.debug('Adding base kit components %s to packageprofile..' % c)
            if c.startswith('component-base') and c not in self.packageprofile:
                self.packageprofile.append(c)

        # cfm will now install these packages/components
        #for p in ni.packages:
        #    logger.debug('Adding package %s to packageprofile..' % p)
        #    if p not in self.packageprofile:
        #        self.packageprofile.append(p)

    def _makeRootPw(self, rootpw):
        return md5crypt.md5crypt(str(rootpw), (str(time.time())))

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
    'repoid':'',        # Repo ID
    'ngtype':'',        # Nodegroup type
    'dbpasswd':'',      # dbpasswd
    'ostype':'',        # OS type
    'installtype': '',  # Type of install to perform
    'nodegrpid':0 ,     # Node group ID
    'appglobal':{},     # Dictionary of all the appglobal data
    'nics':{},          # Dictionary of all the NIC info
    'partitions':{},    # Dictionary of all the Partition info.  Note key is only a counter
    'diskprofile':{},   # Dictionary of disks and partitions
    'packages':[],      # List of packages to install
    'components':[],    # List of components to install
    'scripts':[],       # List of scripts to run
    'cfm': '',           # The CFM data
    'ksprofile' : None,  # The kickstart profile 
    'partitionschema' : {}, # partition schema
    'autoinstallfile' : None, # distro-specific autoinstallation config file
    'niidata': None
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
        self.nodegrpid = 0 
        self.appglobal = {}
        self.nics = {}
        self.partitions = {}
        self.packages = []
        self.components = []
        self.scripts = []
        self.cfm = ''
        self.ksprofile = None
        self.partitionschema = {}
        self.autoinstallfile = None
        self.niidata = None
        
    def parseNII(self):
        """ Parses the NII and places the resulting data into self.niidata """
        try:
            logger.debug('Parsing NII')
            logger.debug('niisource : %s' % self.source) 
            if not self.source :
                self.reset()
                raise EmptyNIISource
        
            self.niidata = NodeInstInfoHandler()
            p = make_parser()
            p.setContentHandler(self.niidata)
            p.parse(self.source)
            for i in ['name', 'installers', 'repo', 'ostype', 'installtype',
                'nodegrpid', 'appglobal', 'nics', 'partitions', 'packages', 'components',
                'scripts', 'cfm', 'ngtype', 'repoid']:
                setattr(self,i,getattr(self.niidata,i))
                logger.debug('%s : %s' % (i,getattr(self,i)))

        except SAXParseException, e:
            msg = "Failure parsing NII!\n" + \
                  "System ID: %s\n" % e.getSystemId() + \
                  "Line: %s\nColumn: %s\n" % (e.getLineNumber(),
                                              e.getColumnNumber()) + \
                  "Message: %s" % e.getMessage()
            logger.error(msg)
            raise ParseNIISourceError, msg
        except EmptyNIISource:
            msg = 'NII Source is empty!'
            logger.error(msg)
            raise ParseNIISourceError, msg
        
    def setup(self, autoinstallfile, niihost, disk_order):
        """ Preparing attributes needed for automatic provisioning.
            A distro-specific autoinstallation configuration filename
            needs to be provided.
            FIXME: This needs to be handled per distro-specific!
        """
        self.parseNII()
        self.autoinstallfile = autoinstallfile
        self.ksprofile = KickstartFromNIIProfile()
        self.ksprofile.prepareKickstartSiteProfile(self)
        self.ksprofile.prepareKickstartNetworkProfile(self, niihost)
        self.diskprofile = self.ksprofile.prepareKickstartDiskProfile(self, disk_order=disk_order)
        self.ksprofile.prepareKickstartPackageProfile(self)
        
    def generateAutoinstall(self):
        """ Generates a distro-specific autoinstallation configuration file.
        """
        kusu_root = path(os.environ.get('KUSU_ROOT', '/opt/kusu'))
        kusu_dist = os.environ['KUSU_DIST']
        kusu_distver = os.environ['KUSU_DISTVER']

        if kusu_dist in ['sles', 'opensuse']:
            template_uri = 'file://%s' % (kusu_root / 'etc' / 'templates' / 'autoinst.tmpl')
        else:
            template_uri = 'file://%s' % (kusu_root / 'etc' / 'templates' / 'kickstart.tmpl')

        try:
            instnum = self.ksprofile.instnum
        except AttributeError:
            instnum = None

        # Note: installsrc is needed for rhel/centos but not for sles
        ic = GenerateAutoInstallScriptCommand(os={'name':kusu_dist, 'version':kusu_distver},
                                              diskprofile=self.diskprofile,
                                              networkprofile=self.ksprofile.networkprofile,
                                              installsrc=self.ksprofile.installsrc,
                                              rootpw=self.ksprofile.rootpw,
                                              tz=self.ksprofile.tz,
                                              tz_utc=self.ksprofile.tz_utc,
                                              lang=self.ksprofile.lang,
                                              keyboard=self.ksprofile.keyboard,
                                              packageprofile=self.ksprofile.packageprofile,
                                              instnum=instnum,
                                              diskorder=self.ksprofile.diskorder,
                                              template_uri=template_uri,
                                              outfile=self.autoinstallfile)

        ic.execute()

    def setUUIDs(self):
         for disk in self.ksprofile.diskprofile.disk_dict.values():
            for partition in disk.partition_dict.values():
                #mount partition as readonly and check UUID dotfile
                try:
                    if partition.native_type.lower().find('ntfs') == -1 \
                       and partition.native_type.lower().find('swap') == -1 \
                       and partition.leave_unchanged == False:
                        
                        tmpdir = tempfile.mkdtemp()
                        partition.mount(mountpoint=tmpdir, readonly=False)
                        
                        """FIXME: Temporarily disable the proper appglobals method of writing the file
                        
                        if (not os.path.exists("%s/.%s" % (tmpdir, self.niidata.appglobal['MASTER_UUID']))):
                            fd = open("%s/.%s" % (tmpdir, self.niidata.appglobal['MASTER_UUID']), "w")
                            fd.close()
                        """
                        
                        #FIXME: writing ".kusu" as a temporary placeholder
                        fd = open("%s/.%s" % (tmpdir, "kusu"), "w")
                        fd.close()
                        
                            
                        partition.unmount()       
                except:
                    logger.debug("Failed to mount [%s] for UUID writing" % (partition.path) )
        
    def commit(self):
        """ This starts the automatic provisioning """

        logger.debug('Committing changes and formatting disk..')
        self.ksprofile.diskprofile.commit()
        self.ksprofile.diskprofile.formatAll()

        #mount each of the formatted disks and write the UUID
        self.setUUIDs()
        
    def generateProfileNII(self, prefix):
        """ Generate the /etc/profile.nii. """
        root = path(prefix)
        etcdir = root / 'etc'
        if not etcdir.exists(): etcdir.mkdir()
        profilenii = etcdir / 'profile.nii'
        self.niidata.saveAppGlobalsEnv(profilenii)

    def getDbPasswd(self, prefix):
        """ Sync /opt/kusu/etc/db.passwd. """
        root = path(prefix)
        etcdir = root / 'opt' / 'kusu' / 'etc'
        if not etcdir.exists(): etcdir.makedirs()
        dbpasswd = etcdir / 'db.passwd'
        self.niidata.saveDbPasswd(dbpasswd)
        # May not want dbpasswd on all nodes!
        # Want the cfm secret though
        cfmdir = root / 'etc' / 'cfm'
        if not cfmdir.exists(): cfmdir.makedirs()
        cfmfile = cfmdir / '.cfmsecret'
        self.niidata.saveCFMSecret(cfmfile)


    def getIpmiPasswd(self, prefix):
        """ Sync /opt/kusu/etc/.ipmi.passwd. """
        root = path(prefix)
        etcdir = root / 'opt' / 'kusu' / 'etc'
        if not etcdir.exists(): etcdir.makedirs()
        ipmipasswd = etcdir / '.ipmi.passwd'
        self.niidata.saveIpmiPassword(ipmipasswd)


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

    def saveLogs(self, destdir='/kusu/mnt/root', prefix='/tmp/kusu/'):
        """Save the kusu.log and kusu.cfg/autoinst.xml to /root."""
        autoinstall_conf = Dispatcher.get('autoinstall_conf')
        kusu_log = path(os.environ.get('KUSU_LOGFILE', '/var/log/kusu/kusu.log'))
        autoinstall_file = path(prefix) / path(autoinstall_conf)
        d = path(destdir)

        if not d.exists():
            d.makedirs()

        kusu_log.copy(d)
        autoinstall_file.copy(d / 'kusu-%s' % autoinstall_conf)

    def download_scripts(self, niihost, prefix='/', script_dir_url=None):
        prefix = path(prefix)
        if script_dir_url is None:
            script_dir_url = 'http://%s/repos/custom_scripts' % niihost

        for script in self.scripts:
            try:
                dl_script = urllib2.urlopen(script_dir_url + '/%s' % script)
                logger.info("Downloaded script '%s'", script)
            except urllib2.HTTPError:   # Pass on 404 errors
                logger.warning("Script '%s' not found!", script)
                continue

            rcdir = prefix / 'etc/rc.kusu.d'
            if not rcdir.exists(): rcdir.makedirs()

            script_file = open(rcdir / script, 'w')
            script_file.write(dl_script.read())
            script_file.close()
            (rcdir / script).chmod(0755)

    def mountKusuMntPts(self, prefix):
        prefix = path(prefix)

        d = self.diskprofile.mountpoint_dict
        mounted = []
        kusu_dist = os.environ.get('KUSU_DIST', None)

        # Mount and create in order
        mountpts = d.keys()
        mountpts.sort()
        for m in mountpts:
            mntpnt = prefix + m

            if not mntpnt.exists():
                mntpnt.makedirs()
                logger.debug('Made %s dir' % mntpnt)
            
            if m=='/boot' and kusu_dist=='sles':
                continue

            # mountpoint has an associated partition,
            # and mount it at the mountpoint
            if d.has_key(m):
                try:
                    logger.debug('Try to mount %s' % m)
                    d[m].mount(mntpnt)
                    mounted.append(m)
                except MountFailedError, e:
                    raise MountFailedError, 'Unable to mount %s on %s' % (d[m].path, m)

        for m in ['/']:
            if m not in mounted:
                raise KusuError, 'Mountpoint: %s not defined' % m

    def setInstallFlag(self, prefix):
        prefix = path(prefix)
        flag = prefix / 'var' / 'lock' / 'subsys' /  'kusu-installer'
        # fix issue where the lock dir can already exist, causing an exception
        if not flag.parent.exists():
            flag.parent.makedirs()
        flag.touch()
