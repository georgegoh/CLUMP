#!/usr/bin/env python
# $Id: installcommand_test.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Copyright 2008 Platform Computing Inc.
#
""" Tests for InstallCommand."""
from nose.tools import assert_raises
from primitive.core.command import CommandFailException
from primitive.core.errors import CommandMissingArgsError
from primitive.installtool.commands import GenerateAutoInstallScriptCommand

def testUnsupportedOS():
    ''' Fail with unsupported OS version. '''
    assert_raises(CommandFailException, GenerateAutoInstallScriptCommand,
                                        os={'name': 'nosupport', 'version': '10.2'},
                                        diskprofile=None,
                                        networkprofile={},
                                        installsrc='http://10.10.11.218',
                                        rootpw='system',
                                        tz='Asia/Singapore',
                                        lang='en_US',
                                        keyboard='english-us',
                                        packageprofile=[],
                                        diskorder=[],
                                        template_uri='',
                                        outfile='')

def testInsufficientOSArgs():
    ''' Fail with insufficient OS args. '''
    assert_raises(CommandMissingArgsError, GenerateAutoInstallScriptCommand,
                                           os={'name': 'sles'},
                                           diskprofile=None,
                                           networkprofile={},
                                           installsrc='http://10.10.11.218',
                                           rootpw='system',
                                           tz='Asia/Singapore',
                                           lang='en_US',
                                           keyboard='english-us',
                                           packageprofile=[],
                                           diskorder=[],
                                           template_uri='',
                                           outfile='')

def testInsufficientArgs():
    ''' Fail with insufficient args. '''
    assert_raises(CommandMissingArgsError, GenerateAutoInstallScriptCommand,
                                           os={'name': 'sles', 'version': '10'},
                                           diskprofile=None,
                                           installsrc='http://10.10.11.218',
                                           rootpw='system',
                                           tz='Asia/Singapore',
                                           lang='en_US',
                                           keyboard='english-us',
                                           diskorder=[])
