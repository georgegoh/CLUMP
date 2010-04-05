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
# $Id: initrd-templates.sles.spec 3135 2009-10-23 05:42:58Z ltsai $
# 

%define initrd_builddir %name
%define ARCH %(echo `arch` | sed 's/i[3456]86/i386/')

Summary: Template Initial RAM disks for Image based installs
Name: initrd-templates
Version: 2.0
Release: 1
Epoch: 1
License: LGPL/GPL
Group: System Environment/Base
Vendor: Platform Computing Inc
BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Requires: kusu-base-installer kusu-base-node
BuildRequires: yum
Source: initrd-templates-%{version}.%{release}.tar.gz

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

touch $RPM_BUILD_ROOT/opt/kusu/initrds/rootfs.%{ARCH}.cpio.gz

mkdir -p $RPM_BUILD_ROOT/opt/kusu/lib/initrd

# Copy overlay directory
mkdir -p $RPM_BUILD_ROOT/opt/kusu/share/initrd-templates
cp -ar --parents overlay/ $RPM_BUILD_ROOT/opt/kusu/share/initrd-templates

install mkinitrd-templates $RPM_BUILD_ROOT/opt/kusu/sbin

%files
%dir /opt/kusu/initrds
%ghost /opt/kusu/initrds/rootfs.%{ARCH}.cpio.gz
/opt/kusu/etc/depmod.pl
/opt/kusu/etc/imageinit.py*
/opt/kusu/etc/imageinit.sh
%config(noreplace) /opt/kusu/etc/templates/mkinitrd-templates.tmpl
/opt/kusu/sbin/mkinitrd-templates
/opt/kusu/share/initrd-templates

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Tue Jun 16 2009 Chew Meng Kuan <mkchew@platform.com> 5.3-1
- Bump version to 5.3 for PCM 1.2.1.

* Mon Oct 13 2008 Tsai Li Ming <ltsai@osgdc.org> 1.0-1
- Sync with OCS (r1609)
- Initial 1.0 release

