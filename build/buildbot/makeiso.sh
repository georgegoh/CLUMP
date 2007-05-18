#!${BASH_EXE}

mkdir -p ${KUSU_BUILD_DIST}/${KUSU_BUILD_DISTVER}/${KUSU_BUILD_ARCH}
source ${KUSU_ROOT}/bin/kusudevenv.sh
BUILDDATE=`date +"%Y%m%d%H%m%S"`
KUSUREVISION=`svn info ${CMAKE_CURRENT_SOURCE_DIR} | grep Revision | awk '{print $2}'`
boot-media-tool make-patch kususrc=${CMAKE_CURRENT_SOURCE_DIR} os=${KUSU_BUILD_DIST} version=${KUSU_BUILD_DISTVER} arch=${KUSU_BUILD_ARCH} patch=updates.img
boot-media-tool make-iso kususrc=${CMAKE_CURRENT_SOURCE_DIR} source=${KUSU_DISTRO_SRC} arch=${KUSU_BUILD_ARCH} iso=${KUSU_BUILD_DIST}/${KUSU_BUILD_DISTVER}/${KUSU_BUILD_ARCH}/kusu-$BUILDDATE-$KUSUREVISION.${KUSU_BUILD_DIST}-${KUSU_BUILD_DISTVER}.${KUSU_BUILD_ARCH}.iso  patch=updates.img
rm -f updates.img
tar -czf ${KUSU_BUILD_DIST}/${KUSU_BUILD_DISTVER}/${KUSU_BUILD_ARCH}/kusu-$BUILDDATE-$KUSUREVISION.${KUSU_BUILD_DIST}-${KUSU_BUILD_DISTVER}.${KUSU_BUILD_ARCH}.src.tgz ${CMAKE_CURRENT_SOURCE_DIR}
rsync -av --rsh=ssh --delete ${KUSU_BUILD_DIST}/${KUSU_BUILD_DISTVER}/${KUSU_BUILD_ARCH} build@ronin:/home/osgdc/www/pub/build/${KUSU_BUILD_DIST}/${KUSU_BUILD_DISTVER}/.

