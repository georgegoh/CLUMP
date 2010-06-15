#!/usr/bin/env python
# $Id$
#
# Copyright 2008 Platform Computing Inc.
#
"""
Tests for SvcRestartCommand
"""

from nose.tools import assert_raises
from nose.tools import assert_equals
from primitive.svctool.commands import SvcRestartCommand
from primitive.core.errors import CommandMissingArgsException

def testSvcRestartCommandInitPositive():
    '''Initialize SvcRestartCommand object with good inputs
       Make sure validation does not throw out false errors.
    '''
    src = SvcRestartCommand(service='test')

def testSvcRestartCommandInitNegative():
    ''' Initialise ScvRestartCommand object with missing inputs
        Make sure the validation does throw out a false validation.
    '''
    assert_raises(CommandMissingArgsException, SvcRestartCommand)

def testSvcRestartCommandAction():
    '''Test to verify that SvcRestartCommand causes 'restart' action
    '''
    src = SvcRestartCommand(service='test')
    assert_equals(src.action, 'restart')

