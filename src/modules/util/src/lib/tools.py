#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import os
from path import path
import kusu.util.log as kusulog
from kusu.util.errors import *

try:
    import subprocess
except:
    from popen5 import subprocess

logger = kusulog.getKusuLog('util.tools')

def copy(src, dest):
    """ Performs a recursive copy. Source can either be 
        http/ftp or a local path
    """

    import urlparse
    import errno

    if urlparse.urlsplit(src)[0] in ['http', 'ftp']:
        p = path(urlparse.urlsplit(src)[2]).splitall()

        # Deals with non-ending slash. 
        # Non-ending slash url ends up with an empty string in the 
        # last index of the list when a splitall is done
        if not p[-1]: 
            cutaway = len(p[1:]) - 1
        else: # non-ending slash
            cutaway = len(p[1:])
            src = src + '/' # Append a trailing slash

        if cutaway <= 0:
            cutaway = 0

        cmd = 'wget -m -np -nH --cut-dirs=%s %s' % (cutaway, src)

        try:
            p = subprocess.Popen(cmd,
                                 cwd = dest,
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            retcode = p.returncode

        except OSError, e:
            if e.errno == errno.ENOENT:
                raise FileDoesNotExistError, 'wget not found' 
            else:
                raise KusuError, 'Unable to copy. Error Message: %s' % os.strerror(e.errno)

        except Exception, e:
            raise KusuError

        if retcode:
            raise CopyFailedError, 'Failed to copy %s to %s' % (src,dest)
        else:
            return True


    else:
        if os.path.exists(src):
            cpio_copytree(src, dest)

        else:  
            raise CopyFailedError, 'Failed to copy %s to %s' % (src,dest)


def cpio_copytree(src,dst):
    """A cpio-based copytree functionality. Only use this when shutil.copytree don't cut
       it.
    """

    # Taken from <unistd.h>, for file/dirs access modes
    # These can be OR'd together
    R_OK = 4   # Test for read permission.
    W_OK = 2   # Test for write permission.
    X_OK = 1   # Test for execute permission.

    # convert paths to be absolute
    src = path(src).abspath()
    dst = path(dst).abspath()
    cwd = path(src)

    if not cwd.exists(): raise IOError, "Source directory does not exist!"

    # create the dst directory if it doesn't exist initially
    if not path(dst).exists():
        if path(dst).parent.access(R_OK|W_OK):
            path(dst).mkdir()
        else:
            raise IOError, "No read/write permissions in parent directory!"
    else:
        if not path(dst).access(R_OK|W_OK): raise IOError, "No read/write permissions in destination directory!"


    findP = subprocess.Popen('find .',cwd=cwd,shell=True,stdout=subprocess.PIPE)
    cpioP = subprocess.Popen('cpio -mpdu --quiet %s' % dst,cwd=cwd,stdin=findP.stdout,shell=True)
    cpioP.communicate()
    return cpioP.returncode


