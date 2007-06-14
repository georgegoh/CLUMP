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

def boot_data_files():
    distros = { 'centos': [4,5],
                'rhel': [4,5],
                'fedora': [6]}
            
    datafiles = []
    datafile = ()
    for k,v in distros.items():
        for version in v:
            for arch in ('i386','x86_64'):
                datafile = ('lib/nodeinstaller/%s/%s/%s' % (k,version,arch), ['src/nodeinstaller/README'])
                datafiles.append(datafile)   
    return datafiles

setup(name="kusu-boot",
    version="0.2",
    author="Najib Ninaba",
    author_email="najib@osgdc.org",
    url="http://www.osgdc.org/project/kusu",
    platforms=["any"],
    packages=['boot'],
    package_dir={'boot':'src/lib'},
    data_files=boot_data_files(),                          
    scripts=['src/bin/boot-media-tool']
     )
