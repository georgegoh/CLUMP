# $Id: CMakeLists.txt 275 2007-04-12 11:56:52Z hirwan $
# Configure
PROJECT(dhcp)
SET(LICENSE_FILE LICENSE)
SET(VERSION_STR 3.1.0a3)
SET(SRC_URL http://ftp.isc.org/isc/dhcp/${PROJECT_NAME}-${VERSION_STR}.tar.gz)
SET(KUSU_MODULE OFF) #Set to ON if this is a Kusu module else set to OFF.

SET(CONFIGURE_PATH ${CMAKE_CURRENT_BINARY_DIR}/src)
INCLUDE(ConfigureMakeInstall)

SET(KUSU_MODULE OFF)

ADD_DEPENDENCIES(build-${PROJECT_NAME} copy-license)
