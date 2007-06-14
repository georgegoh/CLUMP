# Copyright (C) 2007 Platform Computing Corporation
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
Vendor: Platform Computing Corporation
BuildArchitectures: noarch
Requires: kusu-base-installer = 1.0
Requires: kusu-base-node = 1.0
Requires: kusu-boot >= 0.2
Requires: kusu-core >= 0.2
Requires: kusu-hardware >= 0.2
Requires: kusu-kitops >= 0.2
Requires: kusu-networktool >= 0.2
Requires: kusu-path >= 0.2
Requires: kusu-repoman >= 0.2
Requires: kusu-sqlalchemy >= 0.2
Requires: kusu-ui >= 0.2
Requires: kusu-util >= 0.2
Requires: mysql >= 5.0
Requires: mysql-server >= 5.0
Requires: dhcp >= 3.0
Requires: xinetd >= 2.3
Requires: tftp-server >= 0.40
Requires: syslinux >= 3.11
Requires: httpd >= 2.2.3
Requires: python >= 2.4.3
Requires: python-devel >= 2.4.3
Requires: MySQL-python >= 1.2.1
Requires: createrepo >= 0.4.4
Requires: rsync >= 2.6.6
Requires: pdsh >= 2.10
Requires: pdsh-mod-machines >= 2.10
Requires: pdsh-rcmd-rsh >= 2.10
Requires: pdsh-rcmd-ssh >= 2.10
Requires: pdsh-mod-dshgroup >= 2.10


%description
This component provides the node with the Kusu management tools for the 
installers.

%prep

%files

%pre

%post
#equivalent of the roll's XML post section
echo "Running base-installer post"

%preun

%postun
#equivalent of the roll's XML uninstall section
