#! /usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

"""A collection of RPM utilities"""

import rpm
import os
import types
import gzip
from path import path

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
    
    def __init__(self, r):
        """Accepts the following:
           1. RPM header
           2. RPM header filename (foo.hdr)
           3. RPM filename (foo.rpm)"""
        
        if type(r) == types.StringType:
            r = path(r).realpath()
            self.ext = r.ext
            self.file = r
            self.path, self.fname = r.splitpath()

            if self.ext  == '.rpm':
                self.filename = r
                fd = os.open(self.filename, os.O_RDONLY)
                ts = rpm.ts()
                ts.setVSFlags(rpm.RPMVSF_NORSA | rpm.RPMVSF_NODSA)
                self.hdr = ts.hdrFromFdno(fd)
                os.close(fd)
            elif self.ext == '.hdr':
                self._read_header(r)
            else:
                raise Exception, 'Unknown filename: %s' % r
        else:
            if type(r) == rpm.hdr:
                self.hdr = r
            else:
                raise Exception, 'Not a rpm header'
        
        if not self.hdr:
            raise Exception, "Invalid header"
        
                    
    def write_header(self, dir=None, compress=True):
        """Write rpm header to a directory.

           dir:      If dir is None, the current directoy will be used
           compress: Default is True. Compress header with gzip
        """

        n,e,v,r,a = self.get_nevra()
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
        
    def get_filename(self):
        """Returns the fileanme of the rpm"""

        if self.filename:
            return self.filename

        if self.ext == '.rpm':
            return self.filename
        elif self.ext == '.hdr':
            return self._get_filename()
        else:
            return None
        
    def get_splitfilename(self):
        """Returns the tuple (path, filename) of the rpm"""
       
        filename = self.get_filename()

        if filename:
            return path(filename).splitpath()
        else:
            return None

    def get_name(self):
        """Returns the name"""
        return self.hdr[rpm.RPMTAG_NAME]
    
    def get_arch(self):
        """Returns the arch"""
        return self.hdr[rpm.RPMTAG_ARCH]
    
    def get_version(self):
        """Returns the version"""
        return self.hdr[rpm.RPMTAG_VERSION]

    def get_release(self):
        """Returns the release"""
        return self.hdr[rpm.RPMTAG_RELEASE]

    def get_epoch(self):
        """Returns the epoch"""
        if self.hdr[rpm.RPMTAG_EPOCH]:
            return self.hdr[rpm.RPMTAG_EPOCH]
        else:
            return 0
            
    def get_nevra(self):
        """Returns the name,epoch,version,release,arch"""
        n = self.get_name()
        e = self.get_epoch()
        v = self.get_version()
        r = self.get_release()
        a = self.get_arch()

        return (n,e,v,r,a)

    def get_evr(self):
        """Returns the epoch,version,release"""
        e = self.get_epoch()
        v = self.get_version()
        r = self.get_release()

        return (e,v,r)

    def get_nvr(self):
        """Returns the name,version,release"""
        n = self.get_name()
        v = self.get_version()
        r = self.get_release()

        return (n,v,r)

    def get_header(self):
        """Returns the rpm header"""
        return self.hdr

    def get_buildhost(self):
        """Returns the build host"""
        return self.hdr[rpm.RPMTAG_BUILDHOST]

    def get_provides(self):
        """Returns a list of provides"""

        lst = []
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
    
    def get_vendor(self):
        """Returns the vendor"""
        return self.hdr[rpm.RPMTAG_VENDOR]

    def get_install_time(self):
        """Returns the installed time
           None if there's no install time"""
        if not self.hdr[rpm.RPMTAG_INSTALLTIME]:
            return None
        else:
            return self.hdr[rpm.RPMTAG_INSTALLTIME]
   
    def get_file_list(self):
        """Returns the file list"""
        return self.hdr[rpm.RPMTAG_FILENAMES]

    def get_requires(self):
        """Returns a tuple of the require tag"""
        lst = []
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
        
    def get_changelog(self):
        """Returns the changelog in a dictionary, sorted in reverse chronological order"""
        
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

    def get_attributes(self):
        """Returns a list of attributes available for the RPM"""
        return self.rpmtags.keys()
    
    def __eq__(self, other):
        """Determine if 2 rpms are equal"""
               
        n1,e1,v1,r1,a1 = self.get_nevra()
        n2,e2,v2,r2,a2 = other.get_nevra()
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
        n1,e1,v1,r1,a1 = self.get_nevra()
        n2,e2,v2,r2,a2 = other.get_nevra()
        x = self._compareEVR((e1,v1,r1),(e2,v2,r2)) 
     
        #if n1 == n2 and a1 == a2:
        #    return x
        #else:
        #    raise Exception, "Different rpms"

        if n1 == n2:
            if (e1,v1,r1) == (e2,v2,r2):
               return self._compareARCH(a1, a2)
            else:
                return x
        else:
            raise Exception, "Different rpms"

    def __repr__(self):
        str = "<%s instance at %s" % (self.__class__, hex(id(self)))
        
        if self.hdr:
            n,e,v,r,a = self.get_nevra()
            str = str + ". %s-%s-%s.%s" % (n,v,r,a)
        
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
            raise Exception, 'Unable to read rpm header: %s' % f
       
        # try yum headers. yum headers are gzipped
        # Can check for \037\213 too in open(f).read(2)
        try:
            blob = gzip.open(f).read()
            self.hdr = rpm.headerLoad(blob)                 
            isGzip = True
        except IOError:
            isGzip = False
        except Exception:
            raise Exception, 'rpm unable to load header: %s' % f
           
        if not isGzip:
            try:
                blob = open(f, "r").read()
                self.hdr = rpm.headerLoad(blob)                 
            except Exception:
                raise Exception, 'rpm unable to load header: %s' % f
                
    def __getattr__(self, attr):
        if attr not in self.get_attributes():
            raise AttributeError, "'module' object has no attribute '%s'" % attr
            
        return self.hdr[self.rpmtags[attr]]
                    
    def _get_filename(self):
        """Determine the filename from headers"""
        if self.ext == '.hdr':           
            n,e,v,r,a = self.get_nevra()
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
                    if filename.isfile()
                        search = "%s:%s-%s-%s.%s" % (e,n,v,r,a)
                        f = open(filename)
                        stat = f.readlines()
                        f.close()
                        try:
                            i = [s.split('=')[0] for s in stat].index(search)
                        except:
                            return None
                        
                        filename = pkgdir / stat[i].split('=')[1].strip()

                        if filename.isfile()
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


def print_rpm(robj):
    n,e,v,r,a = robj.get_nevra()

    print 'Filename:      ', robj.get_filename()
    print 'Name:          ', n
    print 'Epoch:         ', e
    print 'Version:       ', v
    print 'Release:       ', r
    print 'Arch:          ', a
    print 'Vendor:        ', robj.get_vendor()
    print 'Buildhost:     ', robj.get_buildhost()
    print 'Provides:      ', robj.get_provides()
    print 'Requires:      ', robj.get_requires()
    print 'Install Time:  ', robj.get_install_time()
    print 'Files list:    ', robj.get_file_list()
    
    
if __name__ == '__main__':

    import sys

    f1 = sys.argv[1]
    r1 = RPM(f1)
    
    print_rpm(r1)
   
    if len(sys.argv) > 2:
        f2 = sys.argv[2]
        r2 = RPM(f2)

        print
        print_rpm(r2)
       
        print
        print 'r1 > r2:       ', r1 > r2
        print 'r1 == r2:      ', r1 == r2
        print 'r1 < r2:       ', r1 < r2

    
