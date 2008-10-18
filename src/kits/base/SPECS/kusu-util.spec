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

%define subversion 5

Summary: kusu-util module runtime
Name: kusu-util
Version: 1.1
Release: 1
License: GPLv2
Group: System Environment/Base
Vendor: Platform Computing Inc.
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
BuildArch: noarch
Source: %{name}-%{version}.%{subversion}.tar.gz
BuildRequires: python

%description
This package installs the kusu-util module runtime.

%prep
%setup -q -n %{name}

%build

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT/opt/kusu/etc

# Documentation
install -d $RPM_BUILD_ROOT/opt/kusu/share/doc/util-%{version}
install doc/COPYING $RPM_BUILD_ROOT/opt/kusu/share/doc/util-%{version}
install doc/README-log.txt $RPM_BUILD_ROOT/opt/kusu/share/doc/util-%{version}

# Other files

install etc/distro.conf $RPM_BUILD_ROOT/opt/kusu/etc/

install -d $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/util
install lib/*.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/util/

install -d $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/util/distro

install lib/distro/*.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/util/distro/

%pre

%post

%preun

%postun

%clean
rm -rf $RPM_BUILD_ROOT

%files
/opt/kusu/etc/distro.conf
/opt/kusu/lib/python/kusu/util/*
%dir /opt/kusu/share/doc/util-%{version}
%doc /opt/kusu/share/doc/util-%{version}/COPYING
%doc /opt/kusu/share/doc/util-%{version}/README-log.txt

%changelog
* Mon Oct 13 2008 Tsai Li Ming <ltsai@osgdc.org> 1.0-1
- Sync with OCS (r1609)
- Initial 1.0 release

