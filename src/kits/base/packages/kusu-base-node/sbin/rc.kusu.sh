#!/bin/sh
#
# $Id$
#
#   Copyright 2007 Platform Computing Corporation Inc.
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

# This script is responsible for running any post installation scripts
# that the Kusu installer has provided.
# It will also deal with running any custom user scripts.
# This scripts will also be used when new packages are installed.

# chkconfig: 2345 99 99
# description: RC scripts for Kusu

. /etc/init.d/functions

KUSURCDIR=/etc/rc.kusu.d
KUSUUSCRIPTS=/etc/rc.kusu.custom.d

prog='kusu'

start() {
	echo -n $"Starting $prog: "	
    
    # Run any Kit configuration script.
    for i in $KUSURCDIR/S* ; do
        $i start
        #rm -rf $i
    done

    # Now run any user provided custom scripts
    for i in $KUSUUSCRIPTS/* ; do
        if [ -x $i ] ; then
            $i start
            #rm -rf $i
        fi
    done
}


case "$1" in
  start)
  	start
	;;
  *)
	echo $"Usage: $0 {start}"
	exit 1
esac
