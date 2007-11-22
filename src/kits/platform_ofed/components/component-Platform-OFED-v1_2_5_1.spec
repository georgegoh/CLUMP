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

Summary: Platform OFED Component
Name: component-Platform-OFED-v1_2_5_1
Version: 1.2.5.1
Release: 0
License: Kit is GPL.  OpenIB.org is BSD license
Group: System Environment/Base
Vendor: Platform Computing Corporation
BuildArchitectures: noarch

# Use Exact versions to allow different versions of this kit to co-exist
Requires: dapl = 1.2.1
Requires: dapl-utils = 1.2.1
Requires: ibutils = 1.2
Requires: ipoibtools = 1.1
Requires: kernel-ib = 1.2.5.1
Requires: libibcm = 1.0
Requires: libibcommon = 1.0.4
Requires: libibmad = 1.0.6
Requires: libibumad = 1.0.6
Requires: libibverbs = 1.1.1
Requires: libibverbs-utils = 1.1.1
Requires: libmlx4 = 0.1
Requires: libmthca = 1.0.4
Requires: libopensm = 3.0.3
Requires: libosmcomp = 3.0.3
Requires: libosmvendor = 3.0.3
Requires: librdmacm = 1.0.2
Requires: librdmacm-utils = 1.0.2
Requires: libsdp = 1.1.99
Requires: mstflint = 1.2
Requires: ofed-docs = 1.2.5.1
Requires: ofed-scripts = 1.2.5.1
Requires: openib-diags = 1.2.7
Requires: opensm = 3.0.3
Requires: perftest = 1.2
Requires: sdpnetstat = 1.50
Requires: srptools = 0.0.4
Requires: tvflash = 0.9.0


%description
This package is a meta package for OFED packages

%prep

%pre

%install
/usr/bin/install -m 755 %{_topdir}/S40ofed-setulimit.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/

%post
# Place any component post install code here

%preun

%postun
# Place any component uninstall code here

# Generate scripts for the CFM to remove other packages
/bin/cat << 'EOF' >> /opt/kusu/lib/plugins/cfmclient/%{name}.remove
#!/bin/sh
yum -y remove dapl dapl-utils ibutils ipoibtools kernel-ib libibcm libibcommon libibmad libibumad libibverbs libibverbs-utils libmlx4 libmthca libopensm libosmcomp libosmvendor librdmacm librdmacm-utils libsdp mstflint ofed-scripts openib-diags perftest sdpnetstat srptools tvflash
rm -rf /opt/kusu/lib/plugins/cfmclient/%{name}.remove
EOF

%files
/etc/rc.kusu.d/S40ofed-setulimit.rc.py
