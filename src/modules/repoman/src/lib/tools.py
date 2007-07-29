#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from kusu.util.errors import *
from kusu.core import database as db
from path import path
import sqlalchemy as sa

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
   
    return (kit.rname, kit.version, kit.arch)

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
        if sec in ['fedora', 'centos', 'rhel']:
            cfg[sec] = {}
            for opt in configParser.items(sec):
               key = opt[0]
               value = opt[1]

               cfg[sec][key] = value

    return cfg
 
