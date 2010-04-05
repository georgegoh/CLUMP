#!/usr/bin/env python
# Copyright (C) 2009 Platform Computing Inc.
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

# This plugin generates the contents of the alterego database table
# NOTE:  Addhost is called by nghosts to delete and add nodes to move
#        them between nodegroups.

from kusu.addhost import *

db_available = True
dbconnection = None

try:
    from kusu.core.db import KusuDB

except ImportError:
    db_available = False

def createDBconnection():
    global dbconnection
    if not dbconnection:
        dbconnection = KusuDB()
        try:
            dbconnection.connect('kusudb', 'apache')
        except:
            db_available = False
            dbconnection = None
    return dbconnection


class AddHostPlugin(AddHostPluginBase):

    def _getBootNICAndBMCInfo(self, nics):
        # Get the mac and ip of boot nic, and the ip of BMC
        mac = ip = bmc_ip = None
        for nic in nics.values():
            if not nic["boot"] and nic["nicname"].lower() != 'bmc':
                continue
            #Only handle bmc nic and boot nic, normally only 1 boot nic and 1/0 bmc nic
            if nic["nicname"].lower() == 'bmc':
                bmc_ip = nic["ipaddress"]
            else:
                mac = nic["macaddress"]
                ip = nic["ipaddress"]
        return mac, ip, bmc_ip

    def added(self, nodename, info, prePopulateMode):
        # Populate the alteregos table.  There may be entries already
        ngid = info[nodename][0]["nodegroupid"]
        rack = info[nodename][0]["rack"]
        rank = info[nodename][0]["rank"]
        mac, ip, bmc_ip = self._getBootNICAndBMCInfo(info[nodename])
        if mac == None:
            return False

        old_entry = None

        # Create a database connection with write access
        if not db_available:
            return

        db = createDBconnection()
        if not db:
            return

        # Check if compute node has been in this nodegroup before
        query = "SELECT name, ip FROM alteregos WHERE mac='%s' and ngid=%i" % (mac, ngid)
        try:
            db.execute(query)
            output = db.fetchone()
            old_entry = output[1]
        except:
            pass

        # Insert new entry into alteregos table if compute node is new to the nodegroup
        if not old_entry:
            query = "INSERT INTO alteregos (mac, ngid, name, ip, rack, rank, bmcip) \
                     VALUES ('%s', %i, '%s', '%s', %i, %i, '%s')" \
                     % (mac, ngid, nodename, ip, rack, rank, bmc_ip or '')
        elif bmc_ip:
            query = "UPDATE alteregos SET bmcip='%s' WHERE mac='%s' AND ngid=%i AND bmcip!='%s'" \
                     % (bmc_ip, mac, ngid, bmc_ip)
        try:
            db.execute(query)
        except:
            pass

    def replaced(self, nodename, info):
        # Clean up the alteregos table
        ngid = info[nodename][0]["nodegroupid"]
        mac, ip, bmc_ip = self._getBootNICAndBMCInfo(info[nodename])
        if mac == None:
            return False

        # Create a database connection with write access
        if not db_available:
            return

        db = createDBconnection()
        if not db:
            return

        # Get the old mac address
        query = "SELECT mac FROM alteregos WHERE name='%s' and ngid=%i" % (nodename, ngid)
        try:
            db.execute(query)
            output = db.fetchone()
            oldmac = output[0]
        except:
            return

        if oldmac:
            query = "UPDATE alteregos SET mac='%s' WHERE mac='%s'" % (mac, oldmac)
            try:
                db.execute(query)
            except:
                pass

