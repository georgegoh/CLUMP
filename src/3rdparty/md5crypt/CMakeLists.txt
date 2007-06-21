# $Id: CMakeLists.txt 1201 2007-06-07 05:30:31Z najib $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

# Configure
PROJECT(md5crypt)
SET(LICENSE_FILE COPYING)
SET(VERSION_STR 2.2)
SET(SRC_UR http://sabren.net/code/python/crypt/md5crypt.py)
SET(KUSU_MODULE OFF) #Set to ON if this is a Kusu module else set to OFF.

SET(SETUPPY_PATH ${CMAKE_CURRENT_BINARY_DIR}/src)
SET(SETUPPY_BUILD_ARGS)
SET(SETUPPY_INSTALL_ARGS)
SET(SETUPPY_SDIST_ARGS sdist)
SET(SETUPPY_BDIST_ARGS bdist)

INCLUDE(PythonSetupPy)
SET(KUSU_MODULE OFF)