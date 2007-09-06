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
Requires: component-lava-master-v1.0

%description
This package is destined for the installer node and serves as an 
information container for the database.  

%prep

%install
docdir=$RPM_BUILD_ROOT/repo/www/kits/%{name}/%{version}
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
/repo/www/kits/%{name}/%{version}/index.html
/repo/www/kits/%{name}/%{version}/readme.html
/repo/www/kits/%{name}/%{version}/LICENSE
/repo/www/kits/%{name}/%{version}/lava_admin_1.0.pdf
/repo/www/kits/%{name}/%{version}/lava_using_1.0.pdf


# plugins
/opt/kusu/lib/plugins/addhost/*.py
/opt/kusu/lib/plugins/genconfig/*.py
/opt/kusu/lib/plugins/ngedit/*.py

#%exclude /opt/kusu/lib/plugins/addhost/*.py?
#%exclude /opt/kusu/lib/plugins/genconfig/*.py?
#%exclude /opt/kusu/lib/plugins/ngedit/*.py?

%pre

%post

# Check if MySQL is running if not, start it.
if [ `service mysqld status | grep -c running` -ne 1 ]; then
   service mysqld start
fi

# SQL/Shell/Python code to update the database.. The updates may optionally
# include Node group creation and component association

nodegroup=`sqlrunner -q 'SELECT ngname FROM nodegroups WHERE ngid=2'`
ngedit -c $nodegroup -n new_nodegroup

component=`sqlrunner -q 'SELECT cid FROM components WHERE cname='component-service1'`
sqlrunner -q 'DELETE FROM ng_has_comp WHERE ngid = (SELECT ngid FROM nodegroups WHERE ngname = 'new_nodegroup')'

sqlrunner -q 'INSERT INTO ng_has_comp SET cid=$component, ngid=(SELECT ngid FROM nodegroups WHERE ngname = 'new_nodegroup')'

sqlrunner -q 'INSERT INTO ng_has_comp SET cid=(SELECT cid FROM components WHERE cname = 'component-base-node'), ngid = (SELECT ngid FROM nodegroups WHERE ngname = 'new_nodegroup')'

sqlrunner -q 'UPDATE nodegroups SET ngdesc='Brand Spanking new Node Group''


%preun

# Check if MySQL is running if not, start it.
if [ `service mysqld status | grep -c running` -ne 1 ]; then
   service mysqld start
fi

ngedit -d new_nodegroup

%postun
# Code necessary to cleanup the database from any entries inserted by the %post
