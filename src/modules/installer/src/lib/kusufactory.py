#!/usr/bin/env python
# $Id: kusufactory.py 248 2007-04-10 09:35:57Z ggoh $
#
# Kusu Text Installer Screen Factory.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
"""This module sets up the sequence of screens to be shown in the framework."""
__version__ = "$Revision: 248 $"

import snack
from currypot import *
from kusu.ui.text.screenfactory import BaseScreen, ScreenFactory
from welcome import WelcomeScreen
from language import LanguageSelectionScreen
from keyboard import KeyboardSelectionScreen
from clusterinfo import ClusterInfoScreen
from rootpasswd import RootPasswordScreen
from partition import PartitionScreen
from gatewaydns import GatewayDNSSetupScreen
from tzselect import TZSelectionScreen
from confirm import ConfirmScreen

class ScreenImpl(BaseScreen):
    """This class is a template for other Screen classes."""
    name = 'Welcome'
    msg = 'Welcome to the Kusu installation program. In the ' + \
          'following screens, you will be presented with questions ' + \
          'that will help you configure your new Kusu cluster.\n\n' + \
          'If you do not wish to continue, please select the Quit ' + \
          'option. Otherwise select Next to continue.' 
    buttons = ['Action 1']

    def draw(self):
        self.screenGrid = snack.Grid(1, 1)
        self.screenGrid.setField(snack.TextboxReflowed(text=self.msg,
                                                 width=self.gridWidth),
                                 col=0, row=0)

runtimeDict = {}

class ScreenFactoryImpl(ScreenFactory):
    """The ScreenFactory is defined by the programmer, and passed on to the 
       KusuInstaller class.

    """
    name = 'installer'
    currypot = SQLiteCurrypot()
    ScreenFactory.screens = [WelcomeScreen(currypot, kusuApp=runtimeDict),
                             LanguageSelectionScreen(currypot, kusuApp=runtimeDict),
                             KeyboardSelectionScreen(currypot, kusuApp=runtimeDict),
                             ClusterInfoScreen(currypot, kusuApp=runtimeDict),
                             RootPasswordScreen(currypot, kusuApp=runtimeDict),
                             PartitionScreen(currypot, kusuApp=runtimeDict),
                             GatewayDNSSetupScreen(currypot, kusuApp=runtimeDict),
                             TZSelectionScreen(currypot, kusuApp=runtimeDict),
                             ConfirmScreen(currypot, kusuApp=runtimeDict)
                            ]

