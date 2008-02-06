# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

# Configure
PROJECT(sqlalchemy)
SET(LICENSE_FILE LICENSE)
SET(VERSION_STR 0.3.11)
SET(SRC_URL http://prdownloads.sourceforge.net/sqlalchemy/SQLAlchemy-${VERSION_STR}.tar.gz?download)
SET(KUSU_MODULE OFF) #Set to ON if this is a Kusu module else set to OFF.

SET(SETUPPY_PATH ${CMAKE_CURRENT_BINARY_DIR}/src)
SET(SETUPPY_BUILD_ARGS)
SET(SETUPPY_INSTALL_ARGS)
SET(SETUPPY_SDIST_ARGS sdist)
SET(SETUPPY_BDIST_ARGS bdist)

INCLUDE(PatchSource)
INCLUDE(PythonSetupPy)
SET(KUSU_MODULE OFF)


