#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# $Id: sgil2.py 3126 2009-10-20 07:29:26Z abuck $
#
# Disabling several pylint warnings (no time to clean up at this time)
# pylint: disable-msg=C0103
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
"power" plugin for SGI L2 controllers
Used by SGI Altix 450 and SGI Altix 4700
"""

import kusu.power
import telnetlib

try:
    set
except NameError:
    from sets import Set as set

TIMEOUT = 2.000

class sgil2(kusu.power.Plugin):
    """
    SGI L2 controller for SGI Altix 450/4700
    """

    def _sendCmd(self, cmd, options):
        """
        Send one command to the L2 controller
        cmd -- the command L2 command (excluding partition target)
        options -- plugin options from kusu-power.conf
        Returns a list of output-lines from the command
        """
        self.log.debug("%s: Options: %s" % (self.__name__, str(options)))
        (ip, _username, _password, partitionid) = options.split()
        try:
            s = telnetlib.Telnet(ip)
        except Exception, e:
            raise Exception, "Unable to connect to '%s' : %s" % (ip, e)
        cmd = "partition %s %s" % (partitionid, cmd)
        s.read_until("L2>", TIMEOUT)
        self.log.debug("%s: Sending command %s" % (self.__name__, cmd))
        s.write("%s\n" % cmd)
        output = s.read_until("L2>", TIMEOUT)
        self.log.debug("%s: %s" % (self.__name__, repr(output.split("\r\n")[1:-1])))
        if output.find("ERROR") != -1:
            raise Exception, "%s: L2 command failed: %s" % (self.__name__, output)
        return output.split("\r\n")[1:-1]
    
    def powerStatus(self, node, options):
        """
        Check power status for the node
        """
        self.log.debug("%s: Checking powerstatus for %s" % (self.__name__, node))
        status = self._sendCmd("power", options)
        # Every second line of output should include power status for one brick.
        # Create a set of powerstatuses found.
        statuses = tuple(set(status[1::2]))
        if statuses == ('power appears on',):
            status = kusu.power.STATUSON
        elif statuses == ('power appears off',):
            status = kusu.power.STATUSOFF
        else:
            status = kusu.power.STATUSNA
        return status

    def powerOff(self, node, options):
        """
        Power the node off
        """
        self.log.debug("%s: Turning off %s" % (self.__name__, node))
        output = self._sendCmd("power down", options)
        if output:
            raise Exception, "Power off command failed for node %s" % node
        return kusu.power.SUCCESS

    def powerOn(self, node, options):
        """
        Power the node on
        """
        self.log.debug("%s: Turning on %s" % (self.__name__, node))
        output = self._sendCmd("power up", options)
        if output:
            raise Exception, "Power up command failed for node %s" % node
        return kusu.power.SUCCESS

    def powerCycle(self, node, options):
        """
        Power cycle the node
        """
        return self.powerOn(node, options)



kusu.power.registerPlugin(sgil2)
