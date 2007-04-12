# $Id$
# Configure
PROJECT(Cheetah)
SET(LICENSE_FILE src/LICENSE)
SET(VERSION_STR 2.0rc7)
SET(SRC_URL http://downloads.sourceforge.net/cheetahtemplate/${PROJECT_NAME}--${VERSION_STR}.tar.gz?modtime=1152040991&big_mirror=0)

# Build template



CONFIGURE_FILE(${LICENSE_FILE} ${KUSU_ROOT}/share/doc/${PROJECT_NAME}-${VERSION_STR}/LICENSE COPYONLY)
