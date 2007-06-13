#!/usr/bin/env python
#
# $Id$
#
# Kusu boot generator
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
__version__ = "$Revision$"

from distutils.core import setup
setup(name="kusu-boot",
    version="0.2",
    author="Najib Ninaba",
    author_email="najib@osgdc.org",
    url="http://www.osgdc.org/project/kusu",
    platforms=["any"],
    packages=['boot'],
    package_dir={'boot':'src/lib'},
    data_files=[('share/po',['src/po/kusuapps.po']),
                ('share/doc',['src/doc/LICENSE'])],
    scripts=['src/bin/boot-media-tool']
     )
