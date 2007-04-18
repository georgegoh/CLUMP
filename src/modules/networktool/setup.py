#!/usr/bin/env python
#
# $Id: setup.py 311 2007-04-17 13:45:20Z ltsai $
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

__version__ = "$Revision$"

from distutils.core import setup
setup(name="kusu-networktool",
      version="0.1",
      author="George Goh",
      author_email="ggoh@osgdc.org",
      url="http://www.osgdc.org/project/kusu",
      platforms=["any"],
      packages=['networktool'],
      package_dir={'networktool':'src/lib'}
     )
