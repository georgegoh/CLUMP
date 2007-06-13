#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from distutils.core import setup
setup(name="kusu-kit",
      version="0.2",
      author="Najib Ninaba",
      author_email="najib@osgdc.org",
      url="http://www.osgdc.org/project/kusu",
      platforms=["any"],
      packages = ['kit'],
      package_dir={'kit': 'src/lib'}
     )
