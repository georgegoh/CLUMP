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
    mount -t sysfs none /sys
    ret=$?
    if [ "$ret" -ne '0' ]
    then
        # sysfs mount failed .. udev wont work
	echo "ERROR:  Failed to mount sysfs"
    fi
}

mount_proc() {
    mount -t proc none /proc
    ret=$?
    if [ "$ret" -ne '0' ]
    then
        # proc mount failed.  Disk detection will not work
	echo "ERROR:  Failed to mount /proc"
    fi
}

init_udev() {
    mount -o mode=0755 -t ramfs none /dev
    ret=$?
    if [ "$ret" -ne '0' ]
    then
        # /dev mount failed .. udev wont work
	    echo "ERROR:  Failed to mount /dev"
    fi
    mknod /dev/console c 5 1
    mknod /dev/null c 1 3
    mknod /dev/zero c 1 5
    mkdir /dev/{pts,shm}

    /sbin/start_udev

    echo -e '\000\000\000\000' > /proc/sys/kernel/hotplug
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
init_udev

# Use rngd to generate entropy for /dev/random; this solves a startup
# issue with 'automount' (from the autofs) package
/sbin/rngd -r /dev/urandom

/bin/mount -o remount,rw /
/bin/mount -a
/bin/hostname -F /etc/hostname
/sbin/ifconfig lo 127.0.0.1 up
/sbin/route add -net 127.0.0.0 netmask 255.0.0.0 lo

# now run any rc scripts
/etc/init.d/rcS

# Provide shell for watching what it is doing.
/sbin/getty 38400 tty2 &

/bin/touch /var/log/messages

/imageinit.py
RETVAL=$?
if [ -s /tmp/imageinit.log ] ; then
    cp /tmp/imageinit.log ${NEW_ROOT}/tmp/imageinit.log
fi

if [ $RETVAL -eq 0 ]; then
    exec switch_root ${NEW_ROOT} ${NEW_INIT}
fi

if [ $RETVAL -eq 99 ]; then
    # Imaged node finished 
    echo "Installation Finished.  Rebooting!"
    echo "b" > /proc/sysrq-trigger
fi

echo "Debugging time..."
/sbin/getty 38400 tty1
