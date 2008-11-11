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

%define subversion 3

Summary: Kit building for Kusu
Name: kusu-buildkit
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
Requires: mkisofs
Requires: rpm-build

%description
This package contains a tool to make kits for Kusu.

%prep
%setup -q -n %{name}

%build

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/buildkit
install -d $RPM_BUILD_ROOT/opt/kusu/bin
install -d $RPM_BUILD_ROOT/opt/kusu/etc/templates
install -d $RPM_BUILD_ROOT/opt/kusu/share/doc/buildkit-%{version}

install -m755 bin/buildkit $RPM_BUILD_ROOT/opt/kusu/bin
install -m644 lib/builder.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/buildkit
install -m644 lib/checker.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/buildkit
install -m644 lib/kitsource.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/buildkit
install -m644 lib/methods.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/buildkit
install -m644 lib/tool.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/buildkit
install -m644 lib/__init__.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/buildkit
install -m644 doc/COPYING $RPM_BUILD_ROOT/opt/kusu/share/doc/buildkit-%{version}
install -m644 doc/buildkit.txt $RPM_BUILD_ROOT/opt/kusu/share/doc/buildkit-%{version}
install -m644 etc/templates/*.tmpl $RPM_BUILD_ROOT/opt/kusu/etc/templates
%pre

%post

%preun

%postun

%files
/opt/kusu/lib/python/kusu/buildkit/*
/opt/kusu/bin/buildkit
/opt/kusu/etc/templates/*.tmpl

%doc /opt/kusu/share/doc/buildkit-%{version}/COPYING
%doc /opt/kusu/share/doc/buildkit-%{version}/buildkit.txt

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Mon Oct 13 2008 Tsai Li Ming <ltsai@osgdc.org> 1.0-1
- Sync with OCS (r1609)
- Initial 1.0 release

