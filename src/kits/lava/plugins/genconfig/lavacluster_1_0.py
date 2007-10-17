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

from kusu.genconfig import Report

import os
import sys
import string

global COMPONENT_NAME
COMPONENT_NAME = 'component-lava-compute-v1_0'

class thisReport(Report):

	def haveLsf(self):
		path = "/opt/lava/conf"
		if os.path.exists(path):
			return 1
		return 0

	def getClusterHosts(self):
		filename = "/opt/lava/conf/lsf.cluster.lava"
		if os.path.exists(filename) == 0:
			return False
		
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


	def preHostEndList(self):
		# List the contents of the lsf cluster file up to the "End Host"
		# Note this is to be used in conjunction with "postHostEndList"
		
		filename = "/opt/lava/conf/lsf.cluster.lava" 
		if os.path.exists(filename) == 0:
			return
		
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
		# List the contents of the lsf cluster file from the "End Host" section
		print "End     Host"
                while True:
                        line = fp.readline()
			if len(line) == 0:
                                break
			print line,
			
                fp.close()


	def newLines(self, currenthosts):
		# Add Compute nodes first

		global COMPONENT_NAME

                # Print out the data
                try:
                        res = self.db.getAppsglobals('DefaultLavaHostResource')
                except:
                        res = ""

		query = ('select distinct nodes.name from nodes, nodegroups, ng_has_comp, components where '
			 'nodes.ngid = ng_has_comp.ngid and ng_has_comp.cid = components.cid and '
			 'components.cname = "%s"' % COMPONENT_NAME)

		try:	
    	             self.db.execute(query)
		except:
                     sys.stderr.write(self.gettext("DB_Query_Error\n"))
                     sys.exit(-1)

		nodes = []	
		for name in self.db.fetchall():
			nodes.append(name)
			#print "Got %s\n" % name

		# Add nodes
 
		for node in nodes:
		    if node[0] in currenthosts:
		       continue
                    else:
		       print '%s\t!\t!\t1     3.5 ()    ()    (%s)' % (node[0], res)

        def generateLavaClusterHosts(self):
            print """
#-----------------------------------------------------------------------
# T H I S   I S   A    O N E   P E R   C L U S T E R    F I L E
#
# This is a sample cluster definition file.  There is a cluster
# definition file for each cluster.  This file's name should be
# lsf.cluster."cluster-name".
# See lsf.cluster(5) and the "Inside Platform Lava".
#

Begin   ClusterAdmins
Administrators = lavaadmin
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
%s !       !       1       3.5 ()   ()   ()
End     Host

Begin Parameters
End Parameters

# Begin ResourceMap
# RESOURCENAME  LOCATION
# tmp2          [default]
# nio           [all]
# console       [default]
# End ResourceMap
""" % self.db.getAppglobals('PrimaryInstaller')

        def generateLavaBatchConfig(self):
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
%s 0       ()         ()      ()   ()   ()
End Host
""" % self.db.getAppglobals('PrimaryInstaller')

	def runPlugin(self, pluginargs):
		if self.haveLsf() != 1:
			print "# Error:  Not an Lava machine OR Lava not ready"
			return

		chosts = []

                if not pluginargs: # Default generate cluster file
		   chosts = self.getClusterHosts()
                   if chosts:
		      fp = self.preHostEndList()
		      self.newLines(chosts)
		      self.postHostEndList(fp)
                   else:
                      self.generateLavaClusterHosts()
        
                if len(pluginargs) > 0:
                   if pluginargs[0] == 'cluster':
                      chosts = self.getClusterHosts()
                      if chosts:
                         fp = self.preHostEndList()
                         self.newLines(chosts)
                         self.postHostEndList(fp)
                      else:
                         self.generateLavaClusterHosts()

                   if pluginargs[0] == 'batch':
                      self.generateLavaBatchConfig()
 
