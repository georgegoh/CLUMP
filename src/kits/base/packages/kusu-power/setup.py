#!/usr/bin/env python
#
# $Id$
#
# Copyright 2010 Platform Computing Inc.
#
# Licensed under GPL version 2; See COPYING file for details.
#

"""
Build file
"""
from distutils.core import setup

setup(name='kusu-power',
      version='2.2.1',
      scripts=['src/bin/kusu-power.py'],
      packages=['', 'powerplugins'],
      package_dir={'': 'src/lib', 'powerplugins' : 'src/powerplugins'},
      options = {'install': {'install_scripts': '$base/libexec'}},
      data_files=[('etc', ['src/etc/kusu-power.conf.example']),
                  ('share/doc/kusu-power', ['doc/README', 'doc/RELEASE_NOTES', 'doc/COPYING'])]
      )
