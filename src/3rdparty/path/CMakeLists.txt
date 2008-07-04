# $Id: CMakeLists.txt 1201 2007-06-07 05:30:31Z najib $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

# Configure
PROJECT(path)
SET(LICENSE_FILE COPYING)
SET(VERSION_STR 2.2)
SET(SRC_URL http://www.jorendorff.com/articles/python/path/path-${VERSION_STR}.zip)
SET(KUSU_MODULE OFF) #Set to ON if this is a Kusu module else set to OFF.

SET(SETUPPY_PATH ${CMAKE_CURRENT_BINARY_DIR}/src)
SET(SETUPPY_BUILD_ARGS)
SET(SETUPPY_INSTALL_ARGS)
SET(SETUPPY_SDIST_ARGS sdist)
SET(SETUPPY_BDIST_ARGS bdist)

INCLUDE(PatchSource)
INCLUDE(PythonSetupPy)
SET(KUSU_MODULE OFF)
