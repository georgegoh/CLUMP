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

%define subversion 4

Summary: Partition modules
Name: kusu-partitiontool
Version: 0.10
Release: 4
License: GPLv2
Group: System Environment/Base
Vendor: Project Kusu
BuildArch: noarch
Source: %{name}-%{version}.%{subversion}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-root
Requires: pyparted
URL: http://www.osgdc.org
BuildRequires: python

%description
This package contains python modules for handling partitions.

%prep
%setup -q -n %{name}

%build

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/partitiontool
install -d $RPM_BUILD_ROOT/opt/kusu/share/doc/partitiontool-%{version}

install -m644 lib/common.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/partitiontool
install -m644 lib/disk.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/partitiontool
install -m644 lib/filesystems.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/partitiontool
install -m644 lib/lvm202.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/partitiontool
install -m644 lib/lvm.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/partitiontool
install -m644 lib/nodes.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/partitiontool
install -m644 lib/partitiontool.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/partitiontool
install -m644 lib/__init__.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/partitiontool
install -m644 doc/COPYING $RPM_BUILD_ROOT/opt/kusu/share/doc/partitiontool-%{version}

%pre

%post

%preun

%postun

%files
/opt/kusu/lib/python/kusu/partitiontool/*

%doc /opt/kusu/share/doc/partitiontool-%{version}/COPYING

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Thu Aug 21 2008 Mark Black <mblack@platform.com> 5.1-4
- Reving tar file for RH

* Tue Jun 17 2008 Mike Frisch <mfrisch@platform.com> 5.1-3
- Start extent count at 0, and ignore ioctl failures (#110336)
- Installer fails to boot when the Dell UP is present (#108240)

* Thu Apr 3 2008 Mike Frisch <mfrisch@platform.com>
- Fixed partitioning related issues

* Mon Jan 2 2008 Shawn Starr <sstarr@platform.com>
- Initial release
