# $Id$
SET(KUSU_VERSION 0.1)

## Add 3rd party modules to the build lists
SET(KUSU_3RDPARTY 
  pysqlite
  path
  md5crypt
  cheetah
  urlgrabber
  wget
  thttpd
)

## Add kusu modules to the build lists
SET(KUSU_MODULES 
  core
  autoinstall
  boot
  util
  ui
  partitiontool
  installer
  networktool
  hardware
  kit
  buildkit
)

## Include Kusu globals
SET(CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/build/CMakeScripts)
INCLUDE(KusuGlobals)

MESSAGE(STATUS "Please run make and source ${KUSU_ROOT}/bin/kusudevenv.sh.")





