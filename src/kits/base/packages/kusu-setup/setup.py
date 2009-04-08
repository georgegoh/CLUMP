#!/usr/bin/env python
# $Id$
#
# Kusu Configure
#
# Copyright 2009 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
"""This module creates the setup package for the framework."""
__version__ = "$Revision$"

from distutils.core import setup
setup(name="kusu-setup",
      version="0.1",
      author="George Goh",
      author_email="ggoh@osgdc.org",
      url="http://www.osgdc.org/project/kusu",
      platforms=["any"],
      description="Bootstrap setup for Kusu.",
      long_description="Kusu's Bootstrap Setup.",
      packages = ['setup'],
      package_dir={'setup': 'src/lib'},
      data_files=[('share/doc', ['src/doc/LICENSE'])],
      scripts=['src/bin/kusu-setup']
     )
