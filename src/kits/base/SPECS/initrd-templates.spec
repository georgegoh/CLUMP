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

%define subversion 5
%define initrd_builddir %name

Summary: Template Initial RAM disks for Image based installs
Name: initrd-templates
Version: 0.10
Release: 9
License: LGPL/GPL
Group: System Environment/Base
Vendor: Platform Computing Inc
BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Requires: kusu-base-installer kusu-base-node
BuildRequires: yum
Source: initrd-templates-%{version}.%{subversion}.tar.gz

%description
This package contains the script to generate Kusu base template initrds.

%prep
%setup -q -n initrd-templates

%build

%pre

%post

%preun

%postun

%install
rm -rf $RPM_BUILD_ROOT

mkdir -p $RPM_BUILD_ROOT/opt/kusu/etc
mkdir -p $RPM_BUILD_ROOT/opt/kusu/sbin

cp -ar etc/* $RPM_BUILD_ROOT/opt/kusu/etc

mkdir -p $RPM_BUILD_ROOT/opt/kusu/initrds

touch $RPM_BUILD_ROOT/opt/kusu/initrds/rootfs.x86_64.cpio.gz

mkdir -p $RPM_BUILD_ROOT/opt/kusu/lib/initrd

# Copy overlay directory
mkdir -p $RPM_BUILD_ROOT/opt/kusu/share/initrd-templates
cp -ar --parents overlay/ $RPM_BUILD_ROOT/opt/kusu/share/initrd-templates

install mkinitrd-templates $RPM_BUILD_ROOT/opt/kusu/sbin

install -d $RPM_BUILD_ROOT/etc/rc.kusu.d
install S02initrd-templates.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/

%files
%dir /opt/kusu/initrds
%ghost /opt/kusu/initrds/rootfs.x86_64.cpio.gz
/opt/kusu/etc/depmod.pl
/opt/kusu/etc/imageinit.py
/opt/kusu/etc/imageinit.pyc
/opt/kusu/etc/imageinit.pyo
/opt/kusu/etc/imageinit.sh
/opt/kusu/sbin/mkinitrd-templates
/opt/kusu/share/initrd-templates
/etc/rc.kusu.d/S02initrd-templates.rc.py*

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Thu Aug 21 2008 Mark Black <mblack@platform.com> 5.1-9
- Reving tar file for RH

* Thu Jul 31 2008 Mark Black <mblack@platform.com> 5.1-8
- Reset version/revision after switching build to trunk

* Mon Jun 2 2008 Mike Frisch <mfrisch@platform.com> 5.1-7
- Add missing copyright

* Wed May 28 2008 Mike Frisch <mfrisch@platform.com> 5.1-6
- Remove mkinitrd-templates from post section (#109455)

* Thu May 15 2008 Mike Frisch <mfrisch@platform.com> 5.1-5
- Use RH system files to generate initrd (#108335)
