#!/bin/sh
# $Id$
#
# Kusu specific environment script
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.
#

if [ $# != 0 ]; then
	BASEKITSRC="$1"
	NIPATCHFILESDIR="$BASEKITSRC/packages/kusu-nodeinstaller-patchfiles"
	KUSU_BUILD_ARTEFACTS=${CMAKE_CURRENT_BINARY_DIR}/bin/build-kusu-artefacts
	KUSU_DEPS_CHECK=${CMAKE_CURRENT_BINARY_DIR}/bin/kusu-deps-check
	
	# check tool dependencies
	$KUSU_DEPS_CHECK
	if [ ! $? -eq 0 ]; then
		echo "There are dependencies missing. Please fix before running this again!"
		exit 2
	fi
	
	if [ ! -d "$NIPATCHFILESDIR" ]; then
		echo "Please specify the location of the Base Kit source directory!"
		exit 2
	fi

	echo "Building Fedora Core 6 patchfiles.."
	mkdir -p $NIPATCHFILESDIR/fedora/6/i386
	$KUSU_BUILD_ARTEFACTS make-ni-patch \
	kususrc=${CMAKE_CURRENT_SOURCE_DIR} os=fedora \
	version=6 arch=i386 \
	patch=$NIPATCHFILESDIR/fedora/6/i386/updates.img
	ec=`expr $ec + $?`

	mkdir -p $NIPATCHFILESDIR/fedora/6/x86_64
	$KUSU_BUILD_ARTEFACTS make-ni-patch \
	kususrc=${CMAKE_CURRENT_SOURCE_DIR} os=fedora \
	version=6 arch=x86_64 \
	patch=$NIPATCHFILESDIR/fedora/6/x86_64/updates.img
	ec=`expr $ec + $?`
	
	cp -f ${CMAKE_CURRENT_SOURCE_DIR}/src/dists/fedora/6/nodeinstaller/ks.cfg.tmpl \
	$NIPATCHFILESDIR/fedora/6/i386
	
	cp -f ${CMAKE_CURRENT_SOURCE_DIR}/src/dists/fedora/6/nodeinstaller/ks.cfg.tmpl \
	$NIPATCHFILESDIR/fedora/6/x86_64
		
    echo "Building Fedora 7 patchfiles.."
	mkdir -p $NIPATCHFILESDIR/fedora/7/i386
	$KUSU_BUILD_ARTEFACTS make-ni-patch \
	kususrc=${CMAKE_CURRENT_SOURCE_DIR} os=fedora \
	version=7 arch=i386 \
	patch=$NIPATCHFILESDIR/fedora/7/i386/updates.img
	ec=`expr $ec + $?`

	mkdir -p $NIPATCHFILESDIR/fedora/7/x86_64
	$KUSU_BUILD_ARTEFACTS make-ni-patch \
	kususrc=${CMAKE_CURRENT_SOURCE_DIR} os=fedora \
	version=7 arch=x86_64 \
	patch=$NIPATCHFILESDIR/fedora/7/x86_64/updates.img
	ec=`expr $ec + $?`
	
	cp -f ${CMAKE_CURRENT_SOURCE_DIR}/src/dists/fedora/7/nodeinstaller/ks.cfg.tmpl \
	$NIPATCHFILESDIR/fedora/7/i386
	
	cp -f ${CMAKE_CURRENT_SOURCE_DIR}/src/dists/fedora/7/nodeinstaller/ks.cfg.tmpl \
	$NIPATCHFILESDIR/fedora/7/x86_64

    echo "Building Fedora 8 patchfiles.."
	mkdir -p $NIPATCHFILESDIR/fedora/8/i386
	$KUSU_BUILD_ARTEFACTS make-ni-patch \
	kususrc=${CMAKE_CURRENT_SOURCE_DIR} os=fedora \
	version=8 arch=i386 \
	patch=$NIPATCHFILESDIR/fedora/8/i386/updates.img
	ec=`expr $ec + $?`

	mkdir -p $NIPATCHFILESDIR/fedora/8/x86_64
	$KUSU_BUILD_ARTEFACTS make-ni-patch \
	kususrc=${CMAKE_CURRENT_SOURCE_DIR} os=fedora \
	version=8 arch=x86_64 \
	patch=$NIPATCHFILESDIR/fedora/8/x86_64/updates.img
	ec=`expr $ec + $?`
	
	cp -f ${CMAKE_CURRENT_SOURCE_DIR}/src/dists/fedora/8/nodeinstaller/ks.cfg.tmpl \
	$NIPATCHFILESDIR/fedora/8/i386
	
	cp -f ${CMAKE_CURRENT_SOURCE_DIR}/src/dists/fedora/8/nodeinstaller/ks.cfg.tmpl \
	$NIPATCHFILESDIR/fedora/8/x86_64

	echo "Building Fedora 9 patchfiles.."
	mkdir -p $NIPATCHFILESDIR/fedora/9/i386
	$KUSU_BUILD_ARTEFACTS make-ni-patch \
	kususrc=${CMAKE_CURRENT_SOURCE_DIR} os=fedora \
	version=9 arch=i386 \
	patch=$NIPATCHFILESDIR/fedora/9/i386/updates.img
	ec=`expr $ec + $?`

	mkdir -p $NIPATCHFILESDIR/fedora/9/x86_64
	$KUSU_BUILD_ARTEFACTS make-ni-patch \
	kususrc=${CMAKE_CURRENT_SOURCE_DIR} os=fedora \
	version=9 arch=x86_64 \
	patch=$NIPATCHFILESDIR/fedora/9/x86_64/updates.img
	ec=`expr $ec + $?`
	
	cp -f ${CMAKE_CURRENT_SOURCE_DIR}/src/dists/fedora/9/nodeinstaller/ks.cfg.tmpl \
	$NIPATCHFILESDIR/fedora/9/i386
	
	cp -f ${CMAKE_CURRENT_SOURCE_DIR}/src/dists/fedora/9/nodeinstaller/ks.cfg.tmpl \
	$NIPATCHFILESDIR/fedora/9/x86_64

    echo "Building Centos 4 patchfiles.."
	mkdir -p $NIPATCHFILESDIR/centos/4/i386
	$KUSU_BUILD_ARTEFACTS make-ni-patch \
	kususrc=${CMAKE_CURRENT_SOURCE_DIR} os=centos \
	version=4 arch=i386 \
	patch=$NIPATCHFILESDIR/centos/4/i386/updates.img
	ec=`expr $ec + $?`

	mkdir -p $NIPATCHFILESDIR/centos/4/x86_64
	$KUSU_BUILD_ARTEFACTS make-ni-patch \
	kususrc=${CMAKE_CURRENT_SOURCE_DIR} os=centos \
	version=4 arch=x86_64 \
	patch=$NIPATCHFILESDIR/centos/4/x86_64/updates.img
	ec=`expr $ec + $?`
	
	cp -f ${CMAKE_CURRENT_SOURCE_DIR}/src/dists/centos/4/nodeinstaller/ks.cfg.tmpl \
	$NIPATCHFILESDIR/centos/4/i386
	
	cp -f ${CMAKE_CURRENT_SOURCE_DIR}/src/dists/centos/4/nodeinstaller/ks.cfg.tmpl \
	$NIPATCHFILESDIR/centos/4/x86_64

	echo "Building Centos 5 patchfiles.."
	mkdir -p $NIPATCHFILESDIR/centos/5/i386
	$KUSU_BUILD_ARTEFACTS make-ni-patch \
	kususrc=${CMAKE_CURRENT_SOURCE_DIR} os=centos \
	version=5 arch=i386 \
	patch=$NIPATCHFILESDIR/centos/5/i386/updates.img
	ec=`expr $ec + $?`

	mkdir -p $NIPATCHFILESDIR/centos/5/x86_64
	$KUSU_BUILD_ARTEFACTS make-ni-patch \
	kususrc=${CMAKE_CURRENT_SOURCE_DIR} os=centos \
	version=5 arch=x86_64 \
	patch=$NIPATCHFILESDIR/centos/5/x86_64/updates.img
	ec=`expr $ec + $?`
	
	cp -f ${CMAKE_CURRENT_SOURCE_DIR}/src/dists/centos/5/nodeinstaller/ks.cfg.tmpl \
	$NIPATCHFILESDIR/centos/5/i386
	
	cp -f ${CMAKE_CURRENT_SOURCE_DIR}/src/dists/centos/5/nodeinstaller/ks.cfg.tmpl \
	$NIPATCHFILESDIR/centos/5/x86_64
	
    echo "Building RHEL 4 patchfiles.."
	mkdir -p $NIPATCHFILESDIR/rhel/4/i386
	$KUSU_BUILD_ARTEFACTS make-ni-patch \
	kususrc=${CMAKE_CURRENT_SOURCE_DIR} os=rhel \
	version=4 arch=i386 \
	patch=$NIPATCHFILESDIR/rhel/4/i386/updates.img
	ec=`expr $ec + $?`

	mkdir -p $NIPATCHFILESDIR/rhel/4/x86_64
	$KUSU_BUILD_ARTEFACTS make-ni-patch \
	kususrc=${CMAKE_CURRENT_SOURCE_DIR} os=rhel \
	version=4 arch=x86_64 \
	patch=$NIPATCHFILESDIR/rhel/4/x86_64/updates.img
	ec=`expr $ec + $?`
	
	cp -f ${CMAKE_CURRENT_SOURCE_DIR}/src/dists/rhel/4/nodeinstaller/ks.cfg.tmpl \
	$NIPATCHFILESDIR/rhel/4/i386
	
	cp -f ${CMAKE_CURRENT_SOURCE_DIR}/src/dists/rhel/4/nodeinstaller/ks.cfg.tmpl \
	$NIPATCHFILESDIR/rhel/4/x86_64
	
    echo "Building RHEL 5 patchfiles.."
	mkdir -p $NIPATCHFILESDIR/rhel/5/i386
	$KUSU_BUILD_ARTEFACTS make-ni-patch \
	kususrc=${CMAKE_CURRENT_SOURCE_DIR} os=rhel \
	version=5 arch=i386 \
	patch=$NIPATCHFILESDIR/rhel/5/i386/updates.img
	ec=`expr $ec + $?`

	mkdir -p $NIPATCHFILESDIR/rhel/5/x86_64
	$KUSU_BUILD_ARTEFACTS make-ni-patch \
	kususrc=${CMAKE_CURRENT_SOURCE_DIR} os=rhel \
	version=5 arch=x86_64 \
	patch=$NIPATCHFILESDIR/rhel/5/x86_64/updates.img
	ec=`expr $ec + $?`
	
	cp -f ${CMAKE_CURRENT_SOURCE_DIR}/src/dists/rhel/5/nodeinstaller/ks.cfg.tmpl \
	$NIPATCHFILESDIR/rhel/5/i386
	
	cp -f ${CMAKE_CURRENT_SOURCE_DIR}/src/dists/rhel/5/nodeinstaller/ks.cfg.tmpl \
	$NIPATCHFILESDIR/rhel/5/x86_64

	echo "Building Scientific Linux 5 patchfiles.."
	mkdir -p $NIPATCHFILESDIR/scientificlinux/5/i386
	$KUSU_BUILD_ARTEFACTS make-ni-patch \
	kususrc=${CMAKE_CURRENT_SOURCE_DIR} os=scientificlinux \
	version=5 arch=i386 \
	patch=$NIPATCHFILESDIR/scientificlinux/5/i386/updates.img
	ec=`expr $ec + $?`

	mkdir -p $NIPATCHFILESDIR/scientificlinux/5/x86_64
	$KUSU_BUILD_ARTEFACTS make-ni-patch \
	kususrc=${CMAKE_CURRENT_SOURCE_DIR} os=scientificlinux \
	version=5 arch=x86_64 \
	patch=$NIPATCHFILESDIR/scientificlinux/5/x86_64/updates.img
	ec=`expr $ec + $?`
	
	cp -f ${CMAKE_CURRENT_SOURCE_DIR}/src/dists/scientificlinux/5/nodeinstaller/ks.cfg.tmpl \
	$NIPATCHFILESDIR/scientificlinux/5/i386
	
	cp -f ${CMAKE_CURRENT_SOURCE_DIR}/src/dists/scientificlinux/5/nodeinstaller/ks.cfg.tmpl \
	$NIPATCHFILESDIR/scientificlinux/5/x86_64

	if [ ! $ec -eq 0 ]; then
		echo "Failure building NodeInstaller patchfiles!"
		rm -rf $NIPATCHFILESDIR/fedora
		rm -rf $NIPATCHFILESDIR/centos
		rm -rf $NIPATCHFILESDIR/rhel
		rm -rf $NIPATCHFILESDIR/scientificlinux
		exit 2
	fi
	
	exit 0
	
else
	echo "$0 <BASEKITSRC>"
	exit 1
fi


