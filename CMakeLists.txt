# $Id$
SET(KUSU_VERSION 0.1)

## Add 3rd party modules to the build lists
SET(KUSU_3RDPARTY 
  pyparted
  pysqlite
  path
  md5crypt
  cheetah
  urlgrabber
)

## Add kusu modules to the build lists
SET(KUSU_MODULES 
  core
  autogen
  boot
  util
  ui
  partitiontool
  installer
  networktool
)

## Include Kusu globals
SET(CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/build/CMakeScripts)
INCLUDE(KusuGlobals)




