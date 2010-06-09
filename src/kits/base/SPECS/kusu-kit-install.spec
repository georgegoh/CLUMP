# Copyright (C) 2007 Platform Computing Inc
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

%define _unpackaged_files_terminate_build 0
%define debug_package %{nil}

Summary: kusu-kit-install package
Name: kusu-kit-install
Version: 2.1
Release: 1
License: GPLv2
Group: System Environment/Base
Vendor: Platform Computing Corporation
Source: %{name}-%{version}.%{release}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
BuildArch: noarch
Requires: kusu-base-installer
Requires: kusu-core
Requires: kusu-driverpatch
Requires: kusu-kitops
Requires: kusu-repoman
Requires: kusu-buildkit

%description
One step kit installation command for kusu.

%prep
%setup -q -n %{name}

%install
rm -rf $RPM_BUILD_ROOT

install -d $RPM_BUILD_ROOT/opt/kusu/man/man8
install -d $RPM_BUILD_ROOT/opt/kusu/sbin
install -d $RPM_BUILD_ROOT/opt/kusu/share/doc/kit-install-%{version}
install -d $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/kitinstall

install -m644 lib/__init__.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/kitinstall
install -m644 lib/helper.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/kitinstall
install -m644 lib/kitinstall.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/kitinstall
install -m755 bin/kusu-kit-install $RPM_BUILD_ROOT/opt/kusu/sbin
install -m644 doc/COPYING $RPM_BUILD_ROOT/opt/kusu/share/doc/kit-install-%{version}
gzip -c man/kusu-kit-install.8 > $RPM_BUILD_ROOT/opt/kusu/man/man8/kusu-kit-install.8.gz

%pre

%post

%preun

%postun

%clean

%files
/opt/kusu/sbin/kusu-kit-install
/opt/kusu/lib/python/kusu/kitinstall
/opt/kusu/man/man8/kusu-kit-install.8.gz

%doc $RPM_BUILD_ROOT/opt/kusu/share/doc/kit-install-%{version}/COPYING


%changelog
* Fri Oct 2 2009 Ankit Agarwal <ankit@platform.com> - 5.3-1
- Adding kit-install to trunk, renamed to kusu-kit-install

* Wed Jul 15 2009 Kunal Chowdhury <kunalc@platform.com> - 0.1-1
- Initial release of ansys kit-install component
