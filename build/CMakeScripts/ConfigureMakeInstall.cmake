## Run configure
ADD_CUSTOM_COMMAND(
  OUTPUT  ${CONFIGURE_PATH}/Makefile
  COMMAND ./configure
  ARGS    --prefix=${CONFIGURE_PATH}/installdir ${CONFIGURE_ARGS}
  DEPENDS ${CONFIGURE_PATH}/configure
  WORKING_DIRECTORY ${CONFIGURE_PATH}
  COMMENT "Running configure --prefix=${CONFIGURE_PATH}/installdir ${CONFIGURE_ARGS} in ${CONFIGURE_PATH}"
)
ADD_CUSTOM_TARGET(configure
  DEPENDS ${CONFIGURE_PATH}/Makefile
)

## Run make
ADD_CUSTOM_TARGET(make-all
  COMMAND make all
  DEPENDS ${CONFIGURE_PATH}/Makefile
  WORKING_DIRECTORY ${CONFIGURE_PATH}
  COMMENT "Running make all in ${CONFIGURE_PATH}"
)

## Run make install
ADD_CUSTOM_COMMAND(
  OUTPUT  ${CONFIGURE_PATH}/installdir
  COMMAND make
  ARGS    install
  DEPENDS ${CONFIGURE_PATH}/Makefile
  WORKING_DIRECTORY ${CONFIGURE_PATH}
  COMMENT "Running make install in ${CONFIGURE_PATH}"
)
ADD_CUSTOM_TARGET(make-install
  DEPENDS ${CONFIGURE_PATH}/installdir
)

ADD_DEPENDENCIES(make-install make-all)

ADD_CUSTOM_COMMAND(
  OUTPUT  ${CONFIGURE_PATH}/installdir/share/doc/${PROJECT_NAME}-${VERSION_STR}/LICENSE
  COMMAND ${CMAKE_COMMAND}
  ARGS    -E copy ${CONFIGURE_PATH}/${LICENSE_FILE}
          ${CONFIGURE_PATH}/installdir/share/doc/${PROJECT_NAME}-${VERSION_STR}/LICENSE
  DEPENDS ${CONFIGURE_PATH}/${LICENSE_FILE}
  COMMENT "Copying ${PROJECT_NAME}-${VERSION_STR} license"
)
ADD_CUSTOM_TARGET(copy-license
  DEPENDS ${CONFIGURE_PATH}/installdir/share/doc/${PROJECT_NAME}-${VERSION_STR}/LICENSE
)

SET(SETUPPY_PATH ${CONFIGURE_PATH})
SET(KUSU_MODULE OFF)

ADD_CUSTOM_TARGET(build-${PROJECT_NAME}  ALL echo
  COMMAND ${SETUPPY_PATH}/kusuinstall.sh
  COMMENT "Copying files to ${KUSU_LIB}/python"
)

ADD_DEPENDENCIES(build-${PROJECT_NAME} make-install copy-license)

CONFIGURE_FILE(${CMAKE_MODULE_PATH}/kusuinstall.sh
          ${SETUPPY_PATH}/kusuinstall.sh)
EXEC_PROGRAM(chmod ${SETUPPY_PATH}
  ARGS a+rx ${SETUPPY_PATH}/kusuinstall.sh
)
