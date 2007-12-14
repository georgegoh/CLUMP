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

Summary: LSF Compute Component
Name: component-LSF-Compute-v7_0_1
Version: 7.0.1
Release: 0
License: Commercial
Group: System Environment/Base
Vendor: Platform Computing Corporation
Requires: lsf = 7.0.1
BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-root
Requires: coreutils

%description
This package is a metapackage for LSF compute nodes

%install
rm -rf $RPM_BUILD_ROOT

install -d $RPM_BUILD_ROOT/etc/rc.kusu.d

/usr/bin/install -m 755 %{_topdir}/S10lsf-compute-preconf $RPM_BUILD_ROOT/etc/rc.kusu.d/

%clean
rm -rf $RPM_BUILD_ROOT

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
sed -i -e "s/@CLUSTERNAME@/$CNAME/" /etc/rc.kusu.d/S10lsf-compute-preconf

if [ -x /etc/rc.kusu.d/S10lsf-compute-preconf ]; then
	/etc/rc.kusu.d/S10lsf-compute-preconf
fi

%postun
# Generate scripts for the CFM to remove other packages
/bin/cat << 'EOF' >> /opt/kusu/lib/plugins/cfmclient/%{name}.remove
#!/bin/sh
yum -y remove lsf
rm -rf /opt/kusu/lib/plugins/cfmclient/%{name}.remove
EOF

%files
/etc/rc.kusu.d/S10lsf-compute-preconf
