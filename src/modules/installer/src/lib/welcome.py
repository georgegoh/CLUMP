#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer Welcome Screen.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import socket
import snack
from gettext import gettext as _
from kusu.ui.text import screenfactory, kusuwidgets
from kusu.boot.tool import getPartitionMap, makeDev
from kusu.util.errors import *
from screen import InstallerScreen

class WelcomeScreen(InstallerScreen):
    """This is the welcome screen."""
    name = _('Welcome')
    context = 'Welcome'
    msg = _('Welcome to the Kusu installation program. In the ' + \
          'following screens, you will be presented with questions ' + \
          'that will help you configure your new Kusu cluster.\n\n' + \
          'If you do not wish to continue at any point, please press ' + \
          'the F12 key. Otherwise, press Next to continue.')
    buttons = []

    def drawImpl(self):
        self.screenGrid = snack.Grid(1, 1)
        self.screenGrid.setField(snack.TextboxReflowed(text=self.msg,
                                                       width=self.gridWidth),
                                 col=0, row=0)
        self.prechecks()

    def prechecks(self):
        # get the map of the available partitions
        devmap = getPartitionMap()
        devices = devmap.keys()

        # set up a pattern of the devices we are interested in
        disks = []
        import re
        pat = re.compile('[hs]d\d*')
        for dev in devices:
            m = pat.match(dev)
            if m:
                disks.append(dev)

        if not disks:
            raise NoDisksFoundError, 'This system cannot be set up because ' + \
                      'no disks could be found. Please check your system ' + \
                      'hardware to make sure that you have installed your ' + \
                      'disks correctly.'
