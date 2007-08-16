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
Requires: kusu-base-installer >= 0.1
Requires: kusu-base-node >= 0.1
Requires: kusu-boot >= 0.5
Requires: kusu-buildkit >= 0.5
Requires: kusu-core >= 0.5
Requires: kusu-hardware >= 0.5
Requires: kusu-kitops >= 0.5
Requires: kusu-networktool >= 0.5
Requires: kusu-path >= 0.5
Requires: kusu-partitiontool >= 0.5
Requires: kusu-repoman >= 0.5
Requires: kusu-sqlalchemy >= 0.5
Requires: kusu-ui >= 0.5
Requires: kusu-util >= 0.5
Requires: kusu-nodeinstaller-patchfiles >= 0.5
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
