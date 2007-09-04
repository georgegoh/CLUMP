#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.
__version__ = "$Revision$"

from distutils.core import setup
setup(name="kusu-ngedit",
    version="0.2",
    author="Alex Tumanov",
    author_email="atumanov@platform.com",
    url="http://www.osgdc.org/project/kusu",
    platforms=["any"],
    packages = ['ngedit'],
    scripts=['src/bin/ngedit']
     )
