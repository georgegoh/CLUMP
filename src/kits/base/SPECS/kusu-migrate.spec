# $Id: kusu-migrate.spec 3165 2009-11-03 06:33:22Z yqang $
#
# Copyright (C) 2010 Platform Computing Inc
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

Summary: PCM Migration
Name: kusu-migrate
Version: 2.1
Release: 1
Epoch: 1
License: GPLv2
Group: System Environment/Base
Vendor: Project Kusu
BuildArch: noarch
Source: %{name}-%{version}.%{release}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-root
URL: http://www.osgdc.org
BuildRequires: python

%description
This package contains a tool for migrating PCM settings and configurations.

%prep
%setup -q -n %{name}

%build

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT/opt/kusu/sbin
install -d $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/migrate
install -d $RPM_BUILD_ROOT/opt/kusu/man/man8
install -m755 sbin/kusu-migrate $RPM_BUILD_ROOT/opt/kusu/sbin
install -m644 lib/migrate.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/migrate
install -m644 lib/__init__.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/migrate

gzip -c man/kusu-migrate.8 >$RPM_BUILD_ROOT/opt/kusu/man/man8/kusu-migrate.8.gz

%pre

%post

%preun

%postun

%files
/opt/kusu/sbin/kusu-migrate
/opt/kusu/lib/python/kusu/migrate/*
/opt/kusu/man/man8/kusu-migrate.8.gz

%doc

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Thu Nov 19 2009 Ang Yun Quan <yqang@platform.com> 2.0-1
- Initial release

