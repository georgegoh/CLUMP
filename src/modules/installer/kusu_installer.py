#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer Framework.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
"""This module is the backbone of the Text Installer Framework. It performs the 
   presentation, navigation,and data validation tasks."""
__version__ = "$Revision$"

import sys
import logging
import snack
import gettext
from ui.text import navigator

try:
    t = gettext.translation('kusu', 'locale')
except IOError:
    t = gettext.translation('kusu', '/usr/share/locale')
t.install()

class KusuInstaller(navigator.Navigator):
    """Framework for displaying installation steps and screens.

    The KusuInstaller class takes a screenFactory object, and displays the
    screens in the order described in the screenFactory.

    """
    def __init__(self, screenFactory, screenTitle, showTrail=True):
        import commands
        if commands.getoutput('whoami') != 'root':
            print 'You must be root to run the installer.'
            import sys
            sys.exit(1)

        navigator.Navigator.__init__(self, screenFactory, screenTitle, showTrail)
