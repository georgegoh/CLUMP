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
# $Id$
#

%define subversion 6

Summary: kusu-nodeinstaller-patchfiles 
Name: kusu-nodeinstaller-patchfiles
Version: 1.2
Release: 1
License: GPLv2
Group: System Environment/Base
Vendor: Platform Computing Inc.
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
AutoReq: no
Source: %{name}-%{version}.%{subversion}.tar.gz
BuildRequires: python
Requires: yum-utils
BuildArch: noarch


%description
Kusu NodeInstaller patchfiles contains distro-specific os installer
patches that contain the Kusu NodeInstaller runtime.

%prep
%setup -n %{name} -q

%build

%install
rm -rf $RPM_BUILD_ROOT

mkdir -p $RPM_BUILD_ROOT/opt/kusu/lib/nodeinstaller/bin
mkdir -p $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/genupdates

install -m755 bin/* $RPM_BUILD_ROOT/opt/kusu/lib/nodeinstaller/bin
install -m755 lib/* $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/genupdates

find src/ | cpio -mpdu $RPM_BUILD_ROOT/opt/kusu/lib/nodeinstaller/

install -d $RPM_BUILD_ROOT/opt/kusu/sbin
install -m755 sbin/genupdatesimg.py $RPM_BUILD_ROOT/opt/kusu/sbin/genupdatesimg

install -d $RPM_BUILD_ROOT/opt/kusu/man/man8
install -m444 man/genupdatesimg.8 $RPM_BUILD_ROOT/opt/kusu/man/man8

%pre

%post
rm -rf /opt/kusu/lib/nodeinstaller/{rhel,centos,fedora,sles}

%preun

%postun
if [ $1 -eq 0 ]; then
    # Remove files created by genupdatesimg
    rm -rf /opt/kusu/lib/nodeinstaller/{rhel,centos,fedora,sles}
fi

%clean
rm -rf $RPM_BUILD_ROOT

%files
/opt/kusu/lib/nodeinstaller/bin
/opt/kusu/lib/nodeinstaller/src
/opt/kusu/lib/python/kusu/genupdates
/opt/kusu/sbin/genupdatesimg
/opt/kusu/man/man8/genupdatesimg.8

%changelog
* Mon Oct 13 2008 Tsai Li Ming <ltsai@osgdc.org> 1.0-1
- Sync with OCS (r1609)
- Initial 1.0 release

