#!/usr/bin/env python
#
# $Id$
#

from distutils.core import setup
setup(name="rhpl",
      version="0.148.3",
      author="",
      author_email="",
      url="http://www.redhat.com",
      platforms=["any"],
      packages = ['classic/rhpl'],
      package_dir={'classic/rhpl': 'rhpl'},
)
