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
# $Id: base-installer.spec 2848 2007-11-26 22:02:12Z mblack $
# 

Summary: Component for Kusu Installer Base
Name: component-base-installer
Version: 0.10
Release: 5
License: GPLv2
Group: System Environment/Base
URL: http://www.osgdc.org
Vendor: Platform Computing Inc
BuildArch: noarch
Buildroot: %{_tmppath}/%{name}-%{version}-buildroot
Requires: kusu-base-installer 
Requires: kusu-base-node
Requires: component-gnome-desktop
Requires: kusu-boot
Requires: kusu-buildkit 
Requires: kusu-core 
Requires: kusu-driverpatch 
Requires: kusu-hardware 
Requires: kusu-kitops 
Requires: kusu-networktool 
Requires: kusu-path 
Requires: kusu-partitiontool 
Requires: kusu-repoman 
Requires: python-sqlalchemy
Requires: kusu-ui 
Requires: kusu-util 
Requires: kusu-nodeinstaller-patchfiles
Requires: kusu-nodeinstaller 
Requires: mysql
Requires: mysql-server
Requires: dhcp
Requires: xinetd
Requires: tftp-server
Requires: syslinux
Requires: httpd
Requires: python
Requires: python-devel
Requires: MySQL-python
Requires: createrepo
Requires: rsync
Requires: bind
Requires: caching-nameserver
Requires: pdsh
Requires: pdsh-rcmd-exec
Requires: pdsh-rcmd-rsh
Requires: pdsh-rcmd-ssh
Requires: pdsh-mod-machines
# Can't use pdsh-mod-dshgroup and pdsh-mod-netgroup at the same time
# Requires: pdsh-mod-dshgroup
Requires: pdsh-mod-netgroup
# Requires: pdsh-debuginfo
Requires: environment-modules
Requires: python-cheetah
Requires: python-sqlite2
Requires: python-IPy
Requires: initrd-templates
Requires: pyparted
Requires: rsh
#Requires: kusu-net-tool

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
* Fri Aug 22 2008 Mark Black <mblack@platform.com> 5.1-5
- Removed 'kusu-net-tool'

* Fri Jul 25 2008 Mike Frisch <mfrisch@platform.com> 5.1-4
- Added 'kusu-net-tool'

* Fri Jul 4 2008 Najib Ninaba <najib@platform.com>
- Replaced kusu-ipy with python-IPy

* Thu Jan 10 2008 Platform Computing <support@platform.com>
- Initial release.
