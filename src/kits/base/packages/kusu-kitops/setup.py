#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from distutils.core import setup
setup(name="kusu-kitops",
      version="0.2",
      author="Alexey Tumanov",
      author_email="atumanov@platform.com",
      url="http://www.osgdc.org/project/kusu",
      platforms=["any"],
      packages = ['kitops'],
      package_dir={'kitops': 'src/lib'},
      scripts=['src/bin/kusu-kitops']
     )
