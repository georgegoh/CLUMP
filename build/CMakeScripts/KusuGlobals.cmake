# $Id: KusuGlobals.cmake 293 2007-04-13 04:50:44Z hirwan $
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

SET(KUSU_ROOT $ENV{KUSU_ROOT})
IF(NOT KUSU_ROOT)
  SET(KUSU_ROOT ${KUSU_DEVEL_ROOT}/kusuroot)
ENDIF(NOT KUSU_ROOT)
SET(KUSU_BIN ${KUSU_ROOT}/bin)
SET(KUSU_LIB ${KUSU_ROOT}/lib)
SET(KUSU_BUILD_DIST $ENV{KUSU_BUILD_DIST})
SET(KUSU_BUILD_DISTVER $ENV{KUSU_BUILD_DISTVER})
SET(KUSU_BUILD_ISOBIN $ENV{KUSU_BUILD_ISOBIN})
SET(KUSU_DISTRO_SRC $ENV{KUSU_DISTRO_SRC})
SET(KUSU_BUILD_ARCH $ENV{KUSU_BUILD_ARCH})

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
SET(PYTHONPATH ${KUSU_LIB}/python)
IF(PLATFORM_BITS)
  SET(PYTHONPATH ${PYTHONPATH}:${KUSU_LIB}${PLATFORM_BITS}/python)
ENDIF(PLATFORM_BITS)

FIND_PROGRAM(BASH
  NAMES bash
  PATHS
  /bin
  /usr/bin
  /usr/local/bin
)

CONFIGURE_FILE(${CMAKE_CURRENT_SOURCE_DIR}/bin/kusudevenv.sh
          ${KUSU_BIN}/kusudevenv.sh)

