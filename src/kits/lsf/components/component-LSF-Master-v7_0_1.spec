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

%define compdependency component-LSF-Compute-v7_0_1

Summary: LSF Master Component
Name: component-LSF-Master-v7_0_1
Version: 7.0.1
Release: 0
License: Commercial
Group: System Environment/Base
Vendor: Platform Computing Corporation
Requires: lsf-master-config = 7.0.1
Requires: component-LSF-Compute-v7_0_1 = 7.0.1
BuildArchitectures: noarch

%description
This package is a metapackage for LSF(R)

%prep
mkdir -p $RPM_BUILD_ROOT/etc/rc.kusu.d/

%postun
# Remove user/group on removal of kit
if [ `grep -c lsfadmin /etc/passwd ` -eq 1 ]; then
   /usr/sbin/userdel -r lsfadmin
fi

# Generate scripts for the CFM to remove other packages
/bin/cat << 'EOF' >> /opt/kusu/lib/plugins/cfmclient/%{name}.remove
#!/bin/sh
yum -y remove %{compdependency} lsf-master-config lsf
rm -rf /opt/kusu/lib/plugins/cfmclient/%{name}.remove
rm -rf /opt/kusu/lib/plugins/cfmclient/%{compdependency}.remove
EOF


