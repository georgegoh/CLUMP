#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from distutils.core import setup
setup(name="kusu-hardware",
      version="0.1",
      author="Tsai Li Ming",
      author_email="ltsai@osgdc.org",
      url="http://www.osgdc.org/project/kusu",
      platforms=["any"],
      packages = ['hardware'],
      package_dir={'hardware': 'src/lib'},
      data_files=[('etc/', ['src/etc/pci.ids'])]
     )
