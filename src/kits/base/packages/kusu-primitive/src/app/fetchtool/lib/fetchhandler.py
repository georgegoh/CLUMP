#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
# 
# $Id$ 
# 
# Copyright (C) 2010 Platform Computing Inc. 
# 

import base64
import shutil
import socket
import urllib2
import urlparse
import subprocess
import xmlrpclib
import time

from path import path

from primitive.fetchtool.helper import copyDir
from primitive.fetchtool.helper import isDestWritable
from primitive.fetchtool.helper import decipherWgetErrors
from primitive.fetchtool.helper import checkUserPassFormat
from primitive.core.errors import HTTPAuthException
from primitive.core.errors import ProxyAuthException
from primitive.core.errors import UnknownHostException
from primitive.core.errors import FetchException
from primitive.core.errors import RHNServerException
from primitive.support.proxy import Proxy, HTTPSProxyTransport, getUserinfoFromURI

# urlparse by default does not recognise
# these protocols, so we add them.
for scheme in ('rhn', 'rhns', 'you', 'scp'):
    urlparse.uses_netloc.insert(0, scheme)
    urlparse.uses_query.insert(0, scheme)


class ProtocolFetchHandler(object):
    def __init__(self, **kwargs):
        self.required_args = []
        self.proxy = None

    def fetch(self, **kwargs):
        raise NotImplementedError


class FileFetchHandler(ProtocolFetchHandler):
    ''' FileFetchHandler class is a subclass of FetchHandler which handles file
        transfers local to the system, e.g., copying from a dvd mounted at
        /media/dvd onto /data/foo. It can copy a single file or a directory
        to the specified destination directory.
    '''
    def __init__(self, **kwargs):
        super(FileFetchHandler, self).__init__(**kwargs)

    def fetch(self, **kwargs):
        ''' Check if we are fetching a single file or
            a directory and act accordingly.
        '''
        if kwargs['fetchdir']:
            dest = self.copyDir(kwargs['uri'],
                                kwargs['destdir'],
                                kwargs['overwrite'])
        else:
            dest = self.copyFile(kwargs['uri'],
                                 kwargs['destdir'])
        return (True, dest)

    def copyFile(self, src, dest_dir):
        ''' Copy only one file from the src to destdir. '''
        dest = (path(dest_dir) / path(src).basename()).realpath()
        src_file = path(urlparse.urlparse(src)[2]).realpath()
        if src_file != dest:
            shutil.copy2(src_file, dest)
        return dest 

    def copyDir(self, src_uri, dest_dir, overwrite):
        ''' Fetch the srcdir to destdir. '''
        src_dir = urlparse.urlparse(src_uri)[2]
        # This is a call to the global copydir defined in the helper.
        copyDir(src_dir, dest_dir,
                recursive=True,
                overwrite=overwrite)
        return dest_dir


class HTTPFetchHandler(ProtocolFetchHandler):
    ''' HTTPFetchHandler class is a subclass of FetchHandler which fetches file(s)
        from a HTTP location to a directory local to the system, e.g.,
        downloading "http://www.foo.com/foo.txt" as "foo.txt" in the local
        output directory, or mirroring "http://www.bar.com/foodir/" directory
        structure on the local filesystem.
    '''
    def __init__(self, **kwargs):
        super(HTTPFetchHandler, self).__init__(**kwargs)

    def _getProxyForWget(self, schema):
        '''return <schema>_proxy environ for wget. And if the proxy userinfo contains '@', 
           we should use --proxy-user/--proxy-passwd in wget.
        '''
        if not self.proxy:
            return None, None

        proxyEntry = self.proxy.proxies[schema]
        wget_cmd = []
        if proxyEntry.count('@') > 1:
            proxyEntry, user, password = getUserinfoFromURI(proxyEntry)
            wget_cmd.append('--proxy-user')
            wget_cmd.append(user)
            wget_cmd.append('--proxy-passwd')
            wget_cmd.append(password)

        return {schema+'_proxy':proxyEntry}, wget_cmd

    def isServerAvailable(self, host_port):
        try:
            socket.gethostbyname(host_port.rsplit(':', 1)[0])
        except socket.gaierror:
            return False
        return True

    def _validateURIAuth(self, uri, user, passwd):
        '''To validate the username/password for a URI, as well as through a proxy server'''
        if self.proxy:
            proxy_handler, proxy_auth_handler = self.proxy.getProxyHandler(urlparse.urlsplit(uri)[0])
            opener = urllib2.build_opener(proxy_handler, proxy_auth_handler)
        else:
            opener = urllib2.build_opener()

        # ensure the username and password pair are correct.
        req = urllib2.Request(uri)
        # Didn't use base64.encodestring(). Reason: had '\n' in the middle of the string.
        base64string = base64.b64encode('%s:%s' % (user, passwd))
        authheader = 'Basic %s' % base64string
        req.add_header('Authorization', authheader)
        try:
            opener.open(req)
        except urllib2.URLError, e:
            if hasattr(e, 'code'):
                if e.code == 401:
                    raise HTTPAuthException, 'Site authentication failed.'
                elif e.code == 403:
                    raise HTTPAuthException, 'Requested resource is forbidden. Please check your account.'
                elif e.code == 407:
                    raise ProxyAuthException, 'Proxy authentication failed.'
                else:
                    raise FetchException, 'Unable to authenticate against %s. HTTP return code was %d.' % (uri, e.code)
            elif hasattr(e, 'reason'):
                raise FetchException, 'Server is unreachable, reason: %s' % e.reason
        else:
            return True

    def fetch(self, **kwargs):
        ''' Check if we are fetching a single file or
            mirroring a directory and act accordingly.
        '''
        if 'proxy' in kwargs and kwargs['proxy']:
            self.proxy = kwargs['proxy']

        if not checkUserPassFormat(kwargs['uri']):
            raise InvalidUserPassPairException, 'Invalid username/password given.'

        self.validateArgs(**kwargs)

        if kwargs['fetchdir']:
            dest = self.mirrorDir(kwargs['uri'],
                           kwargs['destdir'])
        else:
            dest = self.downloadFile(kwargs['uri'],
                              kwargs['destdir'])
        return (True, dest)

    def validateArgs(self, **kwargs):
        ''' Override the validate input function with a
            few more checks.
        '''
        uri = kwargs['uri'].strip()
        urlpath, user, passwd = getUserinfoFromURI(uri)
        netloc = urlparse.urlsplit(urlpath)[1]

        if not self.isServerAvailable(netloc):
            raise UnknownHostException

        if user and passwd:
            self._validateURIAuth(urlpath, user, passwd)

    def downloadFile(self, src_uri, dest_dir):
        ''' Download only one file from the src to destdir. '''
        if src_uri.endswith('/'):
            dest_filename = path(urlparse.urlsplit(src_uri[-1])[2]).basename()
        else:
            dest_filename = path(urlparse.urlsplit(src_uri)[2]).basename()
        if not dest_filename:
            raise FetchException,'Unable to obtain a destination file to download'
        dest_path = path(dest_dir) / dest_filename
        if dest_path.exists():
            dest_path.remove()

        wget_env, wget_proxy = self._getProxyForWget('http')
        wget_cmd = ['wget', '--no-verbose', src_uri, '--directory-prefix', dest_dir]
        wget_cmd.extend(wget_proxy or [])
        p = subprocess.Popen(wget_cmd,
                             env=wget_env,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        retcode = p.wait()
        stderr = p.stderr.readlines()
        if retcode:
            #Raises FetchException on errors.
            decipherWgetErrors(src_uri, stderr)
        return path(path(dest_dir) / dest_filename)

    def mirrorDir(self, src_uri, dest_dir):
        ''' Mirror a remote HTTP directory.
            calls 'wget --no-parent -cut-dirs=XX -nH --mirror'.
        '''
        p = path(urlparse.urlsplit(src_uri)[2]).splitall()
        # Deals with non-ending slash.
        # Non-ending clash url ends up with an empty string in the
        # last index of the list when a splitall is done
        if not p[-1]:
            cutaway = len(p[1:]) - 1
        else: # non-ending slash
            cutaway = len(p[1:])
            src_uri = src_uri + '/' # Append a trailing slash
        if cutaway < 0:
            cutaway = 0

        wget_env, wget_proxy = self._getProxyForWget('http')
        wget_cmd = ['wget', '--no-verbose', '--no-parent',
                    '--cut-dirs=%s' % cutaway, '-nH',
                    '--mirror', src_uri, '--directory-prefix', dest_dir]
        wget_cmd.extend(wget_proxy or [])
        wget = subprocess.Popen(wget_cmd,
                                env=wget_env,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        retcode = wget.wait()
        decipherWgetErrors(src_uri, wget.stderr.readlines())
        return dest_dir


class HTTPSFetchHandler(HTTPFetchHandler):
    ''' HTTPSFetchHandler class subclasses from HTTPFetchHandler, and has
        identical function to its superclass, except that it handles the
        https protocol
    '''
    def __init__(self, **kwargs):
        super(HTTPSFetchHandler, self).__init__(**kwargs)

    def downloadFile(self, src_uri, dest_dir):
        ''' Download only one file from the src to destdir. '''
        # Obtain the destination filename after stripping away trailing Slash
        if src_uri.endswith('/'):
            dest_filename = path(urlparse.urlsplit(src_uri[-1])[2]).basename()
        else:
            dest_filename = path(urlparse.urlsplit(src_uri)[2]).basename()
        if not dest_filename:
            raise FetchException,'Unable to obtain a destination file to download'

        dest_path = path(dest_dir) / dest_filename
        if dest_path.exists():
            dest_path.remove()

        wget_env, wget_proxy = self._getProxyForWget('https')
        wget_cmd = ['wget', '--no-verbose', '--no-check-certificate', src_uri, '--directory-prefix', dest_dir]
        wget_cmd.extend(wget_proxy or [])
        p = subprocess.Popen(wget_cmd,
                             env=wget_env,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        retcode = p.wait()
        stderr = p.stderr.readlines()
        if retcode:
            decipherWgetErrors(src_uri, stderr)
        return path(path(dest_dir) / dest_filename)

    def mirrorDir(self, src_uri, dest_dir):
        ''' Mirror a remote HTTPS directory.
            calls 'wget --no-check-certificate --no-parent -nH --mirror'.
        '''
        p = path(urlparse.urlsplit(src_uri)[2]).splitall()
        # Deals with non-ending slash.
        # Non-ending clash url ends up with an empty string in the
        # last index of the list when a splitall is done
        if not p[-1]:
            cutaway = len(p[1:]) - 1
        else: # non-ending slash
            cutaway = len(p[1:])
            src_uri = src_uri + '/' # Append a trailing slash
        if cutaway < 0:
            cutaway = 0

        wget_env, wget_proxy = self._getProxyForWget('https')
        wget_cmd = ['wget', '--no-verbose', '--no-check-certificate', '--no-parent',
                    '--cut-dirs=%s' % cutaway, '-nH',
                    '--mirror', src_uri, '--directory-prefix', dest_dir]
        wget_cmd.extend(wget_proxy or [])
        wget = subprocess.Popen(wget_cmd,
                                env=wget_env,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        retcode = wget.wait()
        decipherWgetErrors(src_uri, wget.stderr.readlines())
        return dest_dir 

class YOUFetchHandler(HTTPSFetchHandler):
    ''' HTTPSFetchHandler class subclasses from HTTPFetchHandler, and has
        identical function to its superclass, except that it handles the
        https protocol
    '''
    def __init__(self, **kwargs):
        super(YOUFetchHandler, self).__init__(**kwargs)

    def fetch(self, **kwargs):
        ''' Check if we are fetching a single file or
            mirroring a directory and act accordingly.
        '''
        if 'proxy' in kwargs and kwargs['proxy']:
            self.proxy = kwargs['proxy']

        if not checkUserPassFormat(kwargs['uri']):
            raise InvalidUserPassPairException, 'Invalid username/password given.'

        # you:// -> https://
        args = urlparse.urlsplit(kwargs['uri'])
        new_args = ['https']
        new_args.extend(args[1:])
        kwargs['uri'] = urlparse.urlunsplit(new_args)

        self.validateArgs(**kwargs)

        dest = self.downloadFile(kwargs['uri'],
                                 kwargs['destdir'])
        return (True, dest)

class RHNFetchHandler(HTTPFetchHandler):
    ''' RHNFetchHandler class can handles the fetch operation from RHN site
    '''
    headers = ['X-RHN-Server-Id',
               'X-RHN-Auth-User-Id',
               'X-RHN-Auth',
               'X-RHN-Auth-Server-Time',
               'X-RHN-Auth-Expire-Offset']
    up2dateURL = 'https://xmlrpc.rhn.redhat.com/XMLRPC'
    #cache for the login info and the login time
    loginInfo = loginTime = None

    def __init__(self, **kwargs):
        super(RHNFetchHandler, self).__init__(**kwargs)
        self.required_args = ['systemid', 'up2dateURL']

    def fetch(self, **kwargs):
        ''' Check if we are fetching a single file or
            mirroring a directory and act accordingly.
        '''                
        if 'proxy' in kwargs and kwargs['proxy']:
            self.proxy = kwargs['proxy']

        self.validateArgs(**kwargs)

        dest = self.downloadFile(kwargs['uri'],
                                 kwargs['destdir'])
        return (True, dest)

    def validateArgs(self, **kwargs):
        ''' Override the validate input function with a
            few more checks for RHN site.
        '''
        self.systemid = kwargs['systemid']
        rhnURL = kwargs['up2dateURL']

        if rhnURL:
            if urlparse.urlsplit(rhnURL)[1] != 'xmlrpc.rhn.redhat.com':
                self.up2dateURL = rhnURL

        netloc = urlparse.urlsplit(self.up2dateURL)[1]
        # check that the host name, user/passwd of rhn is not in the uri.
        if not self.isServerAvailable(netloc):
            raise UnknownHostException

        if self.proxy:
            up2dateServer = xmlrpclib.Server(self.up2dateURL, transport=HTTPSProxyTransport(self.proxy))
        else:
            up2dateServer = xmlrpclib.Server(self.up2dateURL)

        if RHNFetchHandler.loginTime and RHNFetchHandler.loginInfo and not self._isLoginExpired():
            return

        try:
            RHNFetchHandler.loginTime = time.time()
            RHNFetchHandler.loginInfo = up2dateServer.up2date.login(self.systemid)
        except:
            RHNFetchHandler.loginTime = RHNFetchHandler.loginInfo = None
            raise RHNServerException, 'Invalid RHN system ID'

    def _isLoginExpired(self):
        #Check if expired, offset is stored in "X-RHN-Auth-Expire-Offset"
        currentTime = time.time()
        expireTime = RHNFetchHandler.loginTime + float(RHNFetchHandler.loginInfo['X-RHN-Auth-Expire-Offset'])
        return currentTime > expireTime

    def downloadFile(self, src_uri, dest_dir):
        ''' Download only one file from the src to destdir. src_uri format: rhn://channel/packagename'''
        # Obtain the destination filename after stripping away trailing Slash
        if src_uri.endswith('/'):
            dest_filename = path(urlparse.urlsplit(src_uri[-1])[2]).basename()
        else:
            dest_filename = path(urlparse.urlsplit(src_uri)[2]).basename()
        if not dest_filename:
            raise FetchException,'Unable to obtain a destination file to download'

        dest_path = path(dest_dir) / dest_filename
        if dest_path.exists():
            dest_path.remove()

        channelLabel, filepath = urlparse.urlsplit(src_uri)[1:3]
        if dest_path.ext == '.rpm':
            url = self.up2dateURL + '/$RHN/%s/getPackage/%s' % (channelLabel, dest_filename)
        else:
            #For repodata/primary.xml.gz
            url = self.up2dateURL + '/$RHN/%s%s' % (channelLabel, filepath)

        wget_cmd = ['wget', '--no-verbose', '--no-check-certificate', url, '--directory-prefix', dest_dir]
        #add login auth headers
        for h in self.headers:
            if RHNFetchHandler.loginInfo.has_key(h):
                wget_cmd.append('--header')
                wget_cmd.append('%s: %s' % (h, RHNFetchHandler.loginInfo[h]))

        wget_env, wget_proxy = self._getProxyForWget('https')
        wget_cmd.extend(wget_proxy or [])
        p = subprocess.Popen(wget_cmd,
                             env=wget_env,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        retcode = p.wait()
        stderr = p.stderr.readlines()
        if retcode:
            decipherWgetErrors(src_uri, stderr)
        return path(path(dest_dir) / dest_filename)
