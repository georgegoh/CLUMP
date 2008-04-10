#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import os
from path import path
import kusu.util.log as kusulog
import tempfile

from kusu.util.errors import CommandFailedToRunError
from kusu.util.errors import CopyFailedError
from kusu.util.errors import FileDoesNotExistError
from kusu.util.errors import NotSupportedURIError
from kusu.util.errors import ToolNotFound
try:
    import subprocess
except:
    from popen5 import subprocess

logger = kusulog.getKusuLog('util.tools')


TOOLS_DEPS = ['cpio', 'mount', 'umount', 'file', 'strings', 'zcat', 
    'mkisofs', 'tar', 'gzip']
    
X86_ARCHES = ['i386','i486','i586','i686']

def getArch():
    """ Returns the arch of the current system.
        If arch is not supported, 'noarch' will
        be returned.
    """
    cmd = 'arch'
    archP = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
    result = archP.communicate()[0] #only grab the first value, returns 2 values in a tuple
    _arch = result.strip('\n')
    
    if _arch in X86_ARCHES:
        return 'x86'
        
    if _arch == 'x86_64':
        return _arch
        
    return 'noarch'
    
def checkToolDeps(tool):
    """ Check if the tool is indeed available. A ToolNotFound exception 
        will be thrown if any of the tools are missing.
    """
    
    cmd = 'which %s > /dev/null 2>&1' % tool
    whichP = subprocess.Popen(cmd,shell=True)
    whichP.communicate()
    if whichP.returncode <> 0:
        raise ToolNotFound, tool
    return True

def checkAllToolsDeps():
    """ Check if the list of tools needed are indeed available. 
        A ToolNotFound exception will be thrown if any of the tools are
        missing.
    """

    for tool in TOOLS_DEPS:
        checkToolDeps(tool)
        
    return True

def url_mirror_copy(src, dst):
    """Performs a mirror copy of a http or ftp url.
       It will mirror everything that is under the 
       url.
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
                                 cwd = dst,
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            retcode = p.returncode

        except OSError, e:
            if e.errno == errno.ENOENT:
                raise FileDoesNotExistError, 'wget or destination dir not found' 
            else:
                raise CommandFailedToRunError, 'Unable to copy. Error Message: %s' % os.strerror(e.errno)

        except:
            raise CommandFailedToRunError

        if retcode:
            raise CopyFailedError, 'Failed to copy %s to %s' % (src,dst)
        else:
            return True
    else:
        raise NotSupportedURIError



def cpio_copytree(src,dst,cpioProg='cpio',findProg='find'): 
#added a cpioProg and findProg parameter for testing purposes
#this allows us to inject mock values to test error cases
    """A cpio-based copytree functionality. Only use this when shutil.copytree don't cut
       it.
    """
    # Taken from <unistd.h>, for file/dirs access modes
    # These can be OR'd together
    R_OK = 4   # Test for read permission.
    W_OK = 2   # Test for write permission.
#    X_OK = 1   # Test for execute permission. Commented out as its unused.

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
    #we are no longer using a shell
    #therefore the program and its arguments need to be passed as a list
    try:
        findP = subprocess.Popen([findProg,'.'],cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    except OSError,e:
        raise CommandFailedToRunError, "Error running %s : %s" % (findProg , os.strerror(e.errno))
    try:
        try:
            cpioP =  subprocess.Popen([cpioProg, '-mpdu' , '--quiet', '%s' % (dst)],cwd=cwd,stdin=findP.stdout,stderr=subprocess.PIPE)
            err = cpioP.communicate()[1] #required to wait for process to complete. 
        except OSError,e:
            raise CopyFailedError,"Error running %s: %s " % (cpioProg, os.strerror(e.errno)) 
        except Exception,e:
            raise CommandFailedToRunError,"Error running %s: %s" % (cpioProg,e)
    finally:
        findP.communicate() # we need to ensure findP is not lingering on waiting to pipe output with cwd as the mounted media dir

    #even when there are no exceptions raised, sometimes cpio can fail 
    if cpioP.returncode:

        raise CopyFailedError,"%s failed with return code %d : %s " % (cpioProg , cpioP.returncode, err)
    return cpioP.returncode

def mkdtemp(**kwargs):
    """ Creates a temp directory based on KUSU_TMP if available or 
        defaults to tempfile.mkdtemp behavior. The keyword arguments 
        will be passed to tempfile.mkdtemp function.
    """
    if 'KUSU_TMP' in os.environ and 'dir' not in kwargs:
        kwargs['dir'] = os.environ['KUSU_TMP']
    return tempfile.mkdtemp(**kwargs)
        
        


