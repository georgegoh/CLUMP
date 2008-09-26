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

%define subversion 4

Summary: Repository Management
Name: kusu-repoman
Version: 0.10
Release: 7
License: GPLv2
Group: System Environment/Base
Vendor: Project Kusu
BuildArch: noarch
Source: %{name}-%{version}.%{subversion}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-root
URL: http://www.osgdc.org
BuildRequires: python

%description
This package contains tools for managing repositories.

%prep
%setup -q -n %{name}

%build

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/repoman
install -d $RPM_BUILD_ROOT/opt/kusu/bin
install -d $RPM_BUILD_ROOT/opt/kusu/share/doc/repoman-%{version}
install -d $RPM_BUILD_ROOT/opt/kusu/etc/templates

install -m755 bin/repoman $RPM_BUILD_ROOT/opt/kusu/bin
install -m755 bin/repopatch $RPM_BUILD_ROOT/opt/kusu/bin
install -m644 lib/repofactory.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/repoman
install -m644 lib/repo.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/repoman
install -m644 lib/rhn.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/repoman
install -m644 lib/tools.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/repoman
install -m644 lib/updates.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/repoman
install -m644 lib/yum.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/repoman
install -m644 lib/__init__.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/repoman
install -m644 doc/COPYING $RPM_BUILD_ROOT/opt/kusu/share/doc/repoman-%{version}
install -m644 etc/updates.conf $RPM_BUILD_ROOT/opt/kusu/etc
install -m644 etc/templates/update.kit.tmpl $RPM_BUILD_ROOT/opt/kusu/etc/templates

%pre

%post

%preun

%postun

%files
/opt/kusu/lib/python/kusu/repoman/*
/opt/kusu/bin/repoman
/opt/kusu/bin/repopatch
/opt/kusu/etc/updates.conf
/opt/kusu/etc/templates/update.kit.tmpl

%doc /opt/kusu/share/doc/repoman-%{version}/COPYING

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Thu Sep 18 2008 Mark Black <mblack@platform.com> 5.1-6
- Do not use /tmp/kusu for tmp dirs. Bugzilla 461781

* Thu Aug 21 2008 Mark Black <mblack@platform.com> 5.1-6
- Reving tar file for RH

* Thu Jul 31 2008 Mark Black <sstarr@platform.com> 5.1-5
- Reset version/revision after switching build to trunk

* Thu Apr 3 2008 Mike Frisch <mfrisch@platform.com> 5.1-4
- Minor repoman fix

* Mon Jan 2 2008 Shawn Starr <sstarr@platform.com>
- Initial release
