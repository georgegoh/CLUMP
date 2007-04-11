# $Id$
# Configure
PROJECT(path)
SET(LICENSE_FILE src/COPYING)
SET(VERSION_STR 2.2)
SET(SRC_URL http://www.jorendorff.com/articles/python/path/path-${VERSION_STR}.zip)

# Build template



CONFIGURE_FILE(${LICENSE_FILE} ${KUSU_ROOT}/share/doc/${PROJECT_NAME}-${VERSION_STR}/LICENSE COPYONLY)
