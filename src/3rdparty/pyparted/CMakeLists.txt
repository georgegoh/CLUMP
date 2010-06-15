# $Id: CMakeLists.txt 275 2007-04-12 11:56:52Z hirwan $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

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

#Custom command and targets
ADD_CUSTOM_TARGET(move-docdir
  COMMAND mv ${SETUPPY_PATH}/installdir/share/doc/${PROJECT_NAME}-${VERSION_STR}/* 
             ${SETUPPY_PATH}/installdir/share/doc/.
  COMMAND rm -rf ${SETUPPY_PATH}/installdir/share/doc/${PROJECT_NAME}-${VERSION_STR}
  DEPENDS ${SETUPPY_PATH}/installdir
)

ADD_DEPENDENCIES(build-${PROJECT_NAME} setuppy-install copy-license move-docdir)
