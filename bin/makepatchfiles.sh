#!/bin/sh

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

	mkdir -p $NIPATCHFILESDIR/fedora/6/x86_64
	$KUSU_BUILD_ARTEFACTS make-ni-patch \
	kususrc=${CMAKE_CURRENT_SOURCE_DIR} os=fedora \
	version=6 arch=x86_64 \
	patch=$NIPATCHFILESDIR/fedora/6/x86_64/updates.img
	
	cp -f ${CMAKE_CURRENT_SOURCE_DIR}/src/dists/fedora/6/nodeinstaller/ks.cfg.tmpl \
	$NIPATCHFILESDIR/fedora/6/i386
	
	cp -f ${CMAKE_CURRENT_SOURCE_DIR}/src/dists/fedora/6/nodeinstaller/ks.cfg.tmpl \
	$NIPATCHFILESDIR/fedora/6/x86_64
	
	echo "Building Centos 5 patchfiles.."
	mkdir -p $NIPATCHFILESDIR/centos/5/i386
	$KUSU_BUILD_ARTEFACTS make-ni-patch \
	kususrc=${CMAKE_CURRENT_SOURCE_DIR} os=centos \
	version=5 arch=i386 \
	patch=$NIPATCHFILESDIR/centos/5/i386/updates.img

	mkdir -p $NIPATCHFILESDIR/centos/5/x86_64
	$KUSU_BUILD_ARTEFACTS make-ni-patch \
	kususrc=${CMAKE_CURRENT_SOURCE_DIR} os=centos \
	version=5 arch=x86_64 \
	patch=$NIPATCHFILESDIR/centos/5/x86_64/updates.img
	
	cp -f ${CMAKE_CURRENT_SOURCE_DIR}/src/dists/centos/5/nodeinstaller/ks.cfg.tmpl \
	$NIPATCHFILESDIR/centos/5/i386
	
	cp -f ${CMAKE_CURRENT_SOURCE_DIR}/src/dists/centos/5/nodeinstaller/ks.cfg.tmpl \
	$NIPATCHFILESDIR/centos/5/x86_64
	
	exit 0
	
else
	echo "$0 <BASEKITSRC>"
	exit 1
fi


