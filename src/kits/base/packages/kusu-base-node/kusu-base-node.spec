# $Id$
#
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

%define _approot /opt/kusu

Summary: Base Kit for Nodes
Name: kusu-base-node
Version: 1.0
Release: 0
License: Copyright 2007 Platform Computing Corporation
Group: System Environment/Base
Vendor: Platform Computing Corporation
# BuildArchitectures: noarch
Source: %{name}.tar.gz
Buildroot: /var/tmp/%{name}-buildroot
Requires: coreutils 
Requires: chkconfig

%description
This package contains the Kusu Base kit part for nodes.

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
%build
cd %{name}
echo "Root = $RPM_BUILD_ROOT"
make ROOT=$RPM_BUILD_ROOT cfmd


##
## PRE
##
## %pre
## Skipping this because we are not starting with a tar file


##
## POST
##
%post
/sbin/chkconfig --add kusu > /dev/null 2>&1
/sbin/chkconfig kusu on > /dev/null 2>&1
 
%preun
##
## PREUN
##
if [ $1 = 0 ]; then # during removal of a pkg
    /sbin/chkconfig --del kusu > /dev/null 2>&1
fi


##
## POSTUN
##
%postun


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
/etc/init.d/kusu
/etc/rc.kusu.d/
/opt/kusu/*
%exclude /opt/kusu/lib/python/kusu/*.py?
/etc/rc.kusu.custom.d/


##
## CLEAN
##
%clean
/bin/rm -rf $RPM_BUILD_ROOT


