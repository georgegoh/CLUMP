#!${BASH_EXE}
# $Id$
#
# Kusu specific environment script
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.
#

export KUSU_ROOT=${KUSU_INSTALL_PREFIX}
export PYTHONPATH=${PYTHONPATH}
export PATH=$KUSU_ROOT/bin:$KUSU_ROOT/sbin:$PATH
export KUSU_DIST=${KUSU_BUILD_DIST}
export KUSU_DISTVER=${KUSU_BUILD_DISTVER}
export KUSU_DIST_ARCH=${KUSU_BUILD_ARCH}
export KUSU_TMP=${KUSU_TMP}
export KUSU_LOGLEVEL=${KUSU_LOGLEVEL}
export KUSU_LOGFILE=${KUSU_LOGFILE}

