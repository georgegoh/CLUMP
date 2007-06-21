# $Id: PythonSetupPy.camke 293 2007-04-13 04:50:44Z hirwan $
#
# Kusu specific environment script
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.
#
## Python distutils Build template
IF(PYTHONINTERP_FOUND)
  ADD_CUSTOM_COMMAND(
          OUTPUT  ${SETUPPY_PATH}/build
          COMMAND ${PYTHON_EXECUTABLE}
          ARGS    setup.py build ${SETUPPY_BUILD_ARGS}
          DEPENDS ${SETUPPY_PATH}/setup.py
          WORKING_DIRECTORY ${SETUPPY_PATH}
          COMMENT "Running python setup.py build ${SETUPPY_BUILD_ARGS} in ${SETUPPY_PATH}"
  )
  ADD_CUSTOM_TARGET(setuppy-build
    DEPENDS ${SETUPPY_PATH}/build
  )
  
  ADD_CUSTOM_COMMAND(
          OUTPUT  ${SETUPPY_PATH}/installdir
          COMMAND ${PYTHON_EXECUTABLE}
          ARGS    setup.py install --prefix=${SETUPPY_PATH}/installdir ${SETUPPY_INSTALL_ARGS}
#                   --install-data=${SETUPPY_PATH}/installdir/share/doc/${PROJECT_NAME}-${VERSION_STR}
          DEPENDS ${SETUPPY_PATH}/build
          WORKING_DIRECTORY ${SETUPPY_PATH}
          COMMENT "Running python setup.py install ${SETUPPY_INSTALL_ARGS} in ${SETUPPY_PATH}"
  )
  ADD_CUSTOM_TARGET(setuppy-install
    DEPENDS ${SETUPPY_PATH}/installdir
  )
  
  ADD_CUSTOM_COMMAND(
          OUTPUT  ${SETUPPY_PATH}/dist/*.tar.gz
          COMMAND ${PYTHON_EXECUTABLE}
          ARGS    setup.py sdist ${SETUPPY_SDIST_ARGS}
          DEPENDS ${SETUPPY_PATH}/setup.py
          WORKING_DIRECTORY ${SETUPPY_PATH}
          COMMENT "Running python setup.py install ${SETUPPY_INSTALL_ARGS} in ${SETUPPY_PATH}"
  )
  ADD_CUSTOM_TARGET(setuppy-sdist
    DEPENDS ${SETUPPY_PATH}/dist/*.tar.gz
  )
  
  ADD_CUSTOM_COMMAND(
    OUTPUT  ${SETUPPY_PATH}/installdir/share/doc/LICENSE
    COMMAND ${CMAKE_COMMAND}
    ARGS    -E copy ${SETUPPY_PATH}/${LICENSE_FILE}
            ${SETUPPY_PATH}/installdir/share/doc/LICENSE
    DEPENDS ${SETUPPY_PATH}/${LICENSE_FILE}
    COMMENT "Copying ${PROJECT_NAME}-${VERSION_STR} license"
  )
  ADD_CUSTOM_TARGET(copy-license
    DEPENDS ${SETUPPY_PATH}/installdir/share/doc/LICENSE
  )

  IF(KUSU_MODULE)
    ADD_CUSTOM_TARGET(build-${PROJECT_NAME} ALL echo
      COMMAND ${SETUPPY_PATH}/kusuinstall.sh
      ${SETUPPY_PATH}/installdir
      COMMENT "Copying files to ${KUSU_LIB}/python/kusu"
    )
    
    IF(NOT EXISTS ${SETUPPY_PATH}/${LICENSE_FILE})
      CONFIGURE_FILE(${CMAKE_SOURCE_DIR}/docs/gpl.txt
                    ${SETUPPY_PATH}/${LICENSE_FILE} COPYONLY)
    ENDIF(NOT EXISTS ${SETUPPY_PATH}/${LICENSE_FILE})

  ELSE(KUSU_MODULE)
    ADD_CUSTOM_TARGET(build-${PROJECT_NAME} ALL echo
      COMMAND ${SETUPPY_PATH}/kusuinstall.sh
      DEPENDS ${SETUPPY_PATH}/installdir
      COMMENT "Copying files to ${KUSU_LIB}/python"
    )

  ENDIF(KUSU_MODULE)

  CONFIGURE_FILE(${CMAKE_MODULE_PATH}/kusuinstall.sh
          ${SETUPPY_PATH}/kusuinstall.sh)
  EXEC_PROGRAM(chmod ${SETUPPY_PATH}
    ARGS a+rx ${SETUPPY_PATH}/kusuinstall.sh
    OUTPUT_VARIABLE /dev/null
  )
  
  ADD_DEPENDENCIES(build-${PROJECT_NAME} setuppy-install copy-license)

  ADD_CUSTOM_TARGET(clean-${PROJECT_NAME}
    COMMAND rm -rf ${SETUPPY_PATH}/installdir
    COMMENT "Removing installdir from ${SETUPPY_PATH}"
  )

ELSE(PYTHONINTERP_FOUND)
  MESSAGE("python executable not found. Skip building ${PROJECT_NAME}.")
ENDIF(PYTHONINTERP_FOUND)