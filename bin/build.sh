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
    ISO=CentOS-5.2-$KUSU_BUILD_ARCH-bin-DVD.iso
    DISTVER=$KUSU_BUILD_DISTVER
elif [ "$KUSU_BUILD_DIST" = "rhel" ]; then
    ISO=rhel-5.2-server-$KUSU_BUILD_ARCH-dvd.iso
    DISTVER=$KUSU_BUILD_DISTVER
elif [ "$KUSU_BUILD_DIST" = "sles" ]; then
    ISO=SLES-10-SP2-DVD-$KUSU_BUILD_ARCH-GM-DVD1.iso
    DISTVER=$KUSU_BUILD_DISTVER
elif [ "$KUSU_BUILD_DIST" = "opensuse" ]; then
    ISO=openSUSE-10.3-DVD-$KUSU_BUILD_ARCH.iso
    DISTVER=$KUSU_BUILD_DISTVER.$KUSU_BUILD_DISTVER_MINOR
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
if [ ! "$KUSU_BUILD_DIST" = "opensuse" ]; then mount -o loop /data/iso/$ISO $MNT; fi && \
make clean && \
make && \
if [ ! "$KUSU_BUILD_DIST" = "opensuse" ]; then make bootable-iso; fi 

ec=$?

umount $MNT && rmdir $MNT

if [ $ec -eq 0 ]; then

    if [ "$RELEASE_BUILD" -eq 0 ]; then
        mv `basename *.iso .iso`.iso kusu-$KUSU_VERSION.$KUSU_BUILD_DIST-$KUSU_BUILD_DISTVER.$KUSU_BUILD_ARCH.iso;
        if [ -f iso/kit-base-*.i386.iso ]; then
            base_kit_name_version=`basename iso/kit-base-*.iso .i386.iso`;
            cp -f iso/$base_kit_name_version.i386.iso $base_kit_name_version.$KUSU_BUILD_DIST-$DISTVER.$KUSU_BUILD_ARCH.iso;
        elif [ -f iso/*.i586.iso ]; then
            base_kit_name_version=`basename iso/kit-base-*.iso .i586.iso`;
            cp -f iso/$base_kit_name_version.i586.iso $base_kit_name_version.$KUSU_BUILD_DIST-$DISTVER.$KUSU_BUILD_ARCH.iso;
        elif [ -f iso/*.x86_64.iso ]; then
            base_kit_name_version=`basename iso/kit-base-*.iso .x86_64.iso`;
            cp -f iso/$base_kit_name_version.x86_64.iso $base_kit_name_version.$KUSU_BUILD_DIST-$DISTVER.$KUSU_BUILD_ARCH.iso;
        fi 
        scp *.iso build@ronin:build/kusu/release/$KUSU_VERSION
    else
        mv `basename *.iso .iso`.iso kusu-$KUSU_VERSION-`date +%Y%m%d`-$KUSU_REVISION.$KUSU_BUILD_DIST-$KUSU_BUILD_DISTVER.$KUSU_BUILD_ARCH.iso; 
        if [ -f iso/kit-base-*.i386.iso ]; then
            base_kit_name_version=`basename iso/kit-base-*.iso .i386.iso`;
            cp -f iso/$base_kit_name_version.i386.iso $base_kit_name_version-`date +%Y%m%d`-$KUSU_REVISION.$KUSU_BUILD_DIST-$DISTVER.$KUSU_BUILD_ARCH.iso;
        elif [ -f iso/*.i586.iso ]; then
            base_kit_name_version=`basename iso/kit-base-*.iso .i586.iso`;
            cp -f iso/$base_kit_name_version.i586.iso $base_kit_name_version-`date +%Y%m%d`-$KUSU_REVISION.$KUSU_BUILD_DIST-$DISTVER.$KUSU_BUILD_ARCH.iso;
        elif [ -f iso/*.x86_64.iso ]; then
            base_kit_name_version=`basename iso/kit-base-*.iso .x86_64.iso`;
            cp -f iso/$base_kit_name_version.x86_64.iso $base_kit_name_version-`date +%Y%m%d`-$KUSU_REVISION.$KUSU_BUILD_DIST-$DISTVER.$KUSU_BUILD_ARCH.iso;
        fi
        
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

        if [ "$KUSU_BUILD_DIST" = "opensuse" ]; then 
            scp -r $KUSU_VERSION build@ronin:build/kusu/$KUSU_BUILD_DIST/$KUSU_BUILD_DISTVER.$KUSU_BUILD_DISTVER_MINOR/DAILY/
        else
            scp -r $KUSU_VERSION build@ronin:build/kusu/$KUSU_BUILD_DIST/$KUSU_BUILD_DISTVER/DAILY/
        fi
    fi
fi

exit $ec
