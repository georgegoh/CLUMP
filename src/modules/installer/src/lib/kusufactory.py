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
from collection import *
from kusu.ui.text.screenfactory import BaseScreen, ScreenFactory
from welcome import WelcomeScreen
from language import LanguageSelectionScreen
from keyboard import KeyboardSelectionScreen
from clusterinfo import ClusterInfoScreen
from rootpasswd import RootPasswordScreen
from partition import PartitionScreen
from gatewaydns import GatewayDNSSetupScreen
from kits import KitsScreen
from tzselect import TZSelectionScreen
from confirm import ConfirmScreen
from network import NetworkScreen

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
    collection = SQLiteCollection()
    ScreenFactory.screens = [WelcomeScreen(collection, kusuApp=runtimeDict),
                             LanguageSelectionScreen(collection, kusuApp=runtimeDict),
                             KeyboardSelectionScreen(collection, kusuApp=runtimeDict),
                             ClusterInfoScreen(collection, kusuApp=runtimeDict),
                             RootPasswordScreen(collection, kusuApp=runtimeDict),
                             PartitionScreen(collection, kusuApp=runtimeDict),
                             KitsScreen(collection, kusuApp=runtimeDict),
                             NetworkScreen(collection, kusuApp=runtimeDict),
#                             GatewayDNSSetupScreen(collection, kusuApp=runtimeDict),
                             TZSelectionScreen(collection, kusuApp=runtimeDict),
                             ConfirmScreen(collection, kusuApp=runtimeDict)
                            ]

