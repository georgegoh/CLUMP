# $Id$
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

%define subversion 5

Summary: Kusu core libraries and system scripts
Name: kusu-core
Version: 1.1
Release: 1
License: GPLv2
Group: System Environment/Base
Vendor: Project Kusu
BuildArch: noarch
Source: %{name}-%{version}.%{subversion}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-root
Requires: MySQL-python
Requires: python-psycopg2
BuildRequires: python
URL: http://www.osgdc.org

%description
This package contains the Kusu core libraries and system scripts

%prep
%setup -q -n %{name}

%build

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT/opt/kusu/bin
install -d $RPM_BUILD_ROOT/opt/kusu/lib64/python
install -d $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/core
install -d $RPM_BUILD_ROOT/opt/kusu/share/doc/core-%{version}
install -d $RPM_BUILD_ROOT/opt/kusu/etc

install -m644 lib/__init__.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu
install -m644 lib/netutil.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/core
install -m644 lib/app.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/core
install -m644 lib/db.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/core
install -m644 lib/database.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/core
install -m644 lib/rcplugin.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/core
install -m644 lib/__init__.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/core
install -m644 lib/netutil.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/core
install -m644 doc/COPYING $RPM_BUILD_ROOT/opt/kusu/share/doc/core-%{version}
install -m755 bin/kusurc $RPM_BUILD_ROOT/opt/kusu/bin
install -m755 bin/kusuenv.sh $RPM_BUILD_ROOT/opt/kusu/bin

%pre

%post
if [ $1 -eq 1 ]; then
    ln -sf /opt/kusu/bin/kusuenv.sh /etc/profile.d/kusuenv.sh
fi

%preun

%postun

%files
%dir /opt/kusu
%dir /opt/kusu/bin
%dir /opt/kusu/lib
%dir /opt/kusu/lib64
%dir /opt/kusu/lib64/python
%dir /opt/kusu/etc
%dir /opt/kusu/share
%dir /opt/kusu/share/doc
/opt/kusu/lib/python/kusu/__init__.py*
/opt/kusu/lib/python/kusu/core/*
/opt/kusu/bin/kusuenv.sh
/opt/kusu/bin/kusurc
%doc /opt/kusu/share/doc/core-%{version}/COPYING

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Mon Oct 13 2008 Tsai Li Ming <ltsai@osgdc.org> 1.0-1
- Sync with OCS (r1609)
- Initial 1.0 release

