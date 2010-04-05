#!/usr/bin/env python
# $Id$
#
# Copyright 2008 Platform Computing Inc.
#
"""Dispatcher test cases"""
from primitive.system.software.dispatcher import Dispatcher 
from primitive.system.software.probe import getArch,OS,X86_ARCHES
from nose.tools import assert_raises
from path import path
import platform
import subprocess

class TestDispatcher(object):
    """
    Test suite for software module - Work in progress
    """
    def setup(self):
        pass

    def teardown(self):
        pass
    

    def testDispatcherKeyNotFound(self):
        ''' Test that None is returned and not an exception when the key is not found '''
        assert None ==  Dispatcher.get('hello there')
    def testDispatcherKeyFound(self):
        assert Dispatcher.get('webserver_usergroup') != None

class TestProbe(object):
    """
    Test suite for software module - Work in progress
    """
    def setup(self):
        pass

    def teardown(self):
        pass
    

    def testValidOSTuple(self):
        ''' Test valid return values are returned by the OS() function. This test needs to be expanded with new platform support.
        '''
        os,ver,arch = OS()
        SUPPORTED_OS = ['RHEL','SLES','openSUSE','CentOS']
        assert os in SUPPORTED_OS
        assert ver  # this cant be reliably checked for
        assert arch in ['i386','x86_64']

    def testgetArch(self):
        ''' Test that the system arch is in the supported arch dict, if not it raises an error as this is a potential corner case'''
        cmd = 'arch'
        archP = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
        result, code = archP.communicate()
        _arch = result.strip('\n')
        if _arch !=  'x86_64':
            assert _arch in X86_ARCHES
        #if arch == x86_64 we are ok
        assert getArch() in ['i386', 'x86_64']
