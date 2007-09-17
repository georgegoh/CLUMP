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
        query = ("SELECT nodes.name, networks.suffix " +
                 "FROM nodes, nics, networks WHERE nics.nid = nodes.nid " +
                 "AND nics.netid = networks.netid " +
                 "AND nodes.name != (SELECT kvalue FROM appglobals WHERE " +
                 "                  kname='PrimaryInstaller') " +
                 "AND networks.type = 'provision'")

        try:
            self.db.execute(query)
        except:
            sys.stderr.write(self.gettext("DB_Query_Error\n"))
            sys.exit(-1)
        else:
            data = self.db.fetchall()
            for row in data:
                print "%s%s" % row

        #self.dbs = db.DB('mysql', 'kusudb', 'root')
        #pi = self.dbs.AppGlobals.selectfirst_by(kname='PrimaryInstaller').kvalue

        #stmt = db.sa.select([self.dbs.nodes.c.name, self.dbs.networks.c.suffix])
        #stmt.append_from(
        #    self.dbs.nodes.join(self.dbs.nics,
        #                    self.dbs.nodes.c.nid == self.dbs.nics.c.nid).join(
        #                    self.dbs.networks,
        #                    self.dbs.nics.c.netid == self.dbs.networks.c.netid))
        #stmt.append_whereclause(self.dbs.nodes.c.name != pi)
        #stmt.append_whereclause(self.dbs.networks.c.type == 'provision')

        #for row in stmt.execute().fetchall():
        #    print "%s%s" % (row.name, row.suffix)
