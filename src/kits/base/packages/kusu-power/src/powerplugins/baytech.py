#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# $Id: baytech.py 3126 2009-10-20 07:29:26Z abuck $
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
import telnetlib
import time

DEFAULT_PORT = 23
DEFAULT_TIMEOUT = 2.000

class baytech(kusu.power.Plugin):
    """
    Manage Baytech power devices
    """
    def __init__(self, log, name, options):
        kusu.power.Plugin.__init__(self, log, name, options)

        if not self.options or len(self.options) < 1:
            raise Exception, "Unable to initiate device '%s', insuffucient number of options"

        self.ipaddr = self.options[0]

        self.user = None
        self.passwd = None
        self.port = DEFAULT_PORT
        self.timeout = DEFAULT_TIMEOUT
        self.statusarray = {}

        if len(self.options) > 1:
            self.user = self.options[1]
        if len(self.options) > 2:
            self.passwd = self.options[2]
        if len(self.options) > 3:
            self.port = int(self.options[3])
        if len(self.options) > 4:
            self.timeout = float(self.options[4])

        self.session = None
        try:
            self.session = self._connect()
        except:
            pass

    # ----------------------------------------    
    # Private functions
    # ----------------------------------------      

    # ---- Receive responses from a telnet session ----
    def _recvRawResponse(self, s):
        response = ""
        now = time.time()
        while not response:
            response = s.read_some()
            if (time.time() - now) > self.timeout:
                break
        if not response:
            raise Exception, "Protocol timeout"
        return response

    # ---- Wait for a command prompt ----
    def _waitForPrompt(self, s, prompts = ["Enter Selection>", "RPC-3>"]):
        wait = True
        inbuffer = ""
        while wait:
            inbuffer = inbuffer + self._recvRawResponse(s)
            pos = inbuffer.rfind("\n")
            tmpbuf = inbuffer[pos+1:]

            for line in inbuffer.split("\n"):
                line = line.strip()
                self.log.debug("got line '%s'" % (line))
                for prompt in prompts:
                    if line.startswith(prompt):
                        wait = False
                        break
                l = line.split()
                if len(l) == 4 and (l[-1] == "On" or l[-1] == "Off"):
                    try:
                        port = int(l[2])
                        self.statusarray[port] = l[3]
                        self.log.debug("Port status array:")
                        self.log.debug(self.statusarray)
                    except:
                        pass
            if len(tmpbuf) > 0:
                #self.log.debug("have tmpbuf :'%s'" % tmpbuf)
                inbuffer = tmpbuf
            else:
                inbuffer = ""
                
    # ---- Send commands to a socket ----
    def _sendRawCmd(self, s, cmd):
        s.write(cmd + "\r\n")

    # ---- Connect and authenticate to the Baytech switch ----
    def _connect(self):
        try:
            s = telnetlib.Telnet(self.ipaddr, self.port)
        except Exception, e:
            raise Exception, "Unable to connect to '%s' port %d : %s" % (self.ipaddr, self.port, e)

        if self.user and self.passwd:
            # TBD: Authenticate
            pass
        
        try:
            self._waitForPrompt(s)
        except Exception, e:
            s.close()
            raise Exception, "Unable to get initial prompt : %s" % (e)

        # Send "1", Select Outlet Control menu
        try:
            self._sendRawCmd(s, "1")
            self._waitForPrompt(s)
        except Exception, e:
            s.close()
            raise Exception, "Unable to select Outlet Control menu : %s" % (e)
            
        self.log.debug("Successfully connected to '%s' port %d" % (self.ipaddr, self.port))
        return s

    # ---- Send commands to Baytech switch, connect if necessary ----
    def _sendCmd(self, cmd):
        if not self.session:
            self.session = self._connect()

        self._sendRawCmd(self.session, cmd)
        self._waitForPrompt(self.session)

    # ----------------------------------------    
    # Public functions
    # ----------------------------------------      
    
    def powerStatus(self, node, options):
        self.log.debug("%s: Checking powerstatus for %s" % (self.__name__, node))
        myport = int(options)
        status = kusu.power.STATUSNA
        self._sendCmd("")
        try:
            if self.statusarray[myport] == "On":
                status = kusu.power.STATUSON
            elif self.statusarray[myport] == "Off":
                status = kusu.power.STATUSOFF
        except:
            pass

        return status

    def powerOff(self, node, options):
        self.log.debug("%s: Turning off %s" % (self.__name__, node))
        myport = int(options)
        self._sendCmd("off %d" % myport)
        if self.statusarray[myport] != "Off":
            raise Exception, "Poweroff command failed for node %s" % (node)
        return kusu.power.SUCCESS

    def powerOn(self, node, options):
        self.log.debug("%s: Turning on %s" % (self.__name__, node))
        myport = int(options)
        self._sendCmd("on %d" % myport)
        if self.statusarray[myport] != "On":
            raise Exception, "Poweron command failed for node %s" % (node)
        return kusu.power.SUCCESS

    def powerCycle(self, node, options):
        status = self.powerStatus(node, options)
        if status == kusu.power.STATUSON:
            self.log.debug("%s: powerstatus is ON - cycling node : %s" % (self.__name__, node))
            self.powerOff(node, options)
            time.sleep(2)
            self.powerOn(node, options)
        elif status == kusu.power.STATUSOFF:
            self.log.debug("%s: powerstatus is OFF - turning on node: %s" % (self.__name__, node))
            self.powerOn(node, options)
        else:
            raise Exception, "Unable to determine power state for node %s" % node

        return kusu.power.SUCCESS


kusu.power.registerPlugin(baytech)
