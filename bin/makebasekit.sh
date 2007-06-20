#!${BASH_EXE}

CURDIR=$PWD
echo "Making Kusu NodeInstaller patchfiles.."
${CMAKE_CURRENT_BINARY_DIR}/bin/makepatchfiles.sh ${CMAKE_CURRENT_BINARY_DIR}/src/kits/base

if [ ! $? -eq 0 ]; then
	echo "Failure trying to make the Base Kit!"
	exit 2
fi

cd ${CMAKE_CURRENT_BINARY_DIR}/src/kits/base
echo "Making the Base Kit.."
make
echo "Moving kit-*.iso to $CURDIR."
mv -f kit-*.iso $CURDIR
echo "Done."
exit 0



