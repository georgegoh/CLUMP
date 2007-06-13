#!/usr/bin/env python
#
# $Id$
#
# Kusu util generator
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
__version__ = "$Rev:$"

from distutils.core import setup
setup(name="kusu-util",
    version="0.2",
    author="Najib Ninaba",
    author_email="najib@osgdc.org",
    url="http://www.osgdc.org/project/kusu",
    platforms=["any"],
    packages=['util', 'util.distro'],
    package_dir={'util':'src/lib',
                 'util.distro': 'src/lib/distro'},
    data_files=[('etc', ['src/etc/distro.conf']),
                ('share/doc/samples', ['src/doc/samples/verify-fc6-repo'])] 
     )
