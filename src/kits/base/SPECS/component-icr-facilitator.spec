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
Epoch: 1
License: GPLv2
Group: System Environment/Base
BuildArch: noarch
Source: %{name}-%{version}.%{release}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-root
Requires(post): grep, procps, coreutils, net-tools, openssl, shadow-utils
Requires: libgtk-java
Requires: compat-libstdc++-33
Requires: imake
Requires: xorg-x11-resutils
Requires: xorg-x11-xfs-utils
Requires: fontconfig
Requires: freetype
Requires: libFS
Requires: libX11
Requires: libICE
Requires: libXcomposite
Requires: libXcursor
Requires: libXdamage
Requires: libXevie
Requires: libXext
Requires: libXfixes
Requires: libXfont
Requires: libXft
Requires: libXi
Requires: libXinerama
Requires: libXmu
Requires: libXp
Requires: libXrandr
Requires: libXrender
Requires: libXres
Requires: libXScrnSaver
Requires: libXt
Requires: libXTrap
Requires: libXtst
Requires: libXv
Requires: libXvMC
Requires: libXxf86dga
Requires: libXxf86misc
Requires: libXxf86vm
Requires: mesa-libGLw
Requires: mesa-libOSMesa
Requires: openmotif
Requires: xorg-x11-drv-i810
Requires: glx-utils
Requires: xorg-x11-apps
Requires: xterm
Requires: libcap
Requires: gdbm-devel
Requires: elfutils-libelf-devel
Requires: bzip2-devel
Requires: libacl-devel
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

install -m0755 etc/S99intel-cluster-ready $RPM_BUILD_ROOT/etc/rc.kusu.d
install -m0644 etc/icr $RPM_BUILD_ROOT/etc/intel

%clean
rm -rf $RPM_BUILD_ROOT

%pre

%post

if [ -e /var/lock/subsys/kusu-installer ]; then exit 0; fi

cat > '/opt/kusu/lib/plugins/cfmclient/S99-icr.sh' << EOSCRIPT
#!/bin/sh
# If kusu repo not been set up, exit.
if [ ! -e /etc/yum.repos.d/kusu-compute.repo ]; then exit 0; fi

if [ -f /etc/rc.kusu.d/S99intel-cluster-ready ];
then
    /opt/kusu/bin/kusurc /etc/rc.kusu.d/S99intel-cluster-ready
fi

rm -f /opt/kusu/lib/plugins/cfmclient/S99-icr.sh
EOSCRIPT

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
