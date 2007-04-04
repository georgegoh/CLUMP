#!/bin/sh

# This code creates a tftpboot directory and contents

if [ ! -d /tftpboot/ocs/pxelinux.cfg ] ; then
    mkdir -p /tftpboot/ocs/pxelinux.cfg
fi
chgrp -R apache /tftpboot/ocs/pxelinux.cfg

if [ ! -f /etc/xinetd.d/tftp ] ; then
    echo "ERROR:  Xinetd config for tftp not found"
    exit -1
fi

# Fix the tftp config file
awk -F' ' ' $1 == "server_args"                    { print "        server_args   = -s /tftpboot/ocs" }
            $1 == "disable"                        { print "        disable       = no" } 
            $1 != "disable" && $1 != "server_args" { print $0 }' < /etc/xinetd.d/tftp > /etc/xinetd.d/tftp.new
mv /etc/xinetd.d/tftp.new /etc/xinetd.d/tftp

# Restart xinetd
if [ -f /etc/init.d/xinetd ] ; then
    /etc/init.d/xinetd stop
    /etc/init.d/xinetd start
else
    echo "ERROR:  Can't find xinetd startup script"
fi

# Copy over a kernel and initrd to play with
REV=`uname -r`
cp /boot/initrd-${REV}.img /tftpboot/ocs/initrd-${REV}.img
cp /boot/vmlinuz-${REV} /tftpboot/ocs/vmlinuz-${REV}
chmod 644 /tftpboot/ocs/initrd-${REV}.img /tftpboot/ocs/vmlinuz-${REV}

