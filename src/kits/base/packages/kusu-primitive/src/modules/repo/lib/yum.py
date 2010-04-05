#!/usr/bin/env python
#
# $Id$
#

from path import path

import subprocess
import os
from primitive.repo.errors import RepoException
from primitive.repo.errors import RepoCreationError
from primitive.fetchtool.commands import FetchCommand

class YumRepo:
    def __init__(self, repo_path):
        # system module will do this for us in the future
        self.createrepo_cmd = self.__getCreateRepoCmd()
        if not self.createrepo_cmd:
            raise RepoException,\
                'Createrepo not found, unable to create YUM Repo'
        self.repo_path = path(repo_path)

    def __getCreateRepoCmd(self):
        ''' Refactor this into a lookup table in the system module '''
        #True for RHEL and SLES.
        createrepo_cmd = '/usr/bin/createrepo'
        if path(createrepo_cmd).exists():
            return createrepo_cmd
        return False

    def make(self):
        self.makeMeta()
        

    def makeMeta(self):
        cmd = self.createrepo_cmd

        comps = self.getComps()
        if comps:
            cmd = cmd + ' -g %s' % comps
        cmd = cmd + ' %s' % (self.repo_path)
        
        try:
            p = subprocess.Popen(cmd,
                                 cwd=self.repo_path,
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            retcode = p.returncode
        except Exception,e:
            raise RepoCreationError,'Error creating repo %s' % e

        if retcode:
            raise RepoCreationError,\
                   'createrepo failed with return code %d' % retcode

    def getComps(self):
        repodatadir = self.repo_path / 'repodata'
        comps = repodatadir.glob('comps*.xml') 
        if comps: 
            comps = comps[0]
        else:  
            comps = None
        return comps

class RHEL5Repo(YumRepo):
    def __init__(self,repo_path,**unused):
        ''' Initialise a RHEL5 OS repo from path.
        Path is expected to end with /'''
        unused.clear() # get rid of unused args
        self.dirlayout = {}
        self.version = '5'
        if self.isOS(repo_path):
            repo.path = ''.join([repo.path,'Server'])
        # an OS kit has pre-enitialised repodata, however, for KUSU Style
        # repos, we may extend the info in Server, hence set the repo path
        # to the server.
        # the cache still needs to catalog the other repos such as Cluster
        # as provided in the media
        YumRepo.__init__(self,repo_path)

        
    def isOS(self,repo_path):
        ''' Verify if the path holds an exploded OS Media. Ported from Kusu'''
        # FIXME: Need to use a common module
        self.dirlayout['imagesdir'] = 'images'
        self.dirlayout['isolinuxdir'] = 'isolinux'
        self.dirlayout['server.rpmsdir'] = 'Server'
        self.dirlayout['cluster.rpmsdir'] = 'Cluster'
        self.dirlayout['clusterstorage.rpmsdir'] = 'ClusterStorage'
        self.dirlayout['vt.rpmsdir'] = 'VT'
        self.dirlayout['server.repodatadir'] = 'Server/repodata'
        self.dirlayout['cluster.repodatadir'] = 'Cluster/repodata'
        self.dirlayout['clusterstorage.repodatadir'] =\
            'ClusterStorage/repodata'
        self.dirlayout['vt.repodatadir'] = 'VT/repodata'

        if self.__verifySrcPath(repo_path) and self.__verifyVersion():
            return True

    def __verifySrcPath(self,repo_path):
        '''Redhat specific way of verifying the local path.
        Distro.py needs to be brought in properly later'''
        for d in self.dirlayout.values():
            if not os.path.exists(''.join([repo_path,d])):
                return False

    def __verifyVersion(self):
        '''Redhat specific way of getting the distro version'''
        discinfo = self.repo_path + '.discinfo'
        version = None
        if os.path.exists(discinfo):
            fp = file(discinfo, 'r')
            linelst = fp.readlines()
            fp.close()
            line = linelst[1] #second line is usually the name/version
            words = line.split()
            for i in range(0,len(words)):
                if words[i].isdigit():
                    break
            version = words[i]
        else:
            return False
        if self.version == version:
            return True
        else:
            return False
    
    def handleUpdates(self, update_uri):
        ''' Fetches the updates.img from update_uri and places it
            in the images directory.
        '''
        dest_dir = self.repo_path / 'images'
        fc = FetchCommand(uri=update_uri, fetchdir=False,
                          destdir=dest_dir, overwrite=True)
        update_path = fc.execute()


if __name__ == '__main__':
    repo = '/srv/www/htdocs/suse'
    y = YumRepo(repo)
    y.make()

    repo = '/srv/www/htdocs/test'
    y = YumRepo(repo)
    y.make()
