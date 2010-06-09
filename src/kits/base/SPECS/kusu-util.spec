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
# $Id: kusu-util.spec 3135 2009-10-23 05:42:58Z ltsai $
#

Summary: kusu-util module runtime
Name: kusu-util
Version: 2.1
Release: 1
License: GPLv2
Group: System Environment/Base
Vendor: Platform Computing Inc.
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
BuildArch: noarch
Source: %{name}-%{version}.%{release}.tar.gz
BuildRequires: python

%description
This package installs the kusu-util module runtime.

%prep
%setup -q -n %{name}

%build

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT/opt/kusu/etc

# Documentation
install -d $RPM_BUILD_ROOT/opt/kusu/share/doc/util-%{version}
install doc/COPYING $RPM_BUILD_ROOT/opt/kusu/share/doc/util-%{version}
install doc/README-log.txt $RPM_BUILD_ROOT/opt/kusu/share/doc/util-%{version}

# Other files

install etc/distro.conf $RPM_BUILD_ROOT/opt/kusu/etc/

install -d $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/util
install lib/*.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/util/

install -d $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/util/distro

install lib/distro/*.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/util/distro/

%pre

%post

%preun

%postun

%clean
rm -rf $RPM_BUILD_ROOT

%files
/opt/kusu/etc/distro.conf
/opt/kusu/lib/python/kusu/util/*
%dir /opt/kusu/share/doc/util-%{version}
%doc /opt/kusu/share/doc/util-%{version}/COPYING
%doc /opt/kusu/share/doc/util-%{version}/README-log.txt

%changelog
* Tue Jun 16 2009 Chew Meng Kuan <mkchew@platform.com> 5.3-1
- Bump version to 5.3 for PCM 1.2.1.

* Fri Sep 5 2008 Mike Frisch <mfrisch@platform.com> 5.1-7
- Add 'kusu-' prefix to temporary directories created by OCS (#113889)

* Thu Aug 21 2008 Mark Black <mblack@platform.com> 5.1-6
- Reving tar file for RH

* Thu Jul 31 2008 Mark Black <mblack@platform.com> 5.1-5
- Reset version/revision after switching build to trunk

* Wed Jun 4 2008 Shawn Starr <spstarr@platform.com> 5.1-4
- Fixed error message when entering invalid email address (#109791)

* Thu Apr 3 2008 Mike Frisch <mfrisch@platform.com> 5.1-3
- Partitioning related fixes

* Thu Jan 10 2008 Platform Computing <support@platform.com>
- Initial release.
