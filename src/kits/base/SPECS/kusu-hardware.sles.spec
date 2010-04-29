# $Id: kusu-hardware.sles.spec 3135 2009-10-23 05:42:58Z ltsai $
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

Summary: Hardware module
Name: kusu-hardware
Version: 2.1
Release: 1
Epoch: 1
License: GPLv2
Group: System Environment/Base
Vendor: Project Kusu
BuildArch: noarch
Source: %{name}-%{version}.%{release}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-root
URL: http://www.osgdc.org
BuildRequires: python
Requires: pciutils-ids
Requires: usbutils

%description
This package contains libraries for probing hardware.

%prep
%setup -q -n %{name}

%build

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/hardware
install -d $RPM_BUILD_ROOT/opt/kusu/share/doc/hardware-%{version}

install -m644 lib/drive.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/hardware
install -m644 lib/net.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/hardware
install -m644 lib/pci.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/hardware
install -m644 lib/probe.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/hardware
install -m644 lib/__init__.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/hardware
install -m644 doc/COPYING $RPM_BUILD_ROOT/opt/kusu/share/doc/hardware-%{version}

%pre

%post

%preun

%postun

%files
/opt/kusu/lib/python/kusu/hardware/*

%doc /opt/kusu/share/doc/hardware-%{version}/COPYING

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Tue Jun 16 2009 Chew Meng Kuan <mkchew@platform.com> 5.3-1
- Bump version to 5.3 for PCM 1.2.1.

* Mon Oct 13 2008 Tsai Li Ming <ltsai@osgdc.org> 1.0-1
- Sync with OCS (r1609)
- Initial 1.0 release

