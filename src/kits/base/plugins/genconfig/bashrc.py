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
        pass

    def runPlugin(self, pluginargs):
        print "# .bashrc"
        print "# Dynamically generated by: genconfig  (Do not edit!)"
        print "#"

        print "# Source global definitions"
        print "if [ -f /etc/bashrc ]; then"
        print "    . /etc/bashrc"
        print "fi"
        print ""
        print "# User specific aliases and functions"
        print "if [ ! -f ~/.ssh/id_rsa ]; then"
        print "    echo 'No public/private RSA keypair found.'"
        print "    ssh-keygen -t rsa -b 2048 -f ~/.ssh/id_rsa -N \"\""
        print "    cat ~/.ssh/id_rsa.pub > ~/.ssh/authorized_keys"
        print "    chmod 644 ~/.ssh/authorized_keys"
        print "fi"
        print ""
        print "# Load saved modules"
        print "if [ -f  ~/.modulesnapshot ]; then"
        print "    for i in `cat ~/.modulesnapshot`; do"
        print "        module load $i"
        print "    done"
        print "fi"
