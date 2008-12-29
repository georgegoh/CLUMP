#! /usr/bin/env python
#
# $Id$
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

class UnsupportedOSException(Exception): pass

class Downloader(object):
    
    def __init__(self, destdir='.', target_os=OS()):
        self.logger = kusulog.getKusuLog('kusu')
        self.logger.addFileHandler(os.environ['KUSU_LOGFILE'])

        self.destdir = destdir
        if not os.path.exists(self.destdir):
            os.makedirs(destdir)
        
        self.os = target_os
        if self.os[0].lower() not in ['sles', 'opensuse', 'suse']:
            self.logger.error("Unsupported target os %s.%s.%s" % self.os)
            raise UnsupportedOSException, 'This tool only supports yast based repositories'
        
        self.destdir = destdir
    
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
        
        for pkg in toDownload:
            try:
                shutil.copy(pkg.path, self.destdir)
            except IOError, e:
                self.logger.error("Cannot copy %s from %s to %s. Error was: %s" % (pkg.fullName(), pkg.path, self.destdir, e))
                continue

if __name__ == '__main__': #simple test
    util = Downloader()
    util.downloadPackages(['xen', 'crap', 'e*'])

