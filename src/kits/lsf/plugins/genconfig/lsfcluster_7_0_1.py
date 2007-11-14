#! /usr/bin/env python

# Copyright 2007 Platform Computing Inc
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

# Generate cluster file, batch resource files

# Change these lines for newer versions of LSF
APPKEY   = "LSF7_0_1_ClusterName"
COMPNAME = "component-LSF-Master-v7_0_1"


from kusu.genconfig import Report

import sys
import string
import glob
import os.path

global COMPONENT_NAME

class thisReport(Report):

	
	def toolHelp(self):
		print self.gettext("genconfig_LSFcluster_Help")


	def validateCluster(self,clustername):
		global APPKEY
		query = ('select agid from appglobals where kname="%s" '
			 'and kvalue="%s"' % (APPKEY, clustername)) 
		try:
			self.db.execute(query)
		except:
			sys.stderr.write(self.gettext("DB_Query_Error\n"))
			sys.exit(-1)

		row = self.db.fetchone()
		if not row:
			return False
		if row[0] != '':
			return True
		return False


	def locateClusFile(self, clustername):
		'''locateClusFile - Locate the /opt/lsf/conf/lsf.cluster.*
		for this cluster within the CFM then read in its contents.'''
		query = ('SELECT ngname FROM nodegroups, appglobals, ng_has_comp, components '
			 'WHERE appglobals.ngid=nodegroups.ngid AND '
			 'nodegroups.ngid=ng_has_comp.ngid AND '
			 'ng_has_comp.cid=components.cid AND '
			 'components.cname="%s" AND appglobals.kvalue="%s"' % (COMPNAME, clustername))
		try:
			self.db.execute(query)
			row = self.db.fetchall()
		except:
			sys.stderr.write(self.gettext("DB_Query_Error\n"))
			sys.exit(-1)
		     
		if not row:
			return

		for row in self.db.fetchall():
			pattern = "/etc/cfm/%s/opt/lsf/conf/lsf.cluster.*" % row[0]
			flist = glob.glob(pattern)
			
			if len(flist) == 0:
				continue
			
			return flist[0]

		return ""


	def getClusterHosts(self, filename):
		'''getClusterHosts - Get a list of all the current hosts
		in the cluster.'''
		if not os.path.exists(filename):
			return []

		fp = file(filename, 'r')
                data = []
		state = 0
                while True:
                        line = fp.readline()
                        if len(line) == 0:
                                break

                        if line[:1] == '#':
				continue

			if line[:5] == 'Begin':
				what = string.split(line)[1]
				if what == 'Host':
					state = 1

			if line[:3] == 'End':
				what = string.split(line)[1]
				if what == 'Host':
					break		

			if state == 0:
				continue

			if line[:8] == 'HOSTNAME':
				continue

			host = string.split(line)[0]
                        data.append(host)
			# print "Found %s\n" % host
			
                fp.close()
                return data


	def preHostEndList(self, filename):
		'''preHostEndList - List the contents of the lsf cluster file up
		to the "End Host".  Note this is to be used in conjunction
		with "postHostEndList"'''
		
		fp = file(filename, 'r')
                while True:
                        line = fp.readline()
			if len(line) == 0:
                                break

			if line[:3] == 'End':
				what = string.split(line)[1]
				if what == 'Host':
					break

			print line,

                return fp

	
	def postHostEndList(self, fp):
		'''postHostEndList - List the contents of the lsf cluster file from the "End Host" section'''

		print "End     Host"
                while True:
                        line = fp.readline()
			if len(line) == 0:
                                break
			print line,
			
                fp.close()


	def newLines(self, currenthosts, clustername):
		# Add Compute nodes first

		global COMPNAME

                # Print out the data
                try:
			# Set the DefaultLsfHostRes in the database to populate
			# The resource string automatically
                        res = self.db.getAppsglobals('DefaultLsfHostRes')
                except:
                        res = ""

		query = ('SELECT nodes.name '
			 'FROM nodes, appglobals, ng_has_comp, components '
			 'WHERE nics.nid = nodes.nid AND appglobals.ngid=nodes.ngid '
			 'AND ng_has_comp.ngid=nodes.ngid AND ng_has_comp.cid=components.cid ' 
			 'AND appglobals.kvalue="%s" AND components.cname="%s" '
			 'ORDER BY nodes.name' % (clustername, COMPNAME))
		
		try:	
    	             self.db.execute(query)
		except:
                     sys.stderr.write(self.gettext("DB_Query_Error\n"))
                     sys.exit(-1)

		nodes = []	
		for name in self.db.fetchall():
			nodes.append(name)
			#print "Got %s, %s, %d \n" % name

		# Add nodes
		for node in nodes:
			if node in currenthosts:
				continue
			print '%s\t!\t!\t1     3.5 ()    ()    (%s)' % (node, res)


        def genLsfClusterFile(self, clustername):
		'''genLsfClusterFile - Generate the cluster file if one does not exist'''

		print """
#-----------------------------------------------------------------------
# T H I S   I S   A    O N E   P E R   C L U S T E R    F I L E
#
# This is a sample cluster definition file.  There is a cluster
# definition file for each cluster.  This file's name should be
# lsf.cluster."cluster-name".
# See lsf.cluster(5) and the "Inside Platform LSF".
#

Begin   ClusterAdmins
Administrators = lsfadmin
End    ClusterAdmins

Begin   Host
HOSTNAME  model    type        server r1m  mem  swp  RESOURCES    #Keywords
#apple    Sparc5S  SUNSOL       1     3.5  1    2   (sparc bsd)   #Example
#peach    DEC3100  DigitalUNIX  1     3.5  1    2   (alpha osf1)
#banana   HP9K778  HPPA         1     3.5  1    2   (hp68k hpux)
#mango    HP735    HPPA         1     3.5  1    2   (hpux cs)
#grape    SGI4D35  SGI5         1     3.5  1    2   (irix)
#lemon    PC200    LINUX        1     3.5  1    2   (linux)
#pear     IBM350   IBMAIX4      1     3.5  1    2   (aix cs)
#plum     PENT_100 NTX86        1     3.5  1    2   (nt)
#berry    DEC3100  !            1     3.5  1    2   (ultrix fs bsd mips dec)
#orange   !        SUNSOL       1     3.5  1    2   (sparc bsd)   #Example
#prune    !        !            1     3.5  1    2   (convex)
"""

                # Now fill in the list of hosts
		global COMPNAME
		query = ('SELECT DISTINCT nodes.name '
			 'FROM nodes, appglobals, ng_has_comp, components, nics '
			 'WHERE nics.nid = nodes.nid AND appglobals.ngid=nodes.ngid '
			 'AND ng_has_comp.ngid=nodes.ngid AND ng_has_comp.cid=components.cid ' 
			 'AND appglobals.kvalue="%s" AND components.cname="%s" '
			 'ORDER BY nodes.name' % (clustername, COMPNAME))
		
		try:	
			self.db.execute(query)
		except:
			sys.stderr.write(self.gettext("DB_Query_Error\n"))
			sys.exit(-1)

		nodes = []	
		for name in self.db.fetchall():
			print "%s\t!       !       1       3.5 ()   ()   ()" % name
			print """End     Host

Begin Parameters
End Parameters

# Begin ResourceMap
# RESOURCENAME  LOCATION
# tmp2          [default]
# nio           [all]
# console       [default]
# End ResourceMap
"""

        def genLsfBatchHosts(self):
		'''genLsfBatchConfig - Create the lsb.hosts file'''
	
		print """
# The section "host" is optional.  If no hosts are listed here, all hosts
# known by Lava will be used by Batch.  Otherwise only the hosts listed will
# be used by Batch.  The value of keyword HOST_NAME may be an official host
# name (see gethostbyname(3)), a host type/model name (see lsf.shared(5)), or
# the reserved word "default".  The type/model name represents each of the
# hosts which are of that particular host type/model.  The reserved
# word "default" represents all other hosts in the Lava cluster.

# MXJ is the maximum number of jobs which can run on the host at one time.
# If MXJ is set as ! the system automatically assigns it to be the
# number of CPUs on the host.

# DISPATCH_WINDOW is the time windows when the host is available to run
# batch jobs.  The default dispatch window is always open.

# Other columns specify scheduling and stopping thresholds for LIM load
# indices.  A "()" or "-" is used to specify the default value in a column
# and cannot be omitted.

# All the host names (except default) in this example are commented out,
# since they are just examples which may not be suitable for some sites.
# Don't use non-default thresholds unless job dispatch needs to be controlled.

Begin Host
HOST_NAME MXJ   r1m     pg    ls    tmp  DISPATCH_WINDOW  # Keywords
#apple        1    1   3.5/4.5  15/   12/15  0      ()             # Example
#orange       ()   2     3.5  15/18   12/    0/  (5:19:00-1:8:30 20:00-8:30)
#grape        ()   ()   3.5/5   18    15     ()     ()             # Example
#banana       ()   ()    ()     ()    ()     ()     ()             # Example
#pomegranate  3    1     ()     ()    ()     ()     ()             # Example
#SPARCIPC     ()   ()  4.0/5.0  18    16     ()     ()             # Example
default    !    ()      ()    ()     ()     ()             # Example
"""
                # Determine which host is the primary LSF master
		# and list it here so it has no job slots
		master = ''

		print "%s 0       ()         ()      ()   ()   ()" % master
                print "End Host"




	def runPlugin(self, pluginargs):
		if not pluginargs:
			print "# ERROR:  No LSF cluster provided!"
			print self.gettext("genconfig_LSFcluster_Help")
			return

		if pluginargs[0] == '':
			print "# ERROR:  No LSF cluster provided!"
			print self.gettext("genconfig_LSFcluster_Help")
			return
		
		if not self.validateCluster(pluginargs[0]):
			print "# ERROR:  Invalid LSF clustername: %s" % pluginargs[0]
			return

		generate = 'cluster'
		if len(pluginargs) > 1:
			# The second argument is the name of the file to generate
			if pluginargs[1] == 'cluster':
				generate = 'cluster'
			if pluginargs[1] == 'batch':
				generate = 'batch'

		if generate == 'cluster':
			file = self.locateClusFile(pluginargs[0])
			chosts = []
			chosts = self.getClusterHosts(file)
			if chosts:
				fp = self.preHostEndList(file)
				self.newLines(chosts, pluginargs[0])
				self.postHostEndList(fp)
			else:
				self.genLsfClusterFile(pluginargs[0])

		else:
			self.genLsfBatchHosts()
