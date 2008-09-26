# $Id$
#
# Copyright (C) 2008 Platform Computing Inc
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

%define subversion 1

Summary: Network configuration tool for sysadmins
Name: kusu-net-tool
Version: 0.10
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
This package contains a tool for managing network settings.

%prep
%setup -q -n %{name}

%build

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT/opt/kusu/sbin
install -d $RPM_BUILD_ROOT/opt/kusu/share/doc/kusu-net-tool-%{version}

install -m755 sbin/kusu-net-tool.py $RPM_BUILD_ROOT/opt/kusu/sbin/kusu-net-tool
install -m644 doc/COPYING $RPM_BUILD_ROOT/opt/kusu/share/doc/kusu-net-tool-%{version}

%pre

%post

%preun

%postun

%files
/opt/kusu/sbin/kusu-net-tool
%doc /opt/kusu/share/doc/kusu-net-tool-%{version}/COPYING

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Wed Jun 6 2008 Mike Frisch <mfrisch@platform.com> 5.1-1
- Initial release
