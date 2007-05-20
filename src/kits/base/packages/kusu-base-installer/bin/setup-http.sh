#!/bin/sh

# This code creates the Apache directories and config files

if [ ! -d /var/www/html ]; then
    echo "Apache is not installed.  Cannot find: /var/www/html"
    exit
fi

if [ ! -d /repo/repos ] ; then
    mkdir -p /repo/repos
fi
chgrp -R apache /repo/repos

if [ ! -d /opt/ocs/cfm ] ; then
    mkdir -p /opt/ocs/cfm
    chgrp -R apache /opt/ocs/cfm
fi

cd /var/www/html
ln -s /opt/ocs/cfm cfm
ln -s /repo/repos repos
ln -s /repo/images images

# Generate ocs.conf file
if [ -f dbreport.py ] ; then
    ./dbreport.py apache_ocs > /etc/httpd/conf.d/ocs.conf
    service httpd restart
else
    echo "Cannot run: ./dbreport.py apache_ocs > /etc/httpd/conf.d/ocs.conf"
    echo "Run it manually"
fi

if [ -f nodeboot.cgi.py ] ; then
    cp nodeboot.cgi.py /repo/repos/nodeboot.cgi
else
    echo "Cannot run: cp nodeboot.cgi.py /repo/repos/nodeboot.cgi"
    echo "Run it manually"
fi

