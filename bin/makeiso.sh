#!/bin/sh

source $WORKSPACE/kusuroot/bin/kusudevenv.sh
boot-media-tool make-patch kususrc=/data/sandbox/kusu/trunk/ os=fedora version=6 arch=i386 patch=updates.img
boot-media-tool make-iso kususrc=/data/sandbox/kusu/trunk/ source=/mnt arch=i386 iso=/root/kusu.iso  patch=updates.img
