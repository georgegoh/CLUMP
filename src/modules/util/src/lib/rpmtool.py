#! /usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

"""A collection of RPM utilities"""

import rpm
import os
import types
import gzip
import tempfile
from path import path

from kusu.util.errors import *
from kusu.util.structure import Struct

try:
    import subprocess
except:
    from popen5 import subprocess

class RPMCollection(Struct):
    def __init__(self):
        Struct.__init__(self)

    def add(self, r):
        """Add a rpmtool.RPM object into the collection"""

        name = r.getName()
        arch = r.getArch()

        if self.has_key(name):
            if not self[name].has_key(arch):
                self[name][arch] = []
        else:
            self[name] = {}
            self[name][arch] = []

        self[name][arch].append(r)

    def sort(self):
        """Sort the collection"""

        for name, val in self.items():
            for arch in val.keys():
                self[name][arch].sort()

    def getList(self):
        """Returns a list of rpms"""

        listing = []
        for val in self.values():
            for r in val.values():
                listing.extend(r)
        return listing

    def RPMExists(self, name, arch=None):
        """Checks whether a rpm exists"""

        if not self.has_key(name):
            return False
        else:
            if arch:
                if self[name].has_key(arch):
                    return True
                else:
                    return False
            else:
                return True 
         
class RPM:
    """A RPM abstraction class"""
    filename = None       # Filename inclduing the absolute path. For e.g.: /tmp/foo.rpm
    hdr = None            # Header object.
    ext = None            # File extenstion. For e.g: .hdr 
    path = None           # The absolute path. For e.g.: /tmp
    fname = None          # The filename. For e.g.: foo.rpm
    file = None           # The filename that was used to init the RPM. 
    rpmtags = dir(rpm)
    
    # Take the attributes out from the RPMTAG_<attribute>
    rpmtags = {}
    for t in dir(rpm):
        if t.find('RPMTAG') == 0:
            attr = t.split('RPMTAG_')[1].lower()  
            val  = getattr(rpm, t)

            rpmtags[attr] = val
    
    def __init__(self, r=None, **kwargs):
        """Accepts the following:
           1. RPM header
           2. RPM header filename (foo.hdr)
           3. RPM filename (foo.rpm)"""
        
        if r:
            if type(r) in [str, unicode]:
                r = path(r).realpath()
                self.ext = r.ext
                self.file = r
                self.path, self.fname = r.splitpath()

                if self.ext  == '.rpm':
                    self.filename = r
                    fd = os.open(self.filename, os.O_RDONLY)
                    ts = rpm.ts()
                    ts.setVSFlags(-1)
                    try:
                        self.hdr = ts.hdrFromFdno(fd)
                    except:
                        raise InvalidRPMHeader, r
                    os.close(fd)
                elif self.ext == '.hdr':
                    self._read_header(r)
                    self.filename = self._getFilename()
                else:
                    raise UnknownFileTypeError, 'Unknown file: %s' % r
            else:
                if type(r) == rpm.hdr:
                    self.hdr = r
                else:
                    raise UnknownFileTypeError, 'Not a rpm header'
        else:
            self.hdr = {}
            name = kwargs['name']
            version = kwargs['version']
            release = kwargs['release']
            arch = kwargs['arch']
            epoch = kwargs['epoch']

            self.hdr[rpm.RPMTAG_NAME] = name
            self.hdr[rpm.RPMTAG_VERSION] = version
            self.hdr[rpm.RPMTAG_RELEASE] = release
            self.hdr[rpm.RPMTAG_EPOCH] = epoch
            self.hdr[rpm.RPMTAG_ARCH] = arch

            if kwargs.has_key('filename') and kwargs['filename']:
                self.filename = kwargs['filename']
            else:
                self.filename = '%s-%s-%s.%s.rpm' % (name, version, release, arch)

        if not self.hdr:
            raise InvalidRPMHeader, "Invalid header"
                    
    def writeHeader(self, dir='.', compress=True):
        """Write rpm header to a directory.

           dir:      Default is the current working directory
           compress: Default is True. Compress header with gzip
        """

        n,e,v,r,a = self.getNEVRA()
        dst = "%s-%s-%s.%s.hdr" % (n,v,r,a)

        if not dir:
            dir = path.getcwd()
            
        dst = path(dir) / dst
        if dst.exits():
            os.unlink(dst)
        
        if compress:
            h_file = gzip.open(dst, 'w')
        else:
            h_file = file(dst, 'wb')
        h_file.write(self.hdr.unload())
        h_file.close()

        return dst
        
    def getFilename(self):
        """Returns the filename of the rpm"""
        if self.filename:
            return path(self.filename)
        else:       
            return None
        
    def getSplitfilename(self):
        """Returns the tuple (path, filename) of the rpm"""
        filename = self.getFilename()

        if filename:
            return path(filename).splitpath()
        else:
            return None

    def getName(self):
        """Returns the name"""
        return self.hdr[rpm.RPMTAG_NAME]
    
    def getArch(self):
        """Returns the arch"""
        return self.hdr[rpm.RPMTAG_ARCH]
    
    def getVersion(self):
        """Returns the version"""
        return self.hdr[rpm.RPMTAG_VERSION]

    def getRelease(self):
        """Returns the release"""
        return self.hdr[rpm.RPMTAG_RELEASE]

    def getEpoch(self):
        """Returns the epoch"""
        if self.hdr[rpm.RPMTAG_EPOCH]:
            return self.hdr[rpm.RPMTAG_EPOCH]
        else:
            return 0
            
    def getNEVRA(self):
        """Returns the name,epoch,version,release,arch"""
        n = self.getName()
        e = self.getEpoch()
        v = self.getVersion()
        r = self.getRelease()
        a = self.getArch()

        return (n,e,v,r,a)

    def getEVR(self):
        """Returns the epoch,version,release"""
        e = self.getEpoch()
        v = self.getVersion()
        r = self.getRelease()

        return (e,v,r)

    def getNVR(self):
        """Returns the name,version,release"""
        n = self.getName()
        v = self.getVersion()
        r = self.getRelease()

        return (n,v,r)

    def getHeader(self):
        """Returns the rpm header"""
        return self.hdr

    def getBuildhost(self):
        """Returns the build host"""

        if rpm.RPMTAG_BUILDHOST in self.hdr.keys():
            return self.hdr[rpm.RPMTAG_BUILDHOST]
        else:
            return None

    def getProvides(self):
        """Returns a list of provides"""

        lst = []

        if rpm.RPMTAG_PROVIDES not in self.hdr.keys():
            return None

        for i in xrange(len(self.hdr[rpm.RPMTAG_PROVIDES])):
            p = self.hdr[rpm.RPMTAG_PROVIDES][i]
            flag = ""
            if self.hdr[rpm.RPMTAG_PROVIDEFLAGS][i] & rpm.RPMSENSE_LESS:
                flag += "<"
            if self.hdr[rpm.RPMTAG_PROVIDEFLAGS][i] & rpm.RPMSENSE_GREATER:
                flag += ">"
            if self.hdr[rpm.RPMTAG_PROVIDEFLAGS][i] & rpm.RPMSENSE_EQUAL:
                flag += "="

            version = self.hdr[rpm.RPMTAG_PROVIDEVERSION][i]

            lst.append( (p, flag, version) )

        if lst:
            return lst
        else:
            return None
    
    def getVendor(self):
        """Returns the vendor"""
        if rpm.RPMTAG_VENDOR in self.hdr.keys():
            return self.hdr[rpm.RPMTAG_VENDOR]
        else:
            return None

    def getInstallTime(self):
        """Returns the installed time
           None if there's no install time"""
        if rpm.RPMTAG_INSTALLTIME in self.hdr.keys():
            return self.hdr[rpm.RPMTAG_INSTALLTIME]
        else:
            return None

    def getFileList(self):
        """Returns the file list"""
        if type(self.hdr) is types.DictType and \
            not self.hdr.has_key(rpm.RPMTAG_FILENAMES):
            return None
        else:
            return self.hdr[rpm.RPMTAG_FILENAMES]

    def getRequires(self):
        """Returns a tuple of the require tag"""
        lst = []

        if rpm.RPMTAG_REQUIRENAME not in self.hdr.keys():
            return None

        for i in xrange(len(self.hdr[rpm.RPMTAG_REQUIRENAME])):
            flag = ""
            if self.hdr[rpm.RPMTAG_REQUIREFLAGS][i] & rpm.RPMSENSE_LESS:
                flag += "<"
            if self.hdr[rpm.RPMTAG_REQUIREFLAGS][i] & rpm.RPMSENSE_GREATER:
                flag += ">"
            if self.hdr[rpm.RPMTAG_REQUIREFLAGS][i] & rpm.RPMSENSE_EQUAL:
                flag += "="

            version = self.hdr[rpm.RPMTAG_REQUIREVERSION][i]

            p = (self.hdr[rpm.RPMTAG_REQUIRENAME][i], flag, version)

            lst.append(p)
        
        if lst:
            return lst
        else:
            return None
        
    def getChangelog(self):
        """Returns the changelog in a dictionary, sorted in reverse chronological order"""
  
        if (rpm.RPMTAG_CHANGELOGNAME not in self.hdr.keys()) or \
           (rpm.RPMTAG_CHANGELOGTEXT not in self.hdr.keys()) or \
           (rpm.RPMTAG_CHANGELOGTIME not in self.hdr.keys()):
            return None
 
        def _cmp_time(self, other):
            return self['TIME'] - other['TIME']
                            
            
        name = self.hdr[rpm.RPMTAG_CHANGELOGNAME]
        text = self.hdr[rpm.RPMTAG_CHANGELOGTEXT]
        time = self.hdr[rpm.RPMTAG_CHANGELOGTIME]
        
        lst = []
        
        for i in xrange(len(name)):
            d = {}
            d['NAME'] = name[i]
            d['TEXT'] = text[i]
            d['TIME'] = time[i]
            
            lst.append(d)

        lst.sort(_cmp_time)
        lst.reverse()
        return lst

    def getAttributes(self):
        """Returns a list of attributes available for the RPM"""
        return self.rpmtags.keys()
    
    def getSummary(self):
        """Returns the summary"""

        if type(self.hdr) is types.DictType and \
            not self.hdr.has_key(rpm.RPMTAG_SUMMARY):
            return None
        else:
            return self.hdr[rpm.RPMTAG_SUMMARY]
    
    def getConflicts(self):
        """Returns the summary"""
    
        if rpm.RPMTAG_CONFLICTS not in self.hdr.keys():
            return None
        else:
            return self.hdr[rpm.RPMTAG_CONFLICTS]

    def getGroup(self):
        """Returns the functionality group of the RPM"""
        return self.hdr[rpm.RPMTAG_GROUP]

    def extract(self, dir):
        """Extract the contents of the RPM to the dir"""

        cmd = 'rpm2cpio %s' % self.getFilename()
        rpm2cpioP = subprocess.Popen(cmd,
                                     shell=True,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)

        cmd = 'cpio -id'
        cpioP = subprocess.Popen(cmd,
                                 cwd=dir,
                                 shell=True,
                                 stdin=rpm2cpioP.stdout,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        cpioP.communicate()

        return cpioP.returncode

    def __eq__(self, other):
        """Determine if 2 rpms are equal"""
               
        n1,e1,v1,r1,a1 = self.getNEVRA()
        n2,e2,v2,r2,a2 = other.getNEVRA()
        x = self._compareEVR((e1,v1,r1),(e2,v2,r2)) 
        
        if n1 == n2 and a1 == a2 and x == 0:
           return True
        else:
            return False

    def __cmp__(self, other):
        """Compare 2 rpms
           Returns: 1  self is newer than other
                    0  a is same version as b
                    -1 other is newer than self
           Raises an exception when both rpms have different name
        """
        n1,e1,v1,r1,a1 = self.getNEVRA()
        n2,e2,v2,r2,a2 = other.getNEVRA()
        x = self._compareEVR((e1,v1,r1),(e2,v2,r2)) 
     
        if n1 == n2:
            if (e1,v1,r1) == (e2,v2,r2):
               return self._compareARCH(a1, a2)
            else:
                return x
        else:
            raise RPMComparisonError, "Different rpms"

    def __repr__(self):
        str = "<%s instance at %s" % (self.__class__, hex(id(self)))
        
        if self.hdr:
            n,e,v,r,a = self.getNEVRA()
            str = str + ". %s:%s-%s-%s.%s" % (e,n,v,r,a)
        
        return str + ">"
   
    def _compareARCH(self, a1, a2):
        """Compare 2 rpms arch using rpm.archscore"""
        s1 = rpm.archscore(a1)
        s2 = rpm.archscore(a2)

        if s1 > s2:
            return -1
        if s1 < s2:
            return 1
        if s1 == s2:
            return 0

    def _compareEVR(self, (e1, v1, r1), (e2, v2, r2)):
        """Use EVR to compare 2 rpms"""
        # a is newer than b: 1
        # a is same version as b: 0
        # b is newer than a: -1
        
        def toStr(a):
            if type(a) != types.StringType and a != None:
                a = str(a)
            return a

        e1 = toStr(e1)
        v1 = toStr(v1)
        r1 = toStr(r1)
        
        e2 = toStr(e2)
        v2 = toStr(v2)
        r2 = toStr(r2)
        
        x = rpm.labelCompare((e1, v1, r1), (e2, v2, r2))
        return x

    def _read_header(self, f):
        """Read rpm header"""
        if not os.access(f, os.R_OK):
            raise FileReadPermissionError, 'Unable to read rpm header: %s' % f
       
        # try yum headers. yum headers are gzipped
        # Can check for \037\213 too in open(f).read(2)
        try:
            blob = gzip.open(f).read()
            self.hdr = rpm.headerLoad(blob)                 
            isGzip = True
        except IOError:
            isGzip = False
        except Exception:
            raise InvalidRPMHeader, 'rpm unable to load header: %s' % f
           
        if not isGzip:
            try:
                blob = open(f, "r").read()
                self.hdr = rpm.headerLoad(blob)                 
            except Exception:
                raise InvalidRPMHeader, 'rpm unable to load header: %s' % f
                
    def __getattr__(self, attr):
        if attr not in self.getAttributes():
            raise AttributeError, "'module' object has no attribute '%s'" % attr
            
        return self.hdr[self.rpmtags[attr]]
                    
    def _getFilename(self):
        """Determine the filename from headers"""
        if self.ext == '.hdr':           
            n,e,v,r,a = self.getNEVRA()
            fname = "%s-%s-%s.%s.rpm" % (n,v,r,a)

            # Try to detect a yum cache or repo
            if self.path.basename() == 'headers':
                pkgdir   = self.path.dirname() / 'packages'
                filename = pkgdir / fname
            
                # yum cache directory stucture
                # /headers.info
                # /headers
                # /packages
                if filename.isfile():
                    self.filename = filename
                    return self.filename
                
                else:
                    pkgdir   = self.path.dirname()
                    filename = self.path / 'header.info'

                    # yum repo
                    # header.info contains the location of the rpm
                    if filename.isfile():
                        search = "%s:%s-%s-%s.%s" % (e,n,v,r,a)
                        f = open(filename)
                        stat = f.readlines()
                        f.close()
                        try:
                            i = [s.split('=')[0] for s in stat].index(search)
                        except:
                            return None
                        
                        filename = pkgdir / stat[i].split('=')[1].strip()

                        if filename.isfile():
                            self.filename = filename
                            return self.filename
                        else:
                            return None
                    else:
                        return None
            
            else:
                # current dir
                filename = self.path / fname
                if filename.isfile():
                    self.filename = filename
                    return self.filename
                else:
                    return None
            
        else:
            # .rpm file
            return self.filename

def getLatestRPM(dirs=[], ignoreErrors=False):
    """Returns a list of the latest rpms"""

    c = RPMCollection()

    for dir in dirs:
        dir = path(dir)
        for r in dir.files():
            if r.ext == '.rpm' and r.basename() != 'TRANS.TBL':
                try:
                    r = RPM(str(r))
                except InvalidRPMHeader, e:
                    if ignoreErrors:
                        continue
                    else:     
                        raise e

                name = r.getName()
                arch = r.getArch()

                if c.RPMExists(name, arch):
                    if r > c[name][arch][0]:
                        c[name][arch][0] = r 
                else:
                    c.add(r)

    return c
