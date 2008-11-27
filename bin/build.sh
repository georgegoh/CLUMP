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
elif [ "$KUSU_BUILD_DIST" = "sles" ]; then
    ISO=SLES-10-SP2-DVD-$KUSU_BUILD_ARCH-GM-DVD1.iso
elif [ "$KUSU_BUILD_DIST" = "opensuse" ]; then
    ISO=openSUSE-10.3-DVD-$KUSU_BUILD_ARCH.iso
fi

KUSU_REVISION=`svn info ../ | grep 'Last Changed Rev:' | awk '{print $4}'`
KUSU_VERSION=`cat config.mk | grep KUSU_VERSION | awk '{print $3}'`

svn info ../ | grep URL | grep tags/RELEASE
RELEASE_BUILD=$?

if [ "$RELEASE_BUILD" -eq 0 ]; then 
    sed -e "s%@KUSU_REVISION@%$KUSU_REVISION%" \
        config.mk > ../config.mk
else
    sed  -e "s%@KUSU_REVISION@%$KUSU_REVISION.daily%" \
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
        mv `basename *.iso .iso`.iso kusu-$KUSU_VERSION-`date +%Y%m%d`-$KUSU_REVISION.$KUSU_BUILD_DIST-$KUSU_BUILD_DISTVER.$KUSU_BUILD_ARCH.iso; 
        
        DEST_PATH=$KUSU_VERSION/$KUSU_REVISION
        mkdir -p $DEST_PATH
        mkdir -p $DEST_PATH/ISO
        mkdir -p $DEST_PATH/RPMS/{i386,noarch,x86_64}
        mkdir -p $DEST_PATH/SRPMS

        mv *.iso $DEST_PATH/ISO
        cp src/kits/base/SRPMS/*.src.rpm $DEST_PATH/SRPMS

        cp -r src/kits/base/RPMS/i386/*.rpm $DEST_PATH/RPMS/i386
        cp -r src/kits/base/RPMS/noarch/*.rpm $DEST_PATH/RPMS/noarch
        cp -r src/kits/base/RPMS/x86_64/*.rpm $DEST_PATH/RPMS/x86_64

        if [ -d src/kits/base/RPMS/i586 ]; then
            mkdir -p $DEST_PATH/RPMS/i586
            cp -r src/kits/base/RPMS/i586/*.rpm $DEST_PATH/RPMS/i586
        fi

        scp -r $KUSU_VERSION build@ronin:build/kusu/$KUSU_BUILD_DIST/$KUSU_BUILD_DISTVER/DAILY/
    fi
fi

exit $ec
