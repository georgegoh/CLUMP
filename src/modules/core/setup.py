#!/usr/bin/env python
#
# $Id$
#
# Kusu core generator
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
__version__ = "$Revision$"

from distutils.core import setup
setup(name="kusu-core",
    version="0.2",
    author="Najib Ninaba",
    author_email="najib@osgdc.org",
    url="http://www.osgdc.org/project/kusu",
    platforms=["any"],
    packages=['core'],
    package_dir={'core':'src/lib'},
    scripts=['src/bin/kusuenv.sh']
     )
