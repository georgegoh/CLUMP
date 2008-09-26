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

%define subversion 2

Summary: Kusu UI snack widget extensions
Name: kusu-ui
Version: 0.10
Release: 4
License: GPLv2
Group: System Environment/Base
Vendor: Project Kusu
BuildArch: noarch
Source: %{name}-%{version}.%{subversion}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
URL: http://www.osgdc.org
BuildRequires: python

%description
This package contains the Kusu UI snack widget extensions

%prep
%setup -q -n %{name}

%build

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/ui/text
install -d $RPM_BUILD_ROOT/opt/kusu/share/doc/ui-%{version}
install -d $RPM_BUILD_ROOT/opt/kusu/share/examples/ui

install -m644 lib/text/kusuwidgets.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/ui/text
install -m644 lib/text/navigator.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/ui/text
install -m644 lib/text/screenfactory.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/ui/text
install -m644 lib/text/__init__.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/ui
install -m644 lib/text/__init__.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/ui/text
install -m644 doc/COPYING $RPM_BUILD_ROOT/opt/kusu/share/doc/ui-%{version}
install -m644 bin/navigator-text $RPM_BUILD_ROOT/opt/kusu/share/examples/ui

%pre

%post

%preun

%postun

%files
/opt/kusu/lib/python/kusu/ui/*
/opt/kusu/share/examples/ui/navigator-text
%doc /opt/kusu/share/doc/ui-%{version}/COPYING

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Thu Aug 21 2008 Mark Black <mblack@platform.com> 5.1-4
- Reving tar file for RH

* Thu Jul 31 2008 Mark Black <mblack@platform.com> 5.1-3
- Reset version/revision after switching build to trunk

* Thu Apr 3 2008 Mike Frisch <mfrisch@platform.com>
- Fixed partitioning related issues

* Mon Jan 2 2008 Shawn Starr <sstarr@platform.com>
- Initial release
