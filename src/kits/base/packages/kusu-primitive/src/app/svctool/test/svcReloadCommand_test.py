#!/usr/bin/env python
# $Id$
#
# Copyright 2008 Platform Computing Inc.
#
"""
Tests for SvcReloadCommand
"""

from nose.tools import assert_raises
from nose.tools import assert_equals
from primitive.svctool.commands import SvcReloadCommand
from primitive.core.errors import CommandMissingArgsException
from primitive.svctool.commands import ActionNotImplementedException

def testSvcReloadCommandInitPositive():
    '''Initialize SvcReloadCommand object with good inputs
       Make sure validation does not throw out false errors.
    '''
    src = SvcReloadCommand(service='test')

def testSvcReloadCommandInitNegative():
    ''' Initialise ScvReloadCommand object with missing inputs
        Make sure the validation does throw out a false validation.
    '''
    assert_raises(CommandMissingArgsException, SvcReloadCommand)

def testSvcReloadCommandAction():
    '''Test to verify that SvcReloadCommand causes 'reload' action
    '''
    src = SvcReloadCommand(service='test')
    assert_equals(src.action, 'reload')

def testSvcReloadCommandActionNotImplemented():
    '''Test to verify that executing SvcReloadCommand raises ActionNotImplementedException
    '''
    src = SvcReloadCommand(service='test')
    assert_raises(ActionNotImplementedException, src.execute)

