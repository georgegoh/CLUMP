#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from kusu.core import database as db
from path import path
import os
import re
import sys
import pwd

from kusu.genconfig import Report

class thisReport(Report):
    def runPlugin(self, pluginargs):
        self.dbs = db.DB('mysql', 'kusudb', 'root')
        piname = self.dbs.AppGlobals.selectfirst_by(kname='PrimaryInstaller').kvalue

        nodes = self.dbs.Nodes.select()
        
        for node in nodes:
            if node.name == piname:
                continue
            for nic in node.nics:
                if nic.network.type == 'provision':
                    print "%s%s" % (node.name, nic.network.suffix)
