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

Summary: Platform OFED Development Component
Name: component-Platform-OFED-devel-v1_2_5_1
Version: 1.2.5.1
Release: 0
License: Kit is GPL.  OpenIB.org is BSD license
Group: System Environment/Base
Vendor: Platform Computing Corporation
BuildArchitectures: noarch

# Use Exact versions to allow different versions of this kit to co-exist
Requires: dapl-devel = 1.2.1
Requires: kernel-ib-devel = 1.2.5.1
Requires: libibcm-devel = 1.0
Requires: libibcommon-devel = 1.0.4
Requires: libibmad-devel = 1.0.6
Requires: libibumad-devel = 1.0.6
Requires: libibverbs-devel = 1.1.1
Requires: libmlx4-devel = 0.1
Requires: libmthca-devel = 1.0.4
Requires: libopensm-devel = 3.0.3
Requires: libosmcomp-devel = 3.0.3
Requires: libosmvendor-devel = 3.0.3
Requires: librdmacm-devel = 1.0.2
Requires: ofed-src = 1.2.5.1 


%description
This package is a meta package for OFED development packages

%prep

%files

%pre

%post
# Place any component post install code here

%preun

%postun
# Place any component uninstall code here
# Generate scripts for the CFM to remove other packages
/bin/cat << 'EOF' >> /opt/kusu/lib/plugins/cfmclient/%{name}.remove
#!/bin/sh
yum -y remove dapl dapl-devel dapl-utils ibutils ipoibtools kernel-ib kernel-ib-devel libibcm libibcm-devel libibcommon libibcommon-devel libibmad libibmad-devel libibumad libibumad-devel libibverbs libibverbs-devel libibverbs-utils libmlx4 libmlx4-devel libmthca libmthca-devel libopensm libopensm-devel libosmcomp libosmcomp-devel libosmvendor libosmvendor-devel librdmacm librdmacm-devel librdmacm-utils libsdp mstflint ofed-docs ofed-scripts openib-diags opensm perftest sdpnetstat srptools tvflash
rm -rf /opt/kusu/lib/plugins/cfmclient/%{name}.remove
EOF

