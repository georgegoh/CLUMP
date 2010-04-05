#!/usr/bin/env python
# $Id: svcCommand_test.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Copyright 2008 Platform Computing Inc.
#
"""
Tests for base SvcCommand
"""

from nose.tools import assert_raises
from nose.tools import assert_equals
from nose.tools import assert_not_equals
from primitive.svctool.commands import SvcCommand
from primitive.core.errors import CommandMissingArgsException
from primitive.svctool.commands import ActionNotImplementedException
from primitive.svctool.commands import ActionNotSupportedException
from primitive.svctool.commands import PlatformNotSupportedException
from primitive.system.software.dispatcher_dict import dispatcher_dict
from primitive.system.software.probe import OS

def testSvcCommandInitPositive():
    '''Initialize SvcCommand object with good inputs.
       Make sure validation does not throw out false errors.
    '''
    sc = SvcCommand(action='test')

def testSvcCommandInitNegative():
    ''' Initialise ScvCommand object with missing inputs.
        Make sure the validation does throw out an error.
    '''
    assert_raises(CommandMissingArgsException, SvcCommand)

def testSvcCommandAction():
    '''Test to verify that SvcStartCommand causes given action.
    '''
    sc = SvcCommand(action='test')
    assert_equals(sc.action, 'test')

os = ('os', '0.0', 'arch')
verfallback_os = ('os', '0', 'arch')
centos_os = ('CentOS', '0', 'arch')
opensuse_os = ('openSUSE', '0', 'arch')
input_dict = {'service_test' : { os : 'ok' },
              'name_do' : { os : 'ok' },
              'service_do' : { os : 'not ok' },
              'service_verfallback' : { verfallback_os : 'ok' },
              'service_unsupportedplatform' : { ('bad', 'bad', 'bad') : 'not ok' },
              'service_centosfallback' : { ('RHEL', '0', 'arch') : 'ok' },
              'service_opensusefallback' : { ('SLES', '0', 'arch') : 'ok' }
             }

def testSvcCommandGetWithServicePositive():
    '''Test to verify getWithService() returns correct result
    '''
    sc = SvcCommand(action='test')
    sc.service = 'name'
    sc.dispatcher_dict = input_dict
    sc.os = os
    assert_equals(sc.getWithService(), 'ok')

def testSvcCommandGetWithServiceSpecialName():
    '''Test to verify getWithService() checks for generalized special service name
    '''
    sc = SvcCommand(action='do')
    sc.service = 'specialname'
    sc.dispatcher_dict = input_dict
    sc.os = os
    assert_not_equals(sc.getWithService(), 'ok')

def testSvcCommandGetWithServiceVersionFallback():
    '''Test to verify getWithService() checks for major version if major.minor version not found
    '''
    sc = SvcCommand(action='verfallback')
    sc.service = 'name'
    sc.dispatcher_dict = input_dict
    sc.os = os
    assert_equals(sc.getWithService(), 'ok')

def testSvcCommandGetWithServiceCentOSFallback():
    '''Test to verify getWithService() falls back to RHEL for centos
    '''
    sc = SvcCommand(action='centosfallback')
    sc.service = 'name'
    sc.dispatcher_dict = input_dict
    sc.os = centos_os
    assert_equals(sc.getWithService(), 'ok')

def testSvcCommandGetWithServiceOpenSUSEFallback():
    '''Test to verify getWithService() falls back to SLES for opensuse
    '''
    sc = SvcCommand(action='opensusefallback')
    sc.service = 'name'
    sc.dispatcher_dict = input_dict
    sc.os = opensuse_os
    assert_equals(sc.getWithService(), 'ok')

def testSvcCommandGetWithServiceUnsupportedPlatform():
    '''Test to verify an unsupported platform will raise PlatformNotSupportedException
    '''
    sc = SvcCommand(action='unsupportedplatform')
    sc.service = 'name'
    sc.dispatcher_dict = input_dict
    sc.os = os
    assert_raises(PlatformNotSupportedException, sc.getWithService)

def testSvcCommandGetWithServiceUnknownAction():
    '''Test to verify unknown action will raise ActionNotSupportedException
    '''
    sc = SvcCommand(action='unknownaction')
    sc.service = 'name'
    sc.dispatcher_dict = input_dict
    sc.os = os
    assert_raises(ActionNotSupportedException, sc.getWithService)

