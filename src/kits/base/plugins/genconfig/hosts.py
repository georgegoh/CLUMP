# $Id$
#
#   Copyright 2007 Platform Computing Inc
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.
# 	
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
#
#
#


from kusu.genconfig import Report


class thisReport(Report):
    
    def toolHelp(self):
        print self.gettext("genconfig_Hosts_Help")


    def runPlugin(self, pluginargs):
        print "# "
        print "# Dynamically generated by: genconfig  (Do not edit!)"
        print "#"
        print "127.0.0.1\tlocalhost.localdomain\tlocalhost"

        # Get the DNS Zone served by the Installer
        dnszone = self.db.getAppglobals('DNSZone')
        if not dnszone:
            sys.stderr.write(_("genconfig_cannot_determine_DNS_zone\n"))
            sys.exit(0)

        query = ('select nics.ip,nodes.name,networks.suffix,nics.boot '
                 'from nics,nodes,networks where nics.nid = nodes.nid '
                 'and nics.netid = networks.netid order by nics.ip')

        try:
            self.db.execute(query)
        except:
            sys.stderr.write(self.gettext("DB_Query_Error\n"))
            sys.exit(-1)
                    
        else:            
            data = self.db.fetchall()
            for row in data:
                ip, name, suffix, boot = row
                if suffix and suffix != '':
                    if boot == 1:
                        print "%s\t%s%s.%s \t%s.%s \t%s%s \t%s" % (ip, name, suffix ,dnszone, name, dnszone, name, suffix, name)
                    else:
                        print "%s\t%s%s.%s \t%s.%s \t%s%s" % (ip, name, suffix ,dnszone, name, dnszone, name, suffix )
                else:
                    print "%s\t%s.%s \t%s" % (ip, name, dnszone, name)
        
