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
License: GPLv2
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
/bin/cat << 'EOF' > /opt/kusu/lib/plugins/cfmclient/lava-restart
#!/bin/sh
source /etc/profile.nii
checksum=`cat /opt/kusu/etc/cfmfiles.lst | grep "/opt/kusu/cfm/${NII_NGID}/opt/lava/conf/lsf.cluster.lava" | cut -d' ' -f6`
actual_checksum=`md5sum /opt/lava/conf/lsf.cluster.lava | cut -d' ' -f1`

if [ "$checksum" != "$actual_checksumi" ]; then
   badmin hstartup
fi
EOF

if [ ! -z ${NII_NGID} ]; then
   rm -rf /opt/kusu/lib/plugins/cfmclient/lava-restart
fi

%preun

%postun
rm -rf /opt/kusu/lib/plugins/cfmclient/lava-restart

# Remove user/group on removal of component
if [ `grep -c lavaadmin /etc/passwd ` -eq 1 ]; then
   /usr/sbin/userdel -r lavaadmin
fi

# Place any component uninstall code here
# Generate scripts for the CFM to remove other packages
/bin/cat << 'EOF' > /opt/kusu/lib/plugins/cfmclient/%{name}.remove
#!/bin/sh
rpm -e lava

rm -rf /opt/kusu/lib/plugins/cfmclient/%{name}.remove
EOF

# Remove any lava configs on node
rm -rf /opt/lava
