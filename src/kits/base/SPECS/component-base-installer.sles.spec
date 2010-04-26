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
# $Id: component-base-installer.sles.spec 3463 2010-02-01 04:32:44Z binxu $
# 

Summary: Component for Kusu Installer Base
Name: component-base-installer
Version: 2.0
Release: 1
Epoch: 1
License: GPLv2
Group: System Environment/Base
URL: http://www.osgdc.org
Vendor: Platform Computing Inc
BuildArch: noarch
Buildroot: %{_tmppath}/%{name}-%{version}-buildroot
Requires: kusu-base-installer 
Requires: kusu-base-node
#Requires: component-gnome-desktop
Requires: kusu-boot
Requires: kusu-buildkit 
Requires: kusu-core 
Requires: kusu-driverpatch 
Requires: kusu-hardware 
Requires: kusu-kitops 
Requires: kusu-networktool 
Requires: kusu-path 
Requires: kusu-md5crypt
Requires: kusu-power
Requires: kusu-primitive 
Requires: kusu-repoman 
Requires: python-sqlalchemy
Requires: kusu-ui 
Requires: kusu-util 
Requires: kusu-nodeinstaller-patchfiles
Requires: kusu-nodeinstaller 
Requires: kusu-kit-install
Requires: kusu-shell
Requires: kusu-uat
#Requires: mysql
#Requires: mysql-server
Requires: dhcp
Requires: xinetd
Requires: tftp
Requires: syslinux
Requires: apache2
Requires: python
Requires: python-devel
#Requires: MySQL-python
Requires: python-psycopg2
Requires: createrepo
Requires: rsync
Requires: bind
#Requires: caching-nameserver
Requires: pdsh
Requires: pdsh-rcmd-exec
Requires: pdsh-rcmd-rsh
Requires: pdsh-rcmd-ssh
Requires: pdsh-mod-machines
# Can't use pdsh-mod-dshgroup and pdsh-mod-netgroup at the same time
# Requires: pdsh-mod-dshgroup
Requires: pdsh-mod-netgroup
Requires: postgresql
Requires: postgresql-server
# Requires: pdsh-debuginfo
Requires: environment-modules
Requires: python-cheetah
Requires: python-sqlite2
Requires: python-IPy
Requires: initrd-templates
Requires: pyparted
Requires: rsh
Requires: kusu-net-tool
Requires: dhcp-server
Requires: newt
Requires: libnewt0_52
Requires: python-newt
Requires: slang
Requires: python-xml
Requires: inst-source-utils
Requires: makedev
Requires: squashfs
Requires: kusu-appglobals-tool
Requires: kusu-license-tool

%description
This component provides the node with the Kusu management tools for the 
installers.

%prep

%build

%install
rm -rf $RPM_BUILD_ROOT

%files

%clean
rm -rf $RPM_BUILD_ROOT

%pre

%post
#equivalent of post section

%preun

%postun
#equivalent of uninstall section

%changelog
* Fri Nov 6 2009 Andreas Buck <abuck@platform.com> 2.0-1
- added kusu-power

* Tue Jun 16 2009 Chew Meng Kuan <mkchew@platform.com> 5.3-1
- Bump version to 5.3 for PCM 1.2.1.

* Mon Oct 13 2008 Tsai Li Ming <ltsai@osgdc.org> 1.0-1
- Sync with OCS (r1609)
- Initial 1.0 release

