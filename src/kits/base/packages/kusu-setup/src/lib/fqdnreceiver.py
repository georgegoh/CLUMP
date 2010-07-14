#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id$
#
# Copyright (C) 2010 Platform Computing Inc.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of version 2 of the GNU General Public License as published by the
# Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

import sys
import socket
try:
    import subprocess
except ImportError:
    from popen5 import subprocess

from path import path
from kusu.util.verify import verifyFQDN
import message

HOSTS = '/etc/hosts'

class FQDNReceiver(object):

    def __init__(self):
        super(FQDNReceiver, self).__init__()
        self.hostname = ''
        self.prov_domain = None
        self.pub_domain = None

    def pub_dns_discover(self):

        self.pub_domain = socket.gethostname()
        return self._verify_fqdn(self.pub_domain)

    def _verify_fqdn(self, fqdn):

       if not verifyFQDN(fqdn):
           fqdn_probed = False
       else:
           fqdn_probed = True

       return fqdn_probed

    def _probe_fqdn(self, ip):

        if not path(HOSTS).exists():
            fqdn_probed = False
        else:
            fqdn_probed = self._read_hosts()

        if not fqdn_probed:
            message.display("Kusu Setup failed to discover Fully Qualified Domain Name (FQDN) for provision interface.")
            self._prompt_for_fqdn(network_type)

        return True

    def _read_hosts(self):

        fp = open(HOSTS, 'r')
        for line in fp.readlines():
            line = line.strip()
            if line.startswith('#'):
                continue
            if ip is None or not line.find(ip) < 0:
                values = line.split()
                self.prov_domain = values[1].split('.', 1)[-1]
                break

        fp.close()

        return self._verify_fqdn(self.prov_domain)

    def get_fqdn(self):
        """ Interface to expose the provision and public domains. """
        self._prompt_for_fqdn()
        return (self.prov_domain, self.pub_domain)

    def _prompt_for_fqdn(self):
        st = False
        while not st:
            self.prov_domain = message.input("\nPlease specify private cluster domain (example private.dns.zone):")

            st, msg = verifyFQDN(self.prov_domain)
            if msg:
                message.failure("Input Error: %s" % msg, 0)

    fqdn = property(get_fqdn)

if __name__ == "__main__":
    fqdn = FQDNReceiver()
    #fqdn.probe('172.20.0.1')
