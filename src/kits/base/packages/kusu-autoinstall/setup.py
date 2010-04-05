#!/usr/bin/env python
#
# $Id$
#
# Kusu autogen generator
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
__version__ = "$Revision$"

from distutils.core import setup
setup(name="kusu-autoinstall",
      version="0.2",
      author="Tsai Li Ming",
      author_email="ltsai@osgdc.org",
      url="http://www.osgdc.org/project/kusu",
      platforms=["any"],
      packages=['autoinstall'],
      package_dir={'autoinstall':'src/lib'},
      data_files=[('etc/templates', ['src/etc/templates/kickstart.tmpl', \
                                     'src/etc/templates/autoinst.tmpl']), 
                  ('share/doc/samples', ['src/doc/samples/genkickstart'])] 
     )
