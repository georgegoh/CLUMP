#!/usr/bin/env python
#
# $Id$
#
# Kusu Text Installer Network Screen.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.


from kusu.genconfig import Report
import sys

class thisReport(Report):
    def runPlugin(self, pluginargs):
        print "#"
        print "# Dynamically generated by: genconfig  (Do not edit!)"
        print "#"

        # TODO: To improve security, the FQDN should be used for each entry
        # (ie: the DNS zone appended). This will not work unless a DNS service
        # is present on the cluster.
        
        print "localhost"

        query = 'SELECT name FROM nodes'
        try:
            self.db.execute(query)
        except:
            sys.stderr.write(self.gettext("DB_Query_Error\n"))
            sys.exit(-1)
        else:            
            data = self.db.fetchall()

            for row in data:
                print row[0]
