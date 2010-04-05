#!/usr/bin/env python
# $Id$
#
# Copyright 2008 Platform Computing Inc.
#
"""
Tests for SvcEnableCommand
"""

from nose.tools import assert_raises
from nose.tools import assert_equals
from primitive.svctool.commands import SvcEnableCommand
from primitive.core.errors import CommandMissingArgsException

def testSvcEnableCommandInitPositive():
    '''Initialize SvcEnableCommand object with good inputs
       Make sure validation does not throw out false errors.
    '''
    sec = SvcEnableCommand(service='test')

def testSvcEnableCommandInitNegative():
    ''' Initialise ScvEnableCommand object with missing inputs
        Make sure the validation does throw out a false validation.
    '''
    assert_raises(CommandMissingArgsException, SvcEnableCommand)

def testSvcEnableCommandAction():
    '''Test to verify that SvcEnableCommand causes 'enable' action
    '''
    sec = SvcEnableCommand(service='test')
    assert_equals(sec.action, 'enable')

