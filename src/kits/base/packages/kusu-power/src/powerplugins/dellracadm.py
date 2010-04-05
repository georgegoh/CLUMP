#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# $Id: dellracadm.py 3126 2009-10-20 07:29:26Z abuck $
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

RACADM = "/usr/sbin/racadm"

class dellracadm(kusu.power.Plugin):
    """
    Manage RAC power devices
    """
    # ----------------------------------------    
    # Private functions
    # ----------------------------------------      

    # ---- Run command through racadm ----
    def _runCmd(self, options, command):

        if not options:
            raise Exception, "Not enough options given to perform operation"

        options = options.split()
        if len(options) < 3:
            raise Exception, "Not enough options given to perform operation"
            
        ipaddr = options[0]
        user = options[1]
        passwd = options[2]
        
        cmd = kusu.powercmd.PmCommand(RACADM + " -r %s -u %s -p %s %s" % (ipaddr, user, passwd, command))
        return cmd.read()
    
    # ----------------------------------------    
    # Public functions
    # ----------------------------------------      

    def powerStatus(self, node, options):
        self.log.debug("%s: Checking powerstatus for %s" % (self.__name__, node))
        status = kusu.power.STATUSNA
        result = self._runCmd(options, "getmodinfo -m chassis -A")
        if result.split()[4] == "1":
            status = kusu.power.STATUSOFF
        elif result.split()[4] == "2":
            status = kusu.power.STATUSON
        else:
            self.log.debug("%s: Status command failed for node %s (%s)" % (self.__name__, node, result))

        return status

    def powerOff(self, node, options):
        self.log.debug("%s: Turning off %s" % (self.__name__, node))
        result = self._runCmd(options, "serveraction powerdown")
        if result == "":
            self.log.debug("%s: Finished racadm successfully" % (self.__name__))
        else:
            raise Exception, "Poweroff command failed for node %s (%s)" % (node, result)

        return kusu.power.SUCCESS

    def powerOn(self, node, options):
        self.log.debug("%s: Turning on %s" % (self.__name__, node))
        result = self._runCmd(options, "serveraction powerup")
        if result == "":
            self.log.debug("%s: Finished racadm successfully" % (self.__name__))
        else:
            raise Exception, "Poweron command failed for node %s (%s)" % (node, result)

        return kusu.power.SUCCESS

    def powerCycle(self, node, options):
        status = self.powerStatus(node, options)
        if status == kusu.power.STATUSON:
            self.log.debug("%s: powerstatus is ON - cycling node : %s" % (self.__name__, node))
            result = self._runCmd(options, "serveraction powercycle")
            if result == "":
                self.log.debug("%s: Finished racadm successfully" % (self.__name__))
            else:
                raise Exception, "Powercycle command failed for node %s (%s)" % (node, result)
        elif status == kusu.power.STATUSOFF:
            self.log.debug("%s: powerstatus is OFF - turning on node: %s" % (self.__name__, node))
            self.powerOn(node, options)
        else:
            raise Exception, "Unable to determine power state for node %s" % node

        return kusu.power.SUCCESS

    def uidStatus(self, node, options):
        self.log.debug("%s: Checking UID status for %s" % (self.__name__, node))
        status = kusu.power.STATUSNA
        result = self._runCmd(options, "getled -m chassis")
        if result == "OFF":
            status = kusu.power.STATUSOFF
        elif result == "ON":
            status = kusu.power.STATUSON
        else:
            self.log.debug("%s: UID status command failed for node %s (%s)" % (self.__name__, node, result))

        return status

    def uidOff(self, node, options):
        self.log.debug("%s: Turning UID off %s" % (self.__name__, node))
        result = self._runCmd(options, "setled -m chassis OFF")
        if result == "":
            self.log.debug("%s: Finished racadm successfully" % (self.__name__))
        else:
            raise Exception, "UID off command failed for node %s (%s)" % (node, result)

        return kusu.power.SUCCESS

    def uidOn(self, node, options):
        self.log.debug("%s: Turning UID on %s" % (self.__name__, node))
        result = self._runCmd(options, "setled -m chassis ON")
        if result == "":
            self.log.debug("%s: Finished racadm successfully" % (self.__name__))
        else:
            raise Exception, "UID on command failed for node %s (%s)" % (node, result)

        return kusu.power.SUCCESS

kusu.power.registerPlugin(dellracadm)
