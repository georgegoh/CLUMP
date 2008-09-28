#!/bin/sh
# 
# $Id$

if [ -z "$KUSU_BUILD_DIST" ]; then
    KUSU_BUILD_DIST=centos
fi

if [ -z "$KUSU_BUILD_DISTVER" ]; then
    KUSU_BUILD_DISTVER=5
fi

if [ -z "$KUSU_BUILD_ARCH" ]; then
    KUSU_BUILD_ARCH=x86_64
fi

if [ "$KUSU_BUILD_DIST" = "centos" ]; then
    ISO=CentOS-5.1-$KUSU_BUILD_ARCH-bin-DVD.iso
elif [ "$KUSU_BUILD_DIST" = "rhel" ]; then
    ISO=rhel-5.1-server-$KUSU_BUILD_ARCH-dvd.iso
fi

sed -e "s%@KUSU_BUILD_DIST@%$KUSU_BUILD_DIST%" \
    -e "s%@KUSU_BUILD_DISTVER@%$KUSU_BUILD_DISTVER%" \
    -e "s%@KUSU_BUILD_ARCH@%$KUSU_BUILD_ARCH%" config.mk > ../config.mk

MNT=/mnt/share/$KUSU_BUILD_DIST-$KUSU_BUILD_DISTVER-$KUSU_BUILD_ARCH

cd ../ && \
mkdir -p $MNT && \
mount -o loop /data/iso/$ISO $MNT && \
make clean && \
make && \
make bootable-iso 

ec=$?

umount $MNT && rmdir $MNT

if [ $ec -eq 0 ]; then
    mv `basename iso/*.iso .iso`.iso kusu-`cat config.mk | grep KUSU_VERSION | awk '{print $3}'`-`date +%Y%m%d`-`svn info | grep 'Last Changed Rev:' | awk '{print $4}'`.iso; 

    echo "scp *.iso build@ronin:build/$KUSU_BUILD_DIST/$KUSU_BUILD_DISTVER/$KUSU_BUILD_ARCH"; 
fi
