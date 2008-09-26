#!/usr/bin/env python

#
# Copyright (c) 2008 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import sys
from optparse import OptionParser
import popen2
import re
import netutil
import shutil
import os
import kusu.ipfun as ipfun
from kusu.core.app import KusuApp
from kusu.core.db import KusuDB

db = KusuDB()

class MyOptionParser(OptionParser):
    def print_help(self):
        OptionParser.print_help(self)

        print """
actions:

  addinstnic  Add network interface to installer node
  delinstnic  Remove existing network interface from installer node
  updnic      Update network settings
  updnet      Update network definition
  hostinfo    Display existing network configuration for host
"""

# ... get current network configuration for this host
gateway = netutil.findGateway()
nics = netutil.findNics(gateway)

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
    (a, b, c, d) = network.split('.')

    return '%d.%d.%d.%d' % (int(a), int(b), int(c), int(d) + 1)

def validateDeviceName(devname, ngid):
    sql = "select count(networks.netid) from networks, nodegroups,ng_has_net where device='%s' and ng_has_net.netid=networks.netid and ng_has_net.ngid=nodegroups.ngid and nodegroups.ngid=%d" % (devname, ngid)

    db.execute(sql)

    row = db.fetchone()

    if not row:
        return True

    # If row is None, then device is not already in use
    return (row[0] == 0)

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

def getNodeId(ngid):
    sql = "select * from nodes where ngid=%d limit 1" % (ngid)

    db.execute(sql)

    row = db.fetchone()
    if not row:
        return None

    return row[0]

def display_hostinfo(nid, host, nodegroup):
    print 'Host \"%s\" (Nodegroup \"%s\")' % (host, nodegroup)

    sql = "select networks.device, nics.ip, networks.subnet, networks.type, networks.netname, networks.netid from nics, networks where nics.netid=networks.netid and nics.nid=%d order by networks.device" % (nid)

    db.execute(sql)

    print

    for row in db.fetchall():
        bcast = ipfun.getBroadcast(row[1], row[2])
        print '%-6s \"%s\"' % (row[0], row[4])
        print '       Inet addr: %s Bcast: %s Mask: %s' % (row[1], bcast, row[2])
        print '       Type:', row[3]
        print '       Network ID:', row[5]
        print

def hostinfo_handler():
    parser = OptionParser(usage='%prog hostinfo [hostname]')
    (options, args) = parser.parse_args(args=sys.argv[2:])

    if args:
        hostname = args[0]

        sql = 'select nodes.nid, nodes.name, nodegroups.ngname from nodes, nodegroups where nodegroups.ngid=nodes.ngid and nodes.name=\'%s\'' % (hostname)
    else:
        hostname = ''

        # Default to displaying the first node in the installer nodegroup
        # (ngid=1)
        sql = 'select nodes.nid, nodes.name, nodegroups.ngname from nodes, nodegroups where nodegroups.ngid=nodes.ngid and nodes.ngid=1 limit 1'

    # print sql

    db.execute(sql)

    (nid, host, nodegroup) = db.fetchone()

    display_hostinfo(nid, host, nodegroup)

def addinstnic(device, options, ngid=1):
    nid = getNodeId(ngid)
    if not nid:
        print 'Error: unable to get nid from nodegroup ID %d' % (ngid)
        return 2

    p_ip = options.ipaddress
    p_netmask = options.netmask

    if options.network:
        p_network = options.network
    else:
        # Calculate the network from the IP address
        p_network = ipfun.getNetwork(options.ipaddress, options.netmask)

    if not options.startip:
        p_startip = getStartIp(p_network)
    else:
        p_startip = getStartIp(options.startip)

    if not options.gateway:
        p_gateway = getStartIp(p_network)
    else:
        p_gateway = options.gateway

    if not options.descr:
        # This is the same default description used by the installer
        p_descr = 'Installer Net %s' % (device)
    else:
        p_descr = options.descr

    if options.provision:
        p_nettype = 'provision'
    else:
        p_nettype = 'public'
 
    if not options.macaddr:
        if device in nics and 'mac' in nics[device]:
            p_macaddr = nics[device]['mac']
        else:
            p_macaddr = ''
    else:
        p_macaddr = options.macaddr

    sql = """insert into networks (network, subnet, device, suffix, gateway, netname, startip, inc, type) values (
'%s',
'%s',
'%s',
'-%s',
'%s',
'%s',
'%s',
1,
'%s');""" % (p_network, p_netmask, device, device,
    p_gateway, p_descr, p_startip, p_nettype)

    db.execute(sql)

    sql = "select last_insert_id()"

    db.execute(sql)

    row = db.fetchone()

    netid = row[0]

    # print 'netid', netid

    sql = """insert into nics (netid, nid, mac, ip, boot) values (%d, %d, '%s', '%s', false)""" % (netid, nid, p_macaddr, p_ip)

    db.execute(sql)

    sql = "insert into ng_has_net (ngid, netid) values (%d, %d)" % (ngid, netid)

    db.execute(sql)

    print 'Added NIC %s successfully!' % (device)

    nodegroup = get_nodegroup_by_ngid(ngid)
    host = get_host_name_by_nid(nid)

    print

    display_hostinfo(nid, host, nodegroup)

    # Success!
    return 0

def writeRHNetworkConfig(device, options):
    """Using the settings from 'options', generate a Red Hat network
    configuration file"""

    if options.network:
        network = options.network
    else:
        network = ipfun.getNetwork(options.ipaddress, options.netmask)

    bcast = ipfun.getBroadcast(options.ipaddress, options.netmask)

    filename = 'ifcfg-%s' % (device)

    srcfile = '/etc/sysconfig/network-scripts/%s' % (filename)
    dstfile = '/etc/sysconfig/network-scripts/%s.new' % (filename)

    fpdst = open(dstfile, 'w')

    bitmask = 0

    CFG_BROADCAST = 0x1
    CFG_IPADDR = 0x2
    CFG_NETMASK = 0x4
    CFG_NETWORK = 0x8
    CFG_DEVICE = 0x10
    CFG_HWADDR = 0x20
    CFG_ONBOOT = 0x40

    # Set a flag indicating whether or not the file exists before we
    # update/create the replacement
    bCfgExists = os.path.exists(srcfile)

    if bCfgExists:
        fpsrc = open(srcfile)

        for line in fpsrc:
            if re.compile("^BROADCAST=.*").match(line):
                fpdst.write("BROADCAST=%s\n" % (bcast))
                bitmask |= CFG_BROADCAST
                continue
            elif re.compile("^IPADDR=.*").match(line):
                fpdst.write("IPADDR=%s\n" % (options.ipaddress))
                bitmask |= CFG_IPADDR
                continue
            elif re.compile("^NETMASK=.*").match(line):
                fpdst.write("NETMASK=%s\n" % (options.netmask))
                bitmask |= CFG_NETMASK
                continue
            elif re.compile("^NETWORK=.*").match(line):
                fpdst.write("NETWORK=%s\n" % (network))
                bitmask |= CFG_NETWORK
                continue
            elif re.compile("^HWADDR=.*").match(line):
                bitmask |= CFG_HWADDR

                (key, cur_hwaddr) = line.rstrip().split('=')

                if options.macaddr and (options.macaddr != cur_hwaddr):
                    fpdst.write("HWADDR=%s\n" % (options.macaddr.upper()))
                    continue
            elif re.compile("^DEVICE=.*").match(line):
                bitmask |= CFG_DEVICE
            elif re.compile("^ONBOOT=.*").match(line):
                bitmask |= CFG_ONBOOT
            elif re.compile("^BOOTPROTO=.*").match(line):
                continue

            fpdst.write(line)

    # Add any missing options
    if not (bitmask & CFG_DEVICE):
        fpdst.write("DEVICE=%s\n" % (device))
    if not (bitmask & CFG_HWADDR) and (options.macaddr):
        fpdst.write("HWADDR=%s\n" % (options.macaddr.upper()))
    if not (bitmask & CFG_BROADCAST):
        fpdst.write("BROADCAST=%s\n" % (bcast))
    if not (bitmask & CFG_IPADDR):
        fpdst.write("IPADDR=%s\n" % (options.ipaddress))
    if not (bitmask & CFG_NETMASK):
        fpdst.write("NETMASK=%s\n" % (options.netmask))
    if not (bitmask & CFG_NETWORK):
        fpdst.write("NETWORK=%s\n" % (network))
    if not (bitmask & CFG_ONBOOT):
        # Enable any new interface by default
        fpdst.write("ONBOOT=yes\n")

    fpdst.close()

    # Move source file to *.old
    if bCfgExists:
        fpsrc.close()
        shutil.move(srcfile, srcfile + '.old')

    # Move *.new to original file name (ifcfg-xxx)
    shutil.move(dstfile, srcfile)

    # Success!
    return 0

def action_addinstnic(device, options, ngid=1):
    """Handler for 'addinstnic' action"""

    # Validate device name to ensure it does not already exist in
    # database
    if not validateDeviceName(device, ngid):
        print 'Error: device %s is already in use by this host' % (device)
        return 3

    if not device in nics:
        if not options.force:
            # Device is not known to the system, we need the --force flag
            # to allow configuration
            print 'Warning: device %s is not configured with the OS.\nUse --force option to force installation' % (device)
            return 4
    else:
        # Extract available parameters from the Red Hat configuration
        if 'ip' in nics[device]:
            options.ipaddress = nics[device]['ip']

        if 'subnet' in nics[device]:
            options.netmask = nics[device]['subnet']

    # At the absolute minimum, a network interface needs an IP address
    # and a netmask.  From this, we can deduce the other remaining
    # parameters.
    if not options.ipaddress or not options.netmask:
        print 'Error: missing --ip-address and/or --netmask parameters'
        return 5

    # Update/create Red Hat network configuration
    retval = writeRHNetworkConfig(device, options)
    if retval != 0:
        print 'Error: unable to update Red Hat network configuration'
        return 6

    return addinstnic(device, options)

def action_delinstnic(device, options, ngid=1):
    """Handler for 'delinstnic' action"""

    nid = getNodeId(ngid)
    if not nid:
        print 'Error: unable to get nid from nodegroup ID' % (nid)
        return 2

    sql = 'select nodes.name, networks.netid from networks,ng_has_net,nodes,nics where networks.netid=ng_has_net.netid and ng_has_net.ngid=%d and networks.device=\'%s\' and nodes.nid=nics.nid and nics.netid=networks.netid' % (ngid, device)

    # print sql

    db.execute(sql)

    row = db.fetchone()

    if not row:
        print 'Error: Network interface \"%s\" does not exist on this node' % (device)
        return 5

    (hostname, netid) = row

    if not options.force:
        # Confirm that the user actually wants to remove the specified
        # network device
        print 'Are you sure you wish to remove device \"%s\" from host \"%s\" [N/y]?' % (device, hostname),

        resp = raw_input("")

        if not resp in [ 'y', 'Y' ]:
            print 'Aborting delete NIC action'
            return

    # Break the association between the network and the nodegroup
    sql = 'delete from ng_has_net where ngid=%d and netid=%d' % (ngid, netid)

    db.execute(sql)

    sql = 'delete from nics where nid=%d and netid=%d' % (nid, netid)

    db.execute(sql)

    sql = 'delete from networks where netid=%d' % (netid)

    db.execute(sql)

    print 'Device \"%s\" successfully removed!' % (device)

def addinstnic_handler():
    parser = OptionParser(usage='%prog addinstnic <device> [options]')
 
    parser.add_option("--network", dest="network",
        help="Network definition for this interface")
    parser.add_option("--netmask", dest="netmask",
        help="Network mask for this interface")
    parser.add_option("--ip-address", dest="ipaddress", metavar="<ipaddr>",
        help="IP address for this interface")
    parser.add_option("--start-ip", dest="startip", metavar="<ipaddr>",
        help="Starting IP address for this interface")
    parser.add_option("--provision", dest="provision", action="store_true",
        default=False, help="Use network for provisioning")
    parser.add_option("--public", dest="provision", action="store_false",
        default=False, help="Use network for public access")
    parser.add_option("--gateway", dest="gateway", metavar="<ipaddr>",
        help="Specify gateway for network")
    parser.add_option("--desc", dest="descr", metavar="<text>",
        help="Description for added network")
    parser.add_option("--macaddr", dest="macaddr",
        help="MAC address assigned to network device")
    parser.add_option("--force", dest="force", action='store_true',
        default=False,
        help="Allow installation of non-configured network devices")

    (options, args) = parser.parse_args(args=sys.argv[2:])

    return action_addinstnic(args[0], options)

def delinstnic_handler():
    parser = OptionParser(usage='%prog delinstnic <device> [options]')

    parser.add_option("--device", dest="device",
        help="Network interface device name (example: eth0)")

    parser.add_option("--force", dest="force", action="store_true",
        default=False, help="Force delete action")

    (options, args) = parser.parse_args(args=sys.argv[2:])

    if not args:
        parser.print_help()
        return 1

    return action_delinstnic(args[0], options)

def action_updnic(options):
    """Handler for 'updnic' action"""

    # Validate options
    if not options.hostname:
        print 'Error: host name not specified (--host=<hostname>)'
        return 1

    # Retrieve existing settings for this device
    sql = "select nodes.nid, nodes.name, nics.mac, nics.ip, networks.netid, nodegroups.ngname from nodes, nics, networks, nodegroups where nodes.name='%s' and nodes.nid=nics.nid and nics.netid=networks.netid and nodegroups.ngid=nodes.ngid" % (options.hostname)

    if options.device:
        sql += ' and networks.device=\'%s\'' % (options.device)

    # print sql

    db.execute(sql)

    if db.rowcount > 1 and not options.device:
        print 'Error: host %s has more than one network interface.  Use --device=<device name> to specify interface' % (options.hostname)
        return 1

    row = db.fetchone()

    if not row:
        print 'Error: device %s does not exist on this host' % (options.device)
        return 1

    # print row

    nid = row[0]
    host = row[1]
    exist_macaddr = row[2]
    exist_ipaddress = row[3]
    netid = row[4]
    nodegroup = row[5]

    # Get network settings for this nic
    netSettings = getNetworkSettings(netid)
    if not netSettings:
        print 'Error: unable to get network information for network ID %d' % (netid)
        return 2

    # All command-line parameters override default settings
    if options.ipaddress and (options.ipaddress != exist_ipaddress):
        cur_ipaddress = options.ipaddress
    else:
        cur_ipaddress = exist_ipaddress

    # Initialize lists containing SQL query fragments
    nics_updates = []

    if options.ipaddress and (options.ipaddress != exist_ipaddress):
        if not ipfun.onNetwork(netSettings.network, netSettings.netmask,
             options.ipaddress):
            # Specified IP address is not on the previously defined network,
            # demand that the user specify the rest of the required settings
            # (network and subnet)

            if (not options.network) and (not options.netmask):
                print 'Error: Specified IP address %s is not part of this network (%s/%s)' % (options.ipaddress, netSettings.network, netSettings.netmask)
                return 1

        nics_updates.append('ip=\"%s\"' % options.ipaddress)

    if options.macaddr and (options.macaddr != exist_macaddr):
        nics_updates.append('mac=\"%s\"' % options.macaddr)

    # Perform the database updates
    if nics_updates:
        # Build query for 'nics' table
        if nics_updates:
            nics_sql_query = "update nics set " + ", ".join(nics_updates)
            nics_sql_query += ' where netid=%d' % (netid)

            # print nics_sql_query

            db.execute(nics_sql_query)

        if options.device:
            print 'Network settings for device %s updated successfully!' % (options.device)
        else:
            print 'Network settings on host %s updated successfully!' % (options.hostname)

        print

        display_hostinfo(nid, host, nodegroup)
    else:
        print 'No settings have been changed.  Nothing to do!'

    return 0

def updnic_handler():
    parser = OptionParser(usage='%prog updnic [options]')

    parser.add_option("--host", "-m", dest="hostname",
        help="Specify name of host to be updated")

    parser.add_option("--device", dest="device",
        help="Network interface device name (example: eth0)")

    parser.add_option("--ip-address", dest="ipaddress", metavar="<ipaddr>",
        help="IP address for this interface")

    parser.add_option("--macaddr", dest="macaddr",
        help="Specify MAC address for network interface")

    (options, args) = parser.parse_args(args=sys.argv[2:])

    return action_updnic(options)

class NetworkSettings(object):
    def __init__(self):
        network = ''
        netmask = ''
        suffix = ''
        gateway = ''
        descr = ''
        startip = ''
        nettype = ''

def getNetworkSettings(netid):
    # Retrieve existing settings for network
    sql = "select network, subnet, suffix, gateway, netname, startip, type from networks where netid=%d" % (netid)

    db.execute(sql)

    row = db.fetchone()

    if not row:
        # Invalid network ID
        return None

    obj = NetworkSettings()

    obj.network = row[0]
    obj.netmask = row[1]
    obj.suffix = row[2]
    obj.gateway = row[3]
    obj.descr = row[4]
    obj.startip = row[5]
    obj.nettype = row[6]

    return obj

def displayNetworkSettings(netid, netset):
    print '  Network ID:', netid
    print '     Network:', netset.network
    print '     Netmask:', netset.netmask
    print '      Suffix:', netset.suffix
    print '     Gateway:', netset.gateway
    print ' Description:', netset.descr
    print '    Start IP:', netset.startip
    print 'Network type:', netset.nettype
    print

def action_updnet(options):
    """Handler for 'updnet' action"""

    existingNetworkSettings = getNetworkSettings(options.netid)
    if not existingNetworkSettings:
        print 'Error: invalid network ID %d' % (options.netid)
        return 1

    if options.netmask and (options.netmask != existingNetworkSettings.netmask):
        cur_netmask = options.netmask
    else:
        cur_netmask = existingNetworkSettings.netmask

    if options.network and (options.network != existingNetworkSettings.network):
        cur_network = options.network
    else:
        cur_network = existingNetworkSettings.network

    if options.gateway and (options.gateway != existingNetworkSettings.gateway):
        cur_gateway = options.gateway
    else:
        cur_gateway = existingNetworkSettings.gateway

    networks_updates = []

    if options.descr and (options.descr != existingNetworkSettings.descr):
        networks_updates.append('netname=\"%s\"' % options.descr)

    if options.netmask:
        networks_updates.append('subnet=\"%s\"' % options.netmask)

    # Starting IP address
    if options.startip and (options.startip != existingNetworkSettings.startip):
        if not ipfun.onNetwork(cur_network, cur_netmask, options.startip):
            print 'Error: starting IP address %s is not on the network %s/%s' % (options.startip, cur_network, cur_netmask)
            return 1

        networks_updates.append('startip=\"%s\"' % options.startip)

    if existingNetworkSettings.nettype == 'provision' and not options.provision:
        networks_updates.append('type=\"public\"')
    elif existingNetworkSettings.nettype == 'public' and options.provision:
        networks_updates.append('type=\"provision\"')

    if options.network and (options.network != cur_network):
        if not ipfun.onNetwork(options.network, cur_netmask, cur_ipaddress):
            # Existing settings conflict with specified network
            print 'Error: Specified network %s/%s conflicts with existing settings' % (options.network, cur_netmask)
            return 1

        networks_updates.append('network=\"%s\"' % options.network)

    if options.suffix:
        networks_updates.append('suffix=\"%s\"' % options.suffix)

    if options.gateway and (options.gateway != existingNetworkSettings.gateway):
        networks_updates.append('gateway=\"%s\"' % options.gateway)

    # Build query for 'networks' table
    if networks_updates:
        networks_sql_query = "update networks set " + ", ".join(networks_updates)
        networks_sql_query += ' where netid=%d' % (options.netid)

        # print networks_sql_query

        db.execute(networks_sql_query)

        netSettings = getNetworkSettings(options.netid)

        print '\nNetwork ID %d updated successfully!\n' % (options.netid)

        displayNetworkSettings(options.netid, netSettings)
    else:
        print 'Nothing has changed.  Nothing to do!'

def updnet_handler():
    parser = OptionParser(usage="%prog updnet [options]")

    parser.add_option("--desc", dest="descr",
        help="Description for added network/interface", metavar='<text>')

    parser.add_option("--suffix", dest="suffix",
        help="Specify suffix for this network interface")

    parser.add_option("--provision", dest="provision", action="store_true",
        default=False, help="Use network for provisioning")

    parser.add_option("--public", dest="provision", action="store_false",
        default=False, help="Use network for public")

    parser.add_option("--start-ip", dest="startip",
        help="Starting IP address for this interface", metavar="<ipaddr>")

    parser.add_option("--gateway", dest="gateway",
        help="Specify gateway for interface", metavar="<ipaddr>")

    parser.add_option("--netmask", dest="netmask",
        help="Network mask for this interface")

    parser.add_option("--network", dest="network",
        help="Network definition for this interface")

    parser.add_option("--netid", dest="netid",
        type="int",
        help="ID of network to be updated")

    (options, args) = parser.parse_args(args=sys.argv[2:])

    return action_updnet(options)

action_handlers = {
    'hostinfo': hostinfo_handler,
    'addinstnic': addinstnic_handler,
    'delinstnic': delinstnic_handler,
    'updnic': updnic_handler,
    'updnet': updnet_handler
}

class KusuNetToolApp(KusuApp):
    def run(self):
        parser = MyOptionParser(usage="%prog <action> [options]",
             version='%prog ' + self.version)
        parser.disable_interspersed_args()
        (options, args) = parser.parse_args()

        if not args:
            parser.print_help()
            return 1

        action = args[0]

        if not action in action_handlers:
            print 'Error: unrecognized action \"%s\"' % (action)
            return 1

        # ... connect to database
        db.connect(user='root')

        return action_handlers[action]()

def main():
    app = KusuNetToolApp()
    return app.run()

if __name__ == "__main__":
    sys.exit(main())
