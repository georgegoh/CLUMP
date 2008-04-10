#!/usr/bin/env python
#
# $Id: tool_test.py 3148 2008-03-19 03:40:58Z hsaliak $
#
# Copyright 2008 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

import os
from path import path
import tempfile
try:
    import subprocess
except:
    from popen5 import subprocess
from kusu.util import tools
from kusu.util.errors import CopyFailedError
from kusu.util.errors import CommandFailedToRunError
from nose.tools import assert_raises
from kusu.util import testing


def setup():
    pass

def teardown():
    pass


def testgetArch():
    """ Test that getArch returns the same value as the current arch against an alternate implementation """
    arch = 'fictitious'
    assert tools.getArch() != arch
    try:
        subP =  subprocess.Popen(["uname","-p"],stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    except OSError,e:
        assert 'Test failed - unable to get arch. uname -p failed with error: %s ' % os.strerror(e.errno)
    out,err = subP.communicate()
    assert err == ''
    assert out.rstrip()  == tools.getArch()
    
    
def testcheckToolDeps():
    """ Test Check Tool Deps: The function tested runs a 'which' on the command line. """
    assert_raises(tools.ToolNotFound,tools.checkToolDeps,'Garbled Data')
    assert tools.checkToolDeps('uname')




def testcheckAllToolsDeps():
    assert tools.checkAllToolsDeps()


def testurl_mirror_copy():
    """XXX-Write me """
    pass

def testcpio_copytree():
    #this should be moved to setup 
    toDir = tools.mkdtemp(dir='/tmp')
    fromDir = tools.mkdtemp(dir='/tmp')
    testSubDir = tools.mkdtemp(dir=fromDir)
    testFd,testFilename = tempfile.mkstemp(dir=fromDir,text=True)
    testFile = os.fdopen(testFd,'r+')
    testString = "Test for cpioCopytree\n"
    testFile.write(testString)
    testFile.close()
    assert_raises(CommandFailedToRunError,tools.cpio_copytree,fromDir,toDir,findProg='garbled')
    assert_raises(CopyFailedError,tools.cpio_copytree,fromDir,toDir,cpioProg='garbled')
    assert_raises(CopyFailedError,tools.cpio_copytree,fromDir,toDir,cpioProg='mock_cpio.py')
    #test proper functionality - so that it works
    tools.cpio_copytree(fromDir,toDir)
    assert os.path.isdir(fromDir)
    assert os.path.isdir(toDir)
    assert os.path.isdir(testSubDir)
    assert os.path.isfile(testFilename)
    assert os.path.isdir('/'.join([toDir,os.path.basename(testSubDir)]))
    assert os.path.isfile('/'.join([fromDir,os.path.basename(testFilename)]))

    os.remove(testFilename)
    os.rmdir(testSubDir)
    os.remove('/'.join([toDir,os.path.basename(testFilename)]))
    os.rmdir('/'.join([toDir,os.path.basename(testSubDir)]))
    os.rmdir(toDir)
    os.rmdir(fromDir)


        
#test case for space 
#test case for almost full  - shouldnt that be in CopyMedia ?

def testmkdtemp():
    """Test mkdtemp. Test to check the path exists. Test to check that it is a directory.
    Finally, check that an absolute path is returned """
    #test that a tempdir is created and its absolute. test that its basename begins with the parameter we provided
    tempdir = tools.mkdtemp(dir='/tmp')
    assert tempdir != '/tmp' 
    tempdir_path = path(tempdir)
    assert path.exists(tempdir_path)
    assert path.isdir(tempdir_path)
    assert path.isabs(tempdir_path)
    #now remove the path and check it doesnt exist but ensure its not /tmp for some odd reason
    path.rmdir(tempdir_path)
    assert not path.exists(tempdir_path)




