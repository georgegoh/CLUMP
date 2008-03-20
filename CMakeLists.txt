# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

SET(KUSU_VERSION 0.8)

# ## Add 3rd party modules to the build lists
SET(KUSU_3RDPARTY
  pysqlite
  path
  md5crypt
  cheetah
  #urlgrabber
  #wget
  thttpd
  sqlalchemy
  createrepo
  ipy
  #libxml2-python
)

# ## Add kusu modules to the build lists
SET(KUSU_MODULES
  core
  autoinstall
  boot
  util
  ui
  partitiontool
  installer
  nodeinstaller
  networktool
  hardware
  kitops
  repoman
  buildkit
  driverpatch
)

## Add kits to the build lists
SET(KUSU_KITS
"base cacti lava nagios hpc"
)

## Include Kusu globals
SET(CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/build/CMakeScripts)
INCLUDE(KusuGlobals)
SET(CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/build/buildbot)
INCLUDE(prepBuildScripts)

MESSAGE(STATUS "Please run make and source ${KUSU_ROOT}/bin/kusudevenv.sh.")





