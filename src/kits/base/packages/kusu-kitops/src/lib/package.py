#!/usr/bin/env python
#  KUSU Package API
# 
#  $Id: package.py 2110 2009-02-27 21:36:10Z ggoh $
# 
#  Copyright 2007 Platform Computing Corporation
# 
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of version 2 of the GNU General Public License as
#  published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

import os
import sys
import rpm
import urllib
import urlparse
from sets import Set
from kusu.util import rpmtool

class ENotImplemented(Exception): pass
class EInvalidPackage(Exception): pass

def PackageFactory(packurl):
    '''Returns an instance deriving from BasePackage that best suits packurl
       Raises ENotImplemented for packages we don't know how to handle
       Raises EInvalidPackage for packages with no ext'''
    tmpfname = ''
    
    rv = urlparse.urlparse(packurl)
    if rv[0]:
        (tmpfname, headers) = urllib.urlretrieve(packurl)
        abspath = os.path.abspath(tmpfname)
    else:
        abspath = os.path.abspath(packurl)

    (fname,ext) = os.path.splitext(abspath)
    if not ext:
        raise EInvalidPackage, 'Provided package with no extention'
    if ext.lower() == '.rpm':
        return RPMPackage(abspath)
    if ext.lower() == '.deb':
        return DebPackage(abspath)
    #future packages here

    raise ENotImplemented, 'Package handling for %s not implemented' % ext
    

class BasePackage:
    '''Abstract class that defines the interface for RPM information retrieval'''

    def __init__(self, packurl):
        self.pkgtype = ''
        # check if packurl is a URL
        self.__tmpfname = ''
        rv = urlparse.urlparse(packurl)
        if rv[0]:
            (self.__tmpfname, headers) = urllib.urlretrieve(packurl)
            self.abspath = os.path.abspath(self.__tmpfname)
        else:
            self.abspath = os.path.abspath(packurl)

    def uniq(lst):
        '''Takes a list as an argument and returns it with duplicates removed.
           Note that the order is NOT preserved'''
        #this really belongs in a separate utility module
        return list(Set(lst))
    uniq = staticmethod(uniq)

    def getExt(self):
        if self.pkgtype:
            return '.'+self.pkgtype
        return ''

    def getName(self):
        pass

    def getVersion(self):
        pass

    def getRelease(self):
        pass

    def getConflicts(self):
        pass

    def getRequires(self):
        pass

    def getArch(self):
        pass

    def getGroup(self):
        pass

class RPMPackage(BasePackage):
    def __init__(self, packurl):
        BasePackage.__init__(self, packurl)
        self.rpm = rpmtool.RPM(packurl)

    def getName(self):
        return self.rpm.getName()

    def getVersion(self):
        return self.rpm.getVersion()

    def getRelease(self):
        return self.rpm.getRelease()

    def getConflicts(self):
        '''Return the contents of the conflicts tag, eliminating duplicates'''
        return self.uniq(self.rpm.getConflicts())
    
    def getRequires(self):
        '''Return the contents of the requires tag, eliminating duplicates'''
        return self.uniq(self.rpm.getRequires())

    def getDescription(self):
        return self.rpm.getDescription()

    def getSummary(self):
        return self.rpm.getSummary()

    def getArch(self):
        return self.rpm.getArch()

    def getGroup(self):
        return self.rpm.getGroup()

    def getFileList(self):
        return self.rpm.getFileList()


class DebPackage(BasePackage):
    '''near future'''
    def __init__(self, packurl):
        BasePackage.__init__(self,packurl)
        self.pkgtype = 'deb'


    def getName(self):
        pass

    def getVersion(self):
        pass

    def getRelease(self):
        pass

    def getConflicts(self):
        pass

    def getRequires(self):
        pass


def RpmUnitTest(fname):
    bp = PackageFactory(fname)
#    bp = RpmPackage(fname)
    print 'Outdated test, exiting...'
    return
    print 'name = %s'      % bp.getName()
    print 'name = %s'      % bp.getRawTag('name')
    print 'version = %s'   % bp.getVersion()
    print 'version = %s'   % bp.getRawTag('version')
    print 'release = %s'   % bp.getRelease()
    print 'release = %s'   % bp.getRawTag('release')

    print 'conflicts(uniq) = %s' % bp.getConflicts()
    print 'conflicts = %s' % bp.getRawTag('conflicts')
    print 'requires(uniq) = %s'  % bp.getRequires()
    print 'requires = %s'  % bp.getRawTag('requires')

    print 'abspath = %s'   % bp.abspath

    try:
        print 'bogus tag = %s' % bp.getRawTag('foobar')
    except KeyError, msg:
        print "RawTag lookup failed: ", msg
    except Exception,msg:
        print "RawTag lookup failed w/ generic Exception: ", msg

    try:
        print 'bogus tag = %s' % bp.getRawTag(rpm.RPMTAG_NME)
    except AttributeError, msg:
        print 'Invalid RPMTAG name provided - most likely misspelled: ',msg
    except Exception,msg:
        print "RawTag lookup failed w/ generic Exception: ", msg
        

if __name__ == "__main__":
    fname = sys.argv[1]
    RpmUnitTest(fname)
