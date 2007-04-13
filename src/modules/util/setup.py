#!/usr/bin/env python
#
# $Id$
#
# Kusu util generator
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
__version__ = "$Revision$"

from distutils.core import setup
setup(name="kusu-core",
    version="0.1",
    author="Najib Ninaba",
    author_email="najib@osgdc.org",
    url="http://www.osgdc.org/project/kusu",
    platforms=["any"],
    packages=['util'],
    package_dir={'util':'src/lib'}
     )
