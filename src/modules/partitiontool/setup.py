#!/usr/bin/env python
# $Id$
#
# Kusu Disk Partitioner Tool.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
"""This module creates the installer package for the framework."""
__version__ = "$Revision: 237 $"

from distutils.core import setup
setup(name="kusu-partitiontool",
      version="0.2",
      author="George Goh",
      author_email="ggoh@osgdc.org",
      url="http://www.osgdc.org/project/kusu",
      platforms=["any"],
      description="Partition for Kusu.",
      long_description="Kusu's Textual User Interface Installer.",
      packages = ['partitiontool'],
      package_dir={'partitiontool': 'src/lib'},
      data_files=[('share/doc', ['src/doc/LICENSE'])]
     )
