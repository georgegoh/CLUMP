#!/usr/bin/env python
# $Id$
#
# Copyright 2008 Platform Computing Inc.
#
"""
Tests for SvcDisableCommand
"""

from nose.tools import assert_raises
from nose.tools import assert_equals
from primitive.svctool.commands import SvcDisableCommand
from primitive.core.errors import CommandMissingArgsException

def testSvcDisableCommandInitPositive():
    '''Initialize SvcDisableCommand object with good inputs
       Make sure validation does not throw out false errors.
    '''
    sdc = SvcDisableCommand(service='test')

def testSvcDisableCommandInitNegative():
    ''' Initialise ScvDisableCommand object with missing inputs
        Make sure the validation does throw out a false validation.
    '''
    assert_raises(CommandMissingArgsException, SvcDisableCommand)

def testSvcDisableCommandAction():
    '''Test to verify that SvcDisableCommand causes 'disable' action
    '''
    sdc = SvcDisableCommand(service='test')
    assert_equals(sdc.action, 'disable')

