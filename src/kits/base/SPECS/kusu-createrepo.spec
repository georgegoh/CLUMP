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
# $Id: kusu-createrepo.spec 1335 2007-06-14 11:06:48Z najib $
#
%define debug_package %{nil}

Summary: kusu-createrepo module runtime
Name: kusu-createrepo
Version: 0.4.8
Release: 2
License: GPLv2
Group: System Environment/Base
Vendor: Platform Computing Inc.
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
AutoReq: no
Source: %{name}-%{version}.tar.gz
Buildrequires: gcc, python, python-devel, patch
BuildArch: noarch
Requires: python >= 2.1, rpm-python, rpm >= 0:4.1.1
Requires: yum-metadata-parser
Requires: kusu-libxml2-python

%description
This package installs the kusu-createrepo module runtime.

%prep
%setup -n %{name} -q
patch src/bin/createrepo custom/%{version}/createrepo.patch
patch src/bin/modifyrepo custom/%{version}/modifyrepo.patch

%build

%install
%define _approot /opt/kusu
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/%{_approot}

install -d $RPM_BUILD_ROOT/%{_approot}/bin
install -m755 src/bin/createrepo $RPM_BUILD_ROOT/%{_approot}/bin
install -m755 src/bin/modifyrepo $RPM_BUILD_ROOT/%{_approot}/bin

install -d $RPM_BUILD_ROOT/%{_approot}/lib/python/createrepo
install -m755 src/modifyrepo.py $RPM_BUILD_ROOT/%{_approot}/lib/python/createrepo
install -m755 src/dumpMetadata.py $RPM_BUILD_ROOT/%{_approot}/lib/python/createrepo
install -m755 src/genpkgmetadata.py $RPM_BUILD_ROOT/%{_approot}/lib/python/createrepo

install -d $RPM_BUILD_ROOT/%{_approot}/share/doc/%{name}-%{version}
install -m644 src/COPYING $RPM_BUILD_ROOT/%{_approot}/share/doc/%{name}-%{version}
install -m644 src/README $RPM_BUILD_ROOT/%{_approot}/share/doc/%{name}-%{version}

%pre

%post

%preun

%postun

%clean
rm -rf %{buildroot}

%files
%{_approot}
