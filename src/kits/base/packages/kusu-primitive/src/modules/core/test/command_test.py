#!/usr/bin/env python

import os
import tempfile
from  primitive.core.command import *
try:
    import subprocess
except:
    from popen5 import subprocess
#from primitive.modules.core import command
import errno
import logging
import tempfile

from nose.tools import assert_raises

class RankTestCommand(Command):
     def __init__(self):
         Command.__init__(self,name="RankTest",logged=False,locked=False)
         self.pre_ranklist = []
         self.post_ranklist = [] 
     def execImpl(self):
        pass
     def appendPreRank(self,v):
         self.pre_ranklist.append(v)

     def appendPostRank(self,v):
         self.post_ranklist.append(v)

class ExecTestCommand(Command):
     def __init__(self):
         Command.__init__(self,name="ExecTest",logged=False,locked=False)
         self.preCalled = False
         self.postCalled = False
         self.execImplCalled = False
     def execImpl(self):
        self.execImplCalled = True
     # Helpers because you cant do assignments within a lambda
     def setPreCalled(self):
         self.preCalled = True
     def setPostCalled(self):
         self.postCalled = True
     
class RetValTestCommand(Command):
    def __init__(self,*kargs,**kwargs):
        Command.__init__(self,name="RetValTest",logged=False,locked=False)
        self.args = kargs
        self.kwargs = kwargs
    def execImpl(self):
        return self.args,self.kwargs


class TestLockCommand(Command):
    ''' Test command to see if locking works'''
    def __init__(self,**kwargs):
        if 'lockdir' in kwargs.keys():
            self.lockdir = kwargs['lockdir']
        else:
            self.lockdir='/tmp'

        Command.__init__(self,name="LockTest",logged=False,locked=True,
                         lockdir=self.lockdir)
    def execImpl(self):
        assert self.isLocked()
        
class TestLoggingCommand(Command):
    def __init__(self):
        Command.__init__(self,name="LogTest",logged=True,logdir='/tmp',
                             locked=False)
    def execImpl(self):
        #obtain logfile location
        if not self.logged:
            assert False
        #test that logging is enabled here.
        self.logger.info("Test")
        log_string = self.runCommand(("tail -1 %s" % self.logfile))[1]
        assert log_string.strip().split()[-1:][0] == 'Test'
        self.logger.debug("This should not be logged")
        assert log_string.strip().split()[-1:][0] == 'Test'
        #Raise logging level and test if debugging works
        self.logger.setLevel(logging.getLevelName('DEBUG'))
        self.logger.debug('TestDebug')
        log_string = self.runCommand(("tail -1 %s" % self.logfile))[1]
        assert log_string.strip().split()[-1:][0] == 'TestDebug'
        
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

class TestPostExecAfterExceptionCommand(Command):
    ''' Test that post_execs are really executed even after
        an exception in the execImpl.
    '''
    def __init__(self):
        Command.__init__(self,name="LockTest",logged=False,locked=True)
    def execImpl(self):
        raise Exception
 
def setup():
    pass

def teardown():
    pass
def testRetval():
    ''' Running tests to check if return values from execImpl are propagated correctly'''
    # test no args
    t = RetValTestCommand()
    ret =  t.execute()
    assert not ret[0]
    assert not ret[1]
    #test single arg
    t = RetValTestCommand('test')
    ret = t.execute()[0]
    assert ret[0] == 'test'
    # test a list of args
    t = RetValTestCommand('1','2','3')
    ret = t.execute()[0]

    assert ret == ('1','2','3')
    # test a list and dictionary tuple
    t = RetValTestCommand('1','2', foo='bar',baz='quux')
    retlist,retdict = t.execute()
    assert retlist == ('1','2')
    assert retdict['foo'] == 'bar'
    assert retdict['baz'] == 'quux'

def testRanking():
    ''' test pre and post ranking as well as function execution in pre and post '''
    t = RankTestCommand()
    t.registerPreCallback(lambda: t.appendPreRank(10),rank=10)
    t.registerPreCallback(lambda: t.appendPreRank(6),rank=6)
    t.registerPostCallback(lambda: t.appendPostRank(5),rank=5)
    t.registerPostCallback(lambda: t.appendPostRank(9),rank=9)
    t.execute()

    assert t.pre_ranklist == [ 10 , 6 ] # must be in descending order
    assert t.post_ranklist ==  [ 9 , 5 ]

def testExecOrder():
    ''' simple test to test ExecImpl being called after pre and post '''
    t = ExecTestCommand()
    t.registerCallbacks(lambda : t.setPreCalled() , lambda : t.setPostCalled())
    t.execute()
    assert t.preCalled
    assert t.postCalled
    assert t.execImplCalled

def testCommandLocked1():
    ''' Test if locking is set correctly in commands '''
    t = TestLockCommand()
    t.execute()

def touch(file):
    '''helper function to touch file'''
    f = open(file,'w')
    f.close()
        
    
def testCommandLocked2():
    ''' Negative test case - Log to non existent directory and '''

    # This test only works if there are no files currently locked by primitive
    tf = tempfile.mkdtemp('test')
    t = TestLockCommand(lockdir=tf)
    os.removedirs(tf)
    assert not os.path.exists('/tmp/not_exists')
    assert_raises(CommandFailException,t.execute)
def testCommandLocked3():
    ''' Negative test case - touch a file, /tmp/command_test_testlock3 and
    test for exception'''
    lockdir = '/tmp/command_test_testlock3'
    if os.path.exists(lockdir):
        if os.path.isdir(lockdir):
            os.rmdir(lockdir)
        else:
            os.remove(lockdir)
    touch(lockdir)
    assert_raises(CommandFailException,TestLockCommand,lockdir=lockdir)
    os.remove(lockdir)

def testCommandLogging():
    t = TestLoggingCommand()
    t.execute()

def testExecImplException():
    ''' Test post_execs are really executed after
        an exception in execImpl.
    '''
    t = TestPostExecAfterExceptionCommand()
    assert_raises(Exception, t.execute)
    assert not t.isLocked()
