# Copyright (C) 2007 Platform Computing Inc
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.
# 	
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
#
# 
# $Id$
# 


Summary: Kusu Base Installer
Name: kusu-base-installer
Version: 1.0
Release: 0
License: GPLv2
Group: System Environment/Base
Vendor: Platform Computing Inc
BuildArchitectures: noarch
Source: %{name}.tar.gz
Buildroot: /var/tmp/%{name}-buildroot
Requires: openssl
Requires: httpd

%description
This package contains the Kusu installer node tools.

##
## PREP
##
## %prep
## 
## Skipping this because we are not starting with a tar file

##
## SETUP
##
## %setup
## Skipping this because we are not starting with a tar file

##
## BUILD
##
## %build
## Skipping this because we are not starting with a tar file

##
## PRE
##
## %pre
## Skipping this because we are not starting with a tar file


##
## POST
##
%post
if [ ! -f /etc/cfm/.cfmsecret ] ; then
	# Contact Mark prior to touching this!
	if [ ! -d /etc/cfm ] ; then
		mkdir /etc/cfm
	fi
	umask 077
	openssl rand -base64 32 > /etc/cfm/.cfmsecret
	chmod 400 /etc/cfm/.cfmsecret
	chown apache /etc/cfm/.cfmsecret
fi

##
## PREUN
##
%preun

##
## POSTUN
##
%postun
if [ "$1" -eq 0 ] ; then
	if [ -f /etc/cfm/.cfmsecret ] ; then
		rm -rf /etc/cfm/.cfmsecret
	fi
fi


##
## INSTALL
##
%install
cd %{name}
echo "Root = $RPM_BUILD_ROOT"
make ROOT=$RPM_BUILD_ROOT install


##
## FILES
##
%files
%defattr(-,root,root)
/opt/kusu/*
%exclude /opt/kusu/lib/python/kusu/*.py?
%exclude /opt/kusu/lib/python/kusu/ngedit/*.py?
%exclude /opt/kusu/lib/python/kusu/ui/text/*.py?
%exclude /etc/rc.kusu.d/*.py?
#%exclude /opt/kusu/lib/python/kusu/ui/*.py?
/etc/rc.kusu.d/*.py
%defattr(-,apache,apache)
/depot/repos/nodeboot.cgi
/depot/kits
/depot/images
/depot/repos/custom_scripts
/opt/kusu/cfm/changedfiles.lst
#%defattr(400,apache,apache)
#/opt/kusu/etc/db.passwd

##
## CLEAN
##
%clean
/bin/rm -rf $RPM_BUILD_ROOT

