# $Id$
# Configure
PROJECT(wget)
SET(LICENSE_FILE COPYING)
SET(VERSION_STR 1.10.2)
SET(SRC_URL http://ftp.gnu.org/pub/gnu/wget/${PROJECT_NAME}-${VERSION_STR}.tar.gz)
SET(KUSU_MODULE OFF) #Set to ON if this is a Kusu module else set to OFF.

SET(CONFIGURE_PATH ${CMAKE_CURRENT_BINARY_DIR}/src)
SET(CONFIGURE_ARGS --without-ssl --disable-nls)

INCLUDE(ConfigureMakeInstall)
SET(KUSU_MODULE OFF)

ADD_DEPENDENCIES(build-${PROJECT_NAME} setuppy-install copy-license)
