#!/usr/bin/env python
# $Id: svcStopCommand_test.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Copyright 2008 Platform Computing Inc.
#
"""
Tests for SvcStopCommand
"""

from nose.tools import assert_raises
from nose.tools import assert_equals
from primitive.svctool.commands import SvcStopCommand
from primitive.core.errors import CommandMissingArgsException

def testSvcStopCommandInitPositive():
    '''Initialize SvcStopCommand object with good inputs
       Make sure validation does not throw out false errors.
    '''
    ssc = SvcStopCommand(service='test')

def testSvcStopCommandInitNegative():
    ''' Initialise ScvStopCommand object with missing inputs
        Make sure the validation does throw out a false validation.
    '''
    assert_raises(CommandMissingArgsException, SvcStopCommand)

def testSvcStopCommandAction():
    '''Test to verify that SvcStopCommand causes 'stop' action
    '''
    ssc = SvcStopCommand(service='test')
    assert_equals(ssc.action, 'stop')

