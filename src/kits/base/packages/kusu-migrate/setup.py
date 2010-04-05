#!/usr/bin/env python
#
# $Id: setup.py 2946 2009-09-22 02:45:21Z yqang $
#
# Copyright 2010 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from distutils.core import setup
setup(name="kusu-migrate",
      version="2.0",
      author="Ang Yun Quan",
      author_email="yqang@platform.com",
      url="http://www.osgdc.org/project/kusu",
      platforms=["any"],
      packages = ['kusu-migrate'],
      scripts=['src/sbin/kusu-migrate']
     )
