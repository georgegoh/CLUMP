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

# From initrd.scripts
strlen() {
    if [ -z "$1" ]
    then
	echo "usage: strlen <variable_name>"
	die
    fi
    eval echo "\${#${1}}"
}

parse_opt() {
    case "$1" in
	*\=*)
	    local key_name="$(echo "$1" | cut -f1 -d=)"
	    local key_len=$(strlen key_name)
	    local value_start=$((key_len+2))
	    echo "$1" | cut -c ${value_start}-
	    ;;
    esac
}

mount_sysfs() {
    mount -t sysfs /sys /sys
    ret=$?
    if [ "$ret" -ne '0' ]
    then
        # sysfs mount failed .. udev wont work
	echo sysfs mount failed.
    fi
}

chooseKeymap() {
    echo "Loading keymaps"
    cat /lib/keymaps/keymapList
    read -t 10 -p '<< Load keymap (Enter for default): ' keymap
    if [ -e /lib/keymaps/${keymap}.map ]
    then
	echo "Loading the ''${keymap}'' keymap"
	loadkmap < /lib/keymaps/${keymap}.map
    elif [ "$keymap" = '' ]
    then
	echo
	echo "Keeping default keymap"
    else
	echo "Sorry, but keymap ''${keymap}'' is invalid!"
	chooseKeymap
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

mount -t proc proc /proc >/dev/null 2>&1

/bin/mount -o remount,rw /
/bin/mount -t proc proc /proc
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
busybox --install -s

verbose_kmsg
mount_sysfs

# Load the modules (except sd_mod)

# Run BusyBox's mdev to create the devices
# echo "Listing of /dev before running mdev: "; cd /dev; ls -l; cd /
mdev -s
# echo "Listing of /dev after running mdev: "; cd /dev; ls -l; cd /

CMDLINE="$(cat /proc/cmdline)"
# Scan CMDLINE for a real_root= argument
REAL_ROOT=''
for x in ${CMDLINE}
do
	case "${x}" in
		real_root\=*)
			REAL_ROOT=`parse_opt "${x}"`
		;;
	esac
done

# The real_root argument can be a device name, a LABEL or a UUID
if [ -z "${REAL_ROOT}" ]; then
   echo "Root command line: ${CMDLINE}"
   echo "No real_root= argument given, starting ash"
   /bin/ash
   exit 0
fi

if [ "$(echo ${REAL_ROOT}|cut -c -5)" = "/dev/" ]; then
    echo ${REAL_ROOT} is a device name
# Make sure the device exists
    if [ ! -b ${REAL_ROOT} ]; then
	echo The block device ${REAL_ROOT} does not exist
	echo /proc/partitions is
	cat /proc/partitions
	retval=1
    else
	mount -r ${REAL_ROOT} ${NEW_ROOT}
	retval=$?
    fi
elif [ "$(echo ${REAL_ROOT}|cut -c -6)" = "LABEL=" ]; then
    echo ${REAL_ROOT} is a LABEL
    DEV=$(findfs ${REAL_ROOT})
    if [ -z "${DEV}" ]; then
	echo No partition with ${REAL_ROOT} has been found
	retval=1
    else
	mount -r ${DEV} ${NEW_ROOT}
	retval=$?
    fi
elif [ "$(echo ${REAL_ROOT}|cut -c -5)" = "UUID=" ]; then
    echo ${REAL_ROOT} is a UUID
    DEV=$(findfs ${REAL_ROOT})
    if [ -z "${DEV}" ]; then
	echo No partition with ${REAL_ROOT} has been found
	retval=1
    else
	mount -r ${DEV} ${NEW_ROOT}
	retval=$?
    fi
else
    echo ${REAL_ROOT} is unrecognized.
    retval=2
fi
if [ "${retval}" -gt '0' ]; then
    # Start a shell
    if [ "${retval}" -eq '1' ]; then
	echo "Mounting the root fs failed, starting ash"
    fi
    /bin/ash
    exit 0
fi


exec switch_root -c ${CONSOLE} ${NEW_ROOT} ${NEW_INIT}

echo "exec switch_root failed, debugging time again..."
/bin/ash