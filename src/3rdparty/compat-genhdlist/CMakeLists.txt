# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

# Configure
PROJECT(compat-genhdlist)
SET(LICENSE_FILE COPYING)
SET(VERSION_STR 10.1.1.81)
SET(SRC_URL )
SET(KUSU_MODULE OFF) #Set to ON if this is a Kusu module else set to OFF.

SET(CONFIGURE_PATH ${CMAKE_CURRENT_BINARY_DIR}/src)
SET(CONFIGURE_ARGS CFLAGS='-fPIC')

INCLUDE(ConfigureMakeInstall)
SET(KUSU_MODULE OFF)
