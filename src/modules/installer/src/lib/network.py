#!/usr/bin/env python
#
# $Id$
#
# Kusu Text Installer Network Screen.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
__version__ = "$Revision: 237 $"

import socket
import logging
import snack
from gettext import gettext as _
from kusu.ui.text import screenfactory, kusuwidgets
from kusu.ui.text.kusuwidgets import LEFT,CENTER,RIGHT
from kusu.hardware import net

class NetworkScreen(screenfactory.BaseScreen):
    """This is the network screen."""
    name = _('Network')
    context = 'Network'
    msg = _('Please configure your network')
    buttons = []

    def drawImpl(self):
        self.screenGrid = snack.Grid(1, 2)
        
        instruction = snack.Label(self.msg)
        self.screenGrid.setField(instruction, col=0, row=0)

        self.listbox = snack.Listbox(8, scroll=1, returnExit=1)
        for intf, v in net.getInterfaces().items():
            if v['isPhysical']:
                vendor = v['vendor']
                device = v['device']
                self.listbox.append('%s - %s %s' % (intf, vendor, device), intf)

        self.screenGrid.setField(self.listbox, col=0, row=1,
                                 padding=(0,1,0,-1))



