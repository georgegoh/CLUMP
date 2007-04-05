#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer Welcome Screen.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
__version__ = "$Revision$"

import socket
import logging
import snack
from gettext import gettext as _
from ui.text import screenfactory, kusuwidgets

class WelcomeScreen(screenfactory.BaseScreen):
    """This is the welcome screen."""
    name = _('Welcome')
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


