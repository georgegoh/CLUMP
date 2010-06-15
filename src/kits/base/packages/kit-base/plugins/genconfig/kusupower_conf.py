#   Copyright 2010 Platform Computing Inc
#

POWERCONF='/opt/kusu/etc/power_defaults'
IPMI_PASSWD='/opt/kusu/etc/.ipmi.passwd'

import sys
import os
import string
from kusu.genconfig import Report

try:
    set
except:
    from sets import Set as set

class thisReport(Report):
    
    def toolHelp(self):
        """toolHelp - This method provides the help screen for this particular
        plugin.  All plugins must implement this method."""
        print "Generate a template kusu-power.conf file.  If a real file is " \
              "provided then the resulting file will only contain entries " \
              "for the new nodes.  Default values for the login, password " \
              "and power management type are read from %s" % POWERCONF


    def runPlugin(self, pluginargs):
        """runPlugin - This method provides the database report for this
        plugin.  All plugins must implement this method."""

        # read all lines from input file given(if any).
        input_lines = []
        if pluginargs and pluginargs[0] != '':
            if os.path.exists(pluginargs[0]):
                infile = pluginargs[0]
                fin = open(infile, 'r')
                input_lines = fin.readlines()
                fin.close()


        nodelist = self.getAllNodes()
        node_bmcip_dict = self.getNodesBMCDict()
        (ipmi_type, user, passwd) = self.getPMDefaults()

        # if no input file given, print template at top of file,
        # followed by nodes found in DB.
        if not input_lines:
            self._printTemplate()

        # look at given input lines and process them.
        configured_nodes = []
        for line in input_lines:
            if line.strip() and line.strip().startswith('#'):
                print line,
            else:
                node,s = self.handleLine(line, node_bmcip_dict)
                configured_nodes.append(node)
                if node:
                    print s
                else:
                    print s,

        # configure the remaining set of nodes that are not configured.
        unconfigured_nodes = set(nodelist) - set(configured_nodes)
        for node in unconfigured_nodes:
            if node in node_bmcip_dict:
                print '    '.join(['node', node, ipmi_type, node_bmcip_dict[node], user, passwd])
            else:
                print '    '.join(['node', node, ipmi_type, 'IP.Of.Power.Mgr', user, passwd])


    def handleLine(self, line, node_bmcip_dict):
        """
        Handle single line of the input file. Tries to parse line
        according to the 'node' format(see _printTemplate). Failing
        that, it simply returns the original line given.

        Return format (<nodename processed>, <output line>)
        """
        try:
            type,name,device,ip,user,passwd = line.split()
        except:
            return None,line
        # only deal with 'node' types.
        if type != 'node':
            return None,line

        # try to get the BMC IP for node(default to IP that was read).
        bmcip = node_bmcip_dict.get(name, ip)
        s = '    '.join([type,name,device,bmcip,user,passwd])
        return name,s


    def getNodesBMCDict(self):
        """
        Get (name, ip) of nodes with bmc network interfaces.
        """
        query = 'select nodes.name, nics.ip from nodes, nics, networks ' \
                'where nodes.nid=nics.nid and nics.netid=networks.netid and networks.device="bmc"'
        bmcs = {}
        try:
            self.db.execute(query)
            data = self.db.fetchall()
        except:
            sys.stderr.write(self.gettext("DB_Query_Error\n"))
            sys.exit(-1)

        if data:
            for name, bmc in data:
                bmcs[name] = bmc
        return bmcs


    def getAllNodes(self):
        """
        Get all known nodes in this cluster.
        """
        query = ('select nodes.name from nodes order by nodes.name')
        try:
            self.db.execute(query)
            if self.db.rowcount:
                return [t[0] for t in self.db.fetchall()]
            else:
                return []
        except:
            sys.stderr.write(self.gettext("DB_Query_Error\n"))
            sys.exit(-1)


    def getPMDefaults(self):
        """ Find the type, login, password for the power management stuff. """
        type   = 'ipmi15'
        user   = 'kusu-ipmi'
        passwd = ''

        if os.path.exists(IPMI_PASSWD):
            fp = open(IPMI_PASSWD)
            passwd = fp.readline().strip()
            fp.close()

        if os.path.exists(POWERCONF):
            try:
                fin = open(POWERCONF, 'r')
                lines = fin.readlines()
                fin.close()
            except:
                lines = []

            for line in lines:
                if line[0] == "#":
                    continue
                try:
                    key,val = string.split(line, '=', 1)
                except:
                    continue

                if key == 'MPTYPE':
                    type = string.strip(string.rstrip(val), '"')

        return (type,user,passwd)


    def _printTemplate(self):
        """_printTemplate - print out a default template """

        data = '''
### IPMI examples
##device        <devicename>    ipmi            <interface option>
##node          <nodename>      <devicename>    <ip address> [<username>] [<password>]

#device         ipmi15          ipmi            lan
#node           n1              ipmi15          10.2.100.1 admin admin
#node           n2              ipmi15          10.2.100.2 admin admin

#device         ipmi20          ipmi            lanplus
#node           n3              ipmi20          10.2.100.3 admin admin
#node           n4              ipmi20          10.2.100.4 admin admin


### Dell RAC examples
##device        <devicename>    dellrac
##node          <nodename>      <devicename>    <ip address> <username> <password>

#device         racadm          dellrac
#node           r1              racadm          10.2.100.2 admin admin
#node           r2              racadm          10.2.100.3 admin admin

#device         racadm          dellrac
#node           r1              racadm          10.0.3.18 root calvin

# Other types of devices are supported.  Consult the documentation

device          ipmi15          ipmi            lan
'''
        print data
