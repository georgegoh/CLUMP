#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import urlparse
import urllib
import httplib
import sys
from path import path
from kusu.util.distro.kusuexceptions import *

class myftpwrapper(urllib.ftpwrapper):
    # Overrides the default behaviour in urllib.
    # Documented under restrictions in urllib

    def retrfile(self, file, type):
        import ftplib
        self.endtransfer()
        if type in ('d', 'D'): cmd = 'TYPE A'; isdir = 1
        else: cmd = 'TYPE ' + type; isdir = 0
        try:
            self.ftp.voidcmd(cmd)
        except ftplib.all_errors:
            self.init()
            self.ftp.voidcmd(cmd)
        conn = None
        if file and not isdir:
            # Use nlst to see if the file exists at all
            try:
                self.ftp.nlst(file)
            except ftplib.error_perm, reason:
                raise IOError, ('ftp error', reason), sys.exc_info()[2]
            # Restore the transfer mode!
            self.ftp.voidcmd(cmd)
            # Try to retrieve as a file
            try:
                cmd = 'RETR ' + file
                conn = self.ftp.ntransfercmd(cmd)
            except ftplib.error_perm, reason:
                # Raise error if 550 too. Do not do a LIST
                #if str(reason)[:3] != '550':
                    #raise IOError, ('ftp error', reason), sys.exc_info()[2]
                raise IOError, ('ftp error', reason), sys.exc_info()[2]
        if not conn:
            # Set transfer mode to ASCII!
            self.ftp.voidcmd('TYPE A')
            # Try a directory listing
            if file: cmd = 'LIST ' + file
            else: cmd = 'LIST'
            conn = self.ftp.ntransfercmd(cmd)
        self.busy = 1
        # Pass back both a suitably decorated object and a retrieval length
        return (addclosehook(conn[0].makefile('rb'),
                             self.endtransfer), conn[1])



class URLCheck:
    
    def _verifyFTP(self, url):
        # Checks only anon FTP
        orig_ftpwrapper = urllib.ftpwrapper
        urllib.ftpwrapper = myftpwrapper
        
        try:
            u = urllib.urlopen(url)
            u.close()
            
            urllib.ftpwrapper = orig_ftpwrapper
            return True

        except Exception, err:        
            urllib.ftpwrapper = orig_ftpwrapper
            
            if len(err.strerror.args) > 1: # Socket error
                raise FTPError, (str(url), str(err.strerror.args[0]), err.strerror.args[1])
            else:
                raise FTPError, (str(url), str(err.strerror.args[0][:3]), err.strerror.args[0][4:])

    def _verifyHTTP(self,url, method='GET'):
        # Checks only anony FTP

        proto, host,url =  urlparse.urlsplit(url)[0:3]
        original_host = host
    
        response = None

        for cnt in xrange(10):
            # Follow redirect up to 10 times
            
            if response:
                url = response.getheader('location')
                #host,url =  urlparse.urlsplit(url)[1:3]
                proto, host,url =  urlparse.urlsplit(url)[0:3]
                if not host:
                    # Not all servers returns the host in Location header
                    host = original_host
            
            conn = httplib.HTTPConnection(host) 
            try:
                conn.request(method, url, headers={'Range':'bytes=0-0'})
            except Exception, err:
                url = urlparse.urlunsplit((proto,host,url,None,None))
                status = str(err.args[0])
                reason = err.args[1]
                raise HTTPError, (url, status, reason)

            response = conn.getresponse()     
            conn.close() # Close the conn asap
            
            if response.status in [200, 206]:
                # Some server does not implement HEAD and will replace with GET
                return True
            elif response.status >= 300 and response.status <=399:
                # A redirect
                pass
            elif response.status in [405, 501]:
                # Server does not understand HEAD method
                # Will attempt to use GET later on
                break
            else:
                # Other error codes
                url = urlparse.urlunsplit((proto,host,url,None,None))
                status = str(response.status)
                reason = response.reason
                raise HTTPError, (url, status, reason)


        return False

    def verify(self, url):

        proto =  urlparse.urlsplit(url)[0].lower()
        
        if proto in ['http']:
            if not self._verifyHTTP(url, 'HEAD'):
                self._verifyHTTP(url, 'GET')

        elif proto in ['ftp']:
            self._verifyFTP(url)

        else:
            # Why are we here?
            raise KusuError
