#!/usr/bin/env python
#
# $Id$
#

from distutils.core import setup, Extension
setup(name="anaconda",
      version="0.148.3",
      author="",
      author_email="",
      url="http://www.redhat.com",
      platforms=["any"],
      packages = ['classic/anaconda'],
      package_dir={'classic/anaconda': ''},
      scripts = ['bin/pkgorder']
)
