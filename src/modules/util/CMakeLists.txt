# $Id$
PROJECT(util)

SET(SETUPPY_BUILD_ARGS build)
SET(SETUPPY_INSTALL_ARGS install --prefix=${CMAKE_CURRENT_BINARY_DIR}/installdir)
SET(SETUPPY_SDIST_ARGS sdist)
SET(SETUPPY_BDIST_ARGS bdist)

ADD_CUSTOM_COMMAND(
        OUTPUT  ${CMAKE_CURRENT_BINARY_DIR}/build
        COMMAND ${PYTHON_EXECUTABLE}
        ARGS    setup.py ${SETUPPY_BUILD_ARGS}
        DEPENDS setup.py
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
        COMMENT "Running python setup.py ${SETUPPY_BUILD_ARGS} in ${CMAKE_CURRENT_BINARY_DIR}"
)
ADD_CUSTOM_TARGET(buildsrc  ALL echo
  DEPENDS ${CMAKE_CURRENT_BINARY_DIR}/build
)

ADD_CUSTOM_COMMAND(
        OUTPUT  ${CMAKE_CURRENT_BINARY_DIR}/installdir
        COMMAND ${PYTHON_EXECUTABLE}
        ARGS    setup.py ${SETUPPY_INSTALL_ARGS}
        DEPENDS setup.py
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
        COMMENT "Running python setup.py ${SETUPPY_INSTALL_ARGS} in ${CMAKE_CURRENT_BINARY_DIR}"
)
ADD_CUSTOM_TARGET(installsrc  ALL echo
  DEPENDS ${CMAKE_CURRENT_BINARY_DIR}/installdir
)

ADD_CUSTOM_TARGET(build-${PROJECT_NAME} ALL echo
  COMMAND mkdir -p ${CMAKE_CURRENT_BINARY_DIR}/installdir/lib/python
  COMMAND mv    ${CMAKE_CURRENT_BINARY_DIR}/installdir/lib/python${PYTHON_VERSION}/site-packages
                     ${CMAKE_CURRENT_BINARY_DIR}/installdir/lib/python/kusu
  COMMAND cp    -rf ${CMAKE_CURRENT_BINARY_DIR}/installdir/* ${KUSU_ROOT}/.
  COMMAND rm -rf ${CMAKE_CURRENT_BINARY_DIR}/installdir
  COMMENT "Copying files to ${KUSU_LIB}/python/kusu"
)

ADD_DEPENDENCIES(build-${PROJECT_NAME} buildsrc installsrc)
