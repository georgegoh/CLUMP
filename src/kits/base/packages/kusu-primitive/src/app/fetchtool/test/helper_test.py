#!/usr/bin/env python
# $Id: helper_test.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Copyright 2008 Platform Computing Inc.
#
from path import path
from nose.tools import assert_raises
from tempfile import mkdtemp, mkstemp
from primitive.fetchtool.helper import isDestWritable
from primitive.fetchtool.helper import checkUserPassFormat
from primitive.fetchtool.helper import checkForRequiredArgs

def testCheckForRequiredArgsPositive():
    ''' check required args function for FetchCommand'''
    input_dict = { 'a': '', 'b': '', 'c': ''}
    required_args = ['a', 'c']
    valid, missing_args = checkForRequiredArgs(input_dict, required_args)
    assert valid
    assert not missing_args

    input_dict = { 'a': '', 'b': '', 'c': ''}
    required_args = ['a', 'c', 'b']
    valid, missing_args = checkForRequiredArgs(input_dict, required_args)
    assert valid
    assert not missing_args


def testCheckForRequiredArgsNegative():
    ''' check required args function for FetchCommand returns False on failure'''
    input_dict = { 'a': '', 'b': '', 'c': ''}
    required_args = ['d']
    valid, missing_args = checkForRequiredArgs(input_dict, required_args)
    assert not valid
    assert missing_args == ['d']
    input_dict = { 'a': '', 'b': '', 'c': ''}
    required_args = ['a', 'b', 'f', 'z']
    valid, missing_args = checkForRequiredArgs(input_dict, required_args)
    assert not valid
    assert missing_args == ['f', 'z']


def testIsDestWritableDir():
    ''' test isDestWritable on directory'''
    dest_dir = path(mkdtemp(prefix='TestDestWritable-'))
    fetch_dir = False
    overwrite = False
    assert not isDestWritable(dest_dir, fetch_dir, overwrite)
    dest_dir.rmtree()


def testIsDestWritableFile():
    ''' test isDestWritable on file'''
    dest_file = path(mkstemp(prefix='TestDestWritable-')[1])
    fetch_dir = False
    overwrite = False
    assert not isDestWritable(dest_file, fetch_dir, overwrite)
    dest_file.remove()


def testCheckUserPassFormat():
    ''' assert valid types of user/password formats'''
    assert checkUserPassFormat('http://user:pass@localhost')
    assert checkUserPassFormat('https://user:pass@localhost/dir/file')
    assert checkUserPassFormat('ftp://user:pass@localhost/file.ext')
    assert checkUserPassFormat('https://user:@localhost') # blank password

def testCheckUserPassFormatNegative():
    ''' assert invalid types of user/password formats'''
    assert not checkUserPassFormat('http://user@localhost')
