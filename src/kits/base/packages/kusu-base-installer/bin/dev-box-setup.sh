#!/bin/sh

echo "This script installs the packages necessary to develope OCS"

yum install mysql
yum install mysql-server
yum install dhcp
yum install xinetd
yum install tftp-server
yum install httpd
yum install python
yum install python-devel
yum install MySQL-python
yum install createrepo
yum install mod_python
