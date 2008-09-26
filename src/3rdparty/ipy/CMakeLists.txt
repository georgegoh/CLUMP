# $Id: CMakeLists.txt 1548 2007-06-22 11:43:57Z hirwan $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

# Configure
PROJECT(ipy)
SET(LICENSE_FILE COPYING)
SET(VERSION_STR 0.54)
SET(SRC_URL http://cheeseshop.python.org/packages/source/I/IPy/IPy-0.54.tar.gz)
SET(KUSU_MODULE OFF) #Set to ON if this is a Kusu module else set to OFF.

SET(SETUPPY_PATH ${CMAKE_CURRENT_BINARY_DIR}/src)
SET(SETUPPY_BUILD_ARGS)
SET(SETUPPY_INSTALL_ARGS)
SET(SETUPPY_SDIST_ARGS sdist)
SET(SETUPPY_BDIST_ARGS bdist)

INCLUDE(PythonSetupPy)
SET(KUSU_MODULE OFF)