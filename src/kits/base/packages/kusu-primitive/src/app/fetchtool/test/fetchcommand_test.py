#!/usr/bin/env python
# $Id$
#
# Copyright 2008 Platform Computing Inc.
#
"""
Tests for the FetchCommand abstract class.
"""
from nose.tools import assert_raises
from primitive.fetchtool.commands import FetchCommand
from primitive.core.command import CommandFailException
from primitive.core.errors import CommandMissingArgsException

def testFetchCommandInitPositive():
    ''' Initialise FetchCommand object with good inputs
        Make sure the validation does not throw out false errors.
    '''
    fc = FetchCommand(uri='file:///tmp/test', fetchdir=False,
                      destdir='/tmp/dodo', overwrite=True)

def testFetchCommandInitNegative():
    ''' Initialise FetchCommand object with missing inputs
        Make sure the validation does throw out a false validation and the
        correct list of missing input(s).
    '''
    assert_raises(CommandMissingArgsException, FetchCommand,
                                               uri='file:///tmp/test',
                                               fetchdir=False,
                                               destdir='/tmp/dodo')

def testFetchCommandFakeProtocol():
    ''' Initialise FetchCommand with a contrived protocol \
        raises CommandFailException
    '''
    assert_raises(CommandFailException, FetchCommand,
                                        uri='imagi:///nation/land',
                                        fetchdir=False,
                                        destdir='/imagination',
                                        overwrite=False)
