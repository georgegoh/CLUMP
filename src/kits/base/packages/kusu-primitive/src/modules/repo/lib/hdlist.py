#!/usr/bin/env python
#
# $Id$
#
import os
import atexit
import subprocess
from path import path
from primitive.repo.errors import RepoException
from primitive.repo.errors import RepoCreationError

def _pkgorder_cleanup(pid):
    ''' pkgorder currently leaves a /tmp/pkgorder-<pid> artifact
        upon exit. This function cleans up the temp files given
        a pid.
    '''
    pkgorder_tmp = path('/tmp/pkgorder-' + str(pid))
    if pkgorder_tmp.exists():
        pkgorder_tmp.rmtree()


class HDListRepo(object):
    def __getGenHdListCmd(self):
        # FIXME: Refactor this to use system lib
        return 'genhdlist'
    def __getPkgOrderCmd(self):
        #FIXME : Refactor this to use system lib
        return 'pkgorder'
    def __init__(self,repo_path):
        self.genhdlist_cmd = self.__getGenHdListCmd()
        self.pkgorder_cmd  = self.__getPkgOrderCmd()
        if not self.genhdlist_cmd:
            raise RepoException,'Required command genhdlist not found'
        if not  self.pkgorder_cmd:
            raise RepoException,'Required command pkgorder not found'
        self.repo_path = path(repo_path)
        self.pkgorder_pid = -1
        
    def makeMeta(self, os_arch, product_name):
        '''Make meta information for RHEL 4 Repository'''
        env = os.environ
        for p in os.environ.get('PYTHONPATH', '').split(':'):  
            p = path(p)
            
            if (p / 'classic').exists():
                env['PYTHONPATH'] = env['PYTHONPATH'] + ':' + p / 'classic' 
                env['PYTHONPATH'] = env['PYTHONPATH'] + ':' + p / 'classic'\
                    / 'anaconda' 
                
                pkgorder = self.repo_path / 'pkgorder'
   
                try:
                    p1 = subprocess.Popen([self.genhdlist_cmd, '--withnumbers',
                                           '--productpath', product_name, self.repo_path],
                                          env=env,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE)
                    p1.communicate()

                    p2 = subprocess.Popen([self.pkgorder_cmd, self.repo_path,
                                           os_arch, product_name],
                                           env=env,
                                           stdout=file(pkgorder, 'w'),
                                           stderr=subprocess.PIPE)
                    p2.communicate()
                    # pkgorder_cmd does not remove its temp file
                    # so we remove it at exit.
                    atexit.register(_pkgorder_cleanup, p2.pid)
                    p3 = subprocess.Popen([self.genhdlist_cmd, '--fileorder',
                                          pkgorder, '--withnumbers',
                                          '--productpath', product_name,
                                          self.repo_path],
                                          env=env,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE)
                    out, err = p3.communicate()
                    retcode = p3.returncode
                except Exception,e:
                    raise RepoCreationError,'Failed creating HDList Repo %s'% e
                if retcode:
                    raise RepoCreationError,\
                           'genhdlist failed with return code %d' % retcode
                
                if pkgorder.exists(): pkgorder.remove()
        def make(self):
            raise NotImplementedError,'A subclass needs to to implement this'


class RedHat4Repo(HDListRepo):
    def __init__(self, repo_path, os_arch='i386',**unused):

        unused.clear() # get rid of unused args
        self.os_arch = os_arch
        HDListRepo.__init__(self,repo_path)

    def make(self):
        base = self.repo_path / 'RedHat' / 'base'
        rpms  = self.repo_path / 'RedHat' / 'RPMS'

        if not base.exists() or not rpms.exists():
            raise RepoCreationError,\
                'Source directory not in correct format for Redhat 4 repository'
        
        self.makeMeta(self.os_arch, 'RedHat')

class Centos4Repo(HDListRepo):
    def __init__(self, repo_path, os_arch='i386',**unused):
        '''Initialises  a Centos 4 repo.'''
        unused.clear()  # get rid of unused args
        self.os_arch = os_arch
        HDListRepo.__init__(self,repo_path)

    def make(self):
        base = self.repo_path / 'CentOS' / 'base'
        rpms = self.repo_path / 'CentOS' / 'RPMS'

        if not base.exists() or not rpms.exists():
            raise RepoCreationError,'Source directory not in correct format\
 for Redhat 4 repository'

        self.makeMeta( self.os_arch, 'CentOS')


if __name__ == '__main__':
    repo = '/srv/www/htdocs/test'
    y = RedHat4Repo(repo)
    y.make()

