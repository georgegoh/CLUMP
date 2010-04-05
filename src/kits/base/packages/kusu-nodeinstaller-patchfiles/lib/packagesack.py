#! /usr/bin/env python
#
# $Id: packagesack.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Copyright 2008 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from kusu.core import database as db
import os
import path
import kusu.util.log as kusulog
from primitive.system.software.probe import OS
from kusu.repoman.repofactory import RepoFactory
from primitive.support.errors import repodataChecksumException
from sqlalchemy.exceptions import InvalidRequestError
from primitive.core.errors import FetchException

class RepoDBError(Exception): pass
class RepoError(Exception): pass

class Package(object):
    def __init__(self):
        self.name = self.filename = self.path = None
        self.epoch  = self.ver = self.rel = self.arch = None
    
    def fullName(self):
        return '.'.join([str(self.name), str(self.ver), str(self.rel), str(self.arch)])
    
    def packageTuple(self):
        return (self.name, self.epoch, self.ver, self.rel, self.arch)

class YumPackage(Package):
    def __init__(self, rpm):
        Package.__init__(self)
        if rpm is None:
            return
        
        self.filename = rpm.getSplitfilename()[1]
        if rpm.filename.startswith('file://'):
            self.path = rpm.filename[7:]
        else:
            self.path = rpm.filename
        self.epoch = rpm.epoch #integer
        self.ver = rpm.version
        self.rel = rpm.release
        self.arch = rpm.arch
        self.name = rpm.name

class YastPackage(Package):
    def __init__(self, logger, descr_lines, base_dir=''):
        Package.__init__(self)
        base = path.path(base_dir)
        if not base.exists():
            return
        
        self.logger = logger
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
                 temppath = path.path('')
                 if len(location) > 1:
                     temppath = temppath / location[1]
                     if not temppath.exists():
                         temppath = base / location[1]
                 if not temppath.exists():
                     temppath = base / self.arch / self.filename
                 if not temppath.exists():
                     self.logger.error('Could not find package: %s' % self.fullName())
                     temppath = None
                 # will be None if temppath is None and str(temppath) otherwise.
                 self.path = temppath and str(temppath)

class PackageSack:
    
    def __init__(self, logger, target=OS()):
        self.uri_sack = []
        self.logger = logger
        
        dbdriver = os.getenv('KUSU_DB_ENGINE', 'postgres')
        dbdatabase = 'kusudb'
        dbuser = 'apache'
        
        dbs = None
        try:
            dbs = db.DB(dbdriver, dbdatabase, dbuser)
        except:
            msg = 'Unable to connect to the database.'
            self.log.error(msg)
            raise RepoDBError, msg
        
        self.uri_root = dbs.AppGlobals.selectone_by(kname = 'DEPOT_REPOS_ROOT').kvalue
       
        if target[2] in ['i486', 'i586', 'i686']:
            target = target[:2] + ('i386',)
        target = (target[0].lower(),) + target[1:]

        if target[0] in ['sles', 'opensuse', 'suse']:
            self.type = 'yast'
        else:
            self.type = 'yum'
        
        repos = dbs.Repos.select()
        for repo in repos:
            if not repo.os:
                continue

            repo_os = repo.os.name.lower()
            os_tuple = (repo_os, repo.os.major, repo.os.arch)
            full_os_tuple = (repo_os, repo.os.major + '.' + repo.os.minor, repo.os.arch)

            if os_tuple == target or full_os_tuple == target:
                if self.type == 'yast':
                    repo_path = path.path(self.uri_root) / str(repo.repoid)
                    self.uri_sack.append(str(repo_path))
                else:
                    self.uri_sack.append(RepoFactory(dbs).getRepo(repo.repoid).getBaseYumDir('default'))

        if 0 == len(self.uri_sack):
            msg = 'No repositories found for target os: %s-%s-%s' % target
            self.logger.error(msg)
            raise RepoDBError, msg
   
    def listPackages(self):
        if 0 == len(self.uri_sack):
            self.logger.error('No repositories available.')
            return []
        elif self.type == 'yast':
            return self.listYastPackages()
        else:
            return self.listYumPackages()

    def listYumPackages(self):
        from primitive.support.yum import YumRepo
        package_list = []
        for uri in self.uri_sack:
            repo = YumRepo('file://%s' % uri)
            try:
                primary_dict = repo.getPrimary()
            except repodataChecksumException:
                msg = 'Yum repo at %s is corrupted' % uri
                self.logger.error(msg)
                raise RepoError, msg
            except FetchException, IOError:
                msg = 'Error occurred while attempting to access Yum repo at %s' % uri
                self.logger.error(msg)
                raise RepoError, msg
            
            for name in primary_dict:
                for arch in primary_dict[name]:
                    rpm_list = primary_dict[name][arch]
                    pkgs = [YumPackage(rpm) for rpm in rpm_list]
                    package_list.extend([pkg for pkg in pkgs if pkg.name is not None])
        #end for
        return package_list
 
    def listYastPackages(self):
        package_list = []
        for uri in self.uri_sack:
            content = path.path(uri) / 'content'
            try: 
                content_lines = [line.strip().split(' ', 1) for line in content.lines()]
            except IOError:
                msg = 'Could not read Yast Repo Content file at %s.' % uri
                self.logger.error(msg)
                raise RepoError, msg
            
            content_dict = dict(content_lines)
            try:
                data_dir = path.path(uri) / content_dict['DATADIR']
                descr_dir = path.path(uri) / content_dict['DESCRDIR']
            except KeyError:
                msg = 'Yast repo content file - %s is faulty.' % str(content)
                self.logger.error(msg)
                raise RepoError, msg
            
            try:
                packages = descr_dir / 'packages'
                packages_lines = [line.strip() for line in packages.lines()]
            except IOError:
                msg = 'Could not read Yast Repo Packages file at %s.' % uri
                self.logger.error(msg)
                raise RepoError, msg
            
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
            sack_pkgs = [YastPackage(self.logger, pkg_lines, str(data_dir)) for pkg_lines in sack_dump]
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
        flag = path.path(f).exists()
        print str(cntr) + ':' + str(flag) + ' ' + f

