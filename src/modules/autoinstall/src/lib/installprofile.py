#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
# 

import time

class BaseInstall:

    getattr_dict = { 'diskprofile' : None,
                     'package' : [],
                     'networkprofile' : None,
                     'packageprofile' : None,
                     'rootpw': None,
                     'tz': None,
                     'installsrc': None,
                     'lang': None }

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

class Kickstart(BaseInstall):
    def __init__(self):
        for k in ['keyboard']:
            self.getattr_dict[k] = None
 
    def _makeRootPw(self, rootpw):
        import md5crypt
        import time

        # Not support unicode in root password
        return md5crypt.md5crypt(str(rootpw), str(time.time()));



    

