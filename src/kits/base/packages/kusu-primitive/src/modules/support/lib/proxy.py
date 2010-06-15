#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
# 
# $Id$ 
# 
# Copyright (C) 2010 Platform Computing Inc. 
# 

import xmlrpclib
import socket
import urlparse
import urllib
import urllib2

from primitive.core.errors import UnsupportedProxyProtocolException
from primitive.core.errors import UnknownProxyHostException
from primitive.core.errors import BadProxyURIFormatException

def getUserinfoFromURI(uri):
    """getUserinfoFromURI('schema://[username:password@]somewhere') -->
        (schema://somewhere, username, password)"""
    schema = urlparse.urlsplit(uri)[0]
    if not schema:
        return uri, None, None

    try:
        #Reserved chars maybe in the user info, e.g. '@', '/'
        userinfo, host_path = uri.rsplit('@', 1)
    except ValueError:
        #no user info
        return uri, None, None

    userinfo = userinfo[len(schema)+3:]
    new_uri = "%s://%s" % (schema, host_path)
    user, passwd = urllib.splitpasswd(userinfo)
    
    return new_uri, user, passwd


class Proxy(object):
    supported_protocols = ['http','https']
    def __init__(self, proxy):
        """Create new Proxy object.

        proxy: dictionary containing settings for each protocol, for example
            {'http': 'http://user:password@host:port'}

        """
        if not isinstance(proxy, dict):
            raise TypeError, 'Wrong parameter type, dictionary is expected.'

        self.proxies = proxy
        self._validateProxy()

    def _validateProxy(self): 
        if not self.proxies:       #at least one item.
            raise ValueError, 'Must provide at least one proxy item for creating Proxy object.'

        for protocol, proxy_uri in self.proxies.iteritems(): 
            if protocol not in self.supported_protocols:
                raise UnsupportedProxyProtocolException, 'Only support proxy for %s' % self.supported_protocols

            if not self._isProxyURIAvailable(proxy_uri):
                raise BadProxyURIFormatException, 'Wrong proxy URI format, only support http://[username:password@]proxy_host[:port], and given %s.' % proxy_uri

            if '@' in proxy_uri:
                hostinfo = proxy_uri.rsplit('@', 1)[1]
            else:
                hostinfo = urlparse.urlsplit(proxy_uri)[1]
            if not self._isProxyServerAvailable(hostinfo):
                raise UnknownProxyHostException, 'Unknown proxy server name, please check your proxy settings'

    def _isProxyURIAvailable(self, proxy_uri):
        #Firstly split the user info, as some reserved chars in it will cause urlparse not work
        uri, user, passwd = getUserinfoFromURI(proxy_uri)
        #valid for the user part if given
        if (not user and passwd) or (user and not passwd):
            return False

        scheme, hostinfo, urlpath, params, query, fragment = urlparse.urlparse(uri)
        if not (scheme and hostinfo) or urlpath or params or query or fragment:
            return False

        #The proxy server must be a http site(now we only support it).
        if scheme not in ['http']:
            return False

        #valid for the host part, host[:port]
        if ':' not in hostinfo:
            return True  #no port info
        else:
            host, port = hostinfo.rsplit(':',1)
            return host and port.isdigit()

    def _isProxyServerAvailable(self, host_port):
        try:
            socket.gethostbyname(host_port.rsplit(':', 1)[0])
        except socket.gaierror:
            return False
        return True

    def getProxyHandler(self, protocol):
        """get default proxy handler and auth handler objects for the Proxy setting"""
        if protocol in self.proxies:
            proxy_uri = self.proxies[protocol]
        else:
            return None, None

        proxyserver, user, passwd = getUserinfoFromURI(proxy_uri)
        proxy_handler = urllib2.ProxyHandler({protocol:proxyserver})
        proxy_auth_handler = None
        if user and passwd:
            proxy_auth_handler = urllib2.ProxyBasicAuthHandler(DumbProxyPasswordMgr())
            proxy_auth_handler.add_password(None, None, user, passwd)

        return proxy_handler, proxy_auth_handler


class HTTPSProxyTransport(xmlrpclib.SafeTransport):
    def __init__(self, proxy):
        self.proxy = proxy

    def request(self, host, handler, request_body, verbose):
        self.verbose = verbose
        url='https://'+host+handler

        request = urllib2.Request(url)
        request.add_data(request_body)

        # Note: 'Host' and 'Content-Length' are added automatically
        request.add_header("User-Agent", self.user_agent)
        request.add_header("Content-Type", "text/xml")

        proxy_handler, proxy_auth_handler = self.proxy.getProxyHandler('https')
        opener = urllib2.build_opener(proxy_handler, proxy_auth_handler)
        f=opener.open(request)
        return self.parse_response(f)


#refer http://bugs.python.org/issue1519816
class DumbProxyPasswordMgr:
    """workaround for proxy authentication bug in urllib2"""
    def __init__(self):
        self.user = self.passwd = None

    def add_password(self, realm, uri, user, passwd):
        self.user = user
        self.passwd = passwd

    def find_user_password(self, realm, authuri):
        return self.user, self.passwd
