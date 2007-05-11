# $Id:$
# Configure
PROJECT(createrepo)
SET(LICENSE_FILE src/COPYING)
SET(VERSION_STR 0.4.8)
SET(SRC_URL http://linux.duke.edu/projects/metadata/generate/${PROJECT_NAME}-${VERSION_STR}.tar.gz)
SET(KUSU_MODULE OFF) #Set to ON if this is a Kusu module else set to OFF.

SET(SETUPPY_PATH ${CMAKE_CURRENT_BINARY_DIR})
SET(SETUPPY_BUILD_ARGS)
SET(SETUPPY_INSTALL_ARGS)
SET(SETUPPY_SDIST_ARGS sdist)
SET(SETUPPY_BDIST_ARGS bdist)

INCLUDE(PythonSetupPy)
SET(KUSU_MODULE OFF)

#Custom command and targets
ADD_CUSTOM_TARGET(patch-createrepo
  COMMAND patch -p0 < ${CMAKE_CURRENT_BINARY_DIR}/custom/${VERSION_STR}/createrepo.patch
  WORKING_DIRECTORY ${SETUPPY_PATH}/src
)

ADD_DEPENDENCIES(build-${PROJECT_NAME} patch-createrepo setuppy-install copy-license)
