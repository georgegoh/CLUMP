# $Id: kusu-kitops.spec 3165 2009-11-03 06:33:22Z yqang $
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

Summary: Kit Management
Name: kusu-kitops
Version: 2.1
Release: 1
License: GPLv2
Group: System Environment/Base
Vendor: Project Kusu
BuildArch: noarch
Source: %{name}-%{version}.%{release}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-root
URL: http://www.osgdc.org
BuildRequires: python

%description
This package contains a tool for managing kits.

%prep
%setup -q -n %{name}

%build

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/kitops
install -d $RPM_BUILD_ROOT/opt/kusu/bin
install -d $RPM_BUILD_ROOT/opt/kusu/share/doc/kitops-%{version}
install -d $RPM_BUILD_ROOT/opt/kusu/etc

install -m755 bin/kusu-kitops $RPM_BUILD_ROOT/opt/kusu/bin
install -m644 lib/kitops.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/kitops
install -m644 lib/action.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/kitops
install -m644 lib/remotekit.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/kitops
install -m644 lib/addkit_strategies.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/kitops
install -m644 lib/deletekit_strategies.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/kitops
install -m644 lib/package.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/kitops
install -m644 lib/__init__.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/kitops
install -m644 doc/COPYING $RPM_BUILD_ROOT/opt/kusu/share/doc/kitops-%{version}
install -m644 etc/remoterepo.conf $RPM_BUILD_ROOT/opt/kusu/etc

pushd $RPM_BUILD_ROOT/opt/kusu/bin
ln -s /opt/kusu/bin/kusu-kitops kitops
popd


%pre

%post

%preun

%postun

%files
/opt/kusu/lib/python/kusu/kitops/*
/opt/kusu/bin/kitops
/opt/kusu/bin/kusu-kitops
%config(noreplace) /opt/kusu/etc/remoterepo.conf

%doc /opt/kusu/share/doc/kitops-%{version}/COPYING

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Tue Jun 16 2009 Chew Meng Kuan <mkchew@platform.com> 5.3-1
- Bump version to 5.3 for PCM 1.2.1.

* Thu Aug 21 2008 Mark Black <mblack@platform.com> 5.1-7
- Reving tar file for RH

* Thu Jul 31 2008 Mark Black <mblack@platform.com> 5.1-6
- Reset version/revision after switching build to trunk
- Move log files from /tmp/kusu (#113531)

* Mon Jan 2 2008 Shawn Starr <sstarr@platform.com>
- Initial release

