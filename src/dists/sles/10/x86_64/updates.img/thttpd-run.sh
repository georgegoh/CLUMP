#!/bin/sh

# thttpd has been unreliable lately; don't let it give up!
while [ 1 ]
do
    /mounts/instsys/usr/sbin/thttpd -D -nor -nos -p 80 -h 127.0.0.1 -u root -d /kusu/mnt/depot -l /dev/null
done
