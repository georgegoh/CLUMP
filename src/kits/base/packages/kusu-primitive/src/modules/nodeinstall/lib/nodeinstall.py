
#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.


from random import choice
from cStringIO import StringIO
import string
import urllib2
import os
from xml.sax import make_parser, SAXParseException
from path import path

from primitive.core.errors import ModuleException
import primitive.support.log
from primitive.support import compat

from primitive.system.hardware.partitiontool import DiskProfile
from primitive.system.hardware.errors import *
from primitive.system.hardware.disk import Partition

from primitive.autoinstall.kickstart import KickstartFactory, RHEL5KickstartFactory
from primitive.autoinstall.yast import SLES102AutoyastFactory


from primitive.nodeinstall.errors import * 
from primitive.nodeinstall.niifun import NodeInstInfoHandler
from primitive.nodeinstall.partition import adaptNIIPartition
from primitive.nodeinstall.defaults import setupDiskProfile,isDiskFormatted

from primitive.support.util import runCommand
from primitive.system.hardware import probe




try:
    import subprocess
except:
    from popen5 import subprocess

logger = primitive.support.log.getPrimitiveLog('nodeinstall.NodeInstaller')

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
 
# def retrieveNII(niihost,uri_path="sles_os/niidump.txt"):
#     """ Downloads the NII from the niihost.
#     """
#     #uri_path set to intermediate value
#     url = 'http://%s/%s' % (niihost , uri_path)
#     try:
#         dest_dir = temfile.mkdtemp('nodeinstall')
#         try:
#             logger.debug('Fetching %s' % url)
#             status,f = FetchCommand(uri=url, fetchdir=False,destdir=dest_dir,
#                                     override=True).execute()
#             data = f.read()
#             logger.debug('Fetchtool data: %s' % data)
#             f.close()
#         finally:
#             # ensure deletion of dest_dir if its created
#             path(dest_dir).rmtree() 

#         return StringIO(data)
#     except CommandFailException, e:
#         msg = "nodeboot.cgi unavailable. " + \
#               "Fetchcommand failed: %s" % (e)
#         logger.error(msg)
#         raise NIISourceUnavailableError, msg
#     except IOError, e:
#         logger.error('%s', e.reason)
#         raise NIISourceUnavailableError, str(e.reason)


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
        

    def prepareKickstartSiteProfile(self,ni):
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
        try:
            kusu_dist = os.environ['PRIMITIVE_DIST']
            kusu_distver = os.environ['PRIMITIVE_DISTVER']
        except KeyError:
            #default to rhel5 for now
            kusu_dist='rhel'
            kusu_distver='5'

        if kusu_dist == 'rhel' and kusu_distver == '5':
            self.getattr_dict['instnum'] = None

            if ni.appglobal.has_key('InstNum'):
                self.instnum = ni.appglobal['InstNum']

    def prepareKickstartNetworkProfile(self,ni,niihost):
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
            schema, self.diskprofile = adaptNIIPartition(ni.partitions, self.diskprofile)
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
        except OutOfSpaceError, e:
            s = str(e) + '\nPlease remove unwanted partitions/logical volumes, or ' + \
                'modify the partition schema for this nodegroup to reduce the size ' + \
                'of this Logical Volume.'
            raise OutOfSpaceError, s
        return self.diskprofile
       

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
    'repoid':'',        # Repo ID
    'ngtype':'',        # Nodegroup type
#    'dbpasswd':'',      # dbpasswd
    'ostype':'',        # OS type
    'installtype': '',  # Type of install to perform
    'nodegrpid':0 ,     # Node group ID
    'appglobal':{},     # Dictionary of all the appglobal data
    'nics':{},          # Dictionary of all the NIC info
    'partitions':{},    # Dictionary of all the Partition info.  Note key is only a counter
    'diskprofile':{},   # Dictionary of disks and partitions
    'packages':[],      # List of packages to install
 #   'scripts':[],       # List of scripts to run
 #   'cfm': '',           # The CFM data
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
#        self.scripts = []
#        self.cfm = ''
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
                      'nodegrpid', 'appglobal', 'nics', 'partitions', 'packages',
                      'ngtype', 'repoid']:
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
#        self.ksprofile.prepareKickstartPackageProfile(self)
#        self.generateAutoinstall()
        
#     def generateAutoinstall(self):
#         """ Generates a distro-specific autoinstallation configuration file.
#             FIXME: Except that it doesnt.. this needs to be handled per
#             distro-specific!
#         """
# # Call Installtool over here
#         kusu_dist = os.environ['KUSU_DIST']
#         kusu_distver = os.environ['KUSU_DISTVER']

#         if kusu_dist == 'rhel' and kusu_distver == '5':
#             autoscript = Script(RHEL5KickstartFactory(self.ksprofile))
#         if kusu_dist == 'sles' and kusu_distver =='10':
#             autoscript = Script(SLES102AutoyastFactory(self.ksprofile))
#            autoscript = Script(KickstartFactory(self.ksprofile))
#         elif kusu_dist == 'fedora' and kusu_distver == '7':
#             autoscript = Script(Fedora7KickstartFactory(self.ksprofile))
#         elif kusu_dist == 'fedora' and kusu_distver == '8':
#             autoscript = Script(Fedora8KickstartFactory(self.ksprofile))
#         elif kusu_dist == 'fedora' and kusu_distver == '9':
#             autoscript = Script(Fedora9KickstartFactory(self.ksprofile))
#         else:
#             autoscript = Script(KickstartFactory(self.ksprofile))

#         autoscript.write(self.autoinstallfile)
        
    def commit(self):
        """ This starts the automatic provisioning """

        logger.debug('Committing changes and formatting disk..')
        self.ksprofile.diskprofile.commit()
        self.ksprofile.diskprofile.formatAll()
        
    def generateProfileNII(self, prefix):
        """ Generate the /etc/profile.nii. """
        root = path(prefix)
        etcdir = root / 'etc'
        if not etcdir.exists(): etcdir.mkdir()
        profilenii = etcdir / 'profile.nii'
        self.niidata.saveAppGlobalsEnv(profilenii)


#     def getDbPasswd(self, prefix):
#         """ Sync /opt/kusu/etc/db.passwd. """
#         root = path(prefix)
#         etcdir = root / 'opt' / 'kusu' / 'etc'
#         if not etcdir.exists(): etcdir.makedirs()
#         dbpasswd = etcdir / 'db.passwd'
#         self.niidata.saveDbPasswd(dbpasswd)
#         # May not want dbpasswd on all nodes!
#         # Want the cfm secret though
#         cfmdir = root / 'etc' / 'cfm'
#         if not cfmdir.exists(): cfmdir.makedirs()
#         cfmfile = cfmdir / '.cfmsecret'
#         self.niidata.saveCFMSecret(cfmfile)

    def setTimezone(self):
        tzfile = path('/usr/share/zoneinfo') / self.ksprofile.tz
        if tzfile.exists(): tzfile.copy('/etc/localtime')

        hwclock_args = '--hctosys'
        if self.ksprofile.tz_utc:
            hwclock_args += ' -u'

        hwclockP = subprocess.Popen('hwclock %s' % hwclock_args, shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        hwclockP.communicate()
        logger.debug('Setting timezone hwclock args: %s, return code: %s',
                     hwclock_args, hwclockP.returncode)

#     def getSSHPublicKeys(self, hostip, prefix=''):
#         authorized_keys = path(prefix + '/root/.ssh/authorized_keys')

#         if not authorized_keys.dirname().exists():
#             authorized_keys.dirname().makedirs()

#         # /root/.ssh needs to be 0700
#         authorized_keys.dirname().chmod(0700)

#         # grab public_keys file from master, save as authorized_keys
#         cmds = ['wget', 'http://%s/public_keys' % hostip, '-O', authorized_keys]
#         wgetP = subprocess.Popen(cmds, stdout=subprocess.PIPE,
#                                  stderr=subprocess.PIPE)
#         out, err = wgetP.communicate()                                 

#         authorized_keys.chmod(0600)

#     def saveLogs(self, destdir='/mnt/kusu/root', prefix='/tmp/kusu/'):
#         """Save the kusu.log and kusu-ks.cfg to /root."""
#         kusu_log = path(os.environ.get('KUSU_LOGFILE', '/var/log/kusu/kusu.log'))
#         ks_cfg = path(prefix) / path('ks.cfg')
#         d = path(destdir)

#         if not d.exists():
#             d.makedirs()

#         kusu_log.copy(d)
#         ks_cfg.copy(d / 'kusu-ks.cfg')

#     def download_scripts(self, niihost, prefix='/', script_dir_url=None):
#         prefix = path(prefix)
#         if script_dir_url is None:
#             script_dir_url = 'http://%s/repos/custom_scripts' % niihost

#         for script in self.scripts:
#             try:
#                 dl_script = urllib2.urlopen(script_dir_url + '/%s' % script)
#                 logger.info("Downloaded script '%s'", script)
#             except urllib2.HTTPError:   # Pass on 404 errors
#                 logger.warning("Script '%s' not found!", script)
#                 continue

#             rcdir = prefix / 'etc/rc.kusu.d'
#             if not rcdir.exists(): rcdir.makedirs()

#             script_file = open(rcdir / script, 'w')
#             script_file.write(dl_script.read())
#             script_file.close()
#             (rcdir / script).chmod(0755)

    def mountKusuMntPts(self, prefix):
        prefix = path(prefix)

        d = self.diskprofile.mountpoint_dict
        mounted = []

        # Mount and create in order
        for m in ['/', '/root', '/etc']:
            mntpnt = prefix + m

            if not mntpnt.exists():
                mntpnt.makedirs()
                logger.debug('Made %s dir' % mntpnt)
            
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
                raise ModuleException, 'Mountpoint: %s not defined' % m

