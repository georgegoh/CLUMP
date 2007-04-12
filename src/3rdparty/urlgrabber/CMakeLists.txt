# $Id$
# Configure
PROJECT(urlgrabber)
SET(LICENSE_FILE src/LICENSE)
SET(VERSION_STR 3.1.0)
SET(SRC_URL http://linux.duke.edu/projects/urlgrabber/download/${PROJECT_NAME}-${VERSION_STR}.tar.gz)

# Build template



CONFIGURE_FILE(${LICENSE_FILE} ${KUSU_ROOT}/share/doc/${PROJECT_NAME}-${VERSION_STR}/LICENSE COPYONLY)
