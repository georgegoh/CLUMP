#!/usr/bin/env python
#
# $Id: screen.py 524 2008-01-30 06:14:21Z hirwan $
#
# Kusu Screen.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
from kusu.ui.text.screenfactory import BaseScreen

class InstallerScreen(BaseScreen):
    def __init__(self, kiprofile, gridWidth=45):
        BaseScreen.__init__(self, gridWidth=gridWidth)
        self.kiprofile = kiprofile
        self.setDefaults()

    def setDefaults(self):
        pass
