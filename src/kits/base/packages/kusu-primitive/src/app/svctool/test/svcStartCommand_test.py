#!/usr/bin/env python
# $Id: svcStartCommand_test.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Copyright 2008 Platform Computing Inc.
#
"""
Tests for SvcStartCommand
"""

from nose.tools import assert_raises
from nose.tools import assert_equals
from primitive.svctool.commands import SvcStartCommand
from primitive.core.errors import CommandMissingArgsException

def testSvcStartCommandInitPositive():
    '''Initialize SvcStartCommand object with good inputs
       Make sure validation does not throw out false errors.
    '''
    ssc = SvcStartCommand(service='test')

def testSvcStartCommandInitNegative():
    ''' Initialise ScvStartCommand object with missing inputs
        Make sure the validation does throw out a false validation.
    '''
    assert_raises(CommandMissingArgsException, SvcStartCommand)

def testSvcStartCommandAction():
    '''Test to verify that SvcStartCommand causes 'start' action
    '''
    ssc = SvcStartCommand(service='test')
    assert_equals(ssc.action, 'start')

