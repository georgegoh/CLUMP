# $Id$
# Configure
PROJECT(pysqlite)
SET(LICENSE_FILE LICENSE)
SET(VERSION_STR 2.3.3)
SET(SRC_URL http://initd.org/pub/software/pysqlite/releases/2.3/2.3.3/pysqlite-2.3.3.tar.gz)
SET(KUSU_MODULE OFF) #Set to ON if this is a Kusu module else set to OFF.

SET(SETUPPY_PATH ${CMAKE_CURRENT_BINARY_DIR}/src)
SET(SETUPPY_BUILD_ARGS)
SET(SETUPPY_INSTALL_ARGS --install-data=${SETUPPY_PATH}/installdir/share/doc)
SET(SETUPPY_SDIST_ARGS sdist)
SET(SETUPPY_BDIST_ARGS bdist)

INCLUDE(PythonSetupPy)
SET(KUSU_MODULE OFF)

#Custom command and targets
ADD_CUSTOM_TARGET(move-docdir
  COMMAND mv ${SETUPPY_PATH}/installdir/share/doc/pysqlite2-doc/* 
             ${SETUPPY_PATH}/installdir/share/doc/.
  COMMAND rm -rf ${SETUPPY_PATH}/installdir/share/doc/pysqlite2-doc
  DEPENDS ${SETUPPY_PATH}/installdir
)

ADD_DEPENDENCIES(build-${PROJECT_NAME} setuppy-install copy-license move-docdir)