#!/usr/bin/env python

#
# Copyright (c) 2008 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import os
import sys
from kusu.core.app import KusuApp

if os.getuid() != 0:
    KusuApp().errorMessage("nonroot_execution\n")
    sys.exit(-1)

from optparse import OptionParser
import popen2
import re
from kusu.core import netutil
import shutil
import kusu.ipfun as ipfun
import kusu.nodefun as nodefun
from kusu.core.db import KusuDB
import subprocess
import tempfile
import socket
from primitive.system.hardware.net import getPhysicalInterfaces
from psycopg2 import IntegrityError
from path import path
from primitive.system.software.dispatcher import Dispatcher
from primitive.svctool.commands import SvcRestartCommand, SvcStartCommand, SvcExistsCommand
from primitive.system.software.probe import OS
from kusu.util.verify import verifyFQDN
from kusu.util.errors import UnableToSaveDataError
from kusu.core.database import DB

try:
    set
except NameError:
    from sets import Set as set

CFG_BROADCAST = 0x1
CFG_IPADDR    = 0x2
CFG_NETMASK   = 0x4
CFG_NETWORK   = 0x8
CFG_DEVICE    = 0x10
CFG_HWADDR    = 0x20
CFG_ONBOOT    = 0x40
EXIT_ONE = 1 
DEFAULT_LSF_CLUSTER_FILE = '/etc/cfm/templates/lsf/default.lsf.cluster'
PCM_GUI_CHANGE_HOSTNAME_SCRIPT = '/opt/kusu/libexec/changehostnameinpcmgui.sh'
DEVICE_LIST = ['eth', 'ib']

db = KusuDB()
if db.driver == 'mysql':
    db_orm = DB(db.driver, 'kusudb') 
else:
    db_orm = DB('postgres', 'kusudb')


class MyOptionParser(OptionParser):
    def print_help(self):
        OptionParser.print_help(self)

        print """
actions:

  hostname    Change host name of installer
  addinstnic  Add network interface to installer node
  delinstnic  Remove existing network interface from installer node
  updinstnic  Update existing network interface on installer node
  hostinfo    Display existing network configuration for host
  dns         Update DNS settings
"""

    def _add_version_option(self):
        self.add_option("-v", "--version",
                        action="version",
                        help="show program's version number and exit")

# ... get current network configuration for this host
gateway = netutil.findGateway()
nics = getPhysicalInterfaces()

def is_device_supported(device):
    """Returns True if the device is supported"""
    
    for supported in DEVICE_LIST:
        if device.startswith(supported):
            return True

    print '\nError: kusu-net-tool does not support \'%s\' device.\n'\
          'You can add/delete/update only ethernet(ethX) and/or infiniband (ibX) devices through this tool.\n' % device
 
    return False   

def get_ngid_by_nodegroup(nodegroup):
    sql = "select ngid from nodegroups where nodegroups.ngname=\"%s\"" % (
        nodegroup)
    
    db.execute(sql)

    row = db.fetchone()
    if row == None:
        return None

    return row[0]


def get_nodegroup_by_ngid(ngid):
    sql = "select ngname from nodegroups where ngid=%d" % (ngid)

    db.execute(sql)

    row = db.fetchone()

    if row == None:
        return ''

    return row[0]


def get_host_name_by_nid(nid):
    sql = "select name from nodes where nid=%d" % (nid)

    db.execute(sql)

    row = db.fetchone()

    if row == None:
        return ''

    return row[0]


def getStartIp(network):
    """Takes a network address (ie. w.x.y.0) and returns the (default) first
    IP address for that network"""

    (a, b, c, d) = network.split('.')

    return '%d.%d.%d.%d' % (int(a), int(b), int(c), int(d) + 1)


def validateDeviceExists(ifname):
    """Returns true if the specified device exists in the system"""
    return ifname in getPhysicalInterfaces().keys()
    

def validateDeviceInUse(ifname, ngid):
    """Returns True if the specified ifname is in use"""

    sql = ("select networks.netid from "
           "networks, nodegroups, ng_has_net, nics "
           "where device='%s' and nics.netid = networks.netid and "
           "ng_has_net.netid=networks.netid and "
           "ng_has_net.ngid=nodegroups.ngid and "
           "nodegroups.ngid=%d" % (ifname, ngid))

    db.execute(sql)

    return db.rowcount > 0

def isInterfaceAssociatedToOtherNodeGroups(netid, action=None):
    """Returns True if the interface has nodegroups (other than installer nodegroup) associated to it."""
    
    ngid = getPrimaryInstallerIds()[0]
    
    sql = ("select distinct nodegroups.ngid, nodegroups.ngname "
           "from ng_has_net, networks, nics, nodes, nodegroups "
           "where nodes.nid = nics.nid and "
           "nics.netid = networks.netid and "
           "networks.netid = ng_has_net.netid and "
           "ng_has_net.ngid = nodegroups.ngid and "
           "networks.netid = %d " % netid)
   
    if 'update' == action:
        # We can update the interface if no node is present in associated nodegroups.
        sql += " and nodes.ngid = nodegroups.ngid "  
 
    if ngid:
        sql += " and ng_has_net.ngid <> %d " % ngid
    
    db.execute(sql)
    
    if db.rowcount == 0:
        return False

    count = db.rowcount 

    row = db.fetchall()

    for ngid, ngname in row:
        if 'unmanaged' !=  ngname:
            print "Error: Please remove network association using kusu-ngedit for the following nodegroup: %s " % ngname
        else:
            if 'update' != action:
                """The network assocation for unmanaged nodegroup is tied to "default" provision network. 
                   Thus we cannot remove this "default" provision network""" 
 
                print "Error: You can not remove the default provision interface."
                return True

            # Print nodes that are in unmanaged nodegroup. 
            sql = "select nodes.name " \
                  "from nodes, nodegroups " \
                  "where nodegroups.ngname='unmanaged' and " \
                  "nodegroups.ngid = nodes.ngid" 
            
            db.execute(sql)

            nodes = db.fetchall()

            nodeList = [ node[0] for node in nodes ]
            print "You need to remove the following nodes before you can update this interface: %s " % str(nodeList)[1:-1]

    return True      

def ifconfig(devname):
    cmd = 'ifconfig %s' % (devname)

    obj = popen2.Popen4(cmd)

    ifconfig_output = []
    for line in obj.fromchild:
        ifconfig_output.append(line)

    retval = obj.wait()

    obj.fromchild.close()
    obj.tochild.close()

    return (retval, ifconfig_output)


def deviceHardwareExists(devname):
    macaddr = None

    (retval, ifconfig_output) = ifconfig(devname)

    if retval != 0:
        # ifconfig failed, so we assume the hardware does not exist
        return (False,)

    for line in ifconfig_output:
        if line.startswith(devname):
            fields = line.split()

            macaddr = fields[4]

        print line,

    return (True, macaddr)


def getMacAddress(device):
    cmd = 'ifconfig %s | grep HWaddr | awk \'{print $5}\'' % (device)

    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)

    macaddr = None

    for line in p.stdout:
        macaddr = line.rstrip()
        break

    retval = p.wait()

    if retval != 0:
        return None

    if macaddr.lower().find('device not found') != -1:
        return None

    return macaddr


def getPrimaryInstallerIds():
    ocs_hostname = getAppGlobals('PrimaryInstaller')
    sql = "select ngid, nid from nodes where name='%s'" % (ocs_hostname)
    
    db.execute(sql)

    row = db.fetchone()
    if not row:
        return None, None

    return row


def display_hostinfo(nid, host, nodegroup):
    """Display OCS network configuration for specified host"""

    print 'Host \"%s\" (Nodegroup \"%s\")' % (host, nodegroup)

    sql = ("select networks.device, nics.ip, networks.subnet, "
           "networks.type, networks.netname, networks.netid, "
           "networks.gateway, networks.usingdhcp from "
           "nics, networks where "
           "nics.netid=networks.netid and "
           "nics.nid=%d order by networks.device" % (nid))

    db.execute(sql)

    for row in db.fetchall():
        print
        print 'Device: %-6s\nDescription: \"%s\"' % (row[0], row[4])
        if row[7]:
            print 'Skipping address and gateway for dynamic interface'
        else:
            bcast = ipfun.getBroadcast(row[1], row[2])
            print ('Inet addr: %s '
                   'Bcast: %s '
                   'Mask: %s\n'
                   'Gateway: %s' % 
                   (row[1], bcast, row[2], row[6]))
        print 'Type:', row[3]
        print 'Network ID:', row[5]


def updateApache():
    """Update Apache HTTPD settings and restart daemon"""

    webserver_dir = Dispatcher.get('webserver_confdir')
    if not webserver_dir:
        print 'Error finding webserver configuration directory.'
        return

    conf_path = path(webserver_dir) / path('kusu.conf')
    genconfigSafeUpdate('kusu-genconfig apache_conf', conf_path)

    # Restart Apache httpd
    restartService('webserver')


def getRepoList():
    sql = "select repos.reponame from repos"

    try:
        db.execute(sql)
    except:
        return []

    return [ row[0] for row in db.fetchall() ]


def getKitList():
    sql = "select kits.rname from kits"

    try:
        db.execute(sql)
    except:
        return []

    return [ row[0] for row in db.fetchall() ]


def addinstnic(device, options):
    """Add a NIC to an installer node"""

    ngid, nid = getPrimaryInstallerIds()
    if not nid:
        print 'Error: unable to find primary installer node'
        return EXIT_ONE

    p_ip = options.ipaddress
    p_netmask = options.netmask
    p_network = ipfun.getNetwork(options.ipaddress, options.netmask)

    # Validate ip/network/netmask
    if not ipfun.onNetwork(p_network, p_netmask, p_ip):
        print ('Error: invalid network settings\n'
               'IP address: %s, Netmask: %s, Network: %s'
               % (p_ip, p_netmask, p_network))
        return EXIT_ONE

    if not options.startip:
        # If the 'startip' is not specified, use the first IP in the network
        p_startip = getStartIp(p_network)
    else:
        p_startip = options.startip

    if not isUniqueStartIp(p_startip):
        print "Error: this network is already in use; please try a different start IP"
        return EXIT_ONE
        
    if not options.gateway:
        # If 'gateway' is not specified, use the first IP in the network
        # (e.g. w.x.y.1)
        p_gateway = p_startip
    else:
        p_gateway = options.gateway

    p_descr = options.descr

    bProvision = False
    if options.provision:
        p_nettype = 'provision'
        bProvision = True
    else:
        p_nettype = 'public'
 
    if not options.macaddr:
        if device in nics and 'mac' in nics[device]:
            p_macaddr = nics[device]['mac']
        else:
            p_macaddr = getMacAddress(device)
    else:
        p_macaddr = options.macaddr

    if device.startswith('ib'):
        p_macaddr=None
    #we only record ethernet MACs,ignore IBs.
    elif len(p_macaddr)!=17:
        p_macaddr=None

    db.beginTransaction()

    sql = ("insert into networks "
           "(network, subnet, device, suffix, gateway, netname, "
           "startip, inc, type) values "
           "('%s', "
           "'%s', "
           "'%s', "
           "'-%s', "
           "'%s', "
           "'%s', "
           "'%s', "
           "1, "
           "'%s');" 
           % (p_network, p_netmask, device, device, p_gateway, 
              p_descr, p_startip, p_nettype))

    try:
        db.execute(sql)
    except IntegrityError:
        db.undoTransaction()
        print 'Error: there is an existing device with this description'
        return EXIT_ONE

    if db.driver == 'mysql':
        sql = "select last_insert_id()"
    else:
        # Default to postgresql
        sql = "select CURRVAL(pg_get_serial_sequence('networks','netid'));"

    db.execute(sql)

    row = db.fetchone()

    netid = row[0]
    if p_macaddr:
        sql = ("insert into nics (netid, nid, mac, ip, boot) "
               "values "
               "(%d, "
               "%d, "
               "'%s', "
               "'%s', true)" % (netid, nid, p_macaddr, p_ip))
    else:
        sql = ("insert into nics (netid, nid, mac, ip, boot) "
               "values "
               "(%d, "
               "%d, "
               "NULL, "
               "'%s', true)" % (netid, nid, p_ip))

    db.execute(sql)

    sql = ("insert into ng_has_net (ngid, netid) values "
           "(%d, %d)" % (ngid, netid))

    db.execute(sql)

    # Add a dummy 'eth0' device for provisioning networks attached to NICs other than eth0 
    if device != 'eth0' and (device.startswith('eth') or device.startswith('bond')) and options.provision:
        addDummyInterface(p_descr, p_network, p_netmask, p_gateway, p_startip, p_nettype)

    db.endTransaction()

    print 'Added NIC %s successfully!' % (device)

    # Update OCS settings and restart daemon(s)
    updateOCS('add', networks=[p_network], rebuildRepos=bProvision,
              device=device, network=p_network, subnet=p_netmask,
              nettype=p_nettype)

    nodegroup = get_nodegroup_by_ngid(ngid)
    host = get_host_name_by_nid(nid)

    display_hostinfo(nid, host, nodegroup)

    # Success!
    return 0


def addDummyInterface(description, network, netmask, gateway, startip, nettype):
    default_nic = 'eth0'
    prov_descr = '%s-eth0' % (description)

    sql = ("insert into networks "
           "(network, subnet, device, suffix, gateway, netname, "
           "startip, inc, type) values "
           "('%s', "
           "'%s', "
           "'%s', "
           "'-%s', "
           "'%s', "
           "'%s', "
           "'%s', "
           "1, "
           "'%s')" 
           % (network, netmask, default_nic, default_nic, gateway, 
              prov_descr, startip, nettype))

    db.execute(sql)


def deleteDummyInterface(description, network, netmask, gateway, startip, nettype):
    default_nic = 'eth0'
    prov_descr = '%s-eth0' % (description)

    sql = ("delete from ng_has_net "
           "where netid in "
           "(select netid from networks "
           "where network = '%s' and subnet = '%s' "
           "and device = '%s' and suffix = '-%s' "
           "and gateway = '%s' and netname = '%s' "
           "and startip = '%s' and type = '%s' )"
           % (network, netmask, default_nic, default_nic, gateway, prov_descr, startip, nettype))
    db.execute(sql)
    
    sql = ("delete from networks "
           "where network = '%s' and subnet = '%s' "
           "and device = '%s' and suffix = '-%s' "
           "and gateway = '%s' and netname = '%s' "
           "and startip = '%s' and type = '%s'"
           % (network, netmask, default_nic, default_nic, gateway, prov_descr, startip, nettype))
    
    db.execute(sql)

def removeDefaultGw(gateway):
    "Returns true if the gateway is default gateway."
    osname, osver, osarch = OS()
    if osname.lower() in ['sles', 'suse', 'opensuse']:
        return removeSLGateway(gateway)
    else:
        return removeRHGateway(gateway)

def removeSLGateway(gateway):
     
    routeCfg = '/etc/sysconfig/network/routes'
    if not path(routeCfg).exists():
        return False 

    fsrc = open(routeCfg)
    fptmp, tmpfile = tempfile.mkstemp('', 'kusu-')
    fptmp = os.fdopen(fptmp, 'w')
    for line in fsrc:
        if not line.startswith('default'):
            fptmp.write(line)            

    fptmp.close()
    fsrc.close()
    shutil.move(routeCfg, routeCfg + '.orig')
    shutil.move(tmpfile, routeCfg) 
               

def removeRHGateway(gateway):

    routeCfg = '/etc/sysconfig/network'
    if not path(routeCfg).exists():
        return False 

    fsrc = open(routeCfg)
    fptmp, tmpfile = tempfile.mkstemp('', 'kusu-')
    fptmp = os.fdopen(fptmp, 'w')
    for line in fsrc:
        if not line.startswith('GATEWAY'):
            fptmp.write(line)

    fptmp.close()
    fsrc.close()
    shutil.move(routeCfg, routeCfg + '.orig')
    shutil.move(tmpfile, routeCfg) 
    return False


def isDefaultGateway(gateway):
    "Returns true if the gateway is default gateway."
    osname, osver, osarch = OS()
    if osname.lower() in ['sles', 'suse', 'opensuse']:
        return defaultSLGateway(gateway)
    else:
        return defaultRHGateway(gateway)

def defaultSLGateway(gateway):
     
    routeCfg = '/etc/sysconfig/network/routes'
    if not path(routeCfg).exists():
        return False 

    fsrc = open(routeCfg)
    for line in fsrc:
        if line.startswith('default'):
            routeList = line.rstrip().split()
            if routeList[1] == gateway: 
                return True

    return False          
               

def defaultRHGateway(gateway):

    routeCfg = '/etc/sysconfig/network'
    if not path(routeCfg).exists():
        return False 

    fsrc = open(routeCfg)
    for line in fsrc:
        if line.startswith('GATEWAY'):
            routeList = line.rstrip().split('=')
            if routeList[1] == gateway: 
                return True

    return False
  

def updateSystemNetworkConfig(netsettings):
    osname, osver, osarch = OS()
    if osname.lower() in ['sles', 'suse', 'opensuse']:
        return updateSLSystemNetworkConfig(netsettings)
    else:
        return updateRHSystemNetworkConfig(netsettings)

def updateSLSystemNetworkConfig(netsettings):
    """Using the settings from 'options', generate SLES system network conf file"""

    network = ipfun.getNetwork(netsettings.ipaddress, netsettings.netmask)
    bcast = ipfun.getBroadcast(netsettings.ipaddress, netsettings.netmask)

    fptmp, tmpfile = tempfile.mkstemp('', 'kusu-')
    srcfile = ''
   
    if netsettings.device.startswith('ib'):
        hwaddr = getMacAddress(netsettings.device)
        if hwaddr:
            srcfile = '/etc/sysconfig/network/ifcfg-eth-id-%s' % hwaddr
        if not path(srcfile).exists():
            srcfile = '/etc/sysconfig/network/ifcfg-%s' % netsettings.device
    else:
        try:
            hwaddr = nics[netsettings.device]['hwaddr'].lower()
        except KeyError:
            if netsettings.macaddr:
                hwaddr = netsettings.macaddr.lower()
        filename = 'ifcfg-eth-id-%s' % hwaddr
        srcfile = '/etc/sysconfig/network/%s' % (filename)

    if netsettings.device.startswith('ib'):
        hwaddr = ''
        dstfile = '/etc/sysconfig/network/ifcfg-%s' % netsettings.device
    elif netsettings.macaddr:
        hwaddr = netsettings.macaddr.lower()
    else:
        try:
            hwaddr = nics[netsettings.device]['hwaddr'].lower()
        except KeyError:
            print 'Error: Could not determine the interface file to be written.'
            return EXIT_ONE 

    if hwaddr:
        dstfile = '/etc/sysconfig/network/ifcfg-eth-id-%s' % hwaddr

    bitmask = 0

    # Check whether source file exists
    bCfgExists = os.path.exists(srcfile)

    if bCfgExists:
        fpsrc = open(srcfile)

        for line in fpsrc:
            if line.startswith('BROADCAST'):
                os.write(fptmp, "BROADCAST='%s'\n" % (bcast))
                bitmask |= CFG_BROADCAST
                continue
            elif line.startswith('IPADDR'):
                os.write(fptmp, "IPADDR='%s'\n" % (netsettings.ipaddress))
                bitmask |= CFG_IPADDR
                continue
            elif line.startswith('NETMASK'):
                os.write(fptmp, "NETMASK='%s'\n" % (netsettings.netmask))
                bitmask |= CFG_NETMASK
                continue
            elif line.startswith('NETWORK'):
                os.write(fptmp, "NETWORK='%s'\n" % (network))
                bitmask |= CFG_NETWORK
                continue
            elif line.startswith('STARTMODE'):
                bitmask |= CFG_ONBOOT
            elif line.startswith('BOOTPROTO'):
                continue

            os.write(fptmp, line)

    # Add any missing netsettings
    if not (bitmask & CFG_BROADCAST):
        os.write(fptmp, "BROADCAST='%s'\n" % (bcast))
    if not (bitmask & CFG_IPADDR):
        os.write(fptmp, "IPADDR='%s'\n" % (netsettings.ipaddress))
    if not (bitmask & CFG_NETMASK):
        os.write(fptmp, "NETMASK='%s'\n" % (netsettings.netmask))
    if not (bitmask & CFG_NETWORK):
        os.write(fptmp, "NETWORK='%s'\n" % (network))
    if not (bitmask & CFG_ONBOOT):
        # Enable any new interface by default
        os.write(fptmp, "STARTMODE='onboot'\n")

    os.write(fptmp, "BOOTPROTO='static'\n")
    os.close(fptmp)

    # Move source file to *.orig
    if bCfgExists:
        fpsrc.close()
        shutil.move(srcfile, srcfile + '.orig')

    shutil.move(tmpfile, dstfile)

    if netsettings.gateway and netsettings.defaultGw:
        return updateSLDefaultGateway(netsettings.gateway)

    return 0


def updateRHSystemNetworkConfig(netsettings):
    """Using the settings from 'options', generate RHEL system network conf file"""

    network = ipfun.getNetwork(netsettings.ipaddress, netsettings.netmask)
    bcast = ipfun.getBroadcast(netsettings.ipaddress, netsettings.netmask)

    fpdst, dstfile = tempfile.mkstemp('', 'kusu-')
    filename = 'ifcfg-%s' % (netsettings.device)
    srcfile = '/etc/sysconfig/network-scripts/%s' % (filename)

    bitmask = 0

    # Check whether file exists
    bCfgExists = os.path.exists(srcfile)

    if bCfgExists:
        fpsrc = open(srcfile)

        for line in fpsrc:
            if line.startswith('BROADCAST'):
                os.write(fpdst, "BROADCAST=%s\n" % (bcast))
                bitmask |= CFG_BROADCAST
                continue
            elif line.startswith('IPADDR'):
                os.write(fpdst, "IPADDR=%s\n" % (netsettings.ipaddress))
                bitmask |= CFG_IPADDR
                continue
            elif line.startswith('NETMASK'):
                os.write(fpdst, "NETMASK=%s\n" % (netsettings.netmask))
                bitmask |= CFG_NETMASK
                continue
            elif line.startswith('NETWORK'):
                os.write(fpdst, "NETWORK=%s\n" % (network))
                bitmask |= CFG_NETWORK
                continue
            elif line.startswith('HWADDR'):
                if netsettings.device.startswith('ib'):
                    continue
 
                bitmask |= CFG_HWADDR
                if netsettings.macaddr:
                    os.write(fpdst, "HWADDR=%s\n" % (netsettings.macaddr.upper()))
                    continue
            elif line.startswith('DEVICE'):
                bitmask |= CFG_DEVICE
            elif line.startswith('ONBOOT'):
                bitmask |= CFG_ONBOOT
            elif line.startswith('BOOTPROTO'):
                continue

            os.write(fpdst, line)

    # Add any missing netsettings
    if not (bitmask & CFG_DEVICE):
        os.write(fpdst, "DEVICE=%s\n" % (netsettings.device))
    if not (bitmask & CFG_HWADDR) and not netsettings.device.startswith('ib'):
        if netsettings.macaddr:
            macaddr = netsettings.macaddr.upper()
        else:
            # Attempt to determine MAC address for device
            macaddr = getMacAddress(netsettings.device)

        if macaddr:
            os.write(fpdst, "HWADDR=%s\n" % (macaddr))
    if not (bitmask & CFG_BROADCAST):
        os.write(fpdst, "BROADCAST=%s\n" % (bcast))
    if not (bitmask & CFG_IPADDR):
        os.write(fpdst, "IPADDR=%s\n" % (netsettings.ipaddress))
    if not (bitmask & CFG_NETMASK):
        os.write(fpdst, "NETMASK=%s\n" % (netsettings.netmask))
    if not (bitmask & CFG_NETWORK):
        os.write(fpdst, "NETWORK=%s\n" % (network))
    if not (bitmask & CFG_ONBOOT):
        # Enable any new interface by default
        os.write(fpdst, "ONBOOT=yes\n")

    os.close(fpdst)

    # Move source file to *.orig
    if bCfgExists:
        fpsrc.close()
        shutil.move(srcfile, srcfile + '.orig')

    shutil.move(dstfile, srcfile)

    if netsettings.gateway and netsettings.defaultGw:
        return updateRHDefaultGateway(netsettings.gateway)

    # Success!
    return 0


def updateSLDefaultGateway(gateway):
    """Update the default gateway."""
    routeCfg = '/etc/sysconfig/network/routes'
    if not path(routeCfg).exists():
        return 1 
   
    flag = False 
    fptmp, tmpfile = tempfile.mkstemp('', 'kusu-')
    fptmp = os.fdopen(fptmp, 'w')
    fsrc = open(routeCfg)
    for line in fsrc:
        if line.startswith('default'):
            routeList = line.split()
            routeList[1] = gateway 
            line = '\t'.join(routeList) + '\n'
            flag = True
        fptmp.write(line)

    if not flag:
        line = "default\t%s\t-\t-\n" % gateway
        fptmp.write(line)

    fptmp.close()
    fsrc.close()
    shutil.move(routeCfg, routeCfg + '.orig')
    shutil.move(tmpfile, routeCfg)

    return 0

def updateRHDefaultGateway(gateway):
    """Update the default gateway."""
    routeCfg = '/etc/sysconfig/network'
    if not path(routeCfg).exists():
        return 1

    flag = False
    fptmp, tmpfile = tempfile.mkstemp('', 'kusu-')
    fptmp = os.fdopen(fptmp, 'w')
    fsrc = open(routeCfg)
    for line in fsrc:
        if line.startswith('GATEWAY'):
            routeList = line.split('=')
            routeList[1] = gateway 
            line = '='.join(routeList) + '\n'
            flag = True
        fptmp.write(line)

    if not flag:
        line = "GATEWAY=%s\n" % gateway
        fptmp.write(line)

    fptmp.close()
    fsrc.close()
    shutil.move(routeCfg, routeCfg + '.orig')
    shutil.move(tmpfile, routeCfg)

    return 0
                                                                
def displayHostNameInfo(sys_hostname):
    ocs_hostname = getAppGlobals('PrimaryInstaller')
    if not ocs_hostname:
        print ('\nError: unable to determine PCM host name.\n\n'
               'Use \'kusu-net-tool hostname <hostname>\' to '
               're-set the primary installer\nhostname.\n')
        return

    if len(sys_hostname.split('.')) > 1:
        public_dns_zone = getAppGlobals('PublicDNSZone')

        if public_dns_zone:
            ocs_hostname += '.' + public_dns_zone

    
    if sys_hostname.lower() != ocs_hostname.lower():
        print ('\nWARNING: Inconsistency between system host name & '
               'PCM host name!\n\n'
               'System host name: %s\n'
               'PCM host name   : %s\n\n'
               'It might be necessary to reboot the installer '
               '(or restart the networking).\n\n'
               'Otherwise, use \'kusu-net-tool hostname <hostname>\' to '
               're-set the\nprimary installer hostname.\n' % (sys_hostname,
               ocs_hostname))
        return

    print sys_hostname


def getInstallerNetworks():
    """Returns a list of all networks the installer resides on"""
    
    ngid = getPrimaryInstallerIds()[0]
    if not ngid:
        return []

    sql = "select networks.network from networks, ng_has_net " \
          "where ng_has_net.ngid=%d and networks.netid=ng_has_net.netid " \
          "and networks.usingdhcp=false" % ngid

    try:
        db.execute(sql)

        return [ network[0] for network in db.fetchall() if network[0] is not None]
    except:
        return []


def updateClusterHostName(new_ocs_hostname, new_ocs_domain=''):
    """Update the OCS cluster representation of the host name"""

    # Before doing anything, check if the requested hostname exceeds
    # the maximum length.
    max_len = db_orm.nodes.c.name.type.length
    if len(new_ocs_hostname) > max_len:
        raise UnableToSaveDataError, \
            'New hostname is too long for the database. ' + \
            'Maximum acceptable length is %d.' % max_len

    db.beginTransaction()
    nid = getPrimaryInstallerIds()[1]

    if not setAppGlobals('PrimaryInstaller', new_ocs_hostname):
        db.undoTransaction()
        return

    # Update public DNS domain
    if new_ocs_domain and not setAppGlobals('PublicDNSZone', new_ocs_domain):
        db.undoTransaction()
        return

    if not nid:
        db.undoTransaction()
        return

    sql = ('update nodes set name=\'%s\' '
           'where nid=%d' % (new_ocs_hostname, nid))

    db.execute(sql)

    db.endTransaction()


def updateRHHostName(hostname):
    fin = open('/etc/sysconfig/network')

    fout, tmpfile = tempfile.mkstemp('', 'kusu-')

    for line in fin.readlines():
        if re.compile("^HOSTNAME=.*").match(line):
            os.write(fout, "HOSTNAME=%s\n" % (hostname))
            continue

        os.write(fout, line)

    os.close(fout)
    fin.close()

    shutil.move(tmpfile, '/etc/sysconfig/network')

def updateSLHostName(hostname):
    fout, tmpfile = tempfile.mkstemp('', 'kusu-')

    os.write(fout, hostname)
    os.close(fout)

    shutil.move(tmpfile, '/etc/HOSTNAME')


def updateSystemHostName(hostname):
    """Updates the system's hostname"""
    
    os.popen("hostname %s" % hostname)


def regenerate_pmpi_lm_config():
    """Regenerate the platform-mpi license manager config files if scalm is installed."""
    if os.system('rpm -q scalm > /dev/null') == 0:
        os.system('kusu-genconfig pmpilicensing_0_1 server > /opt/scali/etc/scalm.conf')
        os.system('kusu-genconfig pmpilicensing_0_1 node > /opt/scali/etc/node.scalm.conf')


def updateLavaLSFConfig(old_name, new_name):
    kits = getKitList()
    kits = [x.lower() for x in kits]
    if 'lava' in kits or 'platform-lava' in kits:
        updateLavaConfig(old_name, new_name)
    if set(['lsf', 'platform-lsf', 'lsf-workgroup']).intersection(set(kits)):
        updateLSFConfig(old_name, new_name)


def updateLavaConfig(old_name, new_name):
    conf_dir = path('/etc/lava/conf')

    print 'Updating Lava hosts file'
    # Remove host in the lava hosts file and regenerate with genconfig
    hosts = conf_dir / 'hosts'
    tmp_hosts = conf_dir / 'hosts.tmp'

    os.system("grep -v %s %s > %s" % (old_name+'.', hosts, tmp_hosts))
    tmp_hosts.rename(hosts)
    os.system("kusu-genconfig lavahosts_1_0 > %s" % hosts)

    print 'Updating Lava cluster file'
    # Remove host in the lava cluster file and regenerate with genconfig
    cluster = conf_dir / 'lsf.cluster.lava'
    tmp_cluster = conf_dir / 'lsf.cluster.lava.tmp'
    os.system("grep -v %s %s > %s" % ('^'+old_name, cluster, tmp_cluster))
    tmp_cluster.rename(cluster)
    os.system("kusu-genconfig lavacluster_1_0 > %s" % cluster)

    print 'Updating Lava conf file'
    # Replace host in the lava conf file
    conf = conf_dir / 'lsf.conf'
    new_conf = conf_dir / 'lsf.conf.tmp'

    conf_file = conf.open()
    new_conf_file = new_conf.open('w')

    for line in conf_file.readlines():
        if line.startswith('LSF_MASTER_LIST='):
            masters = line[16:].strip()
            lst = masters.strip('"\'').split()
            if old_name in lst:
                lst.remove(old_name)
            lst.append(new_name)
            line = 'LSF_MASTER_LIST="%s"\n' % ' '.join(lst)

        elif line.startswith('LSB_MAILSERVER='):
            line = 'LSB_MAILSERVER=SMTP:%s.%s\n' % (new_name, getAppGlobals('DNSZone'))

        elif line.startswith('LSB_MAILTO='):
            line = 'LSB_MAILTO=!U@%s.%s\n' % (new_name, getAppGlobals('DNSZone'))

        new_conf_file.write(line)

    conf_file.close()
    new_conf_file.close()
    new_conf.rename(conf)

    print 'Updating lsbatch hosts file'
    # Replace host in the lsb hosts file
    lsb_conf_dir = conf_dir / 'lsbatch/lava/configdir'
    lsb_hosts = lsb_conf_dir / 'lsb.hosts'
    tmp_lsb_hosts = lsb_conf_dir / 'lsb.hosts.tmp'

    lsb_hosts_file = lsb_hosts.open()
    tmp_lsb_hosts_file = tmp_lsb_hosts.open('w')
    for line in lsb_hosts_file.readlines():
        if line.startswith(old_name):
            line = new_name + line[len(old_name):]

        tmp_lsb_hosts_file.write(line)

    lsb_hosts_file.close()
    tmp_lsb_hosts_file.close()
    tmp_lsb_hosts.rename(lsb_hosts)

def updateLSFConfig(old_name, new_name):
    # TODO: Need to add LSF regeneration similar to Lava after
    # the fix for respecting local changes is brought into trunk.

    print 'Updating LSF template files'
    # Update hostSection for installer node 
    cmd = "sed --in-place 's/^%s/%s/' %s " % (old_name, new_name, DEFAULT_LSF_CLUSTER_FILE)
    os.system(cmd)

def updateNPMConfig(new_ocs_hostname):

    if not os.path.exists('/opt/lsf/conf/npm/npm.conf'):
        return

    f = open('/opt/lsf/conf/npm/npm.conf', 'r')
    new_npm_conf = []
    for line in f.readlines():
        if line.startswith('NPM_HOST='):
             line = 'NPM_HOST=' + new_ocs_hostname + '\n'
        new_npm_conf.append(line)
    f.close()

    f = open('/opt/lsf/conf/npm/npm.conf', 'w')
    f.writelines(new_npm_conf)
    f.close()

    restartService('npm')


def action_hostname(hostname):
    """Handler for 'hostname' action"""

    cluster_hostname = getAppGlobals('PrimaryInstaller')
    sys_hostname = socket.gethostname()
    if not sys_hostname:
        print ('\nError: unable to retrieve system host name.\n\n'
               'Please check system networking configuration.\n')
        return

    if not (hostname):
        displayHostNameInfo(sys_hostname)
        return
    
    # Split the host name into component parts (hostname + domain)
    if hostname.find('.') != -1:
        (new_ocs_hostname, new_ocs_domain) = hostname.split('.', 1)
    else:
        # Host name is not fully-qualified, remove DNS domain
        new_ocs_hostname = hostname
        new_ocs_domain = ''

    if nodefun.NodeFun().validateNode(new_ocs_hostname):
        print "\nError: Hostname '%s' is already in use in this cluster.\nPlease use a different hostname.\n" % new_ocs_hostname
        return 

    # Just as it says... update the OCS cluster host name
    print 'Updating host name of primary installer'
    try:
        updateClusterHostName(new_ocs_hostname, new_ocs_domain)
    except Exception, e:
        print str(e)
        return

    print 'Primary installer host name is now \"%s\"' % (new_ocs_hostname)

    # Re-generate configuration files and restart daemon(s)
    networks = getInstallerNetworks()
    updateOCS('update', networks=networks)
    
    new_ocs_fqdn = new_ocs_hostname + '.' + (new_ocs_domain or getAppGlobals('PublicDNSZone'))

    # Update RH or SL configuration file
    osname, osver, osarch = OS()
    if osname.lower() in ['sles', 'suse', 'opensuse']:
        updateSLHostName(new_ocs_fqdn)
    else:
        updateRHHostName(new_ocs_fqdn)
    
    updateSystemHostName(new_ocs_fqdn)

    updateLavaLSFConfig(cluster_hostname, new_ocs_hostname)
 
    updatePCMGUIConfig(hostname)

    updateNPMConfig(new_ocs_hostname)

    regenerate_pmpi_lm_config()

    print '\nPlease run \'kusu-addhost -u\' to update the configuration for installed kits.'
    print '\nWARNING: it is necessary to reboot or restart networking!\n'


def action_hostinfo(hostname=None):
    """Handler for 'hostinfo' action"""

    ngid = getPrimaryInstallerIds()[0]
    if not ngid:
        print 'Error: unable to find primary installer node group'
        return 2

    if hostname:
        sql = 'select nodes.nid, nodes.name, nodegroups.ngname from ' \
              'nodes, nodegroups where ' \
              'nodegroups.ngid=nodes.ngid and ' \
              'nodes.name=\'%s\'' % hostname
    else:
        # Default to displaying the first node in the installer nodegroup
        sql = 'select nodes.nid, nodes.name, nodegroups.ngname from ' \
              'nodes, nodegroups where nodegroups.ngid=nodes.ngid and ' \
              'nodes.ngid = %d limit 1' % ngid

    db.execute(sql)

    row = db.fetchone()

    if not row:
        print 'Error: host \'%s\' not found' % hostname
        return

    (nid, host, nodegroup) = row

    display_hostinfo(nid, host, nodegroup)


def substituteIpNetmask(device, options):
    """ Attempts to obtain missing settings from the existing system network configuration """
    try:
        if not options.ipaddress and 'ip' in nics[device]:
            options.ipaddress = nics[device]['ip']
    
        if not options.netmask and 'subnet' in nics[device]:
            options.netmask = nics[device]['subnet']
    except KeyError:
        pass

    return options


def isUniqueIpAddress(ipaddress, nicsid=None):
    sql = "select nicsid from nics where ip = '%s'" % ipaddress
    if nicsid:
        sql += " and nicsid <> %d" % nicsid

    db.execute(sql)
    return db.rowcount == 0


def isUniqueStartIp(startip, netids=[]):
    sql = "select netid from networks where startip = '%s'" % startip
    for netid in netids:
        if netid:
            sql += " and netid <> %d" % netid
       
    db.execute(sql)
    return db.rowcount == 0


def validateCmdLineParameters(device, options, caller=''):

    if options.public and options.provision:
        print 'Error: "--provision" and "--public" can not be used simultaneously'
        return EXIT_ONE

    if not device in nics and caller=='add' and not options.force:
            # Device is not known to the system, we need the --force flag
            # to allow configuration
            print 'Warning: device %s is not configured with the OS.\n' \
                  'Use --force option to force installation' % device
            return EXIT_ONE
    
    # At the absolute minimum, a network interface needs an IP address
    # and a netmask.  From this, we can deduce the other remaining
    # parameters.
    if caller=='add' and not options.ipaddress:
        print 'Error: missing --ip-address parameter; the IP address could not be retrieved from the system'
        return EXIT_ONE

    if caller=='add' and not options.netmask:
        print 'Error: missing --netmask parameter; the netmask could not be retrieved from the system'
        return EXIT_ONE
    
    if options.ipaddress and ipfun.validIP(options.ipaddress) != 1:
        print 'Error: invalid IP address'
        return EXIT_ONE
        
    if options.netmask and ipfun.validIP(options.netmask) != 1:
        print 'Error: invalid netmask'
        return EXIT_ONE
    
    if options.startip and ipfun.validIP(options.startip) != 1:
        print 'Error: invalid starting IP'
        return EXIT_ONE
   
    if options.gateway and ipfun.validIP(options.gateway) != 1:
        print 'Error: invalid gateway'
 
    if caller=='add' and not options.descr:
        print 'Error: missing --desc parameter'
        return EXIT_ONE  
    
    return 0


def action_addinstnic(device, options):
    """Handler for 'addinstnic' action"""

    ngid = getPrimaryInstallerIds()[0]
    if not ngid:
        print 'Error: unable to find primary installer node group'
        return EXIT_ONE

    if options.default and options.provision:
        print 'Error: You can not use option --default with --provision.'
        return EXIT_ONE

    if options.default and not options.gateway:
        print "Warning: No gateway is provided, cannot set default gateway."
 
    if validateDeviceInUse(device, ngid):
        print 'Error: device %s is already configured on this host' % (device)
        return EXIT_ONE
    
    device_exists = validateDeviceExists(device)
    if not device_exists and not options.force:
        print 'Error: device %s does not exist on this host; use --force to override' % (device)
        return EXIT_ONE
    elif not device.startswith('ib') and not device_exists and not options.macaddr:
        print 'Error: device %s does not exist on this host; provide a mac address for it.' % (device)
        return EXIT_ONE
    
    options = substituteIpNetmask(device, options)
   
    retval = validateCmdLineParameters(device, options, caller='add')
    if retval != 0:
        return retval
    
    if not isUniqueIpAddress(options.ipaddress):
        print "Error: this IP address is already used"
        return EXIT_ONE

    network = ipfun.getNetwork(options.ipaddress, options.netmask)
    # Validate ip/network/netmask    
    if not ipfun.onNetwork(network, options.netmask, options.ipaddress):
        print ('Error: invalid network settings\n'
               'IP address: %s, Netmask: %s, Network: %s'
               % (options.ipaddress, options.netmask, network))
        return EXIT_ONE

    if options.gateway and not ipfun.onNetwork(network, options.netmask, options.gateway):
        print ('Error: invalid network configuration!\n\n'
               'Gateway %s is not on network %s/%s\n'
               % (options.gateway, network, options.netmask))
        return EXIT_ONE

    # Add network interface to OCS
    retval = addinstnic(device, options)
    if retval != 0:
        return EXIT_ONE

    # Update/create system network configuration
    netset = OCSNetworkSettings(device)
    netset.ipaddress = options.ipaddress
    netset.netmask = options.netmask
    netset.macaddr = options.macaddr
    netset.gateway = options.gateway
    netset.defaultGw = options.default

    if updateSystemNetworkConfig(netset) != 0:
        print 'Error: unable to update network configuration'
        print 'Please update system network configuration manually'
        return EXIT_ONE

    print '\nPlease run \'kusu-addhost -u\' to update the configuration for installed kits.'
    print '\nWARNING: it is necessary to reboot or restart networking!\n'


def action_delinstnic(device, options):
    """Handler for 'delinstnic' action"""

    removeGateway = False
    ngid, nid = getPrimaryInstallerIds()

    if not nid:
        print "Error: unable to find primary installer node."
        return EXIT_ONE

    sql = ('select nodes.name, networks.netid, networks.network, '
           'networks.subnet, networks.type, networks.gateway, '
           'networks.startip, networks.netname from '
           'networks,ng_has_net,nodes,nics where '
           'networks.netid=ng_has_net.netid and '
           'ng_has_net.ngid=%d and '
           'networks.device=\'%s\' and '
           'nodes.nid=%d and '
           'nodes.nid=nics.nid and '
           'nics.netid=networks.netid' % (ngid, device, nid))

    db.execute(sql)

    row = db.fetchone()

    if not row:
        print ('Error: Network interface \"%s\" '
               'does not exist on this Installer Node.' % (device))
        return EXIT_ONE

    (hostname, netid, network, subnet, nettype, gateway, startip, netname) = row

    if nettype == 'public' and isDefaultGateway(gateway): 
        print "Warning: Default Gateway may not be reachable after removing this \"%s\" interface." % (device)
        removeGateway = True

    if not options.force:
        # Confirm that the user actually wants to remove the specified
        # network device
        print ('Are you sure you wish to remove device \"%s\" '
               'from host \"%s\" [N/y]?' % (device, hostname)),

        resp = raw_input("")

        if not resp in [ 'y', 'Y' ]:
            print 'Aborting delete NIC action.'
            return

    if  isInterfaceAssociatedToOtherNodeGroups(netid):
        print "Error: Device \"%s\" cannot be removed as other nodegroups are associated to it. " % (device)
        return EXIT_ONE

    # Delete the interface
    try:
        db.beginTransaction()
        # Delete from 'ng_has_net' table
        sql = ('delete from ng_has_net '
               'where ngid=%d and netid=%d' % (ngid, netid))
        db.execute(sql)
    
        # Delete from 'nics' table
        sql = 'delete from nics where nid=%d and netid=%d' % (nid, netid)
        db.execute(sql)
     
        # Delete from 'networks' table
        sql = 'delete from networks where netid=%d' % (netid)
        db.execute(sql)

        deleteDummyInterface(netname, network, subnet, gateway, startip, nettype)
        db.endTransaction()
    except Exception,e:
        db.undoTransaction()
        print 'Error updating database, NIC was not deleted: %s ' % e
        return

    rebuildRepos = False
    if nettype == 'provision':
        # Provisioning network being removed, repos must be rebuilt
        rebuildRepos=True

    updateOCS('remove', networks=[network], rebuildRepos=rebuildRepos,
               device=device, network=network, subnet=subnet, nettype=nettype)

    # Update the default gateway.   
    if removeGateway:
        removeDefaultGw(gateway)
 
    #Update network configuration
    print '\nDevice \"%s\" successfully removed!\n'\
          'Please run \'kusu-addhost -u\' to update the configuration for installed kits.' % (device)
    print '\nWARNING: it is necessary to reboot or restart networking!\n'

class OCSNetworkSettings(object):
    """Container class for network settings"""
    def __init__(self, device):
        self.device = device


def getCurrentNICSettings(nid, device):
    """Get current network settings for (nic, device)"""

    try:
        sql = ("select nics.mac, nics.ip, nics.netid, nics.boot, "
              "networks.network, networks.subnet, networks.suffix, "
              "networks.gateway, networks.netname, networks.startip, "
              "networks.type, nics.nicsid from "
              "nics, networks where nics.nid='%s' and networks.device='%s' "
              "and nics.netid=networks.netid" % (nid, device))

        db.execute(sql)

        row = db.fetchone()

        netset = OCSNetworkSettings(device)

        (netset.macaddr, netset.ipaddress, netset.netid, netset.boot,
         netset.network, netset.netmask, netset.suffix, netset.gateway,
         netset.netname, netset.startip, netset.type, netset.nicsid) = row

        return netset
    except:
        return None


def getAssociatedNetworkId(network, netmask, gateway, netname, startIp):
    """Returns the ID of the associated provision network (same network, different device)."""

    sql = ("select netid from networks where "
           "subnet='%s' and network='%s' and device='eth0' and gateway='%s' and netname='%s-eth0' and type='provision' and startip='%s'"
           % (netmask, network, gateway, netname, startIp))

    try:
        db.execute(sql)

        return db.fetchone()
    except:
        return None


def updateNetworksTable(netid, p_network, p_netmask, p_gateway, p_startip, parameters):
    """Update 'networks' table with new settings"""

    sql = ("update networks set network='%s', subnet='%s', gateway='%s', "
           "startip='%s'" % (p_network, p_netmask, p_gateway, p_startip))

    if 'descr' in parameters:
        sql += ', netname=\'%s\'' % (parameters['descr'])

    if 'type' in parameters:
        sql += ', type=\'%s\'' % (parameters['type'])

    sql += ' where netid=%d' % (netid)

    # print sql

    db.execute(sql)


def updateReposTable(nid):
    """
    Updates repos table with settings from networks table.  'nid' is
    the node ID of the primary installer.
    """

    # Get list of IPs from installer node
    sql = ('select nics.ip from nodes,nics,networks where '
           'nodes.nid=%d and nodes.nid=nics.nid and '
           'nics.netid=networks.netid and networks.type="provision"'
           % (nid))

    db.execute(sql)

    # Get list of all IPs for primary installer provisioning network
    # interfaces.
    installers = [ row[0] for row in db.fetchall() ]

    sql = 'update repos set installers=\'' + ','.join(installers) + '\''

    db.execute(sql)


def action_updinstnic(device, options):
    """Handler for 'updinstnic' action"""
    
    ngid, nid = getPrimaryInstallerIds()
    if not ngid:
        print 'Error: unable to find primary installer node group'
        return EXIT_ONE
    
    if not nid:
        print 'Error: unable to get node ID of installer node'
        return EXIT_ONE
    
    if not validateDeviceInUse(device, ngid):
        print 'Error: device %s was not yet added to this host' % (device)
        return EXIT_ONE
    
    options = substituteIpNetmask(device, options)
    
     # Get current settings OCS database for (nid, device)
    netSettings = getCurrentNICSettings(nid, device)
    
    if not netSettings:
        print 'Error: unable to get network settings for device %s' % (device)
        return EXIT_ONE
       
    retval = validateCmdLineParameters(device, options, caller='upd')
    if retval != 0:
        return retval

    if isInterfaceAssociatedToOtherNodeGroups(netSettings.netid, action='update'):
        print "Error: Device \"%s\" cannot be updated as other nodegroups are associated to it. " % (device)
        return EXIT_ONE

    # Apply any overrides from the command-line
    p_ipaddress = options.ipaddress or netSettings.ipaddress
    p_netmask = options.netmask or netSettings.netmask
    p_network = ipfun.getNetwork(p_ipaddress, p_netmask)
    # If gateway was not specified, use existing gateway
    p_gateway = options.gateway or netSettings.gateway

    if not options.startip:
        if ipfun.onNetwork(p_network, p_netmask, netSettings.startip):
            p_startip = netSettings.startip
        else:
            p_startip = getStartIp(p_network)
    else:
        p_startip = options.startip
    
    # Validate ip/network/netmask    
    if not ipfun.onNetwork(p_network, p_netmask, p_startip):
        print ('Error: invalid network settings\n'
               'IP address: %s, Netmask: %s, Network: %s'
               % (p_ip, p_netmask, p_network))
        return EXIT_ONE

    if device.startswith('ib'):
        p_macaddr = ''
    else:
        p_macaddr = options.macaddr or netSettings.macaddr 
    
    p_descr = options.descr or netSettings.netname

    p_type = netSettings.type
    if options.provision:
        p_type = 'provision'
    elif options.public:
        p_type = 'public'

    # Flag to Network type has changed
    bTypeChanged = (netSettings.type != p_type)

    if not ipfun.onNetwork(p_network, p_netmask, p_ipaddress):
        print ('Error: invalid network configuration!\n\n'
               ' IP address: %s, Network: %s, and Netmask: %s\n'
               % (p_ipaddress, p_network, p_netmask))
        return EXIT_ONE 

    if not ipfun.onNetwork(p_network, p_netmask, p_gateway):
        print ('Error: invalid network configuration!\n\n'
               'Gateway %s is not on network %s/%s\n'
               % (p_gateway, p_network, p_netmask))
        return EXIT_ONE

    if not ipfun.onNetwork(p_network, p_netmask, p_startip):
        print ('Error: invalid network configuration!\n\n'
               'Starting IP %s is not on network %s/%s\n'
               % (p_startip, p_network, p_netmask))
        return EXIT_ONE

    if not isUniqueIpAddress(p_ipaddress, netSettings.nicsid):
        print "Error: this IP address is already in use"
        return EXIT_ONE
    
    # Get associated network (same network, different device for provisioning networks)
    assd_network = getAssociatedNetworkId(netSettings.network,
                                          netSettings.netmask,
                                          netSettings.gateway,
                                          netSettings.netname,
                                          netSettings.startip)

    if not isUniqueStartIp(p_startip, [netSettings.netid, assd_network]):
        print "Error: this network is already in use; please try a different start IP"
        return EXIT_ONE

    print '\nNetwork settings for Network ID %d:\n' % (netSettings.netid)
    print '           IP address:', p_ipaddress
    print '              Network:', p_network
    print '              Netmask:', p_netmask
    print '              Gateway:', p_gateway
    print '  Starting IP address:', p_startip
    print '          MAC address:', p_macaddr
    print '          Description:', p_descr
    print '                 Type:', p_type
    print

    db.beginTransaction()

    try:
        # Update 'nics' table
        sql = ("update nics set mac='%s', ip='%s' where nid=%d and netid=%d"
               % (p_macaddr, p_ipaddress, nid, netSettings.netid))

        # print sql

        db.execute(sql)

        # Initialize dict containing settings to be updated
        updatedArgs = {}

        if bTypeChanged:
            # Only apply this change if the setting has changed from
            # the current value.
            updatedArgs = { 'type': p_type }

        if options.descr:
            # Do not bother rewriting the description if it hasn't changed
            updatedArgs['descr'] = p_descr

        # Update 'networks' table
        updateNetworksTable(netSettings.netid, p_network, p_netmask,
                            p_gateway, p_startip, updatedArgs)

        if netSettings.type == 'provision':
            if assd_network:
                updatedArgs['descr'] = '%s-eth0' % p_descr
                updateNetworksTable(assd_network, p_network, p_netmask,
                                    p_gateway, p_startip, updatedArgs)

        if bTypeChanged and p_type == 'provision' and (device.startswith('eth') or device.startswith('bond')):
            addDummyInterface(p_descr, p_network, p_netmask, p_gateway, p_startip, 'provision')
            
        # Updates 'repos' table
        updateReposTable(nid)
    
        print 'Network settings updated successfully!'
    
    except IntegrityError:
        db.undoTransaction()
        print 'Error: there is an existing device with this description'
        return EXIT_ONE
    
    except:
        print 'Error updating network settings!'
        db.undoTransaction()
        return EXIT_ONE

    db.endTransaction()

    updateOCS('update', networks=[p_network], rebuildRepos=bTypeChanged)

    if isExistingService('pmc'):
        restartService('pmc')
    if isExistingService('npm'):
        restartService('npm')

    netset = OCSNetworkSettings(device)
    netset.ipaddress = p_ipaddress
    netset.netmask = p_netmask
    netset.macaddr = p_macaddr
    netset.defaultGw = False
    netset.gateway = ''

    if p_gateway != netSettings.gateway and p_type == 'public':
        if isDefaultGateway(netSettings.gateway):
            netset.gateway = p_gateway
            netset.defaultGw = True

    if updateSystemNetworkConfig(netset) != 0:
        print 'Error: unable to update network configuration'
        print 'Please update system network configuration manually'
        return EXIT_ONE

    print '\nPlease run \'kusu-addhost -u\' to update the configuration for installed kits.'
    print '\nWARNING: it is necessary to reboot or restart networking!\n'

    return 0


class NetworkSettings(object):
    def __init__(self):
        self.network = ''
        self.netmask = ''
        self.suffix = ''
        self.gateway = ''
        self.descr = ''
        self.startip = ''
        self.nettype = ''


def getNetworkSettings(netid):
    try:
        netid = int(netid)
    except TypeError, e:
        print 'Error: network ID \"%s\" is invalid' % (netid)
        return EXIT_ONE

    # Retrieve existing settings for network
    sql = ("select network, subnet, suffix, gateway, netname, "
           "startip, type from networks where netid=%d" % (netid))

    db.execute(sql)

    row = db.fetchone()

    if not row:
        # Invalid network ID
        return None

    obj = NetworkSettings()

    obj.netid = netid
    obj.network = row[0]
    obj.netmask = row[1]
    obj.suffix = row[2]
    obj.gateway = row[3]
    obj.descr = row[4]
    obj.startip = row[5]
    obj.nettype = row[6]

    return obj


def displayNetworkSettings(netset):
    print '  Network ID:', netset.netid
    print '     Network:', netset.network
    print '     Netmask:', netset.netmask
    print '      Suffix:', netset.suffix
    print '     Gateway:', netset.gateway
    print ' Description:', netset.descr
    print '    Start IP:', netset.startip
    print 'Network type:', netset.nettype
    print


def getAppGlobals(kname):
    """Read value from appglobals table"""

    try:
        sql = 'select kvalue from appglobals where kname=\'%s\'' % (kname)

        db.execute(sql)

        row = db.fetchone()

        if not row:
            return None

        return row[0]
    except:
        return None


def setAppGlobals(kname, kvalue, ngid=None):
    """Write value to appglobals table"""

    try:
        sql = ('update appglobals set kvalue=\'%s\' '
               'where kname=\'%s\'' % (kvalue, kname))

        if ngid:
            sql += ' and ngid=%d' % (ngid)

        db.execute(sql)
    except:
        return False

    return True

def getProvisioningInterfaces():
    """Returns a list of network interfaces used for provisioning"""

    installer = getAppGlobals('PrimaryInstaller')
    if not installer:
        print 'Error: unable to determine host name of primary installer'
        return []

    sql = ('select networks.device '
             'from networks,nics,nodes where nodes.nid=nics.nid and '
             'nics.netid=networks.netid and not networks.usingdhcp '
             'and nodes.name="%s" and networks.type="provision"' % installer)

    db.execute(sql)

    return [ row[0] for row in db.fetchall() ]


def updateDhcpd():
    """Update dhcpd configuration"""

    if not int(getAppGlobals('InstallerServeDHCP')):
        return
 
    prov_nics = getProvisioningInterfaces()
    dhcpd_arg = Dispatcher.get('dhcpd_interface_arg')

    if not prov_nics:
        print "There is no provision interface. Please add a provision interface for dhcpd to work."
        return

    try:
        # Open source file
        fp = open('/etc/sysconfig/dhcpd')
    except IOError, e:
        # Unable to open source file
        fp = None

    try:
        fout, tmpfile = tempfile.mkstemp('', 'kusu-dhcpd-')
    except IOError, e:
        print "Error: unable to open tempfile for writing"
        print "dhcpd configuration will not be updated"
        return

    bFound = False
    # Update existing file
    for line in fp.readlines():
        if line.startswith(dhcpd_arg):
            os.write(fout, dhcpd_arg + '="' + ' '.join(prov_nics) + '"\n')
            bFound = True
        else:
            os.write(fout, line)

    if not bFound:
        # If dhcpd_arg entry was not found, add one
        os.write(fout, dhcpd_arg + '="' + " ".join(prov_nics) + '"\n')

    if fp:
        fp.close()

    os.close(fout)

    # Move updated file to original
    shutil.move(tmpfile, '/etc/sysconfig/dhcpd')

    # Rewrite dhcpd configuration
    genconfigSafeUpdate('kusu-genconfig dhcpd', '/etc/dhcpd.conf')

    # Restart dhcpd
    restartService('dhcpd')


def dns_action_info(argv):
    """Display current DNS settings"""

    # Display DNS domain information
    print '\n Public DNS domain:', getAppGlobals('PublicDNSZone') or '<undefined>'
    print 'Private DNS domain:', getAppGlobals('DNSZone') + '\n'

    sql = ('select kname, kvalue from appglobals '
           'where kname in ("dns1", "dns2", "dns3") order by kname')

    db.execute(sql)

    dns_servers = [ (row[0], row[1]) for row in db.fetchall() ]

    if not dns_servers:
        print 'No DNS servers currently defined'
        return 1

    print 'Current DNS servers (in search order):'

    for i, ip in dns_servers:
        print '   %s (%s)' % (ip, i)

    print

    return 0


def startService(svcname, silent=False):
    return service('start', svcname, silent)

def restartService(svcname, silent=False):
    return service('restart', svcname, silent)

def isExistingService(svcname, silent=True):
    return service('exists', svcname, silent)

def service(action, svcname, silent):
    svcname = Dispatcher.get(svcname, default=svcname)

    action_dict = {'start': (SvcStartCommand, 'Starting'),
                   'restart': (SvcRestartCommand, 'Restarting'),
                   'exists': (SvcExistsCommand, 'Testing')
                  }

    try:
        svcCmd, str = action_dict[action]
    except KeyError:
        print 'Command %s not found for %s service' % (action, svcname)
        return 1
    
    if not silent:
        print '%s %s...' % (str, svcname)

    cmd = svcCmd(service=svcname)
    result, retvals = cmd.execute()

    if not silent:
        if result:
            print retvals[0]
        else:
            print retvals[2]

    return result


def genconfigSafeUpdate(genconfig_cmd, updFile):
    newFile = '%s.new' % (updFile)

    genconfig_cmd += ' >%s' % (newFile)

    p = subprocess.Popen(genconfig_cmd, shell=True)
    retval = p.wait()

    if retval == 0:
        shutil.move(newFile, updFile)
        return True

    os.unlink(updFile)
    
    return False


def updateSSH():
    """Update SSH client settings (not SSH daemon restart req'd)"""

    print 'Updating SSH client configuration...'

    genconfigSafeUpdate('kusu-genconfig ssh', '/etc/ssh/ssh_config')


def updateHosts():
    """Update /etc/hosts"""

    print 'Updating /etc/hosts...'

    genconfigSafeUpdate('kusu-genconfig hosts', '/etc/hosts')


def updateInetd():
    """Restart xinetd (for TFTP)"""

    restartService('xinetd')


def updateRepos():
    """
    Rebuild repos to rewrite configuration files, etc.  This should
    only be called if the provision interface(s) have changed as it is
    very time consuming.
    """

    repos = getRepoList()

    print 'Updating repos, please wait...'

    for reponame in repos:
        cmd = 'kusu-repoman -u -r \"%s\"' % (reponame)

        p = subprocess.Popen(cmd, shell=True)
        retval = p.wait()

        if retval != 0:
            print ('Error: kusu-repoman failed to update repo \"%s\"'
                   % (reponame))


def isFirewallRunning():
    cmd = '%s >/dev/null 2>&1' % Dispatcher.get('firewall_status')

    # Assume failure if unable to determine iptables status
    retval = 1

    try:
        p = subprocess.Popen(cmd, shell=True)
        retval = p.wait()
    except OSError, e:
        pass

    return (retval == 0)


def updIptablesRulesForPublicInterface(action, iface):
    # Default list of open ports.  Ultimately, this should be a template
    # the user can edit themselves
      
    openPorts = [(22, 'tcp'), (53, 'tcp'), (53, 'udp'), (80, 'tcp'), 
                  (443, 'tcp')]

    if isExistingService('pmc'):
        openPorts.append((8080, 'tcp'))

    rules = []

    # Set 'iptables' action (either append (-A) or delete (-I))
    iptables_action = '-A'
    if action == 'remove':
        iptables_action = '-D'

    for port, proto in openPorts:
        cmd = ('%s INPUT -i %s -m state --state NEW -p %s '
               '--dport %s -j ACCEPT' % (iptables_action, iface, proto, port))

        rules.append(cmd)

    cmd = '%s INPUT -i %s -j REJECT' % (iptables_action, iface)

    rules.append(cmd)

    return 0, rules


def writeDefaultSuSEfirewallRules(fout):
    os.write(fout, 'FW_ROUTE="yes"\n')
    os.write(fout, 'FW_MASQUERADE="yes"\n')
    os.write(fout, 'FW_PROTECT_FROM_INT="no"\n')
    os.write(fout, 'FW_MASQ_DEV="$FW_DEV_EXT"\n')
    os.write(fout, 'FW_MASQ_NETS="0/0"\n')
    os.write(fout, 'FW_SERVICES_EXT_TCP="22 53 80 443"\n')
    os.write(fout, 'FW_SERVICES_EXT_UDP="53"\n')
    os.write(fout, 'FW_TRUSTED_NETS="127.0.0.1 0/0,icmp"\n')


def updSuSEfirewallRules(action, iface, type='private'):
    file = '/etc/sysconfig/SuSEfirewall2'
    file = Dispatcher.get('firewall_config_file', default=file)

    if type == 'public':
        arg = 'FW_DEV_EXT'
    else:
        arg = 'FW_DEV_INT'

    try: # Open source file
        fp = open(file)
        shutil.move(file, file + '.bak')
    except IOError, e:
        fp = None

    try:
        fout, tmpfile = tempfile.mkstemp('', 'kusu-SuSEfirewall2-')
    except IOError, e:
        print "Error: unable to open tempfile for writing"
        print "SUSEFirewall2 configuration will not be updated"
        return 1

    bFound = False
    if fp:
        # Update existing file
        for line in fp.readlines():
            if line.startswith(arg):
                try:
                    str = line.strip().split('=',1)[1]
                except IndexError:
                    os.write(fout, line)
                    continue

                lst = str.strip('"\'').split(' ')
                if action == 'add':
                    lst.append(iface)
                elif action == 'remove':
                    try:
                        lst.remove(iface)
                    except ValueError:
                        pass

                dev_line = '%s="%s"' % (arg, ' '.join(lst))
                os.write(fout, dev_line + '\n')
                bFound = True

            else:
                os.write(fout, line)
        fp.close()

    elif action == 'remove':
        return 0
    else:
        writeDefaultSuSEfirewallRules(fout)

    if not bFound and action == 'add':
        # If entry was not written, add one
        os.write(fout,  '%s="%s"\n' % (arg, iface))

    os.close(fout)
    # Move updated file to original
    shutil.move(tmpfile, file)
    return 0


def updIptablesRulesForPrivateInterface(action, iface):
    # Adding a private/provisioning network interface

    # Get public networks for host
    pubnets = getPublicNetworks()

    # Get default gateway for system
    gwipaddr = netutil.findGateway()

    if not gwipaddr:
        print 'Error: default gateway not defined for this host'

        return 1, None

    # Get network status for host
    sysnets = getPhysicalInterfaces()

    nets = []
    for dev, net, subnet, dhcp in pubnets:
        if net is None:
            try:
                net = sysnets[dev]['ip']
                subnet = sysnets[dev]['netmask']
            except KeyError:
                continue
        nets.append((dev, net, subnet))

    # Determine the default public interface for this host.  This is required
    # for adding IP forwarding rules from the private interface
    (pubiface, network, subnet) = getDefaultPublicInterface(nets, gwipaddr)

    if not pubiface:
        print
        print ('Error: default gateway %s is not on any defined public '
               'network' % (gwipaddr))
        print
        print 'Public networks as defined in PCM:'
        print

        for device, network, subnet, usingdhcp in pubnets:
            print '\t%s/%s (%s)' % (network or 'DHCP', subnet or 'DHCP', device)

        print
        print 'Networking appears to be misconfigured.  Please remedy the '
        print 'inconsistency and retry the operation.'
        print

        return 1, None

    iptables_action = '-A'
    if action == 'remove':
        iptables_action = '-D'

    rules = []

    cmd = ('%s FORWARD -i %s -o %s -m state '
           '--state RELATED,ESTABLISHED -j ACCEPT' % (iptables_action,
                                                      iface, pubiface))

    rules.append(cmd)

    cmd = '%s FORWARD -i %s -j ACCEPT' % (iptables_action, iface)

    rules.append(cmd)

    cmd = '%s INPUT -i %s -j ACCEPT' % (iptables_action, iface)

    rules.append(cmd)

    return 0, rules


def getPublicNetworks():
    """
    Query Kusu database for list of (device, network, subnet) tuples
    of public networks
    """
    
    ngid = getPrimaryInstallerIds()[0]
    if not ngid:
        return []

    db = KusuDB()

    db.connect('kusudb', 'apache')

    db.execute('select device, network, subnet, usingdhcp '
               'from ng_has_net, networks '
               'where ng_has_net.netid=networks.netid and '
               'ng_has_net.ngid=%d and networks.type=\'public\'' % ngid)

    return [ row for row in db.fetchall() ]


def getDefaultPublicInterface(pubnets, gwipaddr):
    """
    Determine which of the public network contains the default gateway
    """

    # Determine which network the default gateway is on
    bFound = False
    for device, network, subnet in pubnets:
        if ipfun.onNetwork(network, subnet, gwipaddr):
            bFound = True
            break
    if not bFound:
        return (None, None, None)

    return (device, network, subnet)


def updateSuSEfirewall(action, device, type):
    if updSuSEfirewallRules(action, device, type) != 0:
        return 1

    if not isFirewallRunning():
        print 'Error: Firewall is not running.  Do you wish to'
        print 'start the firewall now [N/y]? ',

        value = raw_input()
        if value == '' or value.lower() == 'n':
            return 0

        startService('firewall')

    restartService('firewall')


def updateIptables(action, device, type):
    if type == 'public':
        # Adding a public network interface
        retval, rules = updIptablesRulesForPublicInterface(action, device)
    elif type == 'provision':
        retval, rules = updIptablesRulesForPrivateInterface(action, device)
    else:
        # Unsupported network type
        print 'Error: unsupported network type'
        return 1

    if retval != 0:
        return retval

    if not isFirewallRunning():
        # iptables service is not running.  It needs to be running so we
        # can make accurate adjustments

        print 'Error: Firewall is not running.  Do you wish to'
        print 'start the firewall now [N/y]? ',

        bDiePrematurely = False

        value = raw_input()
        if value == '' or value.lower() == 'n':
            bDiePrematurely = True
        else:
            # Attempt to start iptables service
            cmd = 'service iptables start >/dev/null 2>&1'

            p = subprocess.Popen(cmd, shell=True)
            retval = p.wait()

            if retval != 0:
                print 'Error: unable to start iptables service'

                bDiePrematurely = True

        # This is a catch-all error handler.
        #
        # 'bDiePrematurely' will be set to True if the user instructed us
        # to not start iptables or if starting the iptables service failed

        if bDiePrematurely:
            print
            print 'Warning: unable to update iptables settings for newly'
            print 'added network interface.'
            print
            print ('Please apply the following iptables settings to '
                   '/etc/sysconfig/iptables as appropriate:')

            print
            for rule in rules:
                print 'iptables ' + rule

        # Success!
        #
        # If we got this far, the iptables service was started successfully
        pass

    print 'Applying updated firewall rules...'

    for rule in rules:
        os.system('iptables ' + rule)

    os.system('service iptables save')

    restartService('firewall')


def updateOCS(action, *kw, **args):
    """
    Do the actual work of updating OCS
    """

    networks = []
    nettype = None
    if 'networks' in args:
        networks = args['networks']

    if 'nettype' in args:
        nettype = args['nettype']

    print 'Updating and restarting PCM daemons...'

    updateResolv()
    updateNamed(action, networks=networks, nettype=nettype)
    updateHosts()
    updateDhcpd()
    updateSSH()
    updateApache()
    updateInetd()

    # iptables rules only need to be updated if an installer network
    # interface is added or removed.
    if action in ['add', 'remove']:
        osname, osver, osarch = OS()
        if osname.lower() in ['sles', 'suse', 'opensuse']:
            updateSuSEfirewall(action, args['device'], args['nettype'])
        else:
            updateIptables(action, args['device'], args['nettype'])

    # Only rebuild the repo(s) if the flag is set
    if 'rebuildRepos' in args and args['rebuildRepos']:
        updateRepos()

def updatePCMGUIConfig(hostname = ''):
    """ Update PCMGUI Hostname configuration and restart the service."""

    if hostname and path(PCM_GUI_CHANGE_HOSTNAME_SCRIPT).exists():
        os.system("/bin/sh %s %s" % (PCM_GUI_CHANGE_HOSTNAME_SCRIPT, hostname))
    if isExistingService('pmc'):
        restartService('pmc')


def updateDnsSettings(restart=False):
    """Regenerate /etc/named.conf and (optionally) restart the daemon.  This
    function is called when updating the DNS settings in appglobals.
    """

    if not int(getAppGlobals('InstallerServeDNS')):
        return

    print 'Updating /etc/named.conf'

    rc = genconfigSafeUpdate('kusu-genconfig named', '/etc/named.conf')

    if not rc:
        return False

    # Restart named
    if restart:
        restartService('named')

    return True


def updateResolv():
    print 'Updating /etc/resolv.conf'

    return genconfigSafeUpdate('kusu-genconfig resolv', '/etc/resolv.conf')

def removeReverseDnsCfg(reverseDnsCfg):
    try:
        os.unlink(reverseDnsCfg)
    except OSError, e:
        (_errno, _msg) = e
        if _errno != 2:
             print 'Error removing %s (%s)' % (reverseDnsCfg, _msg)


def updateNamed(action, networks=None, nettype=None):

    if not int(getAppGlobals('InstallerServeDNS')):
        return

    if not updateDnsSettings():
        print 'Error updating /etc/named.conf'
        return False
        
    dns_zone = getAppGlobals('DNSZone')
    named_dir_str = Dispatcher.get('named_dir')

    if not named_dir_str:
        print 'Error determining named directory.'
        return

    named_dir = path(named_dir_str)

    # Update 'zone' for named
    if dns_zone:
        dns_path = path('%s.zone' % dns_zone)
        print 'Updating DNS zone file(s)'

        genconfigSafeUpdate('kusu-genconfig zone',
                            '%s/%s.zone' % (named_dir_str, dns_zone))

    # Iterate over networks, updating configuration for each
    print 'Updating reverse DNS configuration file(s)'

    for network in networks:
        # check whether this network is public
        sql = "select type from networks where network = \'%s\'" % network
        db.execute(sql)
        row = db.fetchone()
        rev_path = path('%s.rev' % network)
        reverseDnsCfg = named_dir / rev_path

        if not row:
            if nettype and not nettype == 'public':
                removeReverseDnsCfg(reverseDnsCfg)
        elif not row[0] == 'public':
            # print 'Building reverse DNS config for %s' % (network)
            if action == 'remove':
                # Remove reverse DNS configuration file for this network
                removeReverseDnsCfg(reverseDnsCfg)
                continue
 
            genconfigSafeUpdate('kusu-genconfig reverse %s' % (network), reverseDnsCfg)

    # Restart named
    restartService('named')

def dns_action_set(argv):
    if len(argv) != 2:
        print 'Error: invalid arguments for action'
        return 1

    kname = argv[0]
    kvalue = argv[1]

    if ipfun.validIP(kvalue) != 1:
        print 'Error: invalid IP address'
        return 6

    if not kname in ['dns1', 'dns2', 'dns3']:
        print ('Error: invalid setting \"%s\".  '
              'Must be \'dns1\', \'dns2\', or \'dns3\'' % (kname))
        return 1

    print 'Updating setting for %s' % (kname)

    sql = 'delete from appglobals where kname=\"%s\"' % (kname)
    db.execute(sql)

    sql = ('insert into appglobals (kname, kvalue) '
           'values (\"%s\", \"%s\")' % (kname, kvalue))

    db.execute(sql)

    updateDnsSettings(True)

    print 'Setting for %s updated successfully.' % (argv[0])

    return 0


def dns_action_unset(argv):
    if len(argv) != 1:
        print 'Error: invalid arguments for action'
        return 1

    kname = argv[0]

    if not kname in ['dns1', 'dns2', 'dns3']:
        print ('Error: invalid setting \"%s\".  '
              'Must be \'dns1\', \'dns2\', or \'dns3\'' % (kname))
        return 1

    print 'Updating setting for %s' % (kname)

    sql = ('select count(kvalue) from appglobals '
           'where kname in (\'dns1\', \'dns2\', \'dns3\')')

    db.execute(sql)

    row = db.fetchone()

    if row[0] <= 1:
        print 'Error: at least one DNS server must be defined'
        return 1

    sql = 'delete from appglobals where kname=\'%s\'' % (kname)
    db.execute(sql)

    updateDnsSettings(True)

    print 'Setting \'%s\' removed successfully' % (kname)

    return 0

def dns_action_domain(argv):
    if not argv:
        # Missing req'd argument(s)
        return -1

    if argv[0].lower() == 'public':
        if len(argv) != 2:
            print 'Error: missing public DNS domain name parameter'
            return False
        if not setAppGlobals('PublicDNSZone', argv[1]):
            print 'Error: unable to set public DNS domain for cluster'
            return False
        # Re-generate configuration files and restart daemon(s)
        action_hostname('%s.%s' % (getAppGlobals('PrimaryInstaller'), argv[1]))
    elif argv[0].lower() == 'private':
        if len(argv) != 2:
            print 'Error: missing private DNS domain name parameter'
            return False
        if not setAppGlobals('DNSZone', argv[1]):
            print 'Error: unable to set public DNS domain for cluster'
            return False
        # Re-generate configuration files and restart daemon(s)
        networks = getInstallerNetworks()
        updateOCS('update', networks=networks)
        print '\nPlease run \'kusu-addhost -u\' to update the configuration for installed kits.'

    return 0

dns_actions = {
    'info': dns_action_info,
    'set': dns_action_set,
    'unset': dns_action_unset,
    'domain': dns_action_domain
}


class DNSOptionParser(OptionParser):
    def print_help(self):
        OptionParser.print_help(self)

        print """
actions:

  info                                Display current DNS settings
  set <dns1|dns2|dns3> <ip address>   Add/replace specified DNS server
  unset <dns1|dns2|dns3>              Unset (remove) specified DNS server
  domain public <domain>              Set public DNS domain
  domain private <domain>             Set private DNS domain
"""


class KusuNetToolApp(KusuApp):
    """Main application class"""

    def __init__(self):
        KusuApp.__init__(self)

        self.action_handlers = {
            'hostname':   self.hostname_handler,
            'hostinfo':   self.hostinfo_handler,
            'addinstnic': self.addinstnic_handler,
            'delinstnic': self.delinstnic_handler,
            'dns':        self.dns_handler,
            'updinstnic': self.updinstnic_handler
        }


    def hostname_handler(self):
        """Handler for 'hostname' action"""

        parser = OptionParser(usage='%prog hostname [hostname]')
        (options, args) = parser.parse_args(args=sys.argv[2:])

        hostname = None
        if args:
            hostname = args[0]
            ret, msg = verifyFQDN(hostname)
            if not ret:
                print 'Error: %s' % msg
                return 1

        action_hostname(hostname)


    def hostinfo_handler(self):
        """Handler for 'hostinfo' action"""

        parser = OptionParser(usage='%prog hostinfo [hostname]')
        (options, args) = parser.parse_args(args=sys.argv[2:])

        hostname = None
        if args:
            hostname = args[0]

        action_hostinfo(hostname)

        print


    def addinstnic_handler(self):
        """Handler for 'addinstnic' action"""

        if len(sys.argv[2:]) < 1:
            print 'Error: network interface name not specified'
            return EXIT_ONE

        parser = OptionParser(usage='%prog addinstnic <device> [options]')
     
        parser.add_option("--netmask", dest="netmask",
            help="Network mask for this interface")
        parser.add_option("--ip-address", dest="ipaddress", metavar="<ipaddr>",
            help="IP address for this interface")
        parser.add_option("--start-ip", dest="startip", metavar="<ipaddr>",
            help="Starting IP address for this interface")
        parser.add_option("--provision", dest="provision", action="store_true",
            default=False, help="Use network for provisioning")
        parser.add_option("--public", dest="public", action="store_true",
            default=False, help="Use network for public access")
        parser.add_option("--gateway", dest="gateway", metavar="<ipaddr>",
            help="Specify gateway for network")
        parser.add_option("--desc", dest="descr", metavar="<text>",
            help="Description for added network")
        parser.add_option("--macaddr", dest="macaddr",
            help="MAC address assigned to network device")
        parser.add_option("--default", dest="default", action="store_true", default=False, help="Use this gateway as the default gateway")
        parser.add_option("--force", dest="force", action='store_true',
            default=False,
            help="Allow installation of non-configured network devices")

        (options, args) = parser.parse_args(args=sys.argv[2:])

        if not args:
            print 'Error: missing network interface name argument'
            print
            print 'Example: kusu-net-tool addinstnic [...] eth0'
            print
            sys.exit(EXIT_ONE)

        if not is_device_supported(args[0]):
            return EXIT_ONE

        return action_addinstnic(args[0], options)


    def delinstnic_handler(self):
        """Handler for 'delinstnic' action"""

        parser = OptionParser(usage='%prog delinstnic <device> [options]')

        parser.add_option("--force", dest="force", action="store_true",
            default=False, help="Force delete action")

        (options, args) = parser.parse_args(args=sys.argv[2:])

        if not args:
            parser.print_help()
            return EXIT_ONE

        device = args[0]

        if not is_device_supported(device):
            return EXIT_ONE

        return action_delinstnic(device, options)


    def updinstnic_handler(self):
        """Handler for 'updinstnic' action"""

        parser = OptionParser(usage="%prog updinstnic <device> [options]")

        parser.add_option("--ip-address", dest="ipaddress", metavar="<ipaddr>",
            help="IP address for this interface")

        parser.add_option("--netmask", dest="netmask",
            help="Network mask for network interface")

        parser.add_option("--macaddr", dest="macaddr",
            help="MAC address for network interface")

        parser.add_option("--gateway", dest="gateway",
            help="Gateway for interface", metavar="<ipaddr>")

        parser.add_option("--start-ip", dest="startip", metavar="<ipaddr>",
            help="Starting IP address for this interface")

        parser.add_option("--desc", dest="descr",
            help="Description for added network/interface", metavar='<text>')

        parser.add_option("--provision", dest="provision", action="store_true",
            default=False, help="Use network for provisioning")

        parser.add_option("--public", dest="public", action="store_true",
            default=False, help="Use network for public")

        (options, args) = parser.parse_args(args=sys.argv[2:])

        if not args:
            parser.print_help()
            return EXIT_ONE

        device = args[0]
        if not is_device_supported(device):
            return EXIT_ONE

        return action_updinstnic(device, options)


    def dns_handler(self):
        """Handler for 'dns' action"""

        parser = DNSOptionParser(usage='%prog dns <action> [options]')
        (options, args) = parser.parse_args(args=sys.argv[2:])

        if len(sys.argv) < 3:
            print 'Error: missing DNS action'
            return EXIT_ONE

        if not sys.argv[2] in dns_actions:
            print 'Error: unrecognized DNS action \"%s\"' % (sys.argv[2])
            return EXIT_ONE

        dns_action = sys.argv[2]

        retval = dns_actions[dns_action](sys.argv[3:])
        if retval != 0:
            if retval == -1:
                print 'Error: invalid/missing arguments to \'dns\' action'
                print

                parser.print_help()

                # Normalize the return value for the time being
                retval = 1

            return retval

        # Success
        return 0


    def run(self):
        parser = MyOptionParser(usage="%prog <action> [options]",
             version='%prog version ' + self.version)
        parser.disable_interspersed_args()
        (options, args) = parser.parse_args()

        if not args:
            parser.print_help()
            return EXIT_ONE

        action = args[0]

        if not action in self.action_handlers:
            print 'Error: unrecognized action \"%s\"' % (action)
            return EXIT_ONE

        # ... connect to database
        db.connect('kusudb', 'apache')

        return self.action_handlers[action]()


if __name__ == "__main__":
    app = KusuNetToolApp()
    sys.exit(app.run())
