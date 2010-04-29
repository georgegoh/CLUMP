# $Id: kusu-driverpatch.spec 3135 2009-10-23 05:42:58Z ltsai $
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

Summary: Driver handling
Name: kusu-driverpatch
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
This package contain a tool handling drivers for different kernels.

%prep
%setup -q -n %{name}

%build

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/driverpatch
install -d $RPM_BUILD_ROOT/opt/kusu/bin
install -d $RPM_BUILD_ROOT/opt/kusu/share/doc/driverpatch-%{version}

install -m755 bin/kusu-driverpatch $RPM_BUILD_ROOT/opt/kusu/bin
install -m755 bin/patchpcitable-script $RPM_BUILD_ROOT/opt/kusu/bin
install -m644 lib/control.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/driverpatch
install -m644 lib/dkms.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/driverpatch
install -m644 lib/kernel.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/driverpatch
install -m644 lib/modules.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/driverpatch
install -m644 lib/modulesfactory.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/driverpatch
install -m644 lib/__init__.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/driverpatch
install -m644 doc/COPYING $RPM_BUILD_ROOT/opt/kusu/share/doc/driverpatch-%{version}

pushd $RPM_BUILD_ROOT/opt/kusu/bin
ln -s /opt/kusu/bin/kusu-driverpatch driverpatch
popd

%pre

%post


%preun

%postun

%files
/opt/kusu/lib/python/kusu/driverpatch/*
/opt/kusu/bin/kusu-driverpatch
/opt/kusu/bin/driverpatch
/opt/kusu/bin/patchpcitable-script

%doc /opt/kusu/share/doc/driverpatch-%{version}/COPYING

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Tue Jun 16 2009 Chew Meng Kuan <mkchew@platform.com> 5.3-1
- Bump version to 5.3 for PCM 1.2.1.

* Thu Aug 21 2008 Mark Black <mblack@platform.com> 5.1-12
- Reving tar file for RH

* Wed Aug 13 2008 Mike Frisch <mfrisch@platform.com> 5.1-11
- Move log file from /tmp/kusu (#113531)

* Tue Feb 26 2008 Najib Ninaba <najib@platform.com>
- Added patchpcitable-script

* Mon Jan 2 2008 Shawn Starr <sstarr@platform.com>
- Initial release
