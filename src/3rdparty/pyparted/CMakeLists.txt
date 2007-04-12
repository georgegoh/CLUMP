# $Id$
# Configure
PROJECT(pyparted)
SET(LICENSE_FILE src/COPYING)
SET(VERSION_STR 1.8.5)
SET(SRC_URL http://people.redhat.com/dcantrel/pyparted/${PROJECT_NAME}-${VERSION_STR}.tar.gz)

SET(CONFIGURE_ARGS CFLAGS='-fPIC')

#### Build template

## Run configure
ADD_CUSTOM_COMMAND(
  OUTPUT  ${CMAKE_CURRENT_BINARY_DIR}/src/Makefile
  COMMAND ./configure
  ARGS    --prefix=${CMAKE_CURRENT_BINARY_DIR}/installdir ${CONFIGURE_ARGS}
  DEPENDS ${CMAKE_CURRENT_BINARY_DIR}/src/configure
  WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/src
  COMMENT "Running configure --prefix=${CMAKE_CURRENT_BINARY_DIR}/installdir ${CONFIGURE_ARGS} in ${CMAKE_CURRENT_BINARY_DIR}/src"
)
ADD_CUSTOM_TARGET(configure  ALL echo
  DEPENDS ${CMAKE_CURRENT_BINARY_DIR}/src/Makefile
)

## Run make
ADD_CUSTOM_TARGET(makeall  ALL echo
  COMMAND make all
  DEPENDS ${CMAKE_CURRENT_BINARY_DIR}/src/Makefile
  WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/src
  COMMENT "Running make all in ${CMAKE_CURRENT_BINARY_DIR}/src"
)

## Run make install
ADD_CUSTOM_COMMAND(
  OUTPUT  ${CMAKE_CURRENT_BINARY_DIR}/installdir
  COMMAND make
  ARGS    install
  DEPENDS ${CMAKE_CURRENT_BINARY_DIR}/src/Makefile
  WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/src
  COMMENT "Running make install in ${CMAKE_CURRENT_BINARY_DIR}/src"
)
ADD_CUSTOM_TARGET(makeinstall  ALL echo
  DEPENDS ${CMAKE_CURRENT_BINARY_DIR}/installdir
)

ADD_CUSTOM_COMMAND(
  OUTPUT  ${CMAKE_CURRENT_BINARY_DIR}/installdir/share/doc/${PROJECT_NAME}-${VERSION_STR}/LICENSE
  COMMAND ${CMAKE_COMMAND}
  ARGS    -E copy ${CMAKE_CURRENT_BINARY_DIR}/${LICENSE_FILE}
          ${CMAKE_CURRENT_BINARY_DIR}/installdir/share/doc/${PROJECT_NAME}-${VERSION_STR}/LICENSE
  DEPENDS ${CMAKE_CURRENT_BINARY_DIR}/${LICENSE_FILE}
  COMMENT "Copying ${PROJECT_NAME}-${VERSION_STR} license"
)
ADD_CUSTOM_TARGET(copylicense  ALL echo
  DEPENDS ${CMAKE_CURRENT_BINARY_DIR}/installdir/share/doc/${PROJECT_NAME}-${VERSION_STR}/LICENSE
)

ADD_CUSTOM_TARGET(build-${PROJECT_NAME}  ALL echo
  COMMAND mkdir -p ${CMAKE_CURRENT_BINARY_DIR}/installdir/lib/python
  COMMAND mv    ${CMAKE_CURRENT_BINARY_DIR}/installdir/lib/python${PYTHON_VERSION}/site-packages
                     ${CMAKE_CURRENT_BINARY_DIR}/installdir/lib/python/kusu
  COMMAND cp    -rf ${CMAKE_CURRENT_BINARY_DIR}/installdir/* ${KUSU_ROOT}/.
  COMMAND rm -rf ${CMAKE_CURRENT_BINARY_DIR}/installdir
  COMMENT "Copying files to ${KUSU_LIB}/python/kusu"
)

ADD_DEPENDENCIES(build-${PROJECT_NAME} configure makeall makeinstall copylicense)
