#!/usr/bin/env python
# $Id: setup.py 237 2007-04-05 08:57:10Z ggoh $
#
# Kusu Text Installer Framework.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
"""This module creates the installer package for the framework."""
__version__ = "$Revision: 237 $"

from distutils.core import setup
setup(name="kusu-installer-text",
      version="0.1",
      author="George Goh",
      author_email="ggoh@osgdc.org",
      url="http://www.osgdc.org/project/kusu",
      platforms=["any"],
      description="TUI installer for Kusu.",
      long_description="Kusu's Textual User Interface Installer.",
      packages = ['installer'],
      package_dir={'installer': 'src/lib'},
      data_files=[('share/po', ['src/po/kusuapps.po']),
                  ('share/doc', ['src/doc/LICENSE']),
                  ('etc', ['src/etc/lang-names']),
                  ('etc', ['src/etc/lang-table'])],
      scripts=['src/bin/installer',
               'src/bin/udhcpc.script']
     )
