#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import socket
import xmlrpclib
import urllib2
import re

from kusu.util import rpmtool
from kusu.util.errors import rhnInvalidLoginError, rhnInvalidSystemError, \
                             rhnURLNotFound, rhnUnknownError, rhnServerError, \
                             rhnError, rhnUnknownMethodError, rhnNoBaseChannelError, \
                             rhnFailedDownloadRPM, rhnInvalidServerID

class RHN:
    headers = ['X-RHN-Server-Id',
               'X-RHN-Auth-User-Id',
               'X-RHN-Auth',
               'X-RHN-Auth-Server-Time',
               'X-RHN-Auth-Expire-Offset']

    rhnURL = 'http://rhn.redhat.com/rpc/api'
    up2dateURL = 'http://xmlrpc.rhn.redhat.com/XMLRPC'

    # From rhnserver.py:
    #if fault.faultCode == -3:
    #    # This username is already taken, or the password is incorrect.
    #    exception = up2dateErrors.AuthenticationOrAccountCreationError(fault.faultString)
    #elif fault.faultCode == -2:
    #    # Invalid username and password combination.
    #    exception = up2dateErrors.AuthenticationOrAccountCreationError(fault.faultString)
    #elif fault.faultCode == -1:
    #    exception = up2dateErrors.UnknownMethodException(fault.faultString)
    #elif fault.faultCode == -13:
    #    # Username is too short.
    #    exception = up2dateErrors.LoginMinLengthError(fault.faultString)
    #elif fault.faultCode == -14:
    #    # too short password
    #    exception = up2dateErrors.PasswordMinLengthError(
    #                              fault.faultString)
    #elif fault.faultCode == -15:
    #    # bad chars in username
    #    exception = up2dateErrors.ValidationError(fault.faultString)
    #elif fault.faultCode == -16:
    #    # Invalid product registration code.
    #    # TODO Should this really be a validation error?
    #    exception = up2dateErrors.ValidationError(fault.faultString)
    #elif fault.faultCode == -19:
    #    # invalid
    #    exception = up2dateErrors.NoBaseChannelError(fault.faultString)
    #elif fault.faultCode == -31:
    #    # No entitlement
    #    exception = up2dateErrors.ServiceNotEnabledException(fault.faultString)
    #elif fault.faultCode == -36:
    #    # rhnException.py says this means "Invalid action."
    #    # TODO find out which is right
    #    exception = up2dateErrors.PasswordError(fault.faultString)
    #elif abs(fault.faultCode) == 49:
    #    exception = up2dateErrors.AbuseError(fault.faultString)
    #elif abs(fault.faultCode) == 60:
    #    exception = up2dateErrors.AuthenticationTicketError(fault.faultString)
    #elif abs(fault.faultCode) == 105:
    #    exception = up2dateErrors.RhnUuidUniquenessError(fault.faultString)
    #elif fault.faultCode == 99:
    #    exception = up2dateErrors.DelayError(fault.faultString)
    #elif fault.faultCode == -106:
    #    # Invalid username.
    #    exception = up2dateErrors.ValidationError(fault.faultString)
    #elif fault.faultCode == -600:
    #    # Invalid username.
    #    exception = up2dateErrors.InvalidRegistrationNumberError(fault.faultString)
    #elif fault.faultCode == -601:
    #    # No entitlements associated with given hardware info
    #    exception = up2dateErrors.NotEntitlingError(fault.faultString)

    rhnErrors = { -1: rhnUnknownMethodError,
                  -2: rhnInvalidLoginError,
                  -9: rhnInvalidSystemError,
                  -19: rhnNoBaseChannelError}

    rhnProtoErrors = { 302: rhnURLNotFound,
                       404: rhnURLNotFound}

    def __init__(self, username, password):
        self.rhnServer = xmlrpclib.Server(self.rhnURL)

        cfg = self.getRHNConfig()
        self.up2dateServer = xmlrpclib.Server(cfg['up2dateURL'])

        self.username = username
        self.password = password

    def call(self, method, *args):
        """Make the call"""
        callStr = '%s(%s)' % (method, ','.join(['args[%s]' % i for i in xrange(len(args))]))
        
        try:
            return eval(callStr)
        
        except (socket.error, socket.herror, socket.gaierror, socket.timeout), e:
            raise rhnServerError, e

        except xmlrpclib.ProtocolError, e:
            errCode = e.errcode
            url = e.url
            errMsg = e.errmsg

            if faultCode in self.rhnProtoErrors.keys():
                raise self.rhnProtoErrors[errCode]
            else:
                raise rhnServerError, (errCode, url, errMsg)

        except xmlrpclib.Fault, e:
            faultCode = e.faultCode
            faultStr = e.faultString

            if faultCode in self.rhnErrors.keys():
                raise self.rhnErrors[faultCode]
            else:
                raise rhnError, (failtCode, faultStr)

        except Exception, e:
            raise e

    def getRHNConfig(self):
        #f = open('/etc/sysconfig/rhn/up2date', 'r')
        return {'up2dateURL': self.up2dateURL}
    
    def login(self):
        """login to RHN"""

        self.session = self.call('self.rhnServer.auth.login', self.username, self.password)
        self.loginInfo = self.call('self.up2dateServer.up2date.login', self.getSystemID())

    def logout(self):
        """logout from RHN"""
        self.call('self.rhnServer.auth.logout', 'self.session')
        self.session = None
        self.loginInfo = None

    def getChannels(self, rhnServerID):
        """Get avalable available for rhnServer ID"""
        channels = self.call('self.rhnServer.channel.software.listSystemChannels', self.session, rhnServerID)
        return channels

    def getLatestPackages(self, channelLabel):
        """Get latest rpms from a channel"""
        rpms = self.call('self.rhnServer.channel.software.listLatestPackages', self.session, channelLabel)

        pkgs = []
        for r in rpms:
            name = r['package_name']
            version = r['package_version']
            release = r['package_release']
            epoch = r['package_epoch']
            arch = r['package_arch_label']

            # None epoch is returned as " "
            if not epoch.strip():
                epoch = None

            r = rpmtool.RPM(name = name,
                            version = version,
                            release = release,
                            epoch = epoch,
                            arch = arch)

            pkgs.append(r)
        return pkgs
       
    def getSystemID(self):
        f = open('/etc/sysconfig/rhn/systemid', 'r')
        systemid = f.read()
        f.close()

        return systemid

    def getServerID(self):
        """Get the sever ID"""
        systemID = xmlrpclib.loads(self.getSystemID())[0][0]['system_id']

        mt = re.compile('\d+').search(systemID)
    
        if mt:
            return int(mt.group())
        else:
            raise rhnInvalidServerID
    
    def getPackage(self, rpm, channelLabel):
        """Get a RPM from the channel"""
       
        code, msg, content = self._getPackage(rpm, channelLabel)

        if code == 401:
            # Authorization required. Expired session
            # login again
            self.login()
            code, msg, content = self._getPackage(rpm, channelLabel)
 
        if content:
            return content
        else:
            raise rhnFailedDownloadRPM, (code, msg)

    def _getPackage(self, rpm, channelLabel):
        code = None
        msg = None
        content = None

        req = urllib2.Request(self.up2dateURL + '/$RHN/%s/getPackage/%s' % (channelLabel, rpm))
        for h in self.headers:
            if self.loginInfo.has_key(h):
                req.add_header(h, self.loginInfo[h])

        try:
            f = urllib2.urlopen(req)
            content = f.read()
            f.close()
            code = 200
        except urllib2.HTTPError, e :
            code = e.code
            msg = e.msg

        return (code, msg, content)
     
