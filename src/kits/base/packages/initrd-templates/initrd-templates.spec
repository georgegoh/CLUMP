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


Summary: Template Initial RAM disks for Image based installs
Name: initrd-templates
Version: 1.0
Release: 0
License: Copyright 2007 Platform Computing Corporation
Group: System Environment/Base
Vendor: Platform Computing Corporation
BuildArchitectures: noarch
Source: %{name}.tar.gz
Buildroot: /var/tmp/%{name}-buildroot

%description
This package contains the Kusu Base template initrd's.  These are
simply initrd's that have been built with the excellent buildroot
package.


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
/opt/kusu/initrds/*
/opt/kusu/etc/depmod.pl
/opt/kusu/etc/imageinit.py
/opt/kusu/etc/imageinit.sh



##
## CLEAN
##
%clean
/bin/rm -rf $RPM_BUILD_ROOT


