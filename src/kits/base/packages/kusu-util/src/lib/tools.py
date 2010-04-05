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
from kusu.util.errors import *
import tempfile
from primitive.svctool.commands import SvcStartCommand
from primitive.svctool.commands import SvcStatusCommand
from primitive.svctool.commands import SvcStopCommand
from primitive.svctool.commands import SvcRestartCommand
from primitive.svctool.commands import SvcReloadCommand
from primitive.svctool.commands import SvcEnableCommand
from primitive.svctool.commands import SvcDisableCommand
from primitive.svctool.commands import SvcListCommand
from primitive.svctool.commands import SvcExistsCommand
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
    result, code = archP.communicate()
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
    
def mkdtemp(**kwargs):
    """ Creates a temp directory based on KUSU_TMP if available or 
        defaults to tempfile.mkdtemp behavior. The keyword arguments 
        will be passed to tempfile.mkdtemp function.
    """
    if 'KUSU_TMP' in os.environ and 'dir' not in kwargs:
        kwargs['dir'] = os.environ['KUSU_TMP']

    if kwargs.has_key('prefix'):
        return tempfile.mkdtemp('', **kwargs)
    else:
        return tempfile.mkdtemp('', 'kusu-', **kwargs)


def service(serviceName, action, **kwargs):
    """ Perform an action on a service.
        Input args:
            serviceName - name of service
            action - one of [start, stop, status,
                             restart, reload, enable,
                             disable, list]
            **kwargs - any other keyword/args relevant to the service
    """
    command_dict = { 'start' : SvcStartCommand,
                     'stop' : SvcStopCommand,
                     'status' : SvcStatusCommand,
                     'restart' : SvcRestartCommand,
                     'reload' : SvcReloadCommand,
                     'enable' : SvcEnableCommand,
                     'disable' : SvcDisableCommand,
                     'list' : SvcListCommand,
                     'exists' : SvcExistsCommand }
    if action in command_dict.keys():
        svc = command_dict[action](service=serviceName, **kwargs)
        return svc.execute()
