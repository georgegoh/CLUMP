# $Id: CMakeLists.txt 270 2007-04-12 04:14:43Z ltsai $
# Configure
PROJECT(urlgrabber)
SET(LICENSE_FILE LICENSE)
SET(VERSION_STR 3.1.0)
SET(SRC_URL http://linux.duke.edu/projects/urlgrabber/download/${PROJECT_NAME}-${VERSION_STR}.tar.gz)
SET(KUSU_MODULE OFF) #Set to ON if this is a Kusu module else set to OFF.

SET(SETUPPY_PATH ${CMAKE_CURRENT_BINARY_DIR}/src)
SET(SETUPPY_BUILD_ARGS)
SET(SETUPPY_INSTALL_ARGS)
SET(SETUPPY_SDIST_ARGS sdist)
SET(SETUPPY_BDIST_ARGS bdist)

INCLUDE(PythonSetupPy)
SET(KUSU_MODULE OFF)

#Custom command and targets
ADD_CUSTOM_TARGET(move-docdir
  COMMAND mv ${SETUPPY_PATH}/installdir/share/doc/${PROJECT_NAME}-${VERSION_STR}/* 
             ${SETUPPY_PATH}/installdir/share/doc/.
  COMMAND rm -rf ${SETUPPY_PATH}/installdir/share/doc/${PROJECT_NAME}-${VERSION_STR}
  DEPENDS ${SETUPPY_PATH}/installdir
)

ADD_DEPENDENCIES(build-${PROJECT_NAME} setuppy-install copy-license move-docdir)