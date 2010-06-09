# Copyright (C) 2008 Platform Computing Inc
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

Summary: Component for Intel(R) Cluster Ready Facilitator
Name: component-icr-facilitator
Version: 2.1
Release: 1
License: GPLv2
Group: System Environment/Base
BuildArch: noarch
Source: %{name}-%{version}.%{release}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-root
Requires(post): grep, procps, coreutils, net-tools, openssl, pwdutils
Requires: libstdc++33
Requires: libstdc++33-32bit
Requires: xorg-x11
Requires: xorg-x11-devel
Requires: xorg-x11-devel-32bit
Requires: fontconfig
Requires: fontconfig-32bit
Requires: freetype
Requires: freetype-32bit
Requires: xorg-x11-libs
Requires: xorg-x11-libs-32bit
Requires: Mesa
Requires: Mesa-32bit
Requires: openmotif-libs
Requires: openmotif-libs-32bit
Requires: xorg-x11-driver-video
Requires: intel-i810-xorg-x11
Requires: freeglut
Requires: xterm
Requires: libcap
Requires: gdbm
Requires: gdbm-devel
Requires: gdbm-32bit
Requires: gdbm-devel-32bit
Requires: libelf
Requires: libelf-32bit
Requires: bzip2
Requires: bzip2-32bit
Requires: libacl
Requires: libacl-devel
Requires: libacl-32bit
Requires: libattr
Requires: libattr-32bit
Requires: libcap
Requires: libcap-32bit
Requires: libpcap
Requires: libpcap-32bit
Requires: gcc
Requires: gcc-c++
Requires: termcap
Requires: termcap-32bit
Requires: pam-32bit
Requires: hdparm

%description
This component sets up cluster for Intel(R) Cluster Ready

%prep
%setup -q -n %{name}

%build

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/etc/intel
mkdir -p $RPM_BUILD_ROOT/etc/rc.kusu.d
mkdir -p $RPM_BUILD_ROOT/usr/bin

install -m0755 etc/S99intel-cluster-ready.sles $RPM_BUILD_ROOT/etc/rc.kusu.d/S99intel-cluster-ready
install -m0644 etc/icr $RPM_BUILD_ROOT/etc/intel

%clean
rm -rf $RPM_BUILD_ROOT

%pre

%post

if [ -e /var/lock/subsys/kusu-installer ]; then exit 0; fi

if [ -f /etc/rc.kusu.d/S99intel-cluster-ready ]; then
    /opt/kusu/bin/kusurc /etc/rc.kusu.d/S99intel-cluster-ready
fi

%preun

%postun

%files
/etc/intel/icr
/etc/rc.kusu.d/S99intel-cluster-ready

%changelog
* Tue Jun 16 2009 Chew Meng Kuan <mkchew@platform.com> 5.3-1
- Bump version to 5.3 for PCM 1.2.1.

* Wed Dec 17 2008 Shawn Starr <sstarr@platform.com> 5.1-2
- Add new dependencies and bump to ICR 1.1

* Thu Oct 16 2008 Shawn Starr <sstarr@platform.com> 5.1-1
- Intel cluster ready component
