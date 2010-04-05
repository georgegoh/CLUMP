#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# $Id$
#
# Disabling several pylint warnings (no time to clean up at this time)
# pylint: disable-msg=C0111,C0103
# pylint: disable-msg=W0102,W0702,R0912,W0612,W0622,R0912
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
import sys

try:
    import xml.sax
except:
    print  "Error. Required xml.sax module not found by Python."
    sys.exit(1)

_SCALI_USER_TOKEN = "SCALI_USER"
_SCALI_PASSWORD_TOKEN = "SCALI_PASSWORD"

_RIBCL_POWER_STATUS = ['<?xml version=\"1.0\"?>', \
                       '<RIBCL VERSION=\"2.0\">', \
                       '<LOGIN USER_LOGIN=\"SCALI_USER\" PASSWORD=\"SCALI_PASSWORD\">', \
                       '<SERVER_INFO MODE=\"read\">', \
                       '<GET_HOST_POWER_STATUS/>' , \
                       '</SERVER_INFO>', \
                       '</LOGIN>', \
                       '</RIBCL>']

_RIBCL_POWER_ON = ['<?xml version=\"1.0\"?>', \
                   '<RIBCL VERSION=\"2.0\">', \
                   '<LOGIN USER_LOGIN=\"SCALI_USER\" PASSWORD=\"SCALI_PASSWORD\">', \
                   '<SERVER_INFO MODE=\"write\">', \
                   '<PRESS_PWR_BTN/>' , \
                   '</SERVER_INFO>', \
                   '</LOGIN>', \
                   '</RIBCL>']

_RIBCL_POWER_OFF = ['<?xml version=\"1.0\"?>', \
                    '<RIBCL VERSION=\"2.0\">', \
                    '<LOGIN USER_LOGIN=\"SCALI_USER\" PASSWORD=\"SCALI_PASSWORD\">', \
                    '<SERVER_INFO MODE=\"write\">', \
                    '<HOLD_PWR_BTN/>' , \
                    '</SERVER_INFO>', \
                    '</LOGIN>', \
                    '</RIBCL>']

_RIBCL_POWER_CYCLE = ['<?xml version=\"1.0\"?>', \
                      '<RIBCL VERSION=\"2.0\">', \
                      '<LOGIN USER_LOGIN=\"SCALI_USER\" PASSWORD=\"SCALI_PASSWORD\">', \
                      '<SERVER_INFO MODE=\"write\">', \
                      '<COLD_BOOT_SERVER/>' , \
                      '</SERVER_INFO>', \
                      '</LOGIN>', \
                      '</RIBCL>']

_RIBCL_UID_STATUS = ['<?xml version=\"1.0\"?>', \
                     '<RIBCL VERSION=\"2.0\">', \
                     '<LOGIN USER_LOGIN=\"SCALI_USER\" PASSWORD=\"SCALI_PASSWORD\">', \
                     '<SERVER_INFO MODE=\"write\">', \
                     '<GET_UID_STATUS />'\
                     '</SERVER_INFO>', \
                     '</LOGIN>', \
                     '</RIBCL>']

_RIBCL_UID_ON = ['<?xml version=\"1.0\"?>', \
                 '<RIBCL VERSION=\"2.0\">', \
                 '<LOGIN USER_LOGIN=\"SCALI_USER\" PASSWORD=\"SCALI_PASSWORD\">', \
                 '<SERVER_INFO MODE=\"write\">', \
                 '<UID_CONTROL UID="Yes"/>' , \
                 '<GET_UID_STATUS />', \
                 '</SERVER_INFO>', \
                 '</LOGIN>', \
                 '</RIBCL>']

_RIBCL_UID_OFF = ['<?xml version=\"1.0\"?>', \
                  '<RIBCL VERSION=\"2.0\">', \
                  '<LOGIN USER_LOGIN=\"SCALI_USER\" PASSWORD=\"SCALI_PASSWORD\">', \
                  '<SERVER_INFO MODE=\"write\">', \
                  '<UID_CONTROL UID="No"/>' , \
                  '<GET_UID_STATUS />', \
                  '</SERVER_INFO>', \
                  '</LOGIN>', \
                  '</RIBCL>']

_DEFAULT_ILO_NOSSLPORT = 80
_DEFAULT_ILO_SSLPORT = 443

class _iLOSocket:

    _BUFFER_SIZE = 4096
    
    def __init__(self, host, port):
        try:
            s = socket.socket()
            s.connect((host, port))
        except Exception, e:
            raise Exception, "Unable to connect to '%s' port %d : %s" % (host, port, e)
        self.socket = s

    def close(self):
        self.socket.close()

    def send(self, data):
        return self.socket.send(data)

    def recv(self):
        return self.socket.recv(self._BUFFER_SIZE)
    
class _iLOSSLSocket(_iLOSocket):
    def __init__(self, host, port):
        _iLOSocket.__init__(self, host, port)

        try:
            ss = socket.ssl(self.socket)
        except Exception, e:
            self.socket.close()
            raise Exception, "Unable initialize SSL with '%s' port %d : %s" % (host, port, e)
        self.sslsocket = ss
    
    def send(self, data):
        return self.sslsocket.write(data)

    def recv(self):
        return self.sslsocket.read()
    
# ------------------------------------------------------------------------------
# Handles XML resspnses from iLO port:
# ------------------------------------------------------------------------------
class _RIBCLHandler(xml.sax.ContentHandler):
    
    retVal = {}
    def __init__(self, attributes):
        xml.sax.ContentHandler.__init__(self)
        self.attributes = attributes
        self.data = []

    def startElement(self, name, attrs):
        elem_names = ['RIBCL', 'RESPONSE', 'GET_UID_STATUS', 'GET_HOST_POWER', 'GET_FW_VERSION']

        if name == 'RIBCL':
            if attrs.getLength() > 0:
                if 'RIBCL' not in self.attributes.keys():    
                    self.attributes['RIBCL'] = [attrs]
                else:
                    self.attributes['RIBCL'].append(attrs)
        elif name == 'RESPONSE':
            if attrs.getLength() > 0:
                if 'RESPONSE' not in self.attributes.keys():
                    self.attributes['RESPONSE'] = [attrs]
                else:
                    self.attributes['RESPONSE'].append(attrs)
        elif name == 'GET_UID_STATUS':
            if attrs.getLength() > 0:
                if 'GET_UID_STATUS' not in self.attributes.keys():    
                    self.attributes['GET_UID_STATUS'] = [attrs]
                else:
                    self.attributes['GET_UID_STATUS'].append(attrs)
        elif name == 'GET_HOST_POWER':
            if attrs.getLength() > 0:
                if 'GET_HOST_POWER' not in self.attributes.keys():    
                    self.attributes['GET_HOST_POWER'] = [attrs]
                else:
                    self.attributes['GET_HOST_POWER'].append(attrs)
        elif name == 'GET_FW_VERSION':
            if attrs.getLength() > 0:
                if 'GET_FW_VERSION' not in self.attributes.keys():    
                    self.attributes['GET_FW_VERSION'] = [attrs]
                else:
                    self.attributes['GET_FW_VERSION'].append(attrs)

class hpilo(kusu.power.Plugin):
    """
    Manage HP iLO power devices
    """

    # ----------------------------------------    
    # Private functions
    # ----------------------------------------      

    # ---- Substituting password and username in predefined CML string ----
    def _insertPassword(self, command, user, password):
        newcommand = []
        for line in command:
            newline = line.replace(_SCALI_USER_TOKEN, user)
            newline = newline.replace(_SCALI_PASSWORD_TOKEN, password)
            newcommand.append(newline)
        return newcommand

    # ---- Doing fix for bogus XML-tags in feedback ----
    def _parseRIBCL(self, input):
        attributes = {}
        error = ''

        # Bogus \r fix (appears in firmware version 1.50)
        input = input.replace('\r', "")
        
        # Bougus double end-tag fix (appears in firmware version 1.40)
        if input.find('RIBCL VERSION="2.0"/') != -1:
            input = input.replace("/RIBCL", "END_RIBCL/")
            
        # Bougus double end-tag fix (appears in firmware version 1.50)
        if input.find('RIBCL VERSION="2.21"/') != -1:
            input = input.replace("/RIBCL", "END_RIBCL/")

        # Bougus double end-tag fix (appears in firmware version 1.80)
        if input.find('RIBCL VERSION="2.22"/') != -1:
            input = input.replace("/RIBCL", "END_RIBCL/")

        # Do some repairs on reply that the sax parser complains about
        # ( atribute names with space in them is replaced by name with underscore)
        if input.find("GET_HOST_POWER") != -1:
            input = input.replace("HOST POWER", "HOST_POWER")

        xml.sax.parseString(input, _RIBCLHandler(attributes))

        return attributes

    # ---- Analyzing output ----
    def _analyzeOutput(self, attr):
        result = []
        for aname in attr.keys():
            # Verify that there has been no errors
            if aname == 'RIBCL':
                for a in attr[aname]:
                    for t in a.getNames():
                        if t == 'VERSION':
                            v = a.getValue(t)
                            # Check for a supported RIBC version
                            if v != "2.0" and v != "2.21" and v != "2.22":
                                raise Exception, "Error! Unsupported 'RIBCL' version %s received" % v
                        else:
                            self.log.warn("unknown attribute {%s} with value {%s} found in element {%s}" \
                                          % (t, a.getValue(t), aname))
            elif aname == 'RESPONSE':
                for a in attr[aname]:
                    for t in a.getNames():
                        if t == 'STATUS':
                            v = a.getValue(t)
                            if v != "0x0000":
                                raise Exception, a.getValue('MESSAGE')
                            elif v == "0x0000" and a.getValue('MESSAGE') != "No error":
                                self.log.info(a.getValue('MESSAGE'))

            elif aname == 'GET_UID_STATUS':
                for a in attr[aname]:
                    for t in a.getNames():
                        if t == 'UID':
                            v = a.getValue(t) 
                            if v not in ['OFF', 'ON', 'FLASHING']:
                                raise Exception, "Unable to recoginze received uid status: %s" % v
                            else:
                                result.append(v)
                        else:
                            self.log.error("Unable to interpret received power status: %s" % t)

            elif aname == 'GET_HOST_POWER':
                for a in attr[aname]:
                    for t in a.getNames():
                        if t == 'HOST_POWER':
                            v = a.getValue(t)
                            if v not in ['ON', 'OFF']:
                                raise Exception, "Unable to recoginze received power status: %s" % v
                            else:
                                result.append(v)
                        else:
                            self.log.error("Unable to interpret received power status: %s" % t)
            else:
                self.log.error("Unable to interpret received attribute: %s" % aname)

        return result

    # ---- Sending command and receiving output -----
    def _executeCommand(self, s, xml_command):
        # Sending complete XML-doc to avoid timout
        all_tags = "".join(xml_command) + "\r\n"

        # Sending all tags in one write
        # All responses will go in receive-buffer
        self.log.debug("Executing XML : '%s'" % all_tags)
        s.send(all_tags)

        # Reading output xml-docs from socket input-buffer
        # Getting one doc pr. tag sent
        output_docs = []
        responses = 0
        try:
            ilo_tag = s.recv()
            while ilo_tag != "":
                self.log.debug("XML response :" + ilo_tag)
                output_docs.append(ilo_tag)
                # If we got responses to all our commands, we're done
                if len(output_docs) == len(xml_command):
                    break
                ilo_tag = s.recv()
        except socket.sslerror:
            # No more to read in socket buffer
            pass

        self.log.debug("Got all XML response")
        
        # Checking that we actually got anything before attempting parse of response
        if len(output_docs) == 0:
            raise Exception, "No response from iLO socket"

        result = []
        # Parsing response xml-docs from iLO
        for rdata in output_docs:

            # HTTP errors
            # ex: "HTTP/1.1 405 Method Not Allowed"
            if rdata.find("HTTP") != -1:
                raise Exception, "HTTP Error : %s" % rdata
            
            # Checking XML header from response
            rdata = rdata.split("\n")

            if rdata[0].replace("\r", "") != '<?xml version="1.0"?>':
                raise Exception, "Unrecognized xml-header as first line in reply from ILO" 

            # Add dummytag in order to parse the separate statements
            data_with_dummy = "<DUMMY>\n" + "\n".join(rdata[1:]) + "\n</DUMMY>"
            # Doing bogus XML-fix
            try:
                attr = self._parseRIBCL(data_with_dummy)
            except Exception, e:
                raise Exception, "Error parsing XML : %s" % e

            # Analyzing output
            res = self._analyzeOutput(attr)
            self.log.debug("Got Result : %s", res)
            if res:
                result = result + res
        self.log.debug("All results : %s", result)
        return result
    
    # ---- Login -> execute command -> close connection ----
    def _loginExecClose(self, cmd, options):

        if not options:
            raise Exception, "Not enough options given to perform operation"

        options = options.split()
        if len(options) < 3:
            raise Exception, "Not enough options given to perform operation"

        host = options[0]
        user = options[1]
        passwd = options[2]

        ipaddr = host.split(":")[0]
        if self.options and self.options[0] == "nossl":
            port = _DEFAULT_ILO_NOSSLPORT
        else:
            port = _DEFAULT_ILO_SSLPORT

        try:
            port = host.split(":")[1]
        except:
            pass
        
        if self.options and self.options[0] == "nossl":
            self.log.debug("Opening non-SSL socket to '%s' port %d", ipaddr, port)
            s = _iLOSocket(ipaddr, port)
        else:
            self.log.debug("Opening SSL socket to '%s' port %d", ipaddr, port)
            s = _iLOSSLSocket(ipaddr, port)

        xml_command = self._insertPassword(cmd, user, passwd)

        # Executing command
        response = self._executeCommand(s, xml_command)
        s.close()
        return response

    # ----------------------------------------    
    # Public functions
    # ----------------------------------------      
    
    def powerStatus(self, node, options):
        self.log.debug("%s: Checking powerstatus for %s" % (self.__name__, node))
        status = kusu.power.STATUSNA
        result = self._loginExecClose(_RIBCL_POWER_STATUS, options)
        if result[0] == "OFF":
            status = kusu.power.STATUSOFF
        elif result[0] == "ON":
            status = kusu.power.STATUSON
        else:
            self.log.debug("%s: Status command failed for node %s (%s)" % (self.__name__, node, result))

        return status

    def powerOff(self, node, options):
        self.log.debug("%s: Turning off %s" % (self.__name__, node))
        result = self._loginExecClose(_RIBCL_POWER_OFF, options)
        if not result:
            self.log.debug("%s: Finished iLO successfully" % (self.__name__))
        else:
            raise Exception, "Poweroff command failed for node %s (%s)" % (node, result)

        return kusu.power.SUCCESS

    def powerOn(self, node, options):
        self.log.debug("%s: Turning on %s" % (self.__name__, node))
        result = self._loginExecClose(_RIBCL_POWER_ON, options)
        if not result:
            self.log.debug("%s: Finished iLO successfully" % (self.__name__))
        else:
            raise Exception, "Poweron command failed for node %s (%s)" % (node, result)
        return kusu.power.SUCCESS

    def powerCycle(self, node, options):
        status = self.powerStatus(node, options)
        if status == kusu.power.STATUSON:
            self.log.debug("%s: powerstatus is ON - cycling node : %s" % (self.__name__, node))
            result = self._loginExecClose(_RIBCL_POWER_CYCLE, options)
            if not result:
                self.log.debug("%s: Finished iLO successfully" % (self.__name__))
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
        result = self._loginExecClose(_RIBCL_UID_STATUS, options)
        if result[0] == "OFF":
            status = kusu.power.STATUSOFF
        elif result[0] == "ON":
            status = kusu.power.STATUSON
        elif result[0] == "FLASHING":
            status = kusu.power.STATUSON
        else:
            self.log.debug("%s: UID status command failed for node %s (%s)" % (self.__name__, node, result))

        return status

    def uidOff(self, node, options):
        self.log.debug("%s: Turning UID off %s" % (self.__name__, node))
        result = self._loginExecClose(_RIBCL_UID_OFF, options)
        if result[0] == "OFF":
            self.log.debug("%s: Finished iLO successfully" % (self.__name__))
        else:
            raise Exception, "UID off command failed for node %s (%s)" % (node, result)

        return kusu.power.SUCCESS

    def uidOn(self, node, options):
        self.log.debug("%s: Turning UID on %s" % (self.__name__, node))
        result = self._loginExecClose(_RIBCL_UID_ON, options)
        if result[0] == "ON":
            self.log.debug("%s: Finished iLO successfully" % (self.__name__))
        else:
            raise Exception, "UID on command failed for node %s (%s)" % (node, result)
        return kusu.power.SUCCESS

kusu.power.registerPlugin(hpilo)
