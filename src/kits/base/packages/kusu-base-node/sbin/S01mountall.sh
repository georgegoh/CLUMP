#!/bin/sh

# /etc/fstab should have an entry for /shared by this time.
# So before we do 'mount -a', create the /shared directory.
mkdir /shared

mount -a
