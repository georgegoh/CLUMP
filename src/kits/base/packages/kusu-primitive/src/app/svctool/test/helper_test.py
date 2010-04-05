#!/usr/bin/env python
# $Id: helper_test.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Copyright 2008 Platform Computing Inc.
#
"""
Tests for base helper functions
"""

from nose.tools import assert_raises
from nose.tools import assert_equals
from primitive.svctool.helper import checkForRequiredArgs, runServiceCommand, dispatcherNameVerArch

def testCheckForRequiredArgsMissing():
    '''Test to verify that missing arguments are caught correctly
    '''
    valid, missing = checkForRequiredArgs({'test' : 'test'}, ['test', 'testmore'])
    assert_equals(valid, False)
    assert_equals(missing, ['testmore'])

def testCheckForRequiredArgsValid():
    '''Test to verify that valid arguments are accepted
    '''
    valid, missing = checkForRequiredArgs({'test' : 'test'}, ['test'])
    assert_equals(valid, True)
    assert_equals(missing, [])

def testRunServiceCommandReturnFlagFalse():
    '''Test to verify that runServiceCommand returns False for bad command
    '''
    assert_equals(runServiceCommand('nonsensicalstuffwhichshouldfailatallcosts')[0], False)


def testDispatcherNameVerArchFallback():
    '''Test to verify centos and opensuse fallbacks
    '''
    assert_equals(dispatcherNameVerArch(('centos','','')), ('RHEL', '', ''))
    assert_equals(dispatcherNameVerArch(('opensuse','','')), ('SLES', '', ''))

def testDispatcherNameVerArchPassThrough():
    '''Test to verify non centos/opensuse os passes throughs
    '''
    assert_equals(dispatcherNameVerArch(('test','','')), ('test', '', ''))

