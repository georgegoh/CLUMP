#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from distutils.core import setup
setup(name="kusu-repoman",
  version="0.2",
  author="Tsai Li Ming",
  author_email="ggoh@osgdc.org",
  url="http://www.osgdc.org/project/kusu",
  platforms=["any"],
  description="Repoman for Kusu.",
  packages = ['repoman'],
  package_dir={'repoman': 'src/lib'},
  scripts=['src/bin/repoman', 'src/bin/repopatch'],
  data_files=[('etc', ['src/etc/updates.conf']),
       ('etc/repoman-templates', ['src/etc/templates/update.kit.tmpl'])] 
  )
