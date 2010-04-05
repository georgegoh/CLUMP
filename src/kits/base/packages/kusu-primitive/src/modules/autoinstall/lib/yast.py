#!/usr/bin/env python
# $Id: yast.py 3361 2010-01-12 03:13:25Z ggoh $
#
# Copyright 2008 Platform Computing Inc.
#
''' The autoinstall module contains factories for generating autoinstall files for
    the various distros.
'''
import os
import time
import md5crypt
import urlparse
from path import path
from tempfile import mkdtemp
from primitive.fetchtool.commands import FetchCommand
from primitive.core.errors import TemplateNotFoundException
from primitive.core.errors import AutoInstallConfigNotCompleteException
from primitive.core.errors import NotImplementedError

class AutoyastFactory(object):
    keys = ['diskprofile',
            'networkprofile',
            'packageprofile',
            'rootpw',
            'tz',
            'tz_utc',
            'installsrc',
            'lang',
            'keyboard',
            'diskorder'
           ]


    def __init__(self, **kwargs):
        self.template_dir = path(mkdtemp(prefix='SLES102AutoyastFactory-'))
        valid_conf, missing = self._validateConf(kwargs)
        if valid_conf:
            self.conf = kwargs
        else:
            raise AutoInstallConfigNotCompleteException, \
                  '%s attributes not found in config.' % missing
        self.setTemplatePath(kwargs)
        self.namespace = {}
        self.basepattern = None

    def __del__(self):
        self.template_dir.rmtree()


    def setTemplatePath(self, conf):
        protocol = urlparse.urlparse(conf['template_uri'])[0]
        fc = FetchCommand(uri=conf['template_uri'], fetchdir=False,
                          destdir=self.template_dir, overwrite=True, lockdir=os.getenv('PRIMITIVE_LOCKDIR', '/var/lock/subsys/primitive'))
        fc.execute()

        self.template = self.template_dir / \
                        path(conf['template_uri']).basename()
        if not self.template.exists():
            raise TemplateNotFoundException, \
                  '%s template not found' % self.template
    

    def _validateConf(self, conf):
        valid = True
        missing = []
        for key in self.keys:
            if not conf.has_key(key):
                valid = False
                missing.append(key)
        return valid, missing


    def getNameSpace(self):
        self.namespace['url'] = self.conf['installsrc']
        self.namespace['rootpw'] = self._getMD5Password()
        self.namespace['tz'] = self.conf['tz']
        self.namespace['tz_utc'] = self.conf['tz_utc']
        self.namespace['lang'] = self.conf['lang']
        self.namespace['langsupport'] = self.conf['lang']
        self.namespace['keybd'] = self.conf['keyboard']
        self.namespace['packages'] = self.conf['packageprofile']
        self.namespace['networks'] = self._getNetworks()
        self.namespace['nameservers'] = self._getNameservers()
        self.namespace['dhcp'] = self._getDHCP()
        self.namespace['partitions'] = self.conf['diskprofile']
        self.namespace['mbrdriveorder'] = ','.join(self.conf['diskorder'])
        self.namespace['mbrbootloader'] = self._useMBR()
        self.namespace['partitionrules'] = self._getPartitionRules()
        self.namespace['defaultgw'] = self._getDefaultGW()
        self.namespace['hostname'] = self._getFQHN()
        self.namespace['domain'] = self._getDomain()
        self.namespace['basepattern'] = self.basepattern
        return self.namespace

    def _getDomain(self):
        networks = self.conf['networkprofile']
        if not networks or not networks.has_key('fqhn_domain') or not networks['fqhn_domain']:
            return 'example.com'
        return networks['fqhn_domain']

    def _getFQHN(self):
        networks = self.conf['networkprofile']
        if not networks or not networks.has_key('fqhn_host') or not networks['fqhn_host']:
            return 'unknown'
        return networks['fqhn_host']

    def _getDefaultGW(self):
        networks = self.conf['networkprofile']
        if not networks or not networks.has_key('default_gw') or not networks['default_gw']:
            return '0.0.0.0'
        return networks['default_gw']

    def _useMBR(self):
        dp = self.conf['diskprofile']
        if not dp:
            return True
        for disk in dp.disk_dict.values():
            for partition in disk.partition_dict.values():
                if partition.native_type=='Dell Utility' or partition.dellUP_flag:
                    return False
        if hasattr(dp, 'use_mbr'):
            return dp.use_mbr
        return True

    def _getPartitionRules(self):
        if not self.conf.has_key('partitionrules'):
            return []

        rules = self.conf['partitionrules']
        for r in rules:
            if r.size:
                r.size = long(r.size) * 1024 * 1024
        return rules

    def _getMD5Password(self):
        return md5crypt.md5crypt(str(self.conf['rootpw']), str(time.time()))

    def _getDHCP(self):
        networks = self.conf['networkprofile']
        if not networks or not networks['interfaces']:
            return False 
        for intf, v in networks['interfaces'].items():
            if v['use_dhcp']:
                return True 
        return False 

    def _getNameservers(self):
        dns_lines = []
        networks = self.conf['networkprofile']

        if not networks:
            return []

        dns = [networks[key] for key in ['dns1', 'dns2', 'dns3'] \
               if networks.has_key(key) and networks[key]]
        return dns

    def _getInterfaceName(self, intf, hwaddr):
        raise NotImplementedError, 'A subclass needs to to implement this'

    def _getNetworks(self):
        # Creates the kickstart option for networking 

        network_lines = []
        networks = self.conf['networkprofile']

        if not networks:
            # No network
            return network_lines

        for intf, v in networks['interfaces'].items():
            intf_name = self._getInterfaceName(intf, v['hwaddr'])
            if v['configure']:
                network_lines.append('<interface>')
                if v['use_dhcp']:
                    s = '    <bootproto>dhcp</bootproto>'
                    s += '\n                <device>%s</device>' % intf_name
                    if v['active_on_boot']:
                        s += '\n                <startmode>onboot</startmode>'
                else:
                    s = '    <bootproto>static</bootproto>'
                    s += '\n                <device>%s</device>' % intf_name
                    s += '\n                <ipaddr>%s</ipaddr>' % v['ip_address']
                    s += '\n                <netmask>%s</netmask>' % v['netmask']
                    if v['active_on_boot']:
                        s += '\n                <startmode>onboot</startmode>'
                network_lines.append(s)
                network_lines.append('</interface>')
            else:
                # Do nothing for not configured interfaces
                pass
        return network_lines


class SLES102AutoyastFactory(AutoyastFactory):

    def __init__(self, **kwargs):
        AutoyastFactory.__init__(self, **kwargs) 
        self.basepattern = 'base'

    def _getInterfaceName(self, intf, hwaddr):
        return "eth-id-%s" % hwaddr


class Opensuse103AutoyastFactory(AutoyastFactory):

    def __init__(self, **kwargs):
        AutoyastFactory.__init__(self, **kwargs) 
        self.basepattern = 'enhanced_base'

    def _getInterfaceName(self, intf, hwaddr):
        return intf

