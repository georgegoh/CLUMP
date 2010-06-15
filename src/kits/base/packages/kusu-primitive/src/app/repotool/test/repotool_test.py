#!/usr/bin/env python
import os
import tempfile
import logging
import tarfile
from primitive.core.command import CommandFailException
from primitive.repotool.commands import CreateRepoCommand
try:
        import subprocess
except:
    from popen5 import subprocess
#from primitive.modules.core import command
from nose import SkipTest
import errno
from path import path
from nose.tools import assert_raises

cachedir =  path(tempfile.mkdtemp(prefix='repotool'))
def setup():
    pass

def teardown():
    global cachedir
    cachedir.rmtree()


def download(filename, dest, cache=cachedir):
    global cachedir

    if (cache / filename).exists():
        (cache / filename).copy(dest)
        return

    import urllib2
    url = 'http://www.osgdc.org/pub/build/tests/modules/primitive/repotool/'
    f = urllib2.urlopen(url + filename)
    content = f.read()
    f.close()

    f = open(cache / filename, 'w')
    f.write(content)
    f.close()

    (cache / filename).copy(dest)


def unpack(filename, dest):
    tar = tarfile.open(filename, 'r:gz')
    for tarinfo in tar:
        tar.extract(tarinfo.name, dest)
    tar.close()

def runCommand(self,cmd):
    try:
        p = subprocess.Popen(cmd,
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()
        retcode = p.returncode
        return retcode,out,err
    except OSError, e:
        if e.errno == errno.ENOENT:
            raise CommandFailException, 'subprocess  path incorrect or  not found' 
        else:
            raise CommandFailException, 'Unable to complete command  Error Message: %s' % os.strerror(e.errno)
        
    except:
        assert False



class TestRepoToolYAST(object):
    def setUp(self):
        self.prefix = path(tempfile.mkdtemp(prefix='repotool'))
        download('os.tgz', self.prefix)
        download('rpm.tgz', self.prefix)
        unpack(self.prefix / 'os.tgz', self.prefix / 'os')
        unpack(self.prefix / 'rpm.tgz', self.prefix / 'rpm')


    def tearDown(self):
        self.prefix.rmtree()
    def testCreateSLESRepoCommand(self):
        '''Test creation of Yast OS and vanilla repos''' 
        repo_path = tempfile.mkdtemp('primitive')
        input_dict = { 'name' : 'CreateRepository',
                       'repoName' : 'TestRepo',
                       'os': 'SLES',
                       'version' : '10',
                       'arch' : 'i386',
                       'kitPath' : self.prefix / 'os' ,
                       'repoType' : 'MULTIPLE',
                       'repoPath' : repo_path, 
                       'logged'  : False }
        t = CreateRepoCommand(**input_dict)
	# pre existing repo path not supported
        assert_raises(CommandFailException,t.execute)
	input_dict['repoPath'] = ''.join([repo_path,  '/os/'])
	t  = CreateRepoCommand(**input_dict)
	t.execute()

	#try non os repo
	input_dict['kitPath'] = self.prefix / 'rpm'
	input_dict['repoPath'] = ''.join([repo_path,  '/rpms/'])
	t = CreateRepoCommand(**input_dict)
	t.execute()
	path(repo_path).rmtree()
	
class TestRepoToolRHEL5(object):
    def setUp(self):
        self.prefix = path(tempfile.mkdtemp(prefix='repotool'))
        download('rpm.tgz', self.prefix)
        download('rhel5-os.tgz', self.prefix)
        unpack(self.prefix / 'rpm.tgz', self.prefix / 'rpm')
        unpack(self.prefix / 'rhel5-os.tgz', self.prefix / 'rhel5')
        self.test_repo_str ='''[testrepo]
name=TestRepo
baseurl=file:////%s/store/%s
enabled=1
gpgcheck=0
'''
        self.output_str ='''Setting up repositories
Reading repository metadata in from local files
Available Packages
kernel.i386                              1-1.2                  testrepo        
perl-Digest-HMAC.noarch                  1.01-15                testrepo        
php-ldap.i386                            5.1.6-7.el5            testrepo        
xorg-x11-xfs-utils.i386                  1:1.0.2-4              testrepo'''

    def teardown(self):
        self.prefix.rmtree()

    def __writeConf(self,arg1,arg2):
        ''' Fills the yum conf template with arguments and returns its path'''
        conf_file = ''.join([self.prefix,'/yum.conf'])
        fn = open(conf_file,'w')
        fn.write((self.test_repo_str % (arg1, arg2)).strip())
        fn.close()
        return conf_file

        
    def testCreateYumRepoCommand(self):
        '''Test Creation of Yum Non OS Repo'''
        orig_path = tempfile.mkdtemp('primitive')
        repo_path = ''.join([orig_path,'/rpms'])
        input_dict = { 'name' : 'CreateRepository',
                       'repoName' : 'TestRepo',
                       'os': 'RHEL',
                       'version' : '5',
                       'arch' : 'i386',
                       'kitPath' : self.prefix / 'rpm' ,
                       'repoType' : 'MULTIPLE',
                       'repoPath' : repo_path,
                       'logged'  : False }
        t = CreateRepoCommand(**input_dict)
	# pre existing repo path not supported
        t.execute()
        # Create a test configuration and point yum to that.
        conf_file = self.__writeConf(repo_path,'')
        ret,out,err = runCommand(self,'yum -c %s list available' % conf_file)
        if ret:
            print err
            assert False
        out = str(out).strip()
        assert len(out.split('\n')) == 7
        #Improve this  test
        assert out == self.output_str
        runCommand(self,'yum -c %s clean all' % conf_file)
        path(orig_path).rmtree()

    def testCreateYumRHEL5RepoCommand(self):
        '''Test creation of repo from sources in the format of RHEL5 media'''

        orig_path = tempfile.mkdtemp('primitive')
        repo_path = ''.join([orig_path,'/rhel5/'])
        input_dict = { 'name' : 'CreateRepository',
                       'repoName' : 'TestRepo',
                       'os': 'RHEL',
                       'version' : '5',
                       'arch' : 'i386',
                       'kitPath' : self.prefix / 'rhel5',
                       'repoType' : 'MULTIPLE',
                       'repoPath' : repo_path, 
                       'logged'  : False }
        t = CreateRepoCommand(**input_dict)
	# pre existing repo path not supported
        t.execute()
        conf_file = self.__writeConf(repo_path,'Server')
        ret,out,err = runCommand(self,'yum -c %s list available' % conf_file)
        if ret:
            print err
            assert False
        
        out = str(out).strip()
        assert len(out.split('\n')) == 7
        
        runCommand(self,'yum -c %s clean all' % conf_file)

        conf_file = self.__writeConf(repo_path,'Cluster')
        ret,out,err = runCommand(self,'yum -c %s list available' % conf_file)
        if ret:
            print err
            assert False
        out = str(out).strip()
        assert len(out.split('\n')) == 7
        assert out == self.output_str
        runCommand(self,'yum -c %s clean all' % conf_file)

        conf_file = self.__writeConf(repo_path,'ClusterStorage')
        ret,out,err = runCommand(self,'yum -c %s list available' % conf_file)
        if ret:
            print err
            assert False
        out = str(out).strip()
        assert len(out.split('\n')) == 7
        assert out == self.output_str
        runCommand(self,'yum -c %s clean all' % conf_file)

        conf_file = self.__writeConf(repo_path,'VT')
        out = runCommand(self,'yum -c %s list available' % conf_file)[1]
        if ret:
            print err
            assert False
        out = out.strip()
        assert  len(out.split('\n')) == 7
        assert out == self.output_str
        runCommand(self,'yum -c %s clean all' % conf_file)
        path(orig_path).rmtree()



class TestRepoToolRHEL4(object):
    def setUp(self):
        self.prefix = path(tempfile.mkdtemp(prefix='repotool'))
        download('rpm.tgz', self.prefix)
        download('rhel4-os.tgz', self.prefix)
        unpack(self.prefix / 'rpm.tgz', self.prefix / 'rpm')
        unpack(self.prefix / 'rhel4-os.tgz', self.prefix / 'rhel4')

    def teardown(self):
        self.prefix.rmtree()


    def __checkHdlist(self,hdlist1,hdlist2):
        ''' Check hdlist1 and 2 contents'''
        # We grovel binary data here for strings
        # As the name most intuitively implies, hdlist1 stores the package names
        # hdlist2 stores the file contents.
        assert os.path.exists(hdlist1)
        assert os.path.exists(hdlist2)
        fn = open(hdlist1, 'r')
        content = fn.read()
        fn.close()
        assert content.find('kernel') != -1
        assert content.find('perl-Digest-HMAC') != -1
        assert content.find('php-ldap') != -1
        assert content.find('xorg-x11-xfs-utils') != -1
        #Grovel hdlist2, the contents.
        fd = open(hdlist2, 'r')
        content = fd.read()
        fd.close()
        assert content.find('vmlinuz') != -1
        assert content.find('HMAC_MD5.pm') != -1
        assert content.find('ldap.ini') != -1
        assert content.find('xfsinfo') != -1
        

        
    def testCreateRhel4SimpleRepoCommand(self):
        '''Negative Test: Creation of RHEL4  Repo from plain set of RPMs'''
        orig_path = tempfile.mkdtemp('primitive')
        repo_path = ''.join([orig_path,'/rpms'])
        input_dict = { 'name' : 'CreateRepository',
                       'repoName' : 'TestRepo',
                       'os': 'RHEL',
                       'version' : '4',
                       'arch' : 'i386',
                       'kitPath' : self.prefix / 'rpm' ,
                       'repoType' : 'MULTIPLE',
                       'repoPath' : repo_path,
                       'logged'  : False }
        t = CreateRepoCommand(**input_dict)
	# Plain repositories not supported for RHEL4
        assert_raises(CommandFailException,t.execute)
        # Create a test configuration and point yum to that.
        
        path(orig_path).rmtree()

    def testCreateRhel4OSRepoCommand(self):
        '''Test creation of repo from sources in the format of RHEL4 media'''

        orig_path = tempfile.mkdtemp('primitive')
        repo_path = ''.join([orig_path,'/rhel4/'])
        input_dict = { 'name' : 'CreateRepository',
                       'repoName' : 'TestRepo',
                       'os': 'RHEL',
                       'version' : '4',
                       'arch' : 'i386',
                       'kitPath' : self.prefix / 'rhel4',
                       'repoType' : 'MULTIPLE',
                       'repoPath' : repo_path, 
                       'logged'  : False }
        t = CreateRepoCommand(**input_dict)
	# pre existing repo path not supported
        t.execute()
        hdlist1 = ''.join([repo_path,'store/RedHat/base/hdlist'])
        hdlist2 = ''.join([repo_path,'store/RedHat/base/hdlist2'])
        self.__checkHdlist(hdlist1,hdlist2)
        path(orig_path).rmtree()

    def testCreateRhel4MountedMediaCommand(self):
        '''Test creation of repo from Media.Skipped normally '''
        raise SkipTest
        orig_path = tempfile.mkdtemp('primitive')
        repo_path = ''.join([orig_path,'/rhel4/'])
        input_dict = { 'name' : 'CreateRepository',
                       'repoName' : 'TestRepo',
                       'os': 'RHEL',
                       'version' : '4',
                       'arch' : 'i386',
                       'kitPath' : '/mnt',
                       'repoType' : 'MULTIPLE',
                       'repoPath' : repo_path, 
                       'logged'  : False }
        t = CreateRepoCommand(**input_dict)
	# pre existing repo path not supported
        t.execute()
        hdlist1 = ''.join([repo_path,'store/RedHat/base/hdlist'])
        hdlist2 = ''.join([repo_path,'store/RedHat/base/hdlist2'])
        assert os.path.exists(hdlist1) 
        assert os.path.exists(hdlist2)
        

        
        
        
