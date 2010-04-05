#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

from kusu.buildkit import DefaultKit, DefaultComponent

class TestDefaultKit(object):
    """ Tests for default values for kits.
    """
    
    def setUp(self):
        self.kit = {'version': '', 'release': '', 'pkgname': '', 'name': '',
                    'arch': '', 'description': '', 'dependencies': [],
                    'license': '', 'scripts': [], 'removable': True}
               
    def testValues(self):
        """ Validates that instance of DefaultKit has all the values needed.
        """
        k = DefaultKit()
        s = set(k.keys())
        
        s1 = set(self.kit.keys())
        
        assert s1.issubset(s)

class TestDefaultComponent(object):
    """ Tests for default values for components.
    """

    def setUp(self):
        self.comp = {'compversion': '', 'comprelease': '', 'pkgname': '', 'name': '',
                    'arch': '', 'description': '', 'ngtypes': [], 'ostype': '',
                    'osversion': ''}

    def testValues(self):
        """ Validates that instance of DefaultComponent has all the values needed.
        """
        c = DefaultComponent()
        s = set(c.keys())

        s1 = set(self.comp.keys())

        assert s1.issubset(s)

