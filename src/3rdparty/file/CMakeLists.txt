# $Id$
# Configure
PROJECT(file)
SET(LICENSE_FILE COPYING)
SET(VERSION_STR 4.21)
SET(SRC_URL ftp://ftp.astron.com/pub/file/${PROJECT_NAME}-${VERSION_STR}.tar.gg)
SET(KUSU_MODULE OFF) #Set to ON if this is a Kusu module else set to OFF.

SET(CONFIGURE_PATH ${CMAKE_CURRENT_BINARY_DIR}/src)
SET(CONFIGURE_ARGS)

INCLUDE(ConfigureMakeInstall)
SET(KUSU_MODULE OFF)
