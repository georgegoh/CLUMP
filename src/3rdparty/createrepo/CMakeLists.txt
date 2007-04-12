# $Id$
# Configure
PROJECT(createrepo)
SET(LICENSE_FILE src/COPYING)
SET(VERSION_STR 0.4.8)
SET(SRC_URL http://linux.duke.edu/projects/metadata/generate/${PROJECT_NAME}-${VERSION_STR}.tar.gz)

# Build template



CONFIGURE_FILE(${LICENSE_FILE} ${KUSU_ROOT}/share/doc/${PROJECT_NAME}-${VERSION_STR}/LICENSE COPYONLY)
