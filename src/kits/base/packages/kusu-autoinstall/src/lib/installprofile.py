#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
# 

from kusu.util.errors import *
import time
import os
from path import path

class BaseInstall:

    getattr_dict = { 'diskprofile' : None,
                     'networkprofile' : None,
                     'packageprofile' : None,
                     'rootpw': None,
                     'tz': None,
                     'installsrc': None,
                     'lang': None,
                     'dbs': None,
                     'prefix': None, 
                     'keyboard': None,
                     'diskorder' : None}

    def __init__(self, db, ngname, prefix=None):
        """prefix for the root directory"""

        if prefix:
            if path(prefix).exists():
                self.prefix = prefix
            else:
                raise InvalidPathError, "path '%s' not found" % prefix

        self.dbs = db
        self.packageprofile = self._getPackageProfile(ngname)

    def __getattr__(self, name):
        if name in self.getattr_dict.keys():
            return self.getattr_dict[name]
        else:
            raise AttributeError, "%s instance has no attribute '%s'" % \
                                  (self.__class__, name)

    def __setattr__(self, item, value):
        if item in self.getattr_dict.keys():
            if item == 'rootpw':
                value = self._makeRootPw(value)
 
            self.getattr_dict[item] = value
        else:
             raise AttributeError, "%s instance has no attribute '%s'" % \
                                  (self.__class__, item)

    def _makeRootPw(self, rootpw):
        pass

    def _getPackageProfile(self, ngname):
        # There can only be 1 installer. Guaranteed by the db. 
        installer = self.dbs.NodeGroups.select_by(ngname=ngname)[0]
        try:
            components = [component.cname for component in installer.components \
                          if not component.kit.isOS]

            pkgs = [pkg.packagename for pkg in installer.packages]

            # also add all kit RPMs
            kitrpms = ["kit-%s" % kit.rname
                       for kit in self.dbs.Kits.select()
                       if not kit.isOS]

            return components + pkgs + kitrpms
        except AttributeError:
            raise AttributeError, 'components: %s' % str(installer.components)

class Kickstart(BaseInstall):
    def __init__(self, db, prefix=None):
        BaseInstall.__init__(self, db, prefix)
        
    def _makeRootPw(self, rootpw):
        import md5crypt
        import time

        # Not support unicode in root password
        return md5crypt.md5crypt(str(rootpw), str(time.time()));

class RHEL5Kickstart(Kickstart):
    def __init__(self, db, prefix=None):
        Kickstart.__init__(self, db, prefix)
        self.getattr_dict['instnum'] = None        

