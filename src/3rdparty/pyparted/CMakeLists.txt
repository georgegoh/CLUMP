# $Id$
# Configure
PROJECT(pyparted)
SET(LICENSE_FILE COPYING)
SET(VERSION_STR 1.8.5)
SET(SRC_URL http://people.redhat.com/dcantrel/pyparted/${PROJECT_NAME}-${VERSION_STR}.tar.gz)
SET(KUSU_MODULE OFF) #Set to ON if this is a Kusu module else set to OFF.

SET(CONFIGURE_PATH ${CMAKE_CURRENT_BINARY_DIR}/src)
SET(CONFIGURE_ARGS CFLAGS='-fPIC')

INCLUDE(ConfigureMakeInstall)
SET(KUSU_MODULE OFF)
