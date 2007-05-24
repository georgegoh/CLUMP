#!${BASH_EXE}

mkdir -m 755 -p ${KUSU_BUILD_DIST}/${KUSU_BUILD_DISTVER}/${KUSU_BUILD_ARCH}
cd ${CMAKE_CURRENT_SOURCE_DIR}/src/kits/base
cp kit-base.spec kit-base.spec.orig
sed -e '/^\%exclude/d' kit-base.spec.orig > kit-base.spec
make
chmod 644 *.iso
cp *.iso /data/scratch/${KUSU_BUILD_DIST}/${KUSU_BUILD_DISTVER}/${KUSU_BUILD_ARCH}/.
rsync -av --rsh=ssh --delete /data/scratch/${KUSU_BUILD_DIST}/${KUSU_BUILD_DISTVER}/${KUSU_BUILD_ARCH} build@ronin:/home/osgdc/www/pub/build/${KUSU_BUILD_DIST}/${KUSU_BUILD_DISTVER}/.