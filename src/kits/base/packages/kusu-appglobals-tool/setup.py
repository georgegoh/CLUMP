!/usr/bin/env python
#
# $Id: setup.py 3271 2009-11-25 08:01:11Z kunalc $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from distutils.core import setup
setup(name="kusu-appglobals-tool",
      version="0.1",
      author="Kunal Chowdhury",
      author_email="kunalc@platform.com",
      url="http://www.osgdc.org/project/kusu",
      platforms=["any"],
      packages = ['kusu-appglobals-tool'],
      package_dir={'kusu-appglobals-tool': 'src/lib'},
      scripts=['src/bin/kusu-appglobals-tool']
     )

