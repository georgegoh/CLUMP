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
# $Id: kusu-md5crypt.spec 1335 2007-06-14 11:06:48Z najib $
#

%define subversion 1

Summary: kusu-md5crypt module runtime
Name: kusu-md5crypt
Version: 1.1
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
This package installs the kusu-md5crypt module runtime.

%prep
%setup -n %{name} -q

%build

%install
%define _approot /opt/kusu
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/%{_approot}

install -d $RPM_BUILD_ROOT/%{_approot}/lib/python
install -m644 src/md5crypt.py $RPM_BUILD_ROOT/%{_approot}/lib/python

install -d $RPM_BUILD_ROOT/%{_approot}/share/doc/%{name}-%{version}
install -m755 src/COPYING $RPM_BUILD_ROOT/%{_approot}/share/doc/%{name}-%{version}

%pre

%post

%preun

%postun

%clean
rm -rf %{buildroot}

%files
%{_approot}

