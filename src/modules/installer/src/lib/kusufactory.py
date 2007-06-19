#!/usr/bin/env python
#
# $Id$
#
# Kusu Text Installer Screen Factory.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.

"""This module sets up the sequence of screens to be shown in the framework."""

import snack
from path import path
from collection import *
from kusu.util.profile import Profile
from kusu.ui.text.screenfactory import ScreenFactory
from welcome import WelcomeScreen
from language import LanguageSelectionScreen
from keyboard import KeyboardSelectionScreen
#from clusterinfo import ClusterInfoScreen
from rootpasswd import RootPasswordScreen
from partition import PartitionScreen
from gatewaydns import GatewayDNSSetupScreen
from kits import KitsScreen
from tzselect import TZSelectionScreen
from confirm import ConfirmScreen
from network import NetworkScreen
from hostname import FQHNScreen
from kusu.core import database as db


# we start with a blank kusu installer profile
kiprofile = Profile()
kiprofile['Kusu Install MntPt'] = '/mnt/kusu'

class ScreenFactoryImpl(ScreenFactory):
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

    # Create db
    dbs = db.DB('sqlite', db=kusudb)
    dbs.bootstrap()
    kiprofile.addDatabase(dbs)

    ScreenFactory.screens = \
        [WelcomeScreen(kiprofile=kiprofile),
         LanguageSelectionScreen(kiprofile=kiprofile),
         KeyboardSelectionScreen(kiprofile=kiprofile),
         #ClusterInfoScreen(kiprofile=kiprofile),
         NetworkScreen(kiprofile=kiprofile),
         GatewayDNSSetupScreen(kiprofile=kiprofile),
         FQHNScreen(kiprofile=kiprofile),
         TZSelectionScreen(kiprofile=kiprofile),
         RootPasswordScreen(kiprofile=kiprofile),
         PartitionScreen(kiprofile=kiprofile),
         KitsScreen(kiprofile=kiprofile),
         ConfirmScreen(kiprofile=kiprofile)
        ]
