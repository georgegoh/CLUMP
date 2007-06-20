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
mv -f kit-base-*.noarch.iso $CURDIR
echo "Created Kusu Base Kit in $CURDIR."
exit 0



