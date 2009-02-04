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

Summary: Kit Management
Name: kusu-kitops
Version: 1.2
Release: 1
License: GPLv2
Group: System Environment/Base
Vendor: Project Kusu
BuildArch: noarch
Source: %{name}-%{version}.%{subversion}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-root
URL: http://www.osgdc.org
BuildRequires: python

%description
This package contains a tool for managing kits.

%prep
%setup -q -n %{name}

%build

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/kitops
install -d $RPM_BUILD_ROOT/opt/kusu/bin
install -d $RPM_BUILD_ROOT/opt/kusu/share/doc/kitops-%{version}

install -m755 bin/kitops $RPM_BUILD_ROOT/opt/kusu/bin
install -m644 lib/kitops.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/kitops
install -m644 lib/addkit_strategies.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/kitops
install -m644 lib/deletekit_strategies.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/kitops
install -m644 lib/package.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/kitops
install -m644 lib/__init__.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/kitops
install -m644 doc/COPYING $RPM_BUILD_ROOT/opt/kusu/share/doc/kitops-%{version}

%pre

%post

%preun

%postun

%files
/opt/kusu/lib/python/kusu/kitops/*
/opt/kusu/bin/kitops

%doc /opt/kusu/share/doc/kitops-%{version}/COPYING

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Mon Oct 13 2008 Tsai Li Ming <ltsai@osgdc.org> 1.0-1
- Sync with OCS (r1609)
- Initial 1.0 release

