#!${BASH_EXE}
# $Id: makemetakit.sh 2809 2007-11-21 07:06:51Z hirwan $
#
# Kusu specific environment script
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.
#


if [ ! -e ${KUSU_ROOT}/bin/kusudevenv.sh ]; then
  ( cd ${CMAKE_BINARY_DIR} && cmake ${CMAKE_SOURCE_DIR} )
fi
if [ ! -e ${KUSU_ROOT}/bin/boot-media-tool ]; then
  ( cd ${CMAKE_BINARY_DIR} && make )
fi
source ${KUSU_ROOT}/bin/kusudevenv.sh
BUILDDATE=`date +"%Y%m%d%H%m%S"`
KUSUREVISION=`svn info ${CMAKE_CURRENT_SOURCE_DIR} | grep "Last Changed Rev" | awk '{print $4}'`

if [ -z $KUSUKITS ]; then
	KUSUKITS="cacti lava nagios"
fi

TMP_KITDIR=`mktemp -d`

for kit in $KUSUKITS;
do
	if [ "$kit" == "base" ]; then
		echo "Skipping Base kit for now. Base kit will be built separately but will be included in the final meta kit ISO."
		continue
	fi
	
	echo "Making the $kit kit.."
	
	if [ -d ${CMAKE_CURRENT_BINARY_DIR}/src/kits/$kit ]; then
		cd ${CMAKE_CURRENT_BINARY_DIR}/src/kits/$kit
		make
	fi
	
	KIT_ISO=`ls ${CMAKE_CURRENT_BINARY_DIR}/src/kits/$kit/kit-$kit-*.iso`
	if [ -f $KIT_ISO ]; then
		mv -f $KIT_ISO $TMP_KITDIR
	fi
	
	if [ ! $? -eq 0 ]; then
		echo "Failure trying to make the $kit kit!"
		rm -rf $TMP_KITDIR
		exit 2
	fi
	
done

echo "Making Kusu NodeInstaller patchfiles.."
${CMAKE_CURRENT_BINARY_DIR}/bin/makepatchfiles.sh ${CMAKE_CURRENT_BINARY_DIR}/src/kits/base

if [ ! $? -eq 0 ]; then
	echo "Failure trying to make the base kit!"
	rm -rf $TMP_KITDIR
	exit 2
fi

cd ${CMAKE_CURRENT_BINARY_DIR}/src/kits/base
echo "Making the base kit.."
make

if [ ! $? -eq 0 ]; then
	echo "Failure trying to make the base kit!"
	rm -rf $TMP_KITDIR
	exit 2
fi

KIT_ISO=`ls ${CMAKE_CURRENT_BINARY_DIR}/src/kits/base/kit-base-*.iso`
if [ -f $KIT_ISO ]; then
	mv -f $KIT_ISO $TMP_KITDIR
	echo "Done."
fi


# check if the kusu runtime still exist and remake if its missing!
if [ ! -e ${KUSU_ROOT}/bin/kusudevenv.sh ]; then
  ( cd ${CMAKE_BINARY_DIR} && cmake ${CMAKE_SOURCE_DIR} )
fi
if [ ! -e ${KUSU_ROOT}/bin/buildkit ]; then
  ( cd ${CMAKE_BINARY_DIR} && make )
fi

if [ -d $KITS_EXTRA_ISO_DIR ]; then
    cp $KITS_EXTRA_ISO_DIR/kit-*.iso $TMP_KITDIR/.
fi

buildkit make-meta dir=$TMP_KITDIR iso=${CMAKE_BINARY_DIR}/metakit-$BUILDDATE-$KUSUREVISION.${KUSU_BUILD_DIST}-${KUSU_BUILD_DISTVER}.${KUSU_BUILD_ARCH}.iso





