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

Summary: Base Kit for Nodes
Name: kusu-base-node
Version: 1.0
Release: 0
License: Copyright 2007 Platform Computing Corporation
Group: System Environment/Base
Vendor: Platform Computing Corporation
BuildArchitectures: noarch
Source: %{name}.tar.gz
Buildroot: /var/tmp/%{name}-buildroot

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
if [ -e /etc/rc.local ]; then
	echo "# Kusu post install script runner" >> /etc/rc.local
        echo "if [ -x /etc/rc.kusu.sh ]; then" >> /etc/rc.local
	echo "    /etc/rc.kusu.sh" >> /etc/rc.local
	echo "fi" >> /etc/rc.local
fi
	

##
## PREUN
##
%preun

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
/etc/rc.kusu.sh
/etc/rc.kusu.d/
/opt/kusu/*
%exclude /opt/kusu/lib/python/kusu/*.py?
/etc/rc.kusu.custom.d/


##
## CLEAN
##
%clean
/bin/rm -rf $RPM_BUILD_ROOT


