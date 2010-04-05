#!/usr/bin/env python
# $Id$
#
# Copyright 2009 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

from kusu.core.app import KusuApp
from kusu.util.tools import getArch
from kusu.util.errors import BuildkitArchError
from kusu.buildkit.tool01 import BuildKit as BuildKit01
from kusu.buildkit.tool02 import BuildKit as BuildKit02
# i18n - grab from KusuApp.
_ = KusuApp()._


def newKitv01(dirname, options):
    """ Make a skeleton for a kit conforming to API v0.1. """
    # get the current arch
    arch = getArch()

    if options.arch != arch and options.arch != 'noarch':
       raise BuildkitArchError 

    # instantiate version 0.1 of Buildkit api.
    bkinst = BuildKit01()

    msg = _('Creating %(kitname)s directory..' % {'kitname':dirname.basename()})
    print msg
    # get the arch
    if options.arch != 'noarch':
        msg = _('Creating kit for %(arch)s architecture..' % {'arch':options.arch})
        bkinst.newKitSrc(dirname)
    else:
        msg = _('Creating kit for all architectures..' % {'arch':options.arch})
        bkinst.newKitSrc(dirname, options.arch)
    print msg

    msg = _('%(kitname)s directory created.' % {'kitname':dirname.basename()})
    print msg


def newKitv02(dirname, options):
    """ Make a skeleton for a kit conforming to API v0.2. """
    # instantiate version 0.2 of Buildkit api.
    bkinst = BuildKit02()

    msg = _('Creating %(kitname)s directory..' % {'kitname':dirname.basename()})
    print msg
    # get the arch
    if options.arch != 'noarch':
        msg = _('Creating kit for %(arch)s architecture..' % {'arch':options.arch})
        bkinst.newKitSrc(dirname)
    else:
        msg = _('Creating kit for all architectures..' % {'arch':options.arch})
        bkinst.newKitSrc(dirname, options.arch)
    print msg

    msg = _('%(kitname)s directory created.' % {'kitname':dirname.basename()})
    print msg


newKitFactory = {'0.1': newKitv01,
    '0.2': newKitv02,
    'default': newKitv02} # default will always be the most current.

