#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
# 

from Cheetah.Template import Template

class Script:

    factory = None

    def __init__(self, factory):
        self.factory = factory

    def setProfile(self, profile):
        try:
            self.factory.setProfile(profile)
        except Exception, e: 
            raise e

    def write(self, f):
        out = open(f, 'w')
        t = Template(file=self.factory.template, searchList=[self.factory.getNameSpace()])  
        out.write(str(t))
        out.close()

