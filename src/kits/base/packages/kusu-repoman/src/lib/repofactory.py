#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id$
#
# Copyright (C) 2010 Platform Computing Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
#

from kusu.repoman import repo, tools
from kusu.util.errors import *
from path import path

class RepoFactory(object):

    class_dict = { 'fedora' : {'6': repo.Fedora6Repo},
                   'centos' : {'5': repo.Centos5Repo},
                   'rhel'   : {'5': repo.Redhat5Repo},
                   'sles'   : {'10': repo.SLES10Repo},
                   'opensuse' : {'10.3': repo.OpenSUSE103Repo},
                   'scientificlinux' : { '5': repo.ScientificLinux5Repo},
                   'scientificlinuxcern' : { '5': repo.ScientificLinuxCern5Repo}}

    def __init__(self, db, prefix='/', test=False):
        """Creates a RepoFactory.

           Accepts the following arguments:
           prefix: prefix of the root directory, if any
           db: The DB class object
        """
        self.db = db
        self.prefix = path(prefix)
        self.test = test

    def getRepo(self, repoid):
        """Returns the repo obj for that repo"""

        os_name, os_major, os_minor, os_arch = tools.getOS(self.db, repoid)

        if os_name == 'opensuse':
            os_version = '%s.%s' % (os_major, os_minor)
        else:
            os_version = os_major

        if not self.class_dict.has_key(os_name) or not self.class_dict[os_name].has_key(os_version):
            raise UnsupportedOS, "%s %s not supported" % (os_name, os_version)

        r = self.class_dict[os_name][os_version](os_arch, self.prefix, self.db)
        r.repoid = repoid
        
        r.repo_path = r.getRepoPath()

        return r
