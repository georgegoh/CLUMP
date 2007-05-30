# $Id: PatchSource.camke 293 2007-04-13 04:50:44Z hirwan $
#search for .patch files in custom dir
#apply patch 

FIND_PROGRAM(PATCH
  NAMES patch
  PATHS
  /bin
  /usr/bin
  /usr/local/bin
)

IF(PATCH)
  FILE(GLOB PATCHFILES "${CMAKE_CURRENT_BINARY_DIR}/custom/${VERSION_STR}/*.patch")
  IF(PATCHFILES)
    FOREACH(patchfile ${PATCHFILES})
      EXEC_PROGRAM(${PATCH} ${CMAKE_CURRENT_BINARY_DIR}/src
        ARGS -p0 < ${patchfile}
      )
    ENDFOREACH(patchfile)
  ENDIF(PATCHFILES)
ELSE(PATCH)
  MESSAGE( SEND_ERROR "patch executable not found. Skip building ${PROJECT_NAME}.")
ENDIF(PATCH)
