#!/usr/bin/env python
#
# $Id: util.py 203 2007-03-29 12:18:16Z ltsai $
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import os

def checkDistro(path, os, version):
    """ Verify a distribution source 
        
        path - Either a HTTP/FTP URL or a local path
        os   - The distro/os name in lower caps
        version - The version of the os
    """
    
    from distro import CheckDistro
    d = CheckDistro()
    d.verify(path, os, version)

def copy(src, dest):
    """ Performs a recursive copy. Source can either be 
        http/ftp or a local path
    """

    import urlparse
    from path import path
    #from kusu.ext.path import path

    if urlparse.urlsplit(src)[0] in ['http', 'ftp']:
        p = path(urlparse.urlsplit(src)[2]).splitall()

        # Deals with non-ending slash. 
        # Non-ending slash url ends up with an empty string in the 
        # last index of the list when a splitall is done
        if not p[-1]:
            cutaway = len(p[1:]) - 1
        else:
            cutaway = len(p[1:])

        ec = os.system('cd %s && \
                        wget -m -np -nH -q --cut-dirs=%s %s' % (dest, cutaway, src))

        if ec:
            raise Exception
        else:
            return True

    else:
        if os.path.exists(src):
            os.system('find %s -depth -print | cpio -pd %s' % (src, dest))
            return True

        else:  
            raise Exception


if __name__ == '__main__':

    # Need to have better testing to cover more grounds
    try:
        checkDistro('http://172.25.208.217/repo/fedora/6/i386/os', 'fedora', '6')
    except Exception, err:
        print err

    try:
        checkDistro('http://172.25.208.218/repo/', 'fedora', '6')
    except Exception, err:
        print err

    try:
        checkDistro('ftp://172.25.208.218/repo/', 'fedora', '6')
    except Exception, err:
        print err

    try:
        checkDistro('ftp://172.25.208.218', 'fedora', '6')    
    except Exception, err:
        print err

    try:
        checkDistro('ftp://172.25.208.217', 'fedora', '6')    
    except Exception, err:
        print err

    try:
        checkDistro('ftp://osgdc.org', 'fedora', '6')    
    except Exception, err:
        print err

    try:
        checkDistro('/home', 'fedora', '6')
    except Exception, err:
        print err
    
    try:
        checkDistro('/data/repo/src/fedora/6/i386/os', 'fedora', '6')
    except Exception, err:
        print err

