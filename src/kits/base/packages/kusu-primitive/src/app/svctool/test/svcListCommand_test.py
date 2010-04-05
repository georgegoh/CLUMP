#!/usr/bin/env python
# $Id: svcListCommand_test.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Copyright 2008 Platform Computing Inc.
#
"""
Tests for SvcListCommand
"""

from nose.tools import assert_raises
from nose.tools import assert_equals
from primitive.svctool.commands import SvcListCommand
from primitive.core.errors import CommandMissingArgsException
from primitive.svctool.commands import ActionNotImplementedException

def testSvcListCommandInitPositive():
    '''Initialize SvcListCommand object with good inputs
       Make sure validation does not throw out false errors.
    '''
    ssc = SvcListCommand()

def testSvcListCommandAction():
    '''Test to verify that SvcListCommand causes 'list' action
    '''
    ssc = SvcListCommand()
    assert_equals(ssc.action, 'list')

def testSvcListCommandActionNotImplemented():
    '''Test to verify that executing SvcListCommand raises ActionNotImplementedException
    '''
    ssc = SvcListCommand()
    assert_raises(ActionNotImplementedException, ssc.execute)

