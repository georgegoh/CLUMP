#!${BASH_EXE}

CURDIR=$PWD
echo "Making Kusu NodeInstaller patchfiles.."
${CMAKE_CURRENT_BINARY_DIR}/bin/makepatchfiles.sh ${CMAKE_CURRENT_BINARY_DIR}/src/kits/base
cd ${CMAKE_CURRENT_BINARY_DIR}/src/kits/base
echo "Making the Base Kit.."
make
mv -f kit-base-*.noarch.iso $CURDIR
echo "Created Kusu Base Kit in $CURDIR."



