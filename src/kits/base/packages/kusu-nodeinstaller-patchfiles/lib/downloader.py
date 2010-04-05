#! /usr/bin/env python
#
# $Id: downloader.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Copyright 2008 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import sys
import shutil
import os
from kusu.genupdates.packages import *
from kusu.genupdates.packagesack import *
import kusu.util.log as kusulog
from primitive.system.software.probe import OS

class RepoDBError(Exception): pass
class RepoError(Exception): pass

class Downloader(object):
    
    def __init__(self, destdir='.', target_os=None):
        self.logger = kusulog.getKusuLog('kusu')
        self.logger.addFileHandler(os.getenv('KUSU_LOGFILE', '/var/log/kusu/kusu.log'))

        self.os = OS()
        if target_os:
            self.os = target_os

        self.destdir = destdir
        if not os.path.exists(self.destdir):
            os.makedirs(destdir)

    def downloadPackages(self, packages):
        sack = PackageSack(self.logger, target=self.os)
        
        avail= sack.listPackages()
        toDownload = []
        
        for req in packages:
            toActOn = []
            exactmatch, matched, unmatched = parsePackages(avail, [req])
            
            for name in unmatched: # if we get back anything in unmatched, it fails
                self.logger.error('No Match for package %s' % name)
            
            if len(exactmatch) > 0:
                toDownload.append(bestPackageFromList(exactmatch, self.os[2]))
            
            if len(matched) > 0:
                for pkg_list in matched:
                    toDownload.append(bestPackageFromList(matched[pkg_list], self.os[2]))
        
        if len(toDownload) == 0:
            self.logger.error('Nothing to download')
        
        downloaded = []
        for pkg in toDownload:
            try:
                shutil.copy(pkg.path, self.destdir)
                downloaded.append(pkg.name)
            except IOError, e:
                self.logger.error("Cannot copy %s from %s to %s. Error was: %s" % (pkg.fullName(), pkg.path, self.destdir, e))
                continue
        
        return downloaded

