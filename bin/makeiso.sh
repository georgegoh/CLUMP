#!${BASH_EXE}
# $Id$
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
boot-media-tool make-patch kususrc=${CMAKE_CURRENT_SOURCE_DIR} os=${KUSU_BUILD_DIST} version=${KUSU_BUILD_DISTVER} arch=${KUSU_BUILD_ARCH} patch=updates.img
#BASEKITISO=`ls ${CMAKE_CURRENT_BINARY_DIR}/src/kits/base/kit-base*.iso`
if [ -f ${CMAKE_CURRENT_BINARY_DIR}/src/kits/base/kit-base*.iso ]
then
  BASEKITISO=`ls ${CMAKE_CURRENT_BINARY_DIR}/src/kits/base/kit-base*.iso`
  boot-media-tool make-iso kususrc=${CMAKE_CURRENT_SOURCE_DIR} source=${KUSU_DISTRO_SRC} arch=${KUSU_BUILD_ARCH} kit=$BASEKITISO iso=kusu-$BUILDDATE-$KUSUREVISION.${KUSU_BUILD_DIST}-${KUSU_BUILD_DISTVER}.${KUSU_BUILD_ARCH}.iso  patch=updates.img
else
  boot-media-tool make-iso kususrc=${CMAKE_CURRENT_SOURCE_DIR} source=${KUSU_DISTRO_SRC} arch=${KUSU_BUILD_ARCH} iso=kusu-$BUILDDATE-$KUSUREVISION.${KUSU_BUILD_DIST}-${KUSU_BUILD_DISTVER}.${KUSU_BUILD_ARCH}.iso  patch=updates.img
fi
rm -f updates.img


