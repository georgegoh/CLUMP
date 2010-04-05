#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# $Id: mpcard.py 3126 2009-10-20 07:29:26Z abuck $
#
# Disabling several pylint warnings (no time to clean up at this time)
# pylint: disable-msg=C0111,C0103
# pylint: disable-msg=W0102,W0702
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
import socket
import string
import time

class hpmpcard(kusu.power.Plugin):
    """
    Manage HP MPCard power devices
    """
    def __init__(self, log, name, options):
        kusu.power.Plugin.__init__(self, log, name, options)

        self.transtable = string.maketrans("", "")
        self.socket = None

    # ----------------------------------------    
    # Private functions
    # ----------------------------------------      

    # ---- Receive responses from a socket ----
    def _recvRawResponse(self, s):
        response = ""
        now = time.time()
        while not response:
            response = s.recv(1024).translate(self.transtable, "\xff\xfb\x01")
            if (time.time() - now) > self.timeout:
                break
        if not response:
            raise Exception, "Protocol timeout"
        return response

    # ---- Wait for a command prompt ----
    def _waitForPrompt(self, s, prompts = ["] MP>"]):
        wait = True
        inbuffer = ""
        while wait:
            inbuffer = inbuffer + self._recvRawResponse(s)
            pos = inbuffer.rfind("\n")
            tmpbuf = inbuffer[pos+1:]
            
            for line in inbuffer.split("\n"):
                line = line.strip()
                #self.log.debug("got line '%s'" % (line))
                for prompt in prompts:
                    if line.startswith(prompt):
                        wait = False
                        break
                l = line.split()
                if len(l) > 4 and (l[-1] == "ON" or l[-1] == "OFF"):
                    try:
                        port = int(l[2].split(":")[0])
                        self.log.debug("Port status array:")
                        self.log.debug(self.statusarray)
                        self.statusarray[port] = l[-1]
                    except:
                        pass
            if len(tmpbuf) > 0:
                #self.log.debug("have tmpbuf :'%s'" % tmpbuf)
                inbuffer = tmpbuf
            else:
                inbuffer = ""
                
    # ---- Send commands to a socket ----
    def _sendRawCmd(self, s, cmd):
        s.send(cmd + "\r\n")

    # ---- Connect and authenticate to the Baytech switch ----
    def _connect(self):
        try:
            s = socket.socket()
            s.connect((self.ipaddr, self.port))
        except Exception, e:
            raise Exception, "Unable to connect to '%s' port %d : %s" % (self.ipaddr, self.port, e)

        try:
            self._waitForPrompt(s, ["User Name"])
            self._sendRawCmd(s, self.user)
        except Exception, e:
            s.close()
            raise Exception, "Unable to get User Name prompt : %s" % (e)

        try:
            self._waitForPrompt(s, ["Password"])
            self._sendRawCmd(s, self.passwd)
        except Exception, e:
            s.close()
            raise Exception, "Unable to get Password prompt : %s" % (e)
            
        try:
            self._waitForPrompt(s)
        except Exception, e:
            s.close()
            raise Exception, "Unable to get main menu prompt : %s" % (e)

        # Send "1", Select Device Manager menu
        try:
            self._sendRawCmd(s, "1")
            self._waitForPrompt(s)
        except Exception, e:
            s.close()
            raise Exception, "Unable to select Device Manager menu : %s" % (e)

        # Send "3", Outlet Control/Config menu
        try:
            self._sendRawCmd(s, "3")
            self._waitForPrompt(s)
        except Exception, e:
            s.close()
            raise Exception, "Unable to select Outlet Control/Config menu : %s" % (e)
            
        self.log.debug("Successfully connected to '%s' port %d" % (self.ipaddr, self.port))
        return s

    # ---- Send commands to Baytech switch, connect if necessary ----
    def _sendCmd(self, cmd, prompts = [">"]):
        if not self.socket:
            self.socket = self._connect()

        for c in cmd.split(";"):
            self._sendRawCmd(self.socket, c)
            self._waitForPrompt(self.socket, prompts)

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

kusu.power.registerPlugin(hpmpcard)
