#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.
__version__ = "$Revision$"

from distutils.core import setup
setup(name="kusu-buildkit",
    version="0.2",
    author="Najib Ninaba",
    author_email="najib@osgdc.org",
    url="http://www.osgdc.org/project/kusu",
    platforms=["any"],
#    data_files=[('share/po',['src/po/kusuapps.po'])],
    scripts=['src/bin/buildkit']
     )
