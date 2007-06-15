#!${BASH_EXE}

mkdir -m 755 -p ${KUSU_BUILD_DIST}/${KUSU_BUILD_DISTVER}/${KUSU_BUILD_ARCH}
cd ${CMAKE_CURRENT_BINARY_DIR}/src/kits/base
for i in `find ./ -name '*.spec'`
do
  cp $i $i.orig
  sed -e '/^\%exclude/d' $i.orig > $i
done
make
ec=$?
if [ $ec != "0" ]
then
  exit $ec
fi
export BUILDDATE=`date +"%Y%m%d%H%m%S"`
export KUSUREVISION=`svn info ${CMAKE_CURRENT_SOURCE_DIR} | grep Revision | awk '{print $2}'`
for i in `ls kit-base-*.iso`
do
  isoname=`echo $i | sed -e 's/noarch.iso//'`
  mv $i $isoname$BUILDDATE-$KUSUREVISION.noarch.iso
  chmod 644 $isoname$BUILDDATE-$KUSUREVISION.noarch.iso
done
cp -p *.iso /data/scratch/${KUSU_BUILD_DIST}/${KUSU_BUILD_DISTVER}/${KUSU_BUILD_ARCH}/.
rsync -av --rsh=ssh --delete /data/scratch/${KUSU_BUILD_DIST}/${KUSU_BUILD_DISTVER}/${KUSU_BUILD_ARCH} build@ronin:/home/osgdc/www/pub/build/${KUSU_BUILD_DIST}/${KUSU_BUILD_DISTVER}/.