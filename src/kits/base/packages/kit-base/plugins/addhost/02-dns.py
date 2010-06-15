# $Id$
#
#   Copyright 2007 Platform Computing Inc
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.
#      
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
#
#

import os

import kusu.core.db
from kusu.addhost import *
from kusu.ipfun import onNetwork, getArpaZone
from primitive.system.software.dispatcher import Dispatcher

class AddHostPlugin(AddHostPluginBase):
    """
    dns plugin for addhost, it will be invoked when execute addhost
    """
    def __init__(self, dbconn):
        AddHostPluginBase.__init__(self, dbconn)
        self.update = False        #update flag
        self.iplists = []
        self.ngid = None           #all node will be in one group during addhost
        self.umngid = None         #unmanaged node group id

    def init(self):
        self.umngid = self.dbconn.getNgidOf('unmanaged')

    def added(self, nodename, info, prePopulateMode):
        if int(self.dbconn.getAppglobals('InstallerServeDNS')):
            self._parsenodeinfo(nodename, info)

    def removed(self, nodename, info):
        if int(self.dbconn.getAppglobals('InstallerServeDNS')):
            self._parsenodeinfo(nodename, info)

    def _parsenodeinfo(self, nodename, info):
        '''
        parse the node info from parameter to avoid accessing DB
        Info Format: nodeInfo["nodename"][index_of_interfaces]['key_item']
        '''
        try:
            if not self.ngid:
                self.ngid = info[nodename][0]['nodegroupid']

            #need to save the ip for unmanaged node, and it only have 1 nic.
            if self.ngid == self.umngid:
                self.iplists.append(info[nodename][0]['ipaddress'])
        except:
            pass #invalid nodeinfo, just pass it        

    def finished(self, nodelist, prePopulateMode):
        """
        update the config files and reload service 'named'
        """
        if not int(self.dbconn.getAppglobals('InstallerServeDNS')):
            return 

        self.named_dir = Dispatcher.get('named_dir')
        dnsZone = self.dbconn.getAppglobals('DNSZone')

        if nodelist and not self.ngid:
            #replace node, need not to update
            return

        if nodelist:
            self._genreverse(self.umngid == self.ngid)
        else:
            #addhost -u
            self._genreverseall()

        #TODO: We should check if the named.conf needs to be updated
        os.system("/opt/kusu/bin/genconfig named > /etc/named.conf")
        os.system("/opt/kusu/bin/genconfig zone > %s/%s.zone" % \
                                                (self.named_dir, dnsZone))

        #reload named service
        os.system("kill -HUP `pidof named`")

    def _genreverseall(self):
        '''
        Generate all reverse file for all private networks.
        '''
        updated_nets = []
        #retrieve all nets
        self.dbconn.execute('select network, subnet from networks '
                            'where usingdhcp=False and type<>"public"')
        nets = self.dbconn.fetchall()
        #TODO:  Avoid overiding reverse file for multiple classless subnet in same arpazone
        #192.0.2.128/25  vs 192.0.2.0/25
        for net, mask in nets:
            arpazone, classnet = getArpaZone(net, mask)
            if net not in updated_nets:
                os.system("/opt/kusu/bin/genconfig reverse %s > %s/%s.rev" % (net, self.named_dir, classnet))
                updated_nets.append(net)

    def _genreverse(self, unmanaged):
        """
        Generate all reverse file for nodes relevant private networks.
        """
        updated_nets = []
        if unmanaged:
            #retrieve all nets
            self.dbconn.execute('select network, subnet from networks '
                                'where usingdhcp=False and type<>"public"'
                                'order by network, subnet')
            #TODO: order by prefix
            nets = self.dbconn.fetchall()
            for ip in self.iplists:
                for net, mask in nets:
                    if onNetwork(net, mask, ip):
                        arpazone, classnet = getArpaZone(net, mask)
                        if net not in updated_nets:
                            os.system("/opt/kusu/bin/genconfig reverse %s > %s/%s.rev" % (net, self.named_dir, classnet))
                            updated_nets.append(net)

        else:
            #get all associated private network in node group
            self.dbconn.execute('select networks.network, networks.subnet from networks, ng_has_net '
                                'where ng_has_net.ngid=%d and ng_has_net.netid=networks.netid '
                                'and networks.usingdhcp=False and networks.type<>"public"' % self.ngid)
            nets = self.dbconn.fetchall()
            #TODO:  Avoid overwriting reverse file for multiple classless subnet
            for net, mask in nets:
                arpazone, classnet = getArpaZone(net, mask)
                if arpazone not in updated_nets:
                    os.system("/opt/kusu/bin/genconfig reverse %s > %s/%s.rev" % (net, self.named_dir, classnet))
                    updated_nets.append(net)

