#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer Framework Installer.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
"""This module creates the installer package for the framework."""
__version__ = "$Revision$"

from distutils.core import setup
setup(name="kusu-installer-tui",
      version="0.1",
      author="George Goh",
      author_email="ggoh@osgdc.org",
      url="http://www.osgdc.org/project/kusu",
      platforms=["any"],
      description="A cookie-trail TUI library based on snack.",
      long_description="A cookie-trail TUI library based on snack.",
      packages = ['kusu-installer-tui', 'kusu-installer-tui.kususcreens',
                  'kusu-installer-tui.kususcreens.partitiontool',
                  'kusu-installer-tui.navigator'],
      package_dir={'kusu-installer-tui': ''},
      data_files=[('/usr/locale/en_US/LC_MESSAGES', ['locale/en_US/LC_MESSAGES/kusu.mo']),
                  ('/usr/share/kusu-installer-tui', ['kususcreens/lang-names']),
                  ('/usr/share/kusu-installer-tui', ['kususcreens/lang-table'])]

     )
