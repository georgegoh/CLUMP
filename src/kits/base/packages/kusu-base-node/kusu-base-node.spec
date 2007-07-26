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
License: Copyright 2007 Platform Computing Inc
Group: System Environment/Base
Vendor: Platform Computing Inc
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
/sbin/chkconfig --add cfmd > /dev/null 2>&1
/sbin/chkconfig cfmd on > /dev/null 2>&1
if [ -d /etc/cfm/Installer/etc ]; then
	ln -s /etc/passwd /etc/cfm/Installer/etc/passwd
	ln -s /etc/shadow /etc/cfm/Installer/etc/shadow
	ln -s /etc/group /etc/cfm/Installer/etc/group
	ln -s /etc/hosts /etc/cfm/Installer/etc/hosts
	echo "# Appended by CFM" > /etc/cfm/Installer/etc/fstab.append
	echo "# Entries below this come from the CFM's fstab.append" >> /etc/cfm/Installer/etc/fstab.append
fi
if [ -d /etc/cfm/Compute/etc ]; then
	ln -s /etc/passwd /etc/cfm/Compute/etc/passwd
	ln -s /etc/shadow /etc/cfm/Compute/etc/shadow
	ln -s /etc/group /etc/cfm/Compute/etc/group
	ln -s /etc/hosts /etc/cfm/Compute/etc/hosts
	echo "# Appended by CFM" > /etc/cfm/Compute/etc/fstab.append
	echo "# Entries below this come from the CFM's fstab.append" >> /etc/cfm/Compute/etc/fstab.append
fi
if [ -d /etc/cfm/Compute-diskless/etc ]; then
	ln -s /etc/passwd /etc/cfm/Compute-diskless/etc/passwd
	ln -s /etc/shadow /etc/cfm/Compute-diskless/etc/shadow
	ln -s /etc/group /etc/cfm/Compute-diskless/etc/group
	ln -s /etc/hosts /etc/cfm/Compute-diskless/etc/hosts
	echo "# Appended by CFM" > /etc/cfm/Compute-diskless/etc/fstab.append
	echo "# Entries below this come from the CFM's fstab.append" >> /etc/cfm/Compute-diskless/etc/fstab.append
fi
if [ -d /etc/cfm/Compute-disked/etc ]; then
	ln -s /etc/passwd /etc/cfm/Compute-disked/etc/passwd
	ln -s /etc/shadow /etc/cfm/Compute-disked/etc/shadow
	ln -s /etc/group /etc/cfm/Compute-disked/etc/group
	ln -s /etc/hosts /etc/cfm/Compute-disked/etc/hosts
	echo "# Appended by CFM" > /etc/cfm/Compute-disked/etc/fstab.append
	echo "# Entries below this come from the CFM's fstab.append" >> /etc/cfm/Compute-disked/etc/fstab.append
fi

 
%preun
##
## PREUN
##
if [ $1 = 0 ]; then # during removal of a pkg
    /sbin/chkconfig --del kusu > /dev/null 2>&1
    /sbin/chkconfig --del cfmd > /dev/null 2>&1
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
/etc/init.d/cfmd
/etc/rc.kusu.d/
/opt/kusu/*
%exclude /opt/kusu/lib/python/kusu/*.py?
/etc/rc.kusu.custom.d/
/etc/cfm/*


##
## CLEAN
##
%clean
/bin/rm -rf $RPM_BUILD_ROOT


