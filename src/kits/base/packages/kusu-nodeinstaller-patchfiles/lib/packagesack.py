#! /usr/bin/env python
#
# $Id$
#
# Copyright 2008 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from kusu.core import database as db
from kusu.repoman.tools import getOS
from kusu.util.errors import RepoOSKitError
import os
import kusu.util.log as kusulog
from primitive.system.software.probe import OS

class Package:
    def __init__(self, logger, descr_lines, base_dir=''):
        self.logger = logger
        
        self.name = self.ver = self.rel = self.arch = None
        for arg in descr_lines:
            tag = arg[:5].lower()
            if '=pkg:' == tag:
                try:
                    [self.name, self.ver, self.rel, self.arch] = arg[6:].strip().split()
                except:
                    self.logger.error('Corrupt package metadata found in %s' % arg)
                    self.name = self.ver = self.rel = self.arch = self.path = None
                    return
            elif '=loc:' == tag:
                 location = arg[6:].strip().split()[1:]
                 self.filename = location[0]
                 self.path = None
                 if len(location) > 1:
                     self.path = location[1]
                     if not os.path.exists(self.path):
                         self.path = '%s/%s' % (base_dir, location[1])
                 if not self.path:
                     self.path = '%s/%s/%s' % (base_dir, self.arch, self.filename)
                 if not os.path.exists(self.path):
                     self.logger.error('Could not find package: %s' % str(self.name))
                     self.path = None
    
    def fullName(self):
        return '.'.join([str(self.name), str(self.ver), str(self.rel), str(self.arch)])
    
    def packageTuple(self):
        return (self.name, self.ver, self.rel, self.arch)

class PackageSack:
    
    def __init__(self, logger, target=OS()):
        self.uri_sack = []
        self.logger = logger
        
        dbdriver = os.getenv('KUSU_DB_ENGINE')
        if not dbdriver or dbdriver not in ['mysql','postgres']:
            dbdriver = 'postgres'
        dbdatabase = 'kusudb'
        dbuser = 'apache'
        dbpassword = None
        
        dbs = None
        try:
            dbs = db.DB(dbdriver, dbdatabase, dbuser, dbpassword)
        except:
            self.log.error('Unable to connect to the database. Please check database configuration.')
            return
        
        self.uri_root = dbs.AppGlobals.select_by(kname = 'DEPOT_REPOS_ROOT')[0].kvalue
        
        if target[2] in ['i486', 'i586', 'i686']:
            target[2] = 'i386'
        repos = [item.repoid for item in dbs.Repos.select()]
        for repoid in repos:
            try:
                os_tuple = getOS(dbs, repoid)
                if os_tuple == (target[0].lower(), target[1].split('.')[0], target[2]):
                    self.uri_sack.append('%s/%d/' % (self.uri_root, repoid))
            except RepoOSKitError:
                continue
        if 0 == len(self.uri_sack):
            self.logger.error('No repositories found for target os: %s.%s.%s' % target)
    
    def listPackages(self):
        package_list = []
        if 0 == len(self.uri_sack):
            self.logger.error('No repositories available.')
        else:
            for uri in self.uri_sack:
                content = packages = None
                try:
                    content = open(uri + 'content')
                except IOError:
                    self.log.error('Could not find Yast repo content file in %s.' % uri)
                    continue
                
                try:
                    content_lines = [line.strip().split(' ', 1) for line in content.readlines()]
                finally:
                    content.close()
                
                content_dict = dict(content_lines)
                try:
                    data_dir = content_dict['DATADIR']
                    descr_dir = content_dict['DESCRDIR']
                except KeyError:
                    self.log.error('Yast repo content file - %s is faulty.' % uri + 'content') 
                    continue
                
                try:
                    try:
                        packages = open(uri + descr_dir + '/packages')
                        packages_lines = [line.strip() for line in packages.readlines()]
                    except IOError:
                        self.log.error('Could not find packages file in %s.' % uri + descr_dir)
                        continue
                finally:
                    packages.close()
                
                sack_dump = []
                pkg_dump = []
                for line in packages_lines[2:]:
                    if '##--' == line[:4]:
                        sack_dump.append(pkg_dump)
                        pkg_dump = []
                    else:
                        pkg_dump.append(line)
                
                if len(pkg_dump) > 0:
                    sack_dump.append(pkg_dump)
                sack_pkgs = [Package(self.logger, pkg_lines, uri + data_dir) for pkg_lines in sack_dump]
                package_list.extend([pkg for pkg in sack_pkgs if pkg.name is not None])
            #end for
        return package_list

if __name__ == '__main__':
    logger = kusulog.getKusuLog('kusu')
    logger.addFileHandler(os.environ['KUSU_LOGFILE'])
    sack = PackageSack(logger)
    for uri in sack.uri_sack:
        print uri
    print '='*30
    cntr = 0
    for pkg in sack.listPackages():
        cntr += 1
        f = pkg.path
        flag = os.path.exists(f)
        print str(cntr) + ':' + str(flag) + ' ' + f

