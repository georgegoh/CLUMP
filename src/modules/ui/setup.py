#!/usr/bin/env python
# $Id$
#
# Kusu UI Framework.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
__version__ = "$Revision$"

from distutils.core import setup
setup(name="kusu-ui",
      version="0.2",
      author="George Goh",
      author_email="ggoh@osgdc.org",
      url="http://www.osgdc.org/project/kusu",
      platforms=["any"],
      description="UI Framework for Kusu.",
      long_description="Kusu's User Interface Framework.",
      packages = ['ui', 'ui.text'],
      package_dir={'ui': 'src/lib',
                   'ui.text': 'src/lib/text'},
      data_files=[('share/po', ['src/po/kusuapps.po']),
                  ('share/doc', ['src/doc/LICENSE'])],
      scripts=['src/bin/navigator-text']
     )
