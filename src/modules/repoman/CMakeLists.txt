# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

PROJECT(repoman)
SET(LICENSE_FILE LICENSE)
SET(VERSION_STR ${KUSU_VERSION})
SET(SRC_URL http://www.osgdc.org)
SET(KUSU_MODULE ON) #Set to ON if this is a Kusu module else set to OFF.

SET(SETUPPY_PATH ${CMAKE_CURRENT_BINARY_DIR})
SET(SETUPPY_BUILD_ARGS)
SET(SETUPPY_INSTALL_ARGS)
SET(SETUPPY_SDIST_ARGS sdist)
SET(SETUPPY_BDIST_ARGS bdist)

# Stamp version string 
CONFIGURE_FILE(${SETUPPY_PATH}/src/bin/repoman
               ${SETUPPY_PATH}/src/bin/repoman)
CONFIGURE_FILE(${SETUPPY_PATH}/src/bin/repopatch
               ${SETUPPY_PATH}/src/bin/repopatch)
INCLUDE(PythonSetupPy)
SET(KUSU_MODULE OFF)
