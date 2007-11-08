# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

PROJECT(core)
SET(LICENSE_FILE LICENSE)
SET(VERSION_STR ${KUSU_VERSION})
SET(SRC_URL http://www.osgdc.org)
SET(KUSU_MODULE ON) #Set to ON if this is a Kusu module else set to OFF.

SET(KUSU_LOGFILE /var/log/kusu.log)


SET(SETUPPY_PATH ${CMAKE_CURRENT_BINARY_DIR})
SET(SETUPPY_BUILD_ARGS)
SET(SETUPPY_INSTALL_ARGS)
SET(SETUPPY_SDIST_ARGS sdist)
SET(SETUPPY_BDIST_ARGS bdist)

# Get SVN Revision
FIND_PROGRAM(SVN_EXE
  NAMES svn
  PATHS
  /bin
  /usr/bin
  /usr/local/bin
)  
SET(SVN ${SVN_EXE})

SET(KUSU_REVISION)
EXEC_PROGRAM(${SVN} ${CMAKE_SOURCE_DIR}
             ARGS "info | grep \"Last Changed Rev\" | awk '{print $4}'"
             OUTPUT_VARIABLE KUSU_REVISION
)

# Stamp version string and revision number
CONFIGURE_FILE(${SETUPPY_PATH}/src/etc/kusu-release
               ${SETUPPY_PATH}/src/etc/kusu-release)

INCLUDE(PythonSetupPy)
SET(KUSU_MODULE OFF)


