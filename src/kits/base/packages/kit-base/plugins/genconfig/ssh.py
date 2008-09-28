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
import sys

class thisReport(Report):
    
    def toolHelp(self):
        print self.gettext("genconfig_Ssh_Help")

    def runPlugin(self, pluginargs):
        print "# "
        print "# Dynamically generated by: genconfig  (Do not edit!)"
        print "#"

       # Get the DNS Zone served by the Installer
        dnszone = self.db.getAppglobals('DNSZone')
        if not dnszone:
            sys.stderr.write(self.gettext("genconfig_cannot_determine_DNS_zone\n"))
            sys.exit(0)

        query = ('select nics.ip,nodes.name,networks.suffix,nics.boot '
                 'from nics,nodes,networks where nics.nid = nodes.nid '
                 'and nics.netid = networks.netid and '
                 'networks.usingdhcp = 0 order by nics.ip')

        try:
            self.db.execute(query)
        except:
            sys.stderr.write(self.gettext("DB_Query_Error\n"))
            sys.exit(-1)

        else:
            data = self.db.fetchall()
            for row in data:
                ip, name, suffix, boot = row

               
                print 'Host ' + ip
                print '\tStrictHostKeyChecking no'

                if suffix:
                    print 'Host %s%s.%s' % (name, suffix ,dnszone)
                    print '\tStrictHostKeyChecking no'
               
                    print 'Host %s%s' % (name, suffix)
                    print '\tStrictHostKeyChecking no'
               

                print 'Host ' + '%s.%s' % (name, dnszone) 
                print '\tStrictHostKeyChecking no'
                
                print 'Host ' + name
                print '\tStrictHostKeyChecking no'

                print

            print 'Host *'
            print '\t# ssh_config defaults'
            print '\tGSSAPIAuthentication yes'
            print '\tForwardX11Trusted yes'
            print '\tSendEnv LANG LC_CTYPE LC_NUMERIC LC_TIME LC_COLLATE LC_MONETARY LC_MESSAGES'
            print '\tSendEnv LC_PAPER LC_NAME LC_ADDRESS LC_TELEPHONE LC_MEASUREMENT'
            print '\tSendEnv LC_IDENTIFICATION LC_ALL'
            print '\t# kusu defaults'
            print '\tNoHostAuthenticationForLocalhost yes'