#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# $Id$
#
# Module --------------------------------------------------------------------
#
# $RCSfile$
#
# COPYRIGHT NOTICE
#
# Copyright 2010 Platform Computing Inc.
#
# Licensed under GPL version 2; See COPYING for details.
#
# CREATED
#   Author: sp
#   Date:   2006/06/24
#
# LAST CHANGED
#   $Author: $
#   $Date: $
#
# ---------------------------------------------------------------------------

"""
Manage APC Switched Rack Power Distribution Unit via SNMP.
"""

import kusu.power
import kusu.powercmd
# powernet3.4.3.mib:
#OID = 
# "enterprises.apc.products.hardware.masterswitch.sPDUOutletControl.sPDUOutletControlTable.sPDUOutletControlEntry.sPDUOutletCtl"
CTRL_OID = "1.3.6.1.4.1.318.1.1.12.3.3.1.1.4"
CTRL_ON = 1
CTRL_OFF = 2
CTRL_REBOOT = 3

class apcap7953(kusu.power.Plugin):
    """
    Manage APC Switched Rack Power Distribution Unit via SNMP
    Tested on APC 7953
    """
    #pylint: disable-msg=C0103
    def __init__(self, log, name, options):
        kusu.power.Plugin.__init__(self, log, name, options)

        if not self.options or len(self.options) < 3:
            raise Exception, "Unable to initiate device '%s', insuffucient number of options" % (name)

        self.ipaddr = self.options[0]
        self.user = self.options[1]
        self.passwd = self.options[2]

    def _snmpget(self, oid):
        """
        snmpget wrapper
        """
        cmdline = "/usr/bin/snmpget -v 1 -c %s -O v %s %s" % (self.passwd, self.ipaddr, oid)
        self.log.debug(cmdline)
        status = kusu.powercmd.PmCommand(cmdline).read()
        self.log.debug(status)
        return status

    def _snmpset(self, oid, oidtype, value):
        """
        snmpset wrapper
        """
        cmdline = "/usr/bin/snmpset -v 1 -c %s %s %s %s %s" % (self.passwd, self.ipaddr, oid, oidtype, value)
        self.log.debug(cmdline)
        status = kusu.powercmd.PmCommand(cmdline).read()
        self.log.debug(status)

    def powerStatus(self, node, options):
        """
        power status command
        """
        self.log.debug("%s: Checking powerstatus for %s" % (self.__name__, node))
        myport = int(options)
        status = int(self._snmpget("%s.%d" % (CTRL_OID, myport)))
        if status == CTRL_ON:
            return kusu.power.STATUSON
        elif status == CTRL_OFF:
            return kusu.power.STATUSOFF
        else:
            return kusu.power.STATUSNA

    def powerOff(self, node, options):
        """
        power off command
        """
        self.log.debug("%s: Turning off %s" % (self.__name__, node))
        myport = int(options)
        self._snmpset("%s.%d" % (CTRL_OID, myport), "i", CTRL_OFF)
        return kusu.power.SUCCESS

    def powerOn(self, node, options):
        """
        power on command
        """
        self.log.debug("%s: Turning on %s" % (self.__name__, node))
        myport = int(options)
        self._snmpset("%s.%d" % (CTRL_OID, myport), "i", CTRL_ON)
        return kusu.power.SUCCESS

    def powerCycle(self, node, options):
        """
        power cycle command
        """
        self.log.debug("%s: Turning on %s" % (self.__name__, node))
        myport = int(options)
        self._snmpset("%s.%d" % (CTRL_OID, myport), "i", CTRL_REBOOT)
        return kusu.power.SUCCESS


kusu.power.registerPlugin(apcap7953)
