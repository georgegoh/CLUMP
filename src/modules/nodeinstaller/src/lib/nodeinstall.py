#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE for details.

import sys
import os
from kusu.autoinstall.scriptfactory import KickstartFactory
from kusu.autoinstall.autoinstall import Script
from kusu.autoinstall.installprofile import Kickstart


class NodeInstaller(object):
    """ The model for nodeinstaller. This class provides access to
        the data and methods to perform the operations for automatic
        node provisioning. 
    """

    def __init__(self, arg):
        super(NodeInstaller, self).__init__()
        self.arg = arg
        



