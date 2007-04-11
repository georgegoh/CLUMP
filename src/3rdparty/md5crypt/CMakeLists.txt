# $Id$
# Configure
PROJECT(md5crypt)
SET(LICENSE_FILE src/COPYING)
#SET(VERSION_STR 2.2)
SET(SRC_UR http://sabren.net/code/python/crypt/md5crypt.py)

# Build template



CONFIGURE_FILE(${LICENSE_FILE} ${KUSU_ROOT}/share/doc/${PROJECT_NAME}/LICENSE COPYONLY)
