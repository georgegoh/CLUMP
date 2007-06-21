#!${BASH_EXE}
# $Id: makebasekitiso.sh 293 2007-04-13 04:50:44Z hirwan $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

if [ -f ${KUSU_ROOT}/bin/kusudevenv.sh ]; then
  source ${KUSU_ROOT}/bin/kusudevenv.sh
fi
${CMAKE_CURRENT_BINARY_DIR}/bin/makepatchfiles.sh ${CMAKE_CURRENT_BINARY_DIR}/src/kits/base
if [ ! $? -eq 0 ]; then
	echo "Failure making the NodeInstaller patchfiles!"
	exit 2
fi
cd ${CMAKE_CURRENT_BINARY_DIR}/src/kits/base
make
ec=$?
if [ $ec != "0" ]
then
  exit $ec
fi
