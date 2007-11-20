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

%define lsf_version 7.0.1
%define lsf_version_us 7_0_1

Summary: LSF Master Component
Name: component-LSF-Master-v%{lsf_version_us}
Version: %{lsf_version}
Release: 0
License: Commercial
Group: System Environment/Base
Vendor: Platform Computing Corporation
Requires: lsf = %{lsf_version}
Requires: lsf-master-config = %{lsf_version}
BuildArchitectures: noarch

%description
This package is a metapackage for LSF(R)

%prep
mkdir -p $RPM_BUILD_ROOT/etc/rc.kusu.d/

%install
/usr/bin/install -m 755 %{_topdir}/S10lsf-master-preconf $RPM_BUILD_ROOT/etc/rc.kusu.d/

%post
# sqlrunner is only available on the installer node
if [ -f /etc/profile.nii ]; then
	. /etc/profile.nii

	CNAME="$LSF7_0_1_ClusterName"
else
	CNAME=$( sqlrunner -q "SELECT kvalue FROM appglobals WHERE kname='PrimaryInstaller'" )
fi

if [ -z "$CNAME" ]; then
	echo "CNAME is blank; use a default"
	CNAME="CLUSTER_NAME_NOT_DEFINED"
fi

# Update cluster name in pre-configuration script
sed -i -e "s/@CLUSTERNAME@/$CNAME/" /etc/rc.kusu.d/S10lsf-master-preconf

if [ -x /etc/rc.kusu.d/S10lsf-master-preconf ]; then
	/etc/rc.kusu.d/S10lsf-master-preconf
fi

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

%files
/etc/rc.kusu.d/S10lsf-master-preconf
