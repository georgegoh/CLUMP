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

%define subversion 1

Summary: Kusu release file
Name: kusu-release
Version: 1.1
Release: 1
License: GPLv2
Group: System Environment/Base
Vendor: Platform Computing Inc.
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
BuildArch: noarch
Source: %{name}-%{version}.%{subversion}.tar.gz

%description
Kusu release file

%prep
%setup -q -n %{name}

%build

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT/etc
install -d $RPM_BUILD_ROOT/etc/pki/rpm-gpg

install -m644 src/kusu-release $RPM_BUILD_ROOT/etc
install -m644 src/RPM-GPG-KEY-KUSU $RPM_BUILD_ROOT/etc/pki/rpm-gpg

%pre

%post

%preun

%postun

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
/etc/kusu-release
/etc/pki/rpm-gpg/RPM-GPG-KEY-KUSU

%changelog
* Mon Oct 20 2008 Tsai Li Ming <ltsai@osgdc.org> 1.1-1
- Kusu release file

