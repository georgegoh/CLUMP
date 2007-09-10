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
# $Id$
# 

Summary: Component for Kusu Installer Base
Name: component-base-installer
Version: 0.1
Release: 0
License: GPLv2
Group: System Environment/Base
Vendor: Platform Computing Inc
BuildArchitectures: noarch
Requires: kusu-base-installer 
Requires: kusu-base-node 
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
Requires: kusu-sqlalchemy 
Requires: kusu-ui 
Requires: kusu-util 
Requires: kusu-nodeinstaller-patchfiles 
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
Requires: pdsh-mod-dshgroup
Requires: pdsh-mod-netgroup
Requires: pdsh-debuginfo
Requires: kusu-cheetah
Requires: kusu-pysqlite
Requires: kusu-ipy
Requires: initrd-templates
Requires: pyparted
Requires: rsh
# X Libraries
Requires: libFS
Requires: libXScrnSaver
Requires: libXTrap
Requires: libXaw
Requires: libXcomposite
Requires: libXdamage
Requires: libXevie
Requires: libXfont
Requires: libXfontcache
Requires: libXmu
Requires: libXpm
Requires: libXres
Requires: libXtst
Requires: libXv
Requires: libXxf86dga
Requires: libXxf86misc
Requires: libxkbfile
Requires: urw-fonts
Requires: xkeyboard-config
Requires: xorg-x11-font-utils
Requires: xorg-x11-fonts-base
Requires: xorg-x11-server-utils
Requires: xorg-x11-utils
Requires: xorg-x11-xauth
Requires: xorg-x11-xfs
Requires: xorg-x11-xkb-utils
# X Libraries - END

%description
This component provides the node with the Kusu management tools for the 
installers.

%prep

%files

%pre

%post
#equivalent of post section

%preun

%postun
#equivalent of uninstall section
