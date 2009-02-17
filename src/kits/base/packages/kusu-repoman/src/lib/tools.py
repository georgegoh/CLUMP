#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from kusu.util.errors import *
from path import path
import re

def repoExists(dbs, repoid):
    """Checks whether a repo exists"""

    repo = dbs.Repos.select_by(repoid=repoid)

    if repo:
        return True
    else:
        return False

def nodeGroupExists(dbs, ngname):
    """Checks whether a nodegroup exists"""

    ng = dbs.NodeGroups.select_by(ngname=ngname)

    if ng:
        return True
    else:
        return False

def repoForNodeGroupExists(dbs, ngname):
    """Checks whether a repo exists for a particular nodegroup"""

    ng = dbs.NodeGroups.select_by(ngname=ngname)

    ng = ng[0]

    if ng.repoid:
        return True
    else:
        return False


def getRepoFromNodeGroup(dbs, ngname):
    """Gets the repoid for a nodegroup"""

    ng = dbs.NodeGroups.select_by(ngname = ngname)

    if ng:
        return ng[0].repoid
    else:
        return None

def repoInUse(dbs, repoid):
    ngs = dbs.NodeGroups.select_by(repoid = repoid)
    
    if ngs:
        return True
    else:
        return False

def kitInUse(dbs, kid):
    repos = dbs.ReposHaveKits.select_by(kid = kid)
    
    if repos:
        return True
    else:
        return False

def getOS(dbs, repoid_or_ngname):
    """Returns OS (rname, version, arch) tuple from database 
       based on the repoid or nodegroup name"""

    key = repoid_or_ngname

    # Do not depend on os type in repo
    # repoid
    if type(key) in [int, long]: # float/complex not included 
        kit = dbs.Kits.select_by(dbs.ReposHaveKits.c.kid == dbs.Kits.c.kid,
                                dbs.ReposHaveKits.c.repoid == key,
                                dbs.Kits.c.isOS)

    # nodegroup name
    elif type(key) in [str, unicode]:
        kit = db.findKitsFromNodeGroup(dbs,
                                       columns=['rname', 'version', 'arch'],
                                       kitargs={'isOS': True}, 
                                       ngargs={'ngname': key})
    else:
        raise TypeError, 'Invalid type for key: %s' % key

    # There should only 1 be os kit for a repo. 
    if len(kit) == 0:
        raise RepoOSKitError, '\'%s\' has no OS Kit' % key
    elif len(kit) != 1:
        raise RepoOSKitError, '\'%s\' has more than 1 OS Kit' % key
    else:
        kit = kit[0]

    oskit = kit.os
    return (oskit.name, oskit.major, oskit.minor, oskit.arch)

def getKits(dbs, ngname):
    """Returns a list of kits for a nodegroup"""
    ng = dbs.NodeGroups.select_by(ngname=ngname)[0]

    kits = {} 
    for component in ng.components:
        # Store all the kits, uniq them via dictionary
        kits[component.kit.kid] = component.kit

    return kits.values()

def getFile(uri):
    import urlparse
    import urllib2

    schema, ignore, p, ignore, ignore = urlparse.urlsplit(uri)

    if schema in ['http', 'ftp']:
        f = urllib2.urlopen(uri) 
        content = f.read()
        f.close()

    elif schema in ['file', '']:
        # '' to assume just a path
        f = open(p, 'r')
        content = f.read()
        f.close()

    else:
        raise UnsupportedURIError, uri

    return content

def getConfig(file):
    import ConfigParser

    if not path(file).exists():
        raise FileDoesNotExistError, file

    configParser = ConfigParser.ConfigParser()
    configParser.read(file)
    
    cfg = {}
    sections = configParser.sections()

    for sec in sections:
        if sec in ['fedora', 'centos', 'rhel', 'sles', 'opensuse', 
                   'rhel-5-i386', 'rhel-5-x86_64']:
            cfg[sec] = {}
            for opt in configParser.items(sec):
               key = opt[0]
               value = opt[1]

               cfg[sec][key] = value

    return cfg
 
#def getLowestKernel(rpmPkgs, arch):
#    """Get a min arch of a kernel"""
#    
#    if rpmPkgs.has_key('kernel'):
#        if self.os_arch == 'x86_64':
#            # We want to use x64 kernel
#            kernelRPM = rpmPkgs['kernel']['x86_64'][0]
#        elif self.os_arch == 'i386':
#            # Take the lowest arch
#            if rpmPkgs['kernel'].has_key('i386'):
#                kernelRPM = rpmPkgs['kernel']['i386'][0]
#            elif rpmPkgs['kernel'].has_key('i486'):
#                kernelRPM = rpmPkgs['kernel']['i486'][0]
#            elif rpmPkgs['kernel'].has_key('i586'):
#                kernelRPM = rpmPkgs['kernel']['i586'][0]
#            elif rpmPkgs['kernel'].has_key('i686'):
#                kernelRPM = rpmPkgs['kernel']['i686'][0]
#    else:
#        kernelRPM = None
#
#    return kernelRPM

def getPackageFilePath(dbs, repoid, packagename):
    """Returns the path of the packagename based on the repoid.
       packagename is the filename of the package (e.g foo-1.2-1.i386.rpm).
       Raises FileDoesNotExistError if not found"""
   
    if not repoExists(dbs, repoid):
        raise RepoNotFoundError, repoid

    from kusu.repoman import repofactory
    rfactory = repofactory.RepoFactory(dbs)
    repo = rfactory.getRepo(repoid)
    packageFilePath = repo.getPackageFilePath(packagename)

    if packageFilePath:
        return packageFilePath
    else:
        raise FileDoesNotExistError

def getKernelPackages(dbs, repoid):
    '''Returns a list of kernels'''

    if not repoExists(dbs, repoid):
        raise RepoNotFoundError, repoid

    from kusu.repoman import repofactory
    rfactory = repofactory.RepoFactory(dbs)
    repo = rfactory.getRepo(repoid)
    return repo.getKernelPackages()

def getPackagePath(dbs, repoid):
    '''Returns a list of path where packages are located in'''
  
    if not repoExists(dbs, repoid):
        raise RepoNotFoundError, repoid

    from kusu.repoman import repofactory
    rfactory = repofactory.RepoFactory(dbs)
    repo = rfactory.getRepo(repoid)
    return repo.getPackagesDir()

def getBaseYumDir(dbs, repoid):
    '''Returns the path where the repodata dir for yum resides in'''

    if not repoExists(dbs, repoid):
        raise RepoNotFoundError, repoid

    from kusu.repoman import repofactory
    rfactory = repofactory.RepoFactory(dbs)
    repo = rfactory.getRepo(repoid)

    if repo.os_name in ['rhel', 'centos', 'fedora']:
        return repo.getBaseYumDir()
    else:
        return None

def isRepoStale(dbs, repoid):
    '''Returns whether a repo has been refreshed and up to date'''

    if not repoExists(dbs, repoid):
        raise RepoNotFoundError, repoid

    from kusu.repoman import repofactory
    rfactory = repofactory.RepoFactory(dbs)
    repo = rfactory.getRepo(repoid)

    return repo.isStale()

def getEffictiveOSVersion(dbs, repoid):
    '''Returns the effective OS version for the repo'''

    if not repoExists(dbs, repoid):
        raise RepoNotFoundError, repoid

    from kusu.repoman import repofactory
    rfactory = repofactory.RepoFactory(dbs)
    repo = rfactory.getRepo(repoid)
    return repo.getEffectiveOSVersion()
 
