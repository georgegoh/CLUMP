#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# $Id: ibmbc.py 3126 2009-10-20 07:29:26Z abuck $
#
# Disabling several pylint warnings (no time to clean up at this time)
# pylint: disable-msg=C0103
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

"""
Manage IBM BladeCenter power devices
"""

import kusu.power
import telnetlib
import time

DEFAULT_PORT = 23
DEFAULT_TIMEOUT = 2.000

class ibmbc(kusu.power.Plugin):
    """
    Manage IBM BladeCenter power devices
    """
    def __init__(self, log, name, options):
        kusu.power.Plugin.__init__(self, log, name, options)

        if not self.options or len(self.options) < 3:
            raise Exception, "Unable to initiate device '%s', insuffucient number of options" % (name)

        self.ipaddr = self.options[0]
        self.user = self.options[1]
        self.passwd = self.options[2]

        self.port = DEFAULT_PORT
        self.timeout = DEFAULT_TIMEOUT

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

    def _recvRawResponse(self, s):
        """
        Receive responses from a telnet session
        """
        response = ""
        now = time.time()
        while not response:
            response = s.read_some()
            if (time.time() - now) > self.timeout:
                break
        if not response:
            raise Exception, "Protocol timeout"
        return response

    def _waitForPrompt(self, s, prompts = ["system>"]):
        """
        Wait for a command prompt 
        """
        wait = True
        inbuffer = ""
        response = []
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
            response = inbuffer.replace("\r", "").split("\n")
            if len(tmpbuf) > 0:
                self.log.debug("have tmpbuf :'%s'" % tmpbuf)
                inbuffer = tmpbuf
            else:
                inbuffer = ""
        return response

    def _sendRawCmd(self, s, cmd):
        """
        Send commands to a telnet session
        """
        s.write(cmd + "\r\n")

    def _connect(self):
        """
        Connect and authenticate to the chassis
        """
        try:
            s = telnetlib.Telnet(self.ipaddr, self.port)
        except Exception, e:
            raise Exception, "Unable to connect to '%s' port %d : %s" % (self.ipaddr, self.port, e)

        try:
            self._waitForPrompt(s, ["username:"])
            self._sendRawCmd(s, self.user)
        except Exception, e:
            s.close()
            raise Exception, "Unable to get User Name prompt : %s" % (e)

        try:
            self._waitForPrompt(s, ["password:"])
            self._sendRawCmd(s, self.passwd)
        except Exception, e:
            s.close()
            raise Exception, "Unable to get Password prompt : %s" % (e)
            
        try:
            self._waitForPrompt(s)
        except Exception, e:
            s.close()
            raise Exception, "Unable to get main menu prompt : %s" % (e)
            
        self.log.debug("Successfully connected to '%s' port %d" % (self.ipaddr, self.port))
        return s

    def _sendCmd(self, cmd):
        """
        Send commands to chassis, connect if necessary
        """
        if not self.session:
            self.session = self._connect()

        self._sendRawCmd(self.session, cmd)
        return self._waitForPrompt(self.session)

    # ----------------------------------------    
    # Public functions
    # ----------------------------------------      
    
    def powerStatus(self, node, options):
        """
        Return the power status
        """
        self.log.debug("%s: Checking powerstatus for %s" % (self.__name__, node))
        myslot = int(options)
        status = kusu.power.STATUSNA
        response = self._sendCmd("power -state -T blade[%d]" % myslot)
        self.log.debug("%s: Finished power command : %s" % (self.__name__, response))
        if len(response) == 3 and response[1] == "On":
            status = kusu.power.STATUSON
        elif len(response) == 3 and response[1] == "Off":
            status = kusu.power.STATUSOFF

        return status

    def powerOff(self, node, options):
        """
        Turn off
        """ 
        self.log.debug("%s: Turning off %s" % (self.__name__, node))
        myslot = int(options)
        response = self._sendCmd("power -off -T blade[%d]" % myslot)
        self.log.debug("%s: Finished power command : %s" % (self.__name__, response))
        if len(response) != 3 or response[1] != "OK":
            raise Exception, "Poweroff command failed for node %s" % (node)
        return kusu.power.SUCCESS

    def powerOn(self, node, options):
        """
        Turn on
        """ 
        self.log.debug("%s: Turning on %s" % (self.__name__, node))
        myslot = int(options)
        response = self._sendCmd("power -on -T blade[%d]" % myslot)
        self.log.debug("%s: Finished power command : %s" % (self.__name__, response))
        if len(response) != 3 or response[1] != "OK":
            raise Exception, "Poweron command failed for node %s" % (node)
        return kusu.power.SUCCESS

    def powerCycle(self, node, options):
        """
        Power cycle (power off, wait 6 seconds, power on)
        """ 
        status = self.powerStatus(node, options)
        if status == kusu.power.STATUSON:
            self.log.debug("%s: powerstatus is ON - cycling node : %s" % (self.__name__, node))
            self.powerOff(node, options)
            time.sleep(6)
            self.powerOn(node, options)
        elif status == kusu.power.STATUSOFF:
            self.log.debug("%s: powerstatus is OFF - turning on node: %s" % (self.__name__, node))
            self.powerOn(node, options)
        else:
            raise Exception, "Unable to determine power state for node %s" % node

        return kusu.power.SUCCESS

    def uidStatus(self, node, options):
        """
        Get the status of the UID lamp
        """
        self.log.debug("%s: Checking UID status for %s" % (self.__name__, node))
        myslot = int(options)
        status = kusu.power.STATUSNA
        response = self._sendCmd("identify -T blade[%d]" % myslot)
        self.log.debug("%s: Finished UID command : %s" % (self.__name__, response))
        if len(response) == 3 and response[1] == "-s on":
            status = kusu.power.STATUSON
        elif len(response) == 3 and response[1] == "-s off":
            status = kusu.power.STATUSOFF

        return status

    def uidOff(self, node, options):
        """
        Disable UID    
        """ 
        self.log.debug("%s: Turning UID off %s" % (self.__name__, node))
        myslot = int(options)
        response = self._sendCmd("identify -s off -T blade[%d]" % myslot)
        self.log.debug("%s: Finished UID command : %s" % (self.__name__, response))
        if len(response) != 3 or response[1] != "OK":
            raise Exception, "UID off command failed for node %s" % node
        return kusu.power.SUCCESS

    def uidOn(self, node, options):
        """
        Enable UID
        """ 
        self.log.debug("%s: Turning UID on %s" % (self.__name__, node))
        myslot = int(options)
        response = self._sendCmd("identify -s on -T blade[%d]" % myslot)
        self.log.debug("%s: Finished UID command : %s" % (self.__name__, response))
        if len(response) != 3 or response[1] != "OK":
            raise Exception, "UID on command failed for node %s" % node
        return kusu.power.SUCCESS


kusu.power.registerPlugin(ibmbc)
