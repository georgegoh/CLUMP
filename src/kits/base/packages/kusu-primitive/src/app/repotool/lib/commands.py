import os
import sys
import shutil
import tempfile
from primitive.core.command import Command
from primitive.core.command import CommandFailException
# TODO: refactor all repos into a single location
from primitive.repo.yast import YastRepo

from primitive.repo.yum import RHEL5Repo
from primitive.repo.hdlist import RedHat4Repo
from primitive.repo.errors import RepoException
from primitive.repo.errors import RepoCreationError

from path import path

class CreateRepoCommand(Command):
    def __init__(self,**kwargs):
        Command.__init__(self,**kwargs)
        self.REPO_TYPES = [ 'SINGLE', 'MULTIPLE' ] 
        #scan for required arguments
        try:
            self.reponame = kwargs['repoName']
            self.repo_os = kwargs['os']
            self.repo_osver = kwargs['version']
            self.repo_arch = kwargs['arch']
            self.kit_path = kwargs['kitPath']
            self.repo_type = kwargs['repoType']
            self.repo_path = kwargs['repoPath']
            self.repo_type = kwargs['repoType']
        except KeyError,e:
            raise CommandFailException,'Missing key not supplied : %s' % e
        if not self.repo_path.endswith('/'):
            self.repo_path =  ''.join([self.repo_path,'/'])
        if not self.kit_path.endswith('/'):
            self.kit_path =  ''.join([self.kit_path,'/'])
        if self.repo_type not in self.REPO_TYPES:
            raise CommandFailException,\
                   'Repo type %s unsupported'% self.repo_type
        if self.repo_type != 'MULTIPLE':
            raise NotImplementedError,\
                   'Only MULTIPLE (kusu style repos) implemented'
        #optional arguments
        if 'additionalKits' in kwargs:
            if type(kwargs['additionalKits']) != type([]):
                raise CommandFailException,'Expected a list of additional kits'
            self.additional_kits = kwargs['additionalKits']
        if 'updates' in kwargs:
            self.updates_uri = kwargs['updates']
        else:
            self.updates_uri = None

        #support for kits not implemented yet
        #initialise local repo dispatch dictionary
        self.repo_factory = {\
            ('SLES','10','i386') : YastRepo ,
            ('RHEL','4','i386') :  RedHat4Repo,
            ('RHEL','5','i386') : RHEL5Repo}

    def execImpl(self):
        repo_p = path(self.repo_path)
        if repo_p.exists():
            if repo_p.isfile():
                raise CommandFailException,'Invalid repo Path given %s' % repo_p
            else:
                # how do we handle an already existing dir.. ?
                raise CommandFailException,\
                    'XXX-FIXME: Repo already exists at %s'% repo_p
        try:
            cache_dir = repo_p / 'cache/'
            store_dir = repo_p/ 'store/'
            cache_dir.makedirs()
        except IOError,e:
            raise CommandFailException,'Failed creating dirs for repo: %s',e
        try:
            #this code needs to be revisited
            shutil.copytree(self.kit_path, store_dir,symlinks=True)
        except Exception,e:
            raise CommandFailException,\
                   'Failed copying the source to repository : %s' % e
        
        try:
            repo = self.repo_factory[(self.repo_os,
                                      self.repo_osver,
                                      self.repo_arch)](store_dir,
                                                       os=self.repo_os,
                                                       os_arch=self.repo_arch,
                                                       os_ver=self.repo_osver)
        except KeyError,e:
            raise CommandFailException,\
                   'Unable to find a suitable repository for OS \
                   : %s Version %s  Arch %s' % (self.repo_os,self.repo_osver,
                                                self.repo_arch)
        try:
            repo.make()
        except RepoException,e :
            raise CommandFailException,"Failed to create repository!:%s " % e

        if self.updates_uri:
            repo.handleUpdates(updates_uri)
