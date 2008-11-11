# Copyright (C) 2007 Platform Computing Inc.
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
# $Id$
#

%define subversion 6

Summary: kusu-nodeinstaller module runtime
Name: kusu-nodeinstaller
Version: 1.2
Release: 1
License: GPLv2
Group: System Environment/Base
Vendor: Platform Computing Inc.
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
AutoReq: no
Source: %{name}-%{version}.%{subversion}.tar.gz
Buildrequires: gcc, python, python-devel, patch
BuildArch: noarch

%description
This package installs the kusu-nodeinstaller module runtime.

%prep
%setup -n %{name} -q

%build

%install
%define _approot /opt/kusu
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/%{_approot}

install -d $RPM_BUILD_ROOT/%{_approot}/bin
install -m755 bin/updatestate $RPM_BUILD_ROOT/%{_approot}/bin
install -m755 bin/nodeinstaller $RPM_BUILD_ROOT/%{_approot}/bin

install -d $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/nodeinstaller
install -m644 lib/__init__.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/nodeinstaller
install -m644 lib/niifun.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/nodeinstaller
install -m644 lib/nodeinstall.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/nodeinstaller
install -m644 lib/partitionfilterchain.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/nodeinstaller
install -m644 lib/partition.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/nodeinstaller

%pre

%post

%preun

%postun

%clean
rm -rf %{buildroot}

%files
%{_approot}

%changelog
* Mon Oct 13 2008 Tsai Li Ming <ltsai@osgdc.org> 1.0-1
- Sync with OCS (r1609)
- Initial 1.0 release

