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
    packages = ['buildkit'],
    package_dir = {'buildkit' : 'src/lib'},
    scripts=['src/bin/buildkit'],
    data_files=[('etc/buildkit-templates', ['src/etc/templates/rpmmacros.tmpl']),
                ('etc/buildkit-templates', ['src/etc/templates/package.spec.tmpl']),
                ('etc/buildkit-templates', ['src/etc/templates/component.spec.tmpl']),
                ('etc/buildkit-templates', ['src/etc/templates/build.kit.tmpl']),
                ('etc/buildkit-templates', ['src/etc/templates/kit.spec.tmpl']),
                ('etc/buildkit-templates', ['src/etc/templates/00-post-script.sh.tmpl']),
                ('etc/buildkit-templates', ['src/etc/templates/00-postun-script.sh.tmpl'])]
     )
