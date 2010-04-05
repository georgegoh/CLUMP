# $Id: kusu-boot.spec 3135 2009-10-23 05:42:58Z ltsai $
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

Summary: Boot Media tool
Name: kusu-boot
Version: 2.0
Release: 1
Epoch: 1
License: GPLv2
Group: System Environment/Base
Vendor: Platform Computing Corporation
BuildArch: noarch
Source: %{name}-%{version}.%{release}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-root
URL: http://ocssrc.platform.com/
BuildRequires: python

%description
This package contains a program to create CD/DVDs with custom ramdisks.

%prep
%setup -q -n %{name}

%build

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/boot
install -d $RPM_BUILD_ROOT/opt/kusu/bin
install -d $RPM_BUILD_ROOT/opt/kusu/share/doc/boot-%{version}

install -m755 bin/boot-media-tool $RPM_BUILD_ROOT/opt/kusu/bin
install -m644 lib/distro.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/boot
install -m644 lib/image.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/boot
install -m644 lib/tool.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/boot
install -m644 lib/__init__.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/boot
install -m644 doc/COPYING $RPM_BUILD_ROOT/opt/kusu/share/doc/boot-%{version}

%pre

%post

%preun

%postun

%files
/opt/kusu/lib/python/kusu/boot/*
/opt/kusu/bin/boot-media-tool

%doc /opt/kusu/share/doc/boot-%{version}/COPYING

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Tue Jun 16 2009 Chew Meng Kuan <mkchew@platform.com> 5.3-1
- Bump version to 5.3 for PCM 1.2.1.

* Thu Aug 21 2008 Mark Black <mblack@platform.com> 5.1-3
- Reving tar file for RH

* Mon Jan 2 2008 Shawn Starr <sstarr@platform.com>
- Initial release

