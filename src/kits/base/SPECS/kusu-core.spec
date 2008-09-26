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
Version: 0.10
Release: 10
License: GPLv2
Group: System Environment/Base
Vendor: Project Kusu
BuildArch: noarch
Source: %{name}-%{version}.%{subversion}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-root
Requires: MySQL-python
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
install -m644 etc/kusu-release $RPM_BUILD_ROOT/opt/kusu/etc

%pre

%post
if [ $1 -eq 1 ]; then
    ln -sf /opt/kusu/bin/kusuenv.sh /etc/profile.d/kusuenv.sh
    ln -sf /opt/kusu/etc/kusu-release /etc/kusu-release
fi

%preun

%postun
if [ $1 -eq 0 ]; then
    rm -f /etc/profile.d/kusuenv.sh /etc/kusu-release
fi

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
/opt/kusu/etc/kusu-release
%doc /opt/kusu/share/doc/core-%{version}/COPYING

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Thu Sep 18 2008 Mike Frisch <mfrisch@platform.com> 5.1-10
- Sync with RH HPC

* Fri Sep 5 2008 Mike Frisch <mfrisch@platform.com> 5.1-9
- Fixes problem with boothost failing when being called from CGI script
  (#114570)
- Change KUSU_TMP to be /tmp (#113889)

* Thu Jul 31 2008 Mark Black <mblack@platform.com> 5.1-8
- Reset version/revision after switching build to trunk

* Wed Jun 11 2008 Mike Frisch <mfrisch@platform.com> 5.1-11
- Added 'netutil.py' module

* Wed Apr 16 2008 Mike Frisch <mfrisch@platform.com> 5.1-5
- Partitioning issues resolved (#104419)

* Thu Apr 10 2008 Mike Frisch <mfrisch@platform.com> 5.1-4
- Bug fixes

* Mon Jan 2 2008 Shawn Starr <sstarr@platform.com>
- Initial release
