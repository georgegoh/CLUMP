# Copyright (C) 2007 Platform Computing Inc
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
import os
from kusu.ngedit.ngedit import NGEPluginBase

class NGPlugin(NGEPluginBase):
    name= 'Ntop NGEdit Plugin'
    msg = 'This is a non-interactive component plugin'

    def __init__(self, database, kusuApp=None, gridWidth=45):
        NGEPluginBase.__init__(self, database, kusuApp=kusuApp, gridWidth=gridWidth)
        self.setHelpLine("Ntop Kit")

    def add(self):
        assert(self.ngid)
	query = "select ngname from nodegroups where ngid = %s" % self.ngid
	try:
	    self.database.execute(query)
	    ngname = self.database.fetchone()
	except:
            return
 
        self.generateNtopConfig(ngname)
  
    def remove(self):
        assert(self.ngid)
        query = "select ngname from nodegroups where ngid = %s" % self.ngid
        try:
            self.database.execute(query)
            ngname = self.database.fetchone()
        except:
            return
          
            os.unlink("/etc/cfm/%s/etc/ntop.conf" % ngname,'w')

    def generateNtopConfig(self, ngname):
        interfaces = ""
        query = "SELECT networks.device FROM networks,ng_has_net WHERE ng_has_net.netid=networks.netid AND ng_has_net.ngid = %s" % self.ngid
        self.database.execute(query)
        result = self.database.fetchall()
        for device in result:
            interfaces += device[0]
            if device[0]:
               interfaces += ","

        # Strip off end comma.
        if interfaces[len(interfaces)-1] == ',':
           interfaces = interfaces[:-1]
	   
        ntopConfig = """
###  You should copy this file to it's normal location, /etc/etc/ntop.conf
###  and edit it to fit your needs.
###
###       ntop is easily launched with options by referencing this file from
###       a command line like this:
###
###       ntop @/etc/ntop.conf
###
###  Remember, options may also be listed directly on the command line, both
###  before and  after the @/etc/ntop.conf.
###
###  For switches that provide values, e.g. -i, the last one matters.
###  For switches just say 'do things', e..g -M, if it's ANYWHERE in the
###  commands, it will be set.  There's no unset option.
###
###  You can use this to your advantage, for example:
###       ntop @/etc/ntop.conf -i none
###  Overrides the -i in the file.

### Sets the user that ntop runs as.
###  NOTE: This should not be root unless you really understand the security risks.
--user ntop

### Sets the directory that ntop runs from.
--db-file-path /var/ntop

### Interface(s) that ntop will capture on (default: eth0)
--interface %s

### Configures ntop not to trust MAC addrs.  This is used when port mirroring or SPAN
#--no-mac

### Logging messages to syslog (instead of the console):
###  NOTE: To log to a specific facility, use --use-syslog=local3
###  NOTE: The = is REQUIRED and no spaces are permitted.
--use-syslog

### Tells ntop to track only local hosts as specified by the --local-subnets option
#--track-local-hosts

### Sets the port that the HTTP webserver listens on
###  NOTE: --http-server 3000 is the default
#--http-server 3000

### Sets the port that the optional HTTPS webserver listens on
--https-server 3001

### Sets the networks that ntop should consider as local.
###  NOTE: Uses dotted decimal and CIDR notation. Example: 192.168.0.0/24
###        The addresses of the interfaces are always local and don't need to be specified.
#--local-subnets xx.xx.xx.xx/yy

### Sets the domain.  ntop should be able to determine this automatically.
#--domain mydomain.com

### Sets program to run as a daemon
###  NOTE: For more than casual use, you probably want this.
--daemon
""" % (interfaces)
        if self.ngid == 1:
           fptr = open("/etc/ntop.conf", 'w')
        else:
           fptr = open("/etc/cfm/%s/etc/ntop.conf" % ngname,'w')

        fptr.writelines(ntopConfig)
        fptr.close()
