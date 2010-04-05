#!/usr/bin/env python
# $Id: osfamily_test.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Copyright 2008 Platform Computing Inc.
#
"""OS family test cases"""
from primitive.support.osfamily import getOSNames, keys, matchTuple
from primitive.support.osfamily_dict import osfamily_dict
from nose.tools import assert_raises
from path import path

class OSFamilyTest(object):
    """
    Test suite for osfamily - Work in progress
    """
    def setup(self):
        pass

    def teardown(self):
        pass

    def testKeyNotFound(self):
        ''' Test that [] is returned and not an exception when the key is not found '''
        assert [] ==  getOSNames('no such os family')

    def testKeyFound(self):
        test_list = ['test1','test2']
        osfamily_dict['test'] = test_list
        assert test_list == getOSNames('test')

    def testMatch(self):
        rhel_tuples = [('rhel','*','*','*'),('rhel','5','*','*'),('rhel','5','2','*'),('rhel','5','2','i386')]
        assert matchTuple(('rhel','5','2','i386'), rhel_tuples)
        assert matchTuple(('rhel','5','2','x86_64'), rhel_tuples)
        assert matchTuple(('rhel','5','20','x86_64'), rhel_tuples)
        assert matchTuple(('rhel','50','20','x86_64'), rhel_tuples)

    def testNonMatch(self):
        arch_tuple = [('rhel','5','2','i386')]
        minor_tuple = [('rhel','5','1','x86_64')]
        major_tuple = [('rhel','6','2','x86_64')]
        name_tuple = [('crap','5','2','x86_64')]

        arch_wildcard = [('*','*','*','i386')]
        minor_wildcard = [('*','*','1','*')]
        major_wildcard = [('*','6','*','*')]
        name_wildcard = [('crap','*','*','*')]

        assert not matchTuple(('rhel','5','2','x86_64'), arch_tuple)
        assert not matchTuple(('rhel','5','2','x86_64'), minor_tuple)
        assert not matchTuple(('rhel','5','2','x86_64'), major_tuple)
        assert not matchTuple(('rhel','5','2','x86_64'), name_tuple)

        assert not matchTuple(('rhel','5','2','x86_64'), arch_wildcard)
        assert not matchTuple(('rhel','5','2','x86_64'), minor_wildcard)
        assert not matchTuple(('rhel','5','2','x86_64'), major_wildcard)
        assert not matchTuple(('rhel','5','2','x86_64'), name_wildcard)

