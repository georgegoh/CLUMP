#!/bin/sh

# $Id$
#
#  Copyright (C) 2007 Platform Computing
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

# From initrd.defaults
NEW_ROOT="/newroot"
NEW_INIT="/sbin/init"
CONSOLE="/dev/console"

PATH=/sbin:/bin:/usr/sbin:/usr/bin
export PATH


mount_sysfs() {
    mount -t sysfs /sys /sys
    ret=$?
    if [ "$ret" -ne '0' ]
    then
        # sysfs mount failed .. udev wont work
	echo "ERROR:  Failed to mount sysfs"
    fi
}

mount_proc() {
    mount -t proc proc /proc
    ret=$?
    if [ "$ret" -ne '0' ]
    then
        # proc mount failed.  Disk detection will not work
	echo "ERROR:  Failed to mount /proc"
    fi
}

quiet_kmsg() {
    echo '0' > /proc/sys/kernel/printk
}

verbose_kmsg() {
    echo '6' > /proc/sys/kernel/printk
}

# Clean input/output
exec >${CONSOLE} <${CONSOLE} 2>&1

mount_proc
mount_sysfs
verbose_kmsg

/bin/mount -o remount,rw /
/bin/mount -a
/bin/hostname -F /etc/hostname
/sbin/ifconfig lo 127.0.0.1 up
/sbin/route add -net 127.0.0.0 netmask 255.0.0.0 lo

# now run any rc scripts
/etc/init.d/rcS

/sbin/getty 38400 tty1 &
/sbin/getty 38400 tty2 &

/bin/touch /var/log/messages

/imageinit.py


# Install symlinks to all the busybox applets
# busybox --install -s

# Run BusyBox's mdev to create the devices
# echo "Listing of /dev before running mdev: "; cd /dev; ls -l; cd /
# mdev -s
# echo "Listing of /dev after running mdev: "; cd /dev; ls -l; cd /

# exec switch_root -c ${CONSOLE} ${NEW_ROOT} ${NEW_INIT}
exec switch_root ${NEW_ROOT} ${NEW_INIT}

echo "exec switch_root failed, debugging time again..."
/bin/ash