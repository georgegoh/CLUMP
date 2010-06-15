#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from path import path
from kusu.core import rcplugin
import string

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'min_uid_gid'
        self.desc = 'Setting up minimum uid and gid'
        self.ngtypes = ['installer', 'compute', 'compute-imaged', 'compute-diskless']
        self.delete = True

    def run(self):
        """
        Set up minimum UID and GID for all nodes.
        Basically, update /etc/login.defs as follows:
        - Set UID_MIN to 10000
        - Set GID_MIN to 10000
        """
        logindefs = path('/etc/login.defs')
        lines = logindefs.lines()
        for i,line in enumerate(lines):
            if line[0] == '#' or line.strip() == '':
                # Skip comments and blank lines
                continue
            # Use string.split instead of line.split because
            # the latter does not accept maxsplit=1 argument.
            key, discard = string.split(line, maxsplit=1)
            if key in ['UID_MIN', 'GID_MIN']:
                # Replace the line
                lines[i] = "%s\t\t\t10000" % key

        logindefs.write_lines(lines)

        return True

