#!/usr/bin/env python
#
# $Id$
#
# Kusu autogen generator
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
__version__ = "$Revision$"

from distutils.core import setup
setup(name="kusu-autogen",
      version="0.1",
      author="Tsai Li Ming",
      author_email="ltsai@osgdc.org",
      url="http://www.osgdc.org/project/kusu",
      platforms=["any"],
      packages=['autogen'],
      package_dir={'autogen':'src/lib'},
      data_files=[('etc/templates', ['src/etc/templates/kickstart.tmpl'])]
     )
