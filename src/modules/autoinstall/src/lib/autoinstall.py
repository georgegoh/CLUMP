#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
# 

from kusu.util.errors import *
from path import path
from Cheetah.Template import Template

class Script:

    def __init__(self, factory):
        self.factory = factory

    def write(self, f):
        f = path(f)
    
        parent_path = f.dirname()
        if not parent_path.exists():
            raise InvalidPathError, '%s not found' % parent_path

        out = open(f, 'w')

        t = Template(file=str(self.factory.template), searchList=[self.factory.getNameSpace()])  
        out.write(str(t))
        out.close()

