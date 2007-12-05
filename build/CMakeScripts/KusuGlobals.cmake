# $Id: KusuGlobals.cmake 293 2007-04-13 04:50:44Z hirwan $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.
#
## Assert out-of-source build
IF(${CMAKE_BINARY_DIR} STREQUAL ${CMAKE_SOURCE_DIR})
  MESSAGE(FATAL_ERROR "Please build out of source directory.")
ENDIF(${CMAKE_BINARY_DIR} STREQUAL ${CMAKE_SOURCE_DIR})

## Get the python interpreter and version
INCLUDE(FindPythonInterp)

IF(NOT PYTHONINTERP_FOUND)
  MESSAGE(FATAL_ERROR "python executable not found")
ENDIF(NOT PYTHONINTERP_FOUND)

SET(PYTHON_VERSION)
EXEC_PROGRAM(${PYTHON_EXECUTABLE}
  ARGS  "-c 'import sys; print sys.version[:3]'"
  OUTPUT_VARIABLE PYTHON_VERSION
)

SET(PLATFORM)
EXEC_PROGRAM(${PYTHON_EXECUTABLE}
  ARGS  "-c 'import platform; print platform.machine()'"
  OUTPUT_VARIABLE PLATFORM
)


SET(PLATFORM_BITS)
IF(${PLATFORM} STREQUAL "x86_64")
  SET(PLATFORM_BITS 64)
ENDIF(${PLATFORM} STREQUAL "x86_64")

## Set global Kusu variables
SET(KUSU_DEVEL_ROOT ${CMAKE_BINARY_DIR})
MESSAGE(STATUS "KUSU_DEVEL_ROOT=${KUSU_DEVEL_ROOT}")

SET(KUSU_INSTALL_PREFIX $ENV{KUSU_INSTALL_PREFIX})
IF(NOT KUSU_INSTALL_PREFIX)
  SET(KUSU_INSTALL_PREFIX /opt/kusu)
ENDIF(NOT KUSU_INSTALL_PREFIX)

SET(KUSU_ROOT $ENV{KUSU_ROOT})
IF(NOT KUSU_ROOT)
  SET(KUSU_ROOT ${KUSU_DEVEL_ROOT}/kusuroot)
ENDIF(NOT KUSU_ROOT)
IF(EXISTS ${KUSU_ROOT}/etc/kusu-release)
    FILE(READ ${KUSU_ROOT}/etc/kusu-release KUSU_RELEASE)
    MESSAGE("Existing Kusu installation found at ${KUSU_ROOT}. ${KUSU_RELEASE}Setting KUSU_ROOT=${KUSU_DEVEL_ROOT}/kusuroot.")
    SET(KUSU_ROOT ${KUSU_DEVEL_ROOT}/kusuroot)
ENDIF(EXISTS ${KUSU_ROOT}/etc/kusu-release)
SET(KUSU_BIN ${KUSU_ROOT}/bin)
SET(KUSU_LIB ${KUSU_ROOT}/lib)

SET(KUSU_BUILD_DIST $ENV{KUSU_BUILD_DIST})
SET(KUSU_BUILD_DISTVER $ENV{KUSU_BUILD_DISTVER})
IF(NOT KUSU_BUILD_DIST OR
   NOT KUSU_BUILD_DISTVER )
  IF(EXISTS /etc/fedora-release)
    FILE(READ /etc/fedora-release content)
    SET(DISTRO fedora)
    STRING(REGEX MATCH "[0-9.]+" DISTRO_RELEASE ${content})
  ELSEIF(EXISTS /etc/redhat-release)
    FILE(READ /etc/redhat-release content)
    IF(${content} MATCHES "^CentOS")
      SET(DISTRO centos)
      STRING(REGEX MATCH "[0-9.]+" DISTRO_RELEASE ${content})
    ELSEIF(${content} MATCHES "^Red Hat")
      SET(DISTRO rhel)
      STRING(REGEX MATCH "[0-9.]+" DISTRO_RELEASE ${content})
    ENDIF(${content} MATCHES "^CentOS")
  ELSEIF(EXISTS /etc/SuSE-release)
    FILE(READ /etc/SuSE-release content)
    IF(${content} MATCHES "^openSUSE")
      SET(DISTRO opensuse)
      STRING(REGEX MATCH "[0-9.]+" DISTRO_RELEASE ${content})
    ENDIF(${content} MATCHES "^openSUSE")
  ENDIF(EXISTS /etc/fedora-release)
  SET(KUSU_BUILD_DIST ${DISTRO} CACHE STRING "distro" FORCE)
  SET(KUSU_BUILD_DISTVER ${DISTRO_RELEASE} CACHE STRING "distro version" FORCE)
ENDIF(NOT KUSU_BUILD_DIST OR
   NOT KUSU_BUILD_DISTVER)
SET(KUSU_BUILD_ARCH $ENV{KUSU_BUILD_ARCH})
IF(NOT KUSU_BUILD_ARCH)
  IF(${PLATFORM} MATCHES "^i[3-6]?86$")
    SET(KUSU_BUILD_ARCH i386 CACHE STRING "arch" FORCE)
  ELSEIF(${PLATFORM} MATCHES "^x86_64$")
    SET(KUSU_BUILD_ARCH x86_64 CACHE STRING "arch" FORCE)
  ENDIF(${PLATFORM} MATCHES "^i[3-6]?86$")
ENDIF(NOT KUSU_BUILD_ARCH)

SET(KUSU_BUILD_ISOBIN $ENV{KUSU_BUILD_ISOBIN})
SET(KUSU_DISTRO_SRC $ENV{KUSU_DISTRO_SRC})
IF(NOT KUSU_DISTRO_SRC)
  SET(KUSU_DISTRO_SRC $KUSU_DISTRO_SRC)
ENDIF(NOT KUSU_DISTRO_SRC)
SET(KUSU_TMP $ENV{KUSU_TMP})
IF(NOT KUSU_TMP)
  SET(KUSU_TMP /tmp/kusu)
ENDIF(NOT KUSU_TMP)
IF(NOT EXISTS ${KUSU_TMP})
  FILE(MAKE_DIRECTORY ${KUSU_TMP})
ENDIF(NOT EXISTS ${KUSU_TMP})
SET(KUSU_CACHE_DIR ${KUSU_TMP}/cache)
IF(NOT EXISTS ${KUSU_CACHE_DIR})
  FILE(MAKE_DIRECTORY ${KUSU_CACHE_DIR})
ENDIF(NOT EXISTS ${KUSU_CACHE_DIR})
SET(KUSU_LOGLEVEL $ENV{KUSU_LOGLEVEL})
IF(NOT KUSU_LOGLEVEL)
  SET(KUSU_LOGLEVEL DEBUG)
ENDIF(NOT KUSU_LOGLEVEL)
SET(KUSU_LOGFILE $ENV{KUSU_LOGFILE})
IF(NOT KUSU_LOGFILE)
  SET(KUSU_LOGFILE ${KUSU_TMP}/kusu.log)
ENDIF(NOT KUSU_LOGFILE)
SET(KUSUKITS $ENV{KUSUKITS})
IF(NOT KUSUKITS)
  SET(KUSUKITS ${KUSU_KITS})
ENDIF(NOT KUSUKITS)
SET(KITSEXTRAISODIR $ENV{KITS_EXTRA_ISO_DIR})
IF(NOT KITSEXTRAISODIR)
  SET(KITSEXTRAISODIR /data/iso/kits)
ENDIF(NOT KITSEXTRAISODIR)
SET(KIT_ARCHIVE_SITE $ENV{ARCHIVE_SITE})
IF(NOT KIT_ARCHIVE_SITE)
  SET(KIT_ARCHIVE_SITE http://www.osgdc.org/pub/build/kits)
ENDIF(NOT KIT_ARCHIVE_SITE)

## Copy source to devel root
EXEC_PROGRAM(${CMAKE_COMMAND}
  ARGS -E copy_directory ${CMAKE_SOURCE_DIR} 
       ${KUSU_DEVEL_ROOT}
)

## remove old kusuroot and create new kusuroot
FILE(REMOVE_RECURSE ${KUSU_ROOT})
FILE(MAKE_DIRECTORY ${KUSU_ROOT})
FILE(MAKE_DIRECTORY ${KUSU_BIN})
FILE(MAKE_DIRECTORY ${KUSU_LIB})
FILE(MAKE_DIRECTORY ${KUSU_LIB}/python)
FILE(MAKE_DIRECTORY ${KUSU_LIB}/python/kusu)
FILE(WRITE ${KUSU_LIB}/python/kusu/__init__.py "")

## Adding modules directory to top level CMakeLists.txt file

FOREACH(external_module ${KUSU_3RDPARTY})
  ADD_SUBDIRECTORY(${KUSU_DEVEL_ROOT}/src/3rdparty/${external_module} ${KUSU_DEVEL_ROOT}/src/3rdparty/${external_module})
ENDFOREACH(external_module)

FOREACH (kusu_module ${KUSU_MODULES})
  ADD_SUBDIRECTORY(${KUSU_DEVEL_ROOT}/src/modules/${kusu_module} ${KUSU_DEVEL_ROOT}/src/modules/${kusu_module})
ENDFOREACH(kusu_module)

## Generating Kusu development environment
SET(PYTHONPATH $KUSU_ROOT/lib/python)
IF(PLATFORM_BITS)
  SET(PYTHONPATH $KUSU_ROOT/lib${PLATFORM_BITS}/python:${PYTHONPATH})
ENDIF(PLATFORM_BITS)
SET(PYTHONPATH ${PYTHONPATH}:$PYTHONPATH)

FIND_PROGRAM(BASH_EXE
  NAMES bash
  PATHS
  /bin
  /usr/bin
  /usr/local/bin
)
SET(BASH ${BASH_EXE})

CONFIGURE_FILE(${CMAKE_CURRENT_SOURCE_DIR}/bin/kusudevenv.sh
          ${KUSU_BIN}/kusudevenv.sh)

IF(KUSU_BUILD_DIST AND KUSU_BUILD_DISTVER)
  SET(KUSU_LOGFILE /var/log/kusu/kusu.log)
  CONFIGURE_FILE(${CMAKE_CURRENT_BINARY_DIR}/src/modules/core/src/bin/kusuenv.sh 
  ${CMAKE_CURRENT_BINARY_DIR}/src/dists/${KUSU_BUILD_DIST}/${KUSU_BUILD_DISTVER}/${KUSU_BUILD_ARCH}/kusuenv.sh)
  CONFIGURE_FILE(${CMAKE_CURRENT_BINARY_DIR}/src/modules/core/src/bin/kusuenv.sh 
  ${CMAKE_CURRENT_BINARY_DIR}/src/modules/core/src/bin/kusuenv.sh)

  CONFIGURE_FILE(${CMAKE_CURRENT_BINARY_DIR}/bin/makeiso.sh ${CMAKE_CURRENT_BINARY_DIR}/bin/makeiso.sh)
  CONFIGURE_FILE(${CMAKE_CURRENT_BINARY_DIR}/bin/makebasekit.sh                
                 ${CMAKE_CURRENT_BINARY_DIR}/bin/makebasekit.sh)
  CONFIGURE_FILE(${CMAKE_CURRENT_BINARY_DIR}/bin/makemetakit.sh                
                 ${CMAKE_CURRENT_BINARY_DIR}/bin/makemetakit.sh) 
  CONFIGURE_FILE(${CMAKE_CURRENT_BINARY_DIR}/bin/makemetaiso.sh                
                 ${CMAKE_CURRENT_BINARY_DIR}/bin/makemetaiso.sh)
  CONFIGURE_FILE(${CMAKE_CURRENT_BINARY_DIR}/bin/makepatchfiles.sh                
                 ${CMAKE_CURRENT_BINARY_DIR}/bin/makepatchfiles.sh)
  CONFIGURE_FILE(${CMAKE_CURRENT_BINARY_DIR}/build/buildbot/makeiso.sh
                 ${CMAKE_CURRENT_BINARY_DIR}/build/buildbot/makeiso.sh)
  CONFIGURE_FILE(${CMAKE_CURRENT_BINARY_DIR}/build/buildbot/syncstatus.sh
                 ${CMAKE_CURRENT_BINARY_DIR}/build/buildbot/syncstatus.sh)
  CONFIGURE_FILE(${CMAKE_CURRENT_BINARY_DIR}/build/buildbot/makebasekitiso.sh
                 ${CMAKE_CURRENT_BINARY_DIR}/build/buildbot/makebasekitiso.sh)
  CONFIGURE_FILE(${CMAKE_CURRENT_BINARY_DIR}/build/buildbot/makemetaiso.sh
                 ${CMAKE_CURRENT_BINARY_DIR}/build/buildbot/makemetaiso.sh)
ENDIF(KUSU_BUILD_DIST AND KUSU_BUILD_DISTVER)

FILE(GLOB_RECURSE DOTSVN "${CMAKE_CURRENT_BINARY_DIR}/entries")
FOREACH(dotsvn ${DOTSVN})
  GET_FILENAME_COMPONENT(svndir ${dotsvn} PATH)
  EXEC_PROGRAM(
    rm
    ARGS -rf ${svndir}
    OUTPUT_VARIABLE /dev/null
  )
ENDFOREACH(dotsvn)
