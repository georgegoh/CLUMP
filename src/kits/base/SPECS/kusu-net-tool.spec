#
# Copyright (C) 2008-2009 Platform Computing Inc
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

Summary: Network configuration tool for sysadmins
Name: kusu-net-tool
Version: 2.0
Release: 1
Epoch: 1
License: GPLv2
Group: System Environment/Base
Vendor: Project Kusu
BuildArch: noarch
Source: %{name}-%{version}.%{release}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-root
URL: http://www.osgdc.org/
BuildRequires: python

%description
This package contains a tool for managing network settings within PCM.

%prep
%setup -q -n %{name}

%build

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT/opt/kusu/sbin
install -d $RPM_BUILD_ROOT/opt/kusu/share/doc/kusu-net-tool-%{version}
install -d $RPM_BUILD_ROOT/opt/kusu/man/man8

install -m755 sbin/kusu-net-tool.py $RPM_BUILD_ROOT/opt/kusu/sbin/kusu-net-tool
install -m644 doc/COPYING $RPM_BUILD_ROOT/opt/kusu/share/doc/kusu-net-tool-%{version}
gzip -c man/kusu-net-tool.8 >$RPM_BUILD_ROOT/opt/kusu/man/man8/kusu-net-tool.8.gz

%pre

%post

%preun

%postun

%files
/opt/kusu/sbin/kusu-net-tool
%doc /opt/kusu/share/doc/kusu-net-tool-%{version}/COPYING
/opt/kusu/man/man8/kusu-net-tool.8.gz

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Tue Jun 16 2009 Chew Meng Kuan <mkchew@platform.com> 5.3-1
- Bump version to 5.3 for PCM 1.2.1.

* Thu Feb 26 2009 Mike Frisch <mfrisch@platform.com> 5.2-3
- Updates /etc/resolv.conf when DNS settings change (#123861)
- Display error message if invalid parameters specified (#123860)
- Updates iptables settings when NIC added/removed (#122915)

* Wed Feb 4 2009 Mike Frisch <mfrisch@platform.com> 5.2-2
- Added support for PostgreSQL (#121608)
- Fixes problems related to named configuration not being generated correctly

* Wed Jun 6 2008 Mike Frisch <mfrisch@platform.com> 5.1-1
- Initial release
