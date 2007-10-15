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
# 

Summary: Lava compute component
Name: component-lava-compute-v1_0
Version: 1.0
Release: 0
License: LGPL
Group: System Environment/Base
Vendor: Platform Computing Corporation
BuildArchitectures: noarch
Requires: lava = 1.0

%description
This package is a meta package for Lava

%prep

%files

%pre

%post
# Place any component post install code here

%preun

%postun

# Remove user/group on removal of component
if [ `grep -c lavaadmin /etc/passwd ` -eq 1 ]; then
   /usr/sbin/userdel -r lavaadmin
fi

# Place any component uninstall code here
# Generate scripts for the CFM to remove other packages
/bin/cat << 'EOF' >> /opt/kusu/lib/plugins/cfmclient/%{name}.remove
#!/bin/sh
yum -y remove lava

rm -rf /opt/kusu/lib/plugins/cfmclient/%{name}.remove
EOF

