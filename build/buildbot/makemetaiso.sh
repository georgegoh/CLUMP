#!${BASH_EXE}
# $Id$
#
# Kusu specific environment script
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.
#
SCRATCHDIR=`pwd`
mkdir -m 755 -p ${KUSU_BUILD_DIST}/${KUSU_BUILD_DISTVER}/${KUSU_BUILD_ARCH}
cd ${KUSU_BUILD_DIST}/${KUSU_BUILD_DISTVER}/${KUSU_BUILD_ARCH}

if [ ! -e ${KUSU_ROOT}/bin/kusudevenv.sh ]; then
  ( cd ${CMAKE_BINARY_DIR} && cmake ${CMAKE_SOURCE_DIR} )
fi
if [ ! -e ${KUSU_ROOT}/bin/boot-media-tool ]; then
  ( cd ${CMAKE_BINARY_DIR} && make )
fi
source ${KUSU_ROOT}/bin/kusudevenv.sh
BUILDDATE=`date +"%Y%m%d%H%m%S"`
KUSUREVISION=`svn info ${CMAKE_CURRENT_SOURCE_DIR} | grep "Last Changed Rev" | awk '{print $4}'`
boot-media-tool make-patch kususrc=${CMAKE_CURRENT_SOURCE_DIR} os=${KUSU_BUILD_DIST} version=${KUSU_BUILD_DISTVER} arch=${KUSU_BUILD_ARCH} patch=updates.img
if [ $? != "0" ]
then
  exit 1
fi
METAKIT=`ls ${CMAKE_CURRENT_BINARY_DIR}/metakit-*.iso`
if [ -f $METAKIT ]
then
  boot-media-tool make-iso kususrc=${CMAKE_CURRENT_SOURCE_DIR} source=${KUSU_DISTRO_SRC} arch=${KUSU_BUILD_ARCH} kit=$METAKIT iso=kusu-$BUILDDATE-$KUSUREVISION.${KUSU_BUILD_DIST}-${KUSU_BUILD_DISTVER}.${KUSU_BUILD_ARCH}.iso  patch=updates.img
else
  echo "No meta kit found. Run ${CMAKE_BINARY_DIR}/bin/makemetakit.sh to generate one."
  exit 1
fi
if [ $? != "0" ]
then
  exit 1
fi
rm -f updates.img

ln -sf kusu-$BUILDDATE-$KUSUREVISION.${KUSU_BUILD_DIST}-${KUSU_BUILD_DISTVER}.${KUSU_BUILD_ARCH}.iso \
        kusu-${KUSU_BUILD_DIST}-${KUSU_BUILD_DISTVER}.${KUSU_BUILD_ARCH}.latest.iso

tar -czf kusu-$BUILDDATE-$KUSUREVISION.${KUSU_BUILD_DIST}-${KUSU_BUILD_DISTVER}.${KUSU_BUILD_ARCH}.src.tgz ${CMAKE_CURRENT_SOURCE_DIR}
chmod 644 kusu-$BUILDDATE-$KUSUREVISION.${KUSU_BUILD_DIST}-${KUSU_BUILD_DISTVER}.${KUSU_BUILD_ARCH}.*
rsync -av --rsh=ssh --delete $SCRATCHDIR/${KUSU_BUILD_DIST}/${KUSU_BUILD_DISTVER}/${KUSU_BUILD_ARCH} build@ronin:/home/osgdc/www/pub/build/${KUSU_BUILD_DIST}/${KUSU_BUILD_DISTVER}/.


