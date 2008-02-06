# $Id: CMakeLists.txt 1201 2007-06-07 05:30:31Z najib $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

# Configure
PROJECT(cheetah)
SET(LICENSE_FILE LICENSE)
SET(VERSION_STR 2.0.1)
SET(SRC_URL http://downloads.sourceforge.net/cheetahtemplate/${PROJECT_NAME}-${VERSION_STR}.tar.gz?modtime=1152040991&big_mirror=0)
SET(KUSU_MODULE OFF) #Set to ON if this is a Kusu module else set to OFF.

SET(SETUPPY_PATH ${CMAKE_CURRENT_BINARY_DIR}/src)
SET(SETUPPY_BUILD_ARGS)
SET(SETUPPY_INSTALL_ARGS)
SET(SETUPPY_SDIST_ARGS sdist)
SET(SETUPPY_BDIST_ARGS bdist)

INCLUDE(PythonSetupPy)
SET(KUSU_MODULE OFF)
