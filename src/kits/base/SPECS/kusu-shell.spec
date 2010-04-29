# $Id: kusu-shell.spec 3238 2009-11-17 11:46:38Z mike $
#
# Copyright (C) 2010 Platform Computing Inc.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of version 2 of the GNU General Public License as published by the
# Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

Summary: Kusu shell libraries, plugins and scripts
Name: kusu-shell
Version: 2.1
Release: 1
Epoch: 1
License: GPLv2
Group: System Environment/Base
Vendor: Project Kusu
BuildArch: noarch
Source: %{name}-%{version}.%{release}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-root
Requires: kusu-core
BuildRequires: python
URL: http://www.osgdc.org

%description
This package contains the Kusu shell libraries, plugins and scripts

%prep
%setup -q -n %{name}

%build

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/shell
install -d $RPM_BUILD_ROOT/opt/kusu/lib/plugins/shell
install -d $RPM_BUILD_ROOT/opt/kusu/bin
install -d $RPM_BUILD_ROOT/opt/kusu/man/man8

install -m644 lib/__init__.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/shell
install -m644 lib/kusu_shell_app.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/shell
install -m644 lib/status.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/shell
install -m644 plugins/shell/status_app.py $RPM_BUILD_ROOT/opt/kusu/lib/plugins/shell
install -m755 bin/kusu $RPM_BUILD_ROOT/opt/kusu/bin
gzip -c man/kusu.8 > $RPM_BUILD_ROOT/opt/kusu/man/man8/kusu.8.gz

%files
%dir /opt/kusu/lib/python/kusu/shell
%dir /opt/kusu/lib/plugins/shell
/opt/kusu/lib/python/kusu/shell/*
/opt/kusu/lib/plugins/shell/status_app.py*
/opt/kusu/bin/kusu
/opt/kusu/man/man8/kusu.8.gz

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Wed Nov 11 2009 Mike Mazur <mmazur@platform.com> 2.0-1
- Initial release
