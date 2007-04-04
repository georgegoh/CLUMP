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
License: Copyright 2007 Platform Computing Corporation
Group: System Environment/Base
Vendor: Platform Computing Corporation
BuildArchitectures: noarch
Requires: kusu-base-installer = 1.0
Requires: kusu-base-node = 1.0
Requires: mysql >= 5.0
Requires: mysql-server >= 5.0
Requires: dhcp >= 3.0
Requires: xinetd >= 2.3
Requires: tftp-server >= 0.40
Requires: httpd >= 2.2.3
Requires: python >= 2.4.3
Requires: python-devel >= 2.4.3
Requires: MySQL-python >= 1.2.1
Requires: createrepo >= 0.4.4



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
