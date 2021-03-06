#!/bin/sh

# $Id: imageinit.sh 2590 2007-10-29 19:23:02Z mblack $
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
    mknod /dev/initctl p
    chmod 600 /dev/initctl
    mkdir /dev/{pts,shm}

    if [ -f /sbin/start_udev ]; then
        /sbin/start_udev
    else
        /etc/init.d/boot.udev start
        /etc/init.d/boot.device-mapper start > /dev/null 2>&1
    fi

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
[ -f /sbin/rngd ] && /sbin/rngd -r /dev/urandom

/bin/mount -o remount,rw /
/bin/mount -a
/bin/hostname -F /etc/hostname
/sbin/ifconfig lo 127.0.0.1 up
/sbin/route add -net 127.0.0.0 netmask 255.0.0.0 lo

# now run any rc scripts
if [ -f /etc/init.d/rcS ]; then
    /etc/init.d/rcS
else
    /etc/rc.d/init.d/rcS > /dev/null 2>&1
fi

# Provide shell for watching what it is doing.
if [ -f /sbin/getty ]; then
    /sbin/getty 38400 tty2 &
else
    /sbin/mingetty 38400 tty2 &
fi

/bin/touch /var/log/messages

/imageinit.py

RETVAL=$?
if [ -s /tmp/imageinit.log ] ; then
    cp /tmp/imageinit.log ${NEW_ROOT}/tmp/imageinit.log
fi

/bin/umount /tmp

if [ $RETVAL -eq 0 ]; then
    if [ -f /sbin/switch_root ]; then
        echo '/usr/bin/pkill udhcpc' >> ${NEW_ROOT}/etc/rc.local
        exec switch_root ${NEW_ROOT} ${NEW_INIT}
    else
        killall -9 dhclient > /dev/null 2>&1
        dd if=/dev/urandom of=${NEW_ROOT}/var/lib/misc/random-seed count=1 bs=512 2>/dev/null
        mount --bind /dev ${NEW_ROOT}/dev
        umount /proc
        umount /sys
        rm -fr /etc /opt /svr /boot /home /root /usr/{include,lib,lib64,share,X11R6} /lib/modules
        cd ${NEW_ROOT}
        mount --move . / > /dev/null 2>&1
        exec chroot . sh -c "rm /sbin/modprobe && ln -s /bin/true /sbin/modprobe && ./configure_sles.sh; exec ${NEW_INIT} 3" <dev/console >dev/console 2>&1
    fi
fi

if [ $RETVAL -eq 99 ]; then
    # Imaged node finished 
    echo "Installation Finished.  Rebooting!"
    echo "b" > /proc/sysrq-trigger
fi

echo "Debugging time..."
if [ -f /sbin/getty ]; then
    /sbin/getty 38400 tty1
else
    /bin/bash
fi
