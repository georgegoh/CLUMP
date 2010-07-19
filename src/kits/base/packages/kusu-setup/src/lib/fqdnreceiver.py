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

class FQDNReceiver(object):

    def __init__(self):
        self.hostname = ''
        self.prov_domain = None
        self.pub_domain = None

    def pub_dns_discover(self):
        self.pub_domain = socket.getfqdn()

        return (len(self.pub_domain.split('.'))>1 and \
                verifyFQDN(self.pub_domain)[0])

    def get_fqdn(self):
        """ Interface to expose the provision and public domains. """
        self._prompt_for_fqdn()
        return (self.prov_domain, self.pub_domain)

    def _prompt_for_fqdn(self):
        st = False
        while not st:
            self.prov_domain = message.input("\nSpecify private cluster domain "
                                             "(e.g. private.dns.zone):")

            st, msg = verifyFQDN(self.prov_domain)
            if msg:
                message.failure("Input Error: %s" % msg, 0)

    fqdn = property(get_fqdn)

if __name__ == "__main__":
    fqdn = FQDNReceiver()
    #fqdn.probe('172.20.0.1')
