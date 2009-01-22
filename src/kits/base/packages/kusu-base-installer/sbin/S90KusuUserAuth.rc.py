#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from path import path
from kusu.core import rcplugin
import sys

ETC_DEFAULT_PASSWD = """# This file contains some information for
# the passwd (1) command and other tools
# creating or modifying passwords.

# Define default crypt hash
# CRYPT={des,md5,blowfish}
CRYPT=des

# Use another crypt hash for group passwowrds.
# This is used by gpasswd, fallback is the CRYPT entry.
# GROUP_CRYPT=des

# We can override the default for a special service
# by appending the service name (FILES, YP, NISPLUS, LDAP)

# for local files, use a more secure hash. We
# don't need to be portable here:
CRYPT_FILES=blowfish
# sometimes we need to specify special options for
# a hash (variable is prepended by the name of the
# crypt hash).
BLOWFISH_CRYPT_FILES=5

# For NIS, we should always use DES:
CRYPT_YP=des
"""

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'user_auth'
        self.desc = 'Setting up User Authentication'
        self.ngtypes = ['installer']
        self.delete = True

    def run(self):
        """
        Configure user authentication according to the authentication 
        scheme set in AppGlobals.KusuAuthScheme.
        """
        authScheme = self.dbs.AppGlobals.selectfirst_by(kname='KusuAuthScheme').kvalue

        if authScheme == 'files':
            # For local file authentication scheme, generate 
            # the /etc/pam.d/system-auth-ac file needed by
            # rhel/centos nodes to use pam_unix2.so.
            pam_conf_file = path('/etc/pam.d/system-auth-ac')
            self.runCommand('/opt/kusu/bin/genconfig pam_conf > %s' % pam_conf_file)

            if self.os_name in ['rhel', 'centos', 'redhat']:
                # rhel/centos needs this file to tell pam_unix2.so
                # to generate blowfish passwords. sles already has
                # this file.
                etc_default_passwd = path('/etc/default/passwd')
                if not etc_default_passwd.dirname().exists():
                    etc_default_passwd.dirname().makedirs()
                etc_default_passwd.write_text(ETC_DEFAULT_PASSWD)

        return True

