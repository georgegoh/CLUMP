# $Id: kusu-core.spec 3528 2010-02-19 11:31:57Z ankit $
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

Summary: Kusu core libraries and system scripts
Name: kusu-core
Version: 2.1
Release: 1
License: GPLv2
Group: System Environment/Base
Vendor: Project Kusu
BuildArch: noarch
Source: %{name}-%{version}.%{release}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-root
#Requires: MySQL-python
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
install -d $RPM_BUILD_ROOT/opt/kusu/libexec

install -m644 lib/__init__.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu
install -m644 lib/netutil.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/core
install -m644 lib/app.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/core
install -m644 lib/db.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/core
install -m644 lib/database.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/core
install -m644 lib/rcplugin.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/core
install -m644 lib/__init__.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/core
install -m644 lib/netutil.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/core
install -m755 lib/kusu-db-copy.py $RPM_BUILD_ROOT/opt/kusu/libexec/kusu-db-copy
install -m644 doc/COPYING $RPM_BUILD_ROOT/opt/kusu/share/doc/core-%{version}
install -m755 bin/kusurc $RPM_BUILD_ROOT/opt/kusu/bin
install -m755 bin/kusuenv.sh $RPM_BUILD_ROOT/opt/kusu/bin
install -m755 bin/kusu-debug $RPM_BUILD_ROOT/opt/kusu/bin
install -m755 bin/kusu-register.py $RPM_BUILD_ROOT/opt/kusu/bin/kusu-register

%pre

%post
if [ $1 -eq 1 ]; then
    ln -sf /opt/kusu/bin/kusuenv.sh /etc/profile.d/kusuenv.sh
fi

%preun

%postun
if [ $1 -eq 0 ]; then
    rm -f /etc/profile.d/kusuenv.sh
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
/opt/kusu/libexec/kusu-db-copy
/opt/kusu/lib/python/kusu/__init__.py*
/opt/kusu/lib/python/kusu/core/*
/opt/kusu/bin/kusuenv.sh
/opt/kusu/bin/kusurc
/opt/kusu/bin/kusu-debug
/opt/kusu/bin/kusu-register
%doc /opt/kusu/share/doc/core-%{version}/COPYING

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Tue Jun 16 2009 Chew Meng Kuan <mkchew@platform.com> 5.3-1
- Bump version to 5.3 for PCM 1.2.1.

* Mon Dec 22 2008 Mark Black <mblack@platform.com> 5.1-12
- Tighten the security on the kusudb

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
