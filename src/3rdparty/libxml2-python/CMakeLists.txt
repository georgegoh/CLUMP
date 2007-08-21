# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

# Configure
PROJECT(libxml2-python)
SET(LICENSE_FILE Copyright)
SET(VERSION_STR 2.5.11)
SET(SRC_URL ftp://xmlsoft.org/libxml2/python/libxml2-python-2.5.11.tar.gz)
SET(KUSU_MODULE OFF) #Set to ON if this is a Kusu module else set to OFF.

SET(SETUPPY_PATH ${CMAKE_CURRENT_BINARY_DIR}/src)
SET(SETUPPY_BUILD_ARGS)
SET(SETUPPY_INSTALL_ARGS)
SET(SETUPPY_SDIST_ARGS sdist)
SET(SETUPPY_BDIST_ARGS bdist)

INCLUDE(PatchSource)
INCLUDE(PythonSetupPy)

SET(KUSU_MODULE OFF)
