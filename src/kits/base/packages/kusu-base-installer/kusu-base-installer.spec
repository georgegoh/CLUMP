# Copyright (C) 2007 Platform Computing Corporation
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


Summary: Platform Rocks rolls documentation
Name: kusu-base-installer
Version: 1.0
Release: 0
License: GPLv2
Group: System Environment/Base
Vendor: Platform Computing Corporation
BuildArchitectures: noarch
Source: %{name}.tar.gz
Buildroot: /var/tmp/%{name}-buildroot

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
/opt/kusu/*
/etc/rc.kusu.d/S01KusuSetup
%defattr(-,apache,apache)
/depot/repos/nodeboot.cgi
/depot/kits
/depot/images
/depot/repos/custom_scripts
/opt/kusu/cfm/changedfiles.lst

##
## CLEAN
##
%clean
/bin/rm -rf $RPM_BUILD_ROOT


