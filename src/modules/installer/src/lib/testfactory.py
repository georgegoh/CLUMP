#!/usr/bin/env python
#
# $Id$
#
# Kusu Text Installer Screen Factory.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.

"""This module sets up the sequence of screens to be shown in the framework."""

import snack
from path import path
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
from hostname import FQHNScreen
from kusu.ui.text.kusuwidgets import *

class ScreenImpl(BaseScreen):
    """This class is a template for other Screen classes."""
    name = 'Welcome'
    context = 'welcome'
    msg = 'This is sample text that should stretch reasonably long ' + \
          'enough to be realistic in simulating real text in real ' + \
          'screens. In its place could be descriptive text explaining ' + \
          'the current step for the user and what to do next.' 
    buttons = ['Action 1', 'Action 2']

#    def __init__(self, database, kusuApp, number):
#        BaseScreen(self, database, kusuApp)
#        self.number = number

#    def setCallbacks(self):
#        self.buttonsDict['Action 1'].setCallback_(self.action1)
#        self.buttonsDict['Action 2'].setCallback_(self.action2)

    def drawImpl(self):
        self.screenGrid = snack.Grid(1, 3)

        self.screenGrid.setField(snack.TextboxReflowed(text=self.msg,
                                                 width=self.gridWidth),
                                 col=0, row=0)

        self.labelledEntry = LabelledEntry('This is a labelled entry widget',
                                           30, 'This is default text')
        self.screenGrid.setField(self.labelledEntry, col=0, row=1, padding=(0,1,0,1))

        self.colListBox = ColumnListbox(3, [5,8,4,7],
                                        ['Col 1', 'Col 2', 'Col 3', 'Col 4'],
                                        [LEFT, CENTER, CENTER, RIGHT])
        self.colListBox.addRow(['abc', '123', 'stu', '9012'], 'Associated String 1')
        self.colListBox.addRow(['def', '456', 'vwx', '3456'], 'Associated String 2')
        self.colListBox.addRow(['ghi', '789', 'yza', '7890'], 'Associated String 3')
        self.colListBox.addRow(['jkl', '012', 'bcd', '1234'], 'Associated String 4')
        self.colListBox.addRow(['mno', '345', 'efg', '5678'], 'Associated String 5')
        self.colListBox.addRow(['pqr', '678', 'hij', '9012'], 'Associated String 6')
        self.screenGrid.setField(self.colListBox, col=0, row=2, padding=(0,0,0,0))

    def action1(self):
        self.kusuApp[str(self.number) + 'action1'] = 'Clicked'
        return -1

    def action2(self):
        self.kusuApp[str(self.number) + 'action2'] = 'Clicked'

    def formAction(self):
        #self.kusuApp[str(self.number)] = self.colListBox.current()
        pass

runtimeDict = {}

class ScreenFactoryTest(ScreenFactory):
    """The ScreenFactory is defined by the programmer, and passed on to the 
       KusuInstaller class.
    """

    name = 'installer'

    try:
        kusutmp = os.environ['KUSU_TMP']
    except KeyError:
        kusutmp = '/tmp/kusu'
    if kusutmp == '':
        kusutmp = '/tmp/kusu'

    kusudb = path(kusutmp) / 'kusu.db'
    kusudb_parent = path(kusutmp).abspath()
    if not kusudb_parent.exists():
        kusudb_parent.makedirs()

    collection = SQLiteCollection(kusudb)
    ScreenFactory.screens = [ScreenImpl(collection, kusuApp=runtimeDict, gridWidth=60),#, number=1),
                             ScreenImpl(collection, kusuApp=runtimeDict, gridWidth=60),#, number=2),
                             ScreenImpl(collection, kusuApp=runtimeDict, gridWidth=60),#, number=3)
                             ScreenImpl(collection, kusuApp=runtimeDict, gridWidth=60),#number=4),
                             ScreenImpl(collection, kusuApp=runtimeDict, gridWidth=60),#number=5),
                             ScreenImpl(collection, kusuApp=runtimeDict, gridWidth=60),#number=6),
                             ScreenImpl(collection, kusuApp=runtimeDict, gridWidth=60),#number=7),
                             ScreenImpl(collection, kusuApp=runtimeDict, gridWidth=60),#number=8),
                             ScreenImpl(collection, kusuApp=runtimeDict, gridWidth=60),#number=9),
                             ScreenImpl(collection, kusuApp=runtimeDict, gridWidth=60),#number=10),
                             ScreenImpl(collection, kusuApp=runtimeDict, gridWidth=60),#number=11),
                             ScreenImpl(collection, kusuApp=runtimeDict, gridWidth=60),#number=12),
                             ScreenImpl(collection, kusuApp=runtimeDict, gridWidth=60),#number=13),
                             ScreenImpl(collection, kusuApp=runtimeDict, gridWidth=60),#number=14),
                             ScreenImpl(collection, kusuApp=runtimeDict, gridWidth=60)#number=15)
                            ]
