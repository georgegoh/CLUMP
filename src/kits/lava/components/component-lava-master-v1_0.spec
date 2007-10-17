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
Name: component-lava-master-v1_0
Version: 1.0
Release: 0
License: GPLv2
Group: System Environment/Base
Vendor: Platform Computing Corporation
Requires: lava-master-config = 1.0, component-lava-compute-v1_0 = 1.0
BuildArchitectures: noarch

%define compdependency component-lava-compute-v1_0

 
%description
This package is a metapackage for Lava

%prep
mkdir -p $RPM_BUILD_ROOT/etc/rc.kusu.d/

%post
/bin/cat << 'EOF' > /opt/kusu/lib/plugins/cfmclient/lava-restart
#!/bin/sh
source /etc/profile.d/lava.sh
lsadmin reconfig -f 
badmin hstartup
EOF

%install

%postun
# Remove user/group on removal of kit
if [ `grep -c lavaadmin /etc/passwd ` -eq 1 ]; then
   /usr/sbin/userdel -r lavaadmin
fi

# Generate scripts for the CFM to remove other packages
/bin/cat << 'EOF' >> /opt/kusu/lib/plugins/cfmclient/%{name}.remove
#!/bin/sh
yum -y remove component-lava-compute-v1_0 lava-master-config lava
rm -rf /opt/kusu/lib/plugins/cfmclient/%{name}.remove
rm -rf /opt/kusu/lib/plugins/cfmclient/%{compdependency}.remove
EOF

%files
