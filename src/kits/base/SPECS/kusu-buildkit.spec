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
Version: 0.10
Release: 5
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
* Thu Aug 21 2008 Mark Black <mblack@platform.com> 5.1-5
- Reving tar file for RH

* Thu Mar 27 2008 Mike Frisch <mfrisch@platform.com> 5.1-4
- Remove AutoReq tag at the request of Red Hat

* Thu Mar 20 2008 Mike Frisch <mfrisch@platform.com> 5.1-3
- Change location of Kusu installer lock file in templates

* Mon Jan 2 2008 Shawn Starr <sstarr@platform.com> 5.1-0
- Initial release
