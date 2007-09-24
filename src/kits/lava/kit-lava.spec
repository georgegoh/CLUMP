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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
# 
#
Summary: Lava Kit
Name: kit-lava
Version: 1.0
Release: 0
License: Something
Group: System Environment/Base
Vendor: Platform Computing Corporation
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
BuildArch: noarch
AutoReq: no

%description
This package is destined for the installer node and serves as an 
information container for the database.  

%prep

%install
docdir=$RPM_BUILD_ROOT/depot/www/kits/%{name}/%{version}
plugdir=$RPM_BUILD_ROOT/opt/kusu/lib/plugins

rm -rf $RPM_BUILD_ROOT
mkdir -p $docdir

# Add your own plugins if needed
mkdir -p $plugdir/addhost
mkdir -p $plugdir/genconfig
mkdir -p $plugdir/ngedit

/usr/bin/install -m 444 %{_topdir}/docs/index.html    $docdir
/usr/bin/install -m 444 %{_topdir}/docs/readme.html   $docdir
/usr/bin/install -m 444 %{_topdir}/docs/LICENSE       $docdir
/usr/bin/install -m 444 %{_topdir}/docs/lava_admin_1.0.pdf  $docdir
/usr/bin/install -m 444 %{_topdir}/docs/lava_using_1.0.pdf $docdir

/usr/bin/install -m 444 %{_topdir}/plugins/addhost/*.py    $plugdir/addhost
/usr/bin/install -m 444 %{_topdir}/plugins/genconfig/*.py   $plugdir/genconfig
/usr/bin/install -m 444 %{_topdir}/plugins/ngedit/*.py    $plugdir/ngedit


%clean
rm -rf $RPM_BUILD_ROOT

%files
# documentation
/depot/www/kits/%{name}/%{version}/index.html
/depot/www/kits/%{name}/%{version}/readme.html
/depot/www/kits/%{name}/%{version}/LICENSE
/depot/www/kits/%{name}/%{version}/lava_admin_1.0.pdf
/depot/www/kits/%{name}/%{version}/lava_using_1.0.pdf

# plugins
/opt/kusu/lib/plugins/addhost/*.py
/opt/kusu/lib/plugins/genconfig/*.py
/opt/kusu/lib/plugins/ngedit/*.py

%exclude /opt/kusu/lib/plugins/addhost/*.py?
%exclude /opt/kusu/lib/plugins/genconfig/*.py?
%exclude /opt/kusu/lib/plugins/ngedit/*.py?

%post

# In Anaconda install mode?
if [ -e /tmp/kusu/installer_running ]; then exit 0; fi 

# Check if MySQL is running if not, start it.
if [ `service mysqld status | grep -c running` -ne 1 ]; then
   service mysqld start
fi

# SQL/Shell/Python code to update the database.. The updates may optionally
# include Node group creation and component association

component_id_master=`sqlrunner -q 'SELECT cid FROM components WHERE cname = 'component-lava-master-v1.0'`
component_id_compute=`sqlrunner -q 'SELECT cid FROM components WHERE cname = 'component-lava-compute-v1.0'`

sqlrunner -q 'INSERT INTO ng_has_comp SET ngid = 1, cid = $component_id_master`

sqlrunner -q 'INSERT INTO ng_has_comp SET ngid = 2, cid = $component_id_compute'
sqlrunner -q 'INSERT INTO ng_has_comp SET ngid = 3, cid = $component_id_compute'
sqlrunner -q 'INSERT INTO ng_has_comp SET ngid = 4, cid = $component_id_compute'

%postun

# Check if MySQL is running if not, start it.
if [ `service mysqld status | grep -c running` -ne 1 ]; then
   service mysqld start
fi

# Code necessary to cleanup the database from any entries inserted by the %post

component_id_master=`sqlrunner -q 'SELECT cid FROM components WHERE cname = "component-lava-master-v1.0"'`
component_id_compute=`sqlrunner -q 'SELECT cid FROM components WHERE cname = "component-lava-compute-v1.0"'`

sqlrunner -q 'DELETE FROM ng_has_comp WHERE cid = $component_id_master OR cid = $component_id_compute'


