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

Summary: Ntop Component
Name: component-ntop-v3_3
Version: 3.3
Release: 0
License: GPL
Group: System Environment/Base
Vendor: Platform Computing Corporation
BuildArchitectures: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

# Use Exact versions to allow different versions of this kit to co-exist
Requires: perl-rrdtool, rrdtool, ntop
%description
This package is a meta package for OFED packages

%prep
rm -rf %{_tmppath}/%{name}-%{version}-%{release}-root
mkdir -p %{_tmppath}/%{name}-%{version}-%{release}-root/var/ntop

if [ "%{_arch}" == "x86_64" ]; then
cp ntop_pw.db.64 $RPM_BUILD_ROOT/var/ntop/ntop_pw.db
else
cp ntop_pw.db.32 $RPM_BUILD_ROOT/var/ntop/ntop_pw.db
fi

%files
/var/ntop/ntop_pw.db

%pre

%post
# Place any component post install code here

%preun

%postun
# Place any component uninstall code here

# Generate scripts for the CFM to remove other packages
/bin/cat << 'EOF' >> /opt/kusu/lib/plugins/cfmclient/%{name}.remove
#!/bin/sh
yum -y remove rrdtool ntop
rm -rf /opt/kusu/lib/plugins/cfmclient/%{name}.remove
EOF
