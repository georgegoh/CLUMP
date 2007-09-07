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

Summary: Lava master component
Name: component-lava-master-v1.0
Version: 1.0
Release: 0
License: Something
Group: System Environment/Base
Vendor: Platform Computing Corporation
Requires: lava-1.0 lava-master-config-1.0
BuildArchitectures: noarch

%description
This package is a metapackage for Lava

%prep

%files

%pre

%post
#equivalent of the kits post section for the client

%preun

%postun
#equivalent of the kits uninstall section for the client
