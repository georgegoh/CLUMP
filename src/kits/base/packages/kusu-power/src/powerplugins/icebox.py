#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# $Id: icebox.py 3126 2009-10-20 07:29:26Z abuck $
#
# Disabling several pylint warnings (no time to clean up at this time)
# pylint: disable-msg=C0111,C0103
# pylint: disable-msg=W0702
#
# Module --------------------------------------------------------------------
#
# $RCSfile$
#
# COPYRIGHT NOTICE
#
# Â© 2008 Platform Computing. All Rights Reserved.
# All other trademarks are the property of their respective
# holders.
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
import time
import socket

DEFAULT_NIMP_PORT = 1010
DEFAULT_NIMP_TIMEOUT = 2.000

NIMP_SUCCESS = "OK"

class icebox(kusu.power.Plugin):
    """
    Manage LNXI IceBox power devices
    """
    def __init__(self, log, name, options):
        kusu.power.Plugin.__init__(self, log, name, options)

        if not self.options or len(self.options) < 2:
            raise Exception, "Unable to initiate device '%s', insuffucient number of options"

        self.ipaddr = self.options[0]
        self.passwd = self.options[1]
        self.port = DEFAULT_NIMP_PORT
        self.timeout = DEFAULT_NIMP_TIMEOUT
        
        if len(self.options) > 2:
            self.port = int(self.options[2])
        if len(self.options) > 3:
            self.timeout = float(self.options[3])

        self.socket = None
        try:
            self.socket = self._connect()
        except:
            pass

    # ----------------------------------------    
    # Private functions
    # ----------------------------------------      

    # ---- Send NIMP commands to a socket ----
    def _sendRawNIMPCmd(self, s, cmd):
        s.send(cmd + "\r\n")
        now = time.time()
        response = ""
        while not response:
            response = s.recv(1024).strip()
            if (time.time() - now) > self.timeout:
                break
        return response

    # ---- Connect and authenticate to the Icebox ----
    def _connect(self):
        try:
            s = socket.socket()
            s.connect((self.ipaddr, self.port))
        except Exception, e:
            raise Exception, "Unable to connect to '%s' port %d : %s" % (self.ipaddr, self.port, e)

        try:
            version = s.recv(1024)
        except Exception, e:
            s.close()
            raise Exception, "Unable to determine NIMP version : %s" % (e)

        version = version.strip()
        if version != "V4.0":
            s.close()
            raise Exception, "Unsupported NIMP version '%s'" % (version)

        response = self._sendRawNIMPCmd(s, "auth %s" % self.passwd)
        if response != NIMP_SUCCESS:
            s.close()
            raise Exception, "Error authenticating : %s" % (response)
        self.log.debug("Successfully connected to '%s' port %d" % (self.ipaddr, self.port))
        return s

    # ---- Send commands to IceBox, connect if necessary ----
    def _sendNIMPCmd(self, cmd):
        if not self.socket:
            self.socket = self._connect()
        try:
            response = self._sendRawNIMPCmd(self.socket, cmd)
        except Exception, e:
            self.socket = None
            raise Exception, e
        return response

    # ----------------------------------------    
    # Public functions
    # ----------------------------------------      
    
    def powerStatus(self, node, options):
        self.log.debug("%s: Checking powerstatus for %s" % (self.__name__, node))
        status = kusu.power.STATUSNA
        response = self._sendNIMPCmd("ps %s" % options)
        if response.startswith("ERROR"):
            self.log.error("%s: Status command failed for node %s (%s)" % (self.__name__, node, response))
        else:
            self.log.debug("%s: Finished NIMP command: (%s)" % (self.__name__, response))
            state = response.split(":")[1]
            if state == "1":
                status = kusu.power.STATUSON
            elif state == "0":
                status = kusu.power.STATUSOFF

        return status

    def powerOff(self, node, options):
        self.log.debug("%s: Turning off %s" % (self.__name__, node))
        response = self._sendNIMPCmd("pl %s" % options)
        if response != NIMP_SUCCESS:
            raise Exception, "Poweroff command failed for node %s (%s)" % (node, response)
        self.log.debug("%s: Finished NIMP command: (%s)" % (self.__name__, response))
        return kusu.power.SUCCESS

    def powerOn(self, node, options):
        self.log.debug("%s: Turning on %s" % (self.__name__, node))
        response = self._sendNIMPCmd("ph %s" % options)
        if response != NIMP_SUCCESS:
            raise Exception, "Poweron command failed for node %s (%s)" % (node, response)
        self.log.debug("%s: Finished NIMP command: (%s)" % (self.__name__, response))
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

    def uidStatus(self, node, options):
        self.log.debug("%s: Checking UID status for %s" % (self.__name__, node))
        status = kusu.power.STATUSNA
        response = self._sendNIMPCmd("be %s" % options)
        if response.startswith("ERROR"):
            self.log.error("%s: Status command failed for node %s (%s)" % (self.__name__, node, response))
        else:
            self.log.debug("%s: Finished NIMP command: (%s)" % (self.__name__, response))
            state = response.split(":")[1]
            if state == "ON":
                status = kusu.power.STATUSON
            elif state == "OFF":
                status = kusu.power.STATUSOFF

        return status

    def uidOff(self, node, options):
        self.log.debug("%s: Turning UID off %s" % (self.__name__, node))
        response = self._sendNIMPCmd("be %s off" % options)
        if response != NIMP_SUCCESS:
            raise Exception, "UID off command failed for node %s (%s)" % (node, response)
        self.log.debug("%s: Finished NIMP command: (%s)" % (self.__name__, response))
        return kusu.power.SUCCESS

    def uidOn(self, node, options):
        self.log.debug("%s: Turning UID on %s" % (self.__name__, node))
        response = self._sendNIMPCmd("be %s on" % options)
        if response != NIMP_SUCCESS:
            raise Exception, "UID on command failed for node %s (%s)" % (node, response)
        self.log.debug("%s: Finished NIMP command: (%s)" % (self.__name__, response))
        return kusu.power.SUCCESS


kusu.power.registerPlugin(icebox)
