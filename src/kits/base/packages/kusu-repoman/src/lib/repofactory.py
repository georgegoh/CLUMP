#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from kusu.repoman import repo, tools
from kusu.util.errors import *
from path import path

class RepoFactory(object):

    class_dict = { 'fedora' : {'6': repo.Fedora6Repo},
                   'centos' : {'5': repo.Centos5Repo},
                   'rhel'   : {'5': repo.Redhat5Repo},
                   'sles'   : {'10': repo.SLES10Repo},
                   'opensuse' : {'10.3': repo.OpenSUSE103Repo}}

    def __init__(self, db, prefix='/', test=False):
        """Creates a RepoFactory.

           Accepts the following arguments:
           prefix: prefix of the root directory, if any
           db: The DB clas object
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
