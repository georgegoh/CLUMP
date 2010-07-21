#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# $Id$
#
# Disabling several pylint warnings (no time to clean up at this time)
# pylint: disable-msg=C0111,C0103
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

import kusu.power
import kusu.powercmd
import os

class ipmi(kusu.power.Plugin):
    """
    Manage IPMI power devices
    """
    # ----------------------------------------    
    # Private functions
    # ----------------------------------------      

    # ---- Run command through ipmitool ----
    def _runCmd(self, options, command):
        interface = "lan"
        oemtype = ""
        
        if self.options:
            interface = self.options[0]
            if len(self.options) > 1:
                oemtype = "-o " + self.options[1]

        if not options:
            raise Exception, "Not enough options given to perform operation"

        options = options.split()

        ipaddr = options[0]
        user = ""
        passwd = ""
        
        if len(options) > 1:
            user = "-U %s" % options[1]
        if len(options) > 2:
            passwd = "-P %s" % options[2]

        cmd = kusu.powercmd.PmCommand("ipmitool -I %s %s -H %s %s %s %s" % (interface, oemtype, ipaddr, user, passwd, command))
        return cmd.read()

    # ----------------------------------------    
    # Public functions
    # ----------------------------------------      
    
    def powerStatus(self, node, options):
        self.log.debug("%s: Checking powerstatus for %s" % (self.__name__, node))
        status = kusu.power.STATUSNA
        result = self._runCmd(options, "chassis power status")
        if result.startswith("Chassis Power is"):
            if result.split()[3] == "on":
                status = kusu.power.STATUSON
            elif result.split()[3] == "off":
                status = kusu.power.STATUSOFF
        else:
            self.log.debug("%s: Status command failed for node %s (%s)" % (self.__name__, node, result))
        return status

    # Added for PCM GUI
    def getInfo(self, node, options):
        self.log.debug("%s: Obtaining information for %s" % (self.__name__, node))
        result = self._runCmd(options, "lan print")
        return "\n" + result
    
    def powerOff(self, node, options):
        self.log.debug("%s: Turning off %s" % (self.__name__, node))
        result = self._runCmd(options, "chassis power off")
        if result.startswith("Chassis Power Control: Down/Off"):
            self.log.debug("%s: Finished ipmitool: (%s)" % (self.__name__, result))
        else:
            raise Exception, "Poweroff command failed for node %s (%s)" % (node, result)

        return kusu.power.SUCCESS

    def powerOn(self, node, options):
        self.log.debug("%s: Turning on %s" % (self.__name__, node))
        result = self._runCmd(options, "chassis power on")
        if result.startswith("Chassis Power Control: Up/On"):
            self.log.debug("%s: Finished ipmitool: (%s)" % (self.__name__, result))
        else:
            raise Exception, "Poweron command failed for node %s (%s)" % (node, result)
        return kusu.power.SUCCESS

    def powerCycle(self, node, options):
        status = self.powerStatus(node, options)
        if status == kusu.power.STATUSON:
            self.log.debug("%s: powerstatus is ON - cycling node : %s" % (self.__name__, node))
            result = self._runCmd(options, "chassis power cycle")
            if result.startswith("Chassis Power Control: Cycle"):
                self.log.debug("%s: Finished ipmitool: (%s)" % (self.__name__, result))
            else:
                raise Exception, "Powercycle command failed for node %s (%s)" % (node, result)
        elif status == kusu.power.STATUSOFF:
            self.log.debug("%s: powerstatus is OFF - turning on node: %s" % (self.__name__, node))
            self.powerOn(node, options)
        else:
            raise Exception, "Unable to determine power state for node %s" % node

        return kusu.power.SUCCESS

    def powerReset(self, node, options):
        status = self.powerStatus(node, options)
        if status == kusu.power.STATUSON:
            self.log.debug("%s: powerstatus is ON - resetting node : %s" % (self.__name__, node))
            result = self._runCmd(options, "chassis power reset")
            if result.startswith("Chassis Power Control: Reset"):
                self.log.debug("%s: Finished ipmitool: (%s)" % (self.__name__, result))
            else:
                raise Exception, "Powerreset command failed for node %s (%s)" % (node, result)
        elif status == kusu.power.STATUSOFF:
            self.log.debug("%s: powerstatus is OFF - can't reset: %s" % (self.__name__, node))
            return kusu.power.FAILED
        else:
            raise Exception, "Unable to determine power state for node %s" % node

        return kusu.power.SUCCESS

kusu.power.registerPlugin(ipmi)
