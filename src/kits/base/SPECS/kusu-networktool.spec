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
# $Id: spec.tmpl 1545 2007-06-22 10:47:02Z najib $
#

%define subversion 2

Summary: kusu-networktool module runtime
Name: kusu-networktool
Version: 1.1
Release: 1
License: GPLv2
Group: System Environment/Base
Vendor: Platform Computing Inc.
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
BuildArch: noarch
AutoReq: no
Source: %{name}-%{version}.%{subversion}.tar.gz
BuildRequires: python

%description
This package installs the kusu-networktool module runtime.

%prep
%setup -n %{name} -q

%build

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT/opt/kusu/bin
install bin/udhcpc.script $RPM_BUILD_ROOT/opt/kusu/bin
install -d $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/networktool
install lib/__init__.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/networktool/
install lib/networktool.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/networktool/
install -d $RPM_BUILD_ROOT/opt/kusu/share/doc/networktool-5.0
install doc/LICENSE $RPM_BUILD_ROOT/opt/kusu/share/doc/networktool-5.0

%pre

%post

%preun

%postun

%clean
rm -rf $RPM_BUILD_ROOT

%files
/opt/kusu/bin/udhcpc.script
%dir /opt/kusu/lib/python/kusu/networktool
%dir /opt/kusu/lib/python/kusu/networktool/__init__.py*
%dir /opt/kusu/lib/python/kusu/networktool/networktool.py*
%dir /opt/kusu/share/doc/networktool-5.0
%doc /opt/kusu/share/doc/networktool-5.0/LICENSE

%changelog
* Mon Oct 13 2008 Tsai Li Ming <ltsai@osgdc.org> 1.0-1
- Sync with OCS (r1609)
- Initial 1.0 release

