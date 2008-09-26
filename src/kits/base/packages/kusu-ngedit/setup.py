#!/usr/bin/env python
# $Id: setup.py 524 2008-01-30 06:14:21Z hirwan $
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
    packages = ['ngedit','ngedit.ui','ngedit.ui.text'],
    package_dir = {'ngedit' : 'src/lib',
                'ngedit.ui':'src/lib/ui',
                'ngedit.ui.text': 'src/lib/ui/text'},
    scripts=['src/sbin/ngedit']
     )
