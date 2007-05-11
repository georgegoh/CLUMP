#!/usr/bin/env python
#
# $Id$
#

from distutils.core import setup
setup(name="createrepo",
      version="0.4.8",
      platforms=["any"],
      packages=['createrepo'],
      package_dir={'createrepo': '.'},
      scripts=['bin/createrepo', 
               'bin/modifyrepo']
 
     )
