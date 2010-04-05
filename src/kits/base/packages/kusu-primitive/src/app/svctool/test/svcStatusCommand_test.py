#!/usr/bin/env python
# $Id: svcStatusCommand_test.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Copyright 2008 Platform Computing Inc.
#
"""
Tests for SvcStatusCommand
"""

from nose.tools import assert_raises
from nose.tools import assert_equals
from primitive.svctool.commands import SvcStatusCommand
from primitive.core.errors import CommandMissingArgsException

def testSvcStatusCommandInitPositive():
    '''Initialize SvcStatusCommand object with good inputs
       Make sure validation does not throw out false errors.
    '''
    ssc = SvcStatusCommand(service='test')

def testSvcStatusCommandInitNegative():
    ''' Initialise ScvStatusCommand object with missing inputs
        Make sure the validation does throw out a false validation.
    '''
    assert_raises(CommandMissingArgsException, SvcStatusCommand)

def testSvcStatusCommandAction():
    '''Test to verify that SvcStatusCommand causes 'status' action
    '''
    ssc = SvcStatusCommand(service='test')
    assert_equals(ssc.action, 'status')

