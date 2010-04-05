#!/bin/sh
#
# $Id: rc.kusu.sh 1903 2007-08-07 09:05:41Z ltsai $
#
#   Copyright 2007 Platform Computing Inc.
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

# chkconfig: 2345 98 98
# description: RC scripts for Kusu

### BEGIN INIT INFO
# Provides: kusu
# Required-Start: $local_fs $remote_fs $network cfmclient
# Should-Start: $time postgresql mysql
# Required-Stop:
# Default-Start:  3 5
# Default-Stop:
# description: RC scripts for Kusu
### END INIT INFO

#. /etc/init.d/functions
. /etc/profile.d/kusuenv.sh

KUSURCDIR=/etc/rc.kusu.d
KUSUUSCRIPTS=/etc/rc.kusu.custom.d

prog='kusu'

start() {
    echo $"Starting $prog. This may take a while..."

    # Run any Kit configuration script.
    if [ -d "$KUSURCDIR" ]; then
        /opt/kusu/bin/kusurc $KUSURCDIR
    fi

    # Now run any user provided custom scripts
    if [ -d "$KUSUUSCRIPTS" ]; then
        /opt/kusu/bin/kusurc $KUSUUSCRIPTS
    fi
}


case "$1" in
  start)
  	start
	;;
  *)
	echo $"Usage: $0 {start}"
	exit 1
esac
