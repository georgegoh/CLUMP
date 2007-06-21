# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

# Configure
PROJECT(thttpd)
SET(LICENSE_FILE COPYING)
SET(VERSION_STR 2.25b)
SET(SRC_URL http://www.acme.com/software/thttpd/${PROJECT_NAME}-${VERSION_STR}.tar.gz)
SET(KUSU_MODULE OFF) #Set to ON if this is a Kusu module else set to OFF.

SET(CONFIGURE_PATH ${CMAKE_CURRENT_BINARY_DIR}/src)
SET(CONFIGURE_ARGS)

INCLUDE(PatchSource)
INCLUDE(ConfigureMakeInstall)
SET(KUSU_MODULE OFF)

#Custom command and targets
# ADD_CUSTOM_TARGET(patch
#   COMMAND patch -p0 < ${CMAKE_CURRENT_BINARY_DIR}/custom/${VERSION_STR}/makefile.in.patch 
#   WORKING_DIRECTORY ${SETUPPY_PATH}
# )
# 
# ADD_DEPENDENCIES(build-${PROJECT_NAME} patch make-all make-install copy-license)