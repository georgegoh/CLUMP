#!/bin/sh
#
#   Copyright 2009 Platform Computing Inc
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

# Do not run this script if yum repo has not been set up yet,
# i.e. this is the first time the compute is booting up.
if [ ! -f /etc/yum.repos.d/kusu-compute.repo ]; then
    exit 0
fi

# The purpose of this script is to determine if a change is needed 
# in the BMC or network setup, and to apply it.  This is triggered
# by the existence of a newer flag file

FLAGFILE=/opt/kusu/etc/cfmchanges.lst
UPDATENIC=/opt/kusu/sbin/updatenic
LOGFILE=/var/log/kusu/updatenic.log

# Test to see if a new Flag file has been written
if [ ! -e $FLAGFILE ]; then
    exit 0
fi
CNT=`grep -c 'New_file /etc/.updatenics' $FLAGFILE`

if [ x$CNT != x1 ]; then
    exit 0
fi

# Update the NIC configuration 
if [ -x $UPDATENIC ]; then 
    /bin/mkdir -p `dirname $LOGFILE`
    $UPDATENIC >> $LOGFILE 2>&1
fi
