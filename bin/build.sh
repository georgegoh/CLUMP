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

KUSU_REVISION=`svn info ../ | grep 'Last Changed Rev:' | awk '{print $4}'`
KUSU_VERSION=`cat config.mk | grep KUSU_VERSION | awk '{print $3}'`

svn info ../ | grep URL | grep tags/RELEASE
RELEASE_BUILD=$?

if [ "$RELEASE_BUILD" -eq 0 ]; then 
    sed -e "s%@KUSU_BUILD_DIST@%$KUSU_BUILD_DIST%" \
        -e "s%@KUSU_BUILD_DISTVER@%$KUSU_BUILD_DISTVER%" \
        -e "s%@KUSU_BUILD_ARCH@%$KUSU_BUILD_ARCH%" \
        -e "s%@KUSU_REVISION@%$KUSU_REVISION%" \
        config.mk > ../config.mk
else
    sed -e "s%@KUSU_BUILD_DIST@%$KUSU_BUILD_DIST%" \
        -e "s%@KUSU_BUILD_DISTVER@%$KUSU_BUILD_DISTVER%" \
        -e "s%@KUSU_BUILD_ARCH@%$KUSU_BUILD_ARCH%" \
        -e "s%@KUSU_REVISION@%$KUSU_REVISION.daily%" \
        config.mk > ../config.mk
fi

# sed -e "s%@KUSU_BUILD_DIST@%$KUSU_BUILD_DIST%" \
#     -e "s%@KUSU_BUILD_DISTVER@%$KUSU_BUILD_DISTVER%" \
#     -e "s%@KUSU_BUILD_ARCH@%$KUSU_BUILD_ARCH%" kusuenv.sh > ../src/kits/base/packages/kusu-core/src/bin/kusuenv.sh
# chmod 755 ../src/kits/base/packages/kusu-core/src/bin/kusuenv.sh

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

    if [ "$RELEASE_BUILD" -eq 0 ]; then
        mv `basename *.iso .iso`.iso kusu-$KUSU_VERSION.$KUSU_BUILD_DIST-$KUSU_BUILD_DISTVER.$KUSU_BUILD_ARCH.iso; 
        scp *.iso build@ronin:build/kusu/release/$KUSU_VERSION
    else
        mv `basename *.isio .iso`.iso kusu-$KUSU_VERSION-`date +%Y%m%d`-$KUSU_REVISION.$KUSU_BUILD_DIST-$KUSU_BUILD_DISTVER.$KUSU_BUILD_ARCH.iso; 
        mdkir -p $KUSU_REVISION
        mkdir -p $KUSU_REVISION/ISO
        mkdir -p $KUSU_REVISION/RPMS/{i386,noarch,x86_64}
        mkdir -p $KUSU_REVISION/SRPMS

        mv *.iso $KUSU_REVISION/ISO
        cp src/kits/base/SRPMS/*.src.rpm $KUSU_REVISION/SRPMS

        cp -r src/kits/base/RPMS/i386/*.rpm $KUSU_REVISION/RPMS/i386
        cp -r src/kits/base/RPMS/noarch/*.rpm $KUSU_REVISION/RPMS/noarch
        cp -r src/kits/base/RPMS/x86_64/*.rpm $KUSU_REVISION/RPMS/x86_64

        scp -r $KUSU_REVISION build@ronin:build/kusu/$KUSU_BUILD_DIST/$KUSU_BUILD_DISTVER/
    fi
fi

exit $ec
