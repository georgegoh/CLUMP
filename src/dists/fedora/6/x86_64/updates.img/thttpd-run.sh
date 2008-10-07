#!/bin/sh

# thttpd has been unreliable lately; don't let it give up!
while [ 1 ]
do
    /tmp/updates/usr/sbin/thttpd -D -nor -nos -p 80 -h 127.0.0.1 -u root -d /tmp/www -l /dev/null
done
