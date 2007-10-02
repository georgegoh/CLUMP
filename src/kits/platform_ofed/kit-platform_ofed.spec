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
Summary: Platform OFED Kit
Name: kit-platform_ofed
Version: 1.2.5.1
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

#/usr/bin/install -m 444 %{_topdir}/plugins/addhost/*.py    $plugdir/addhost
#/usr/bin/install -m 444 %{_topdir}/plugins/genconfig/*.py   $plugdir/genconfig
/usr/bin/install -m 444 %{_topdir}/plugins/ngedit/*.py    $plugdir/ngedit


%clean
rm -rf $RPM_BUILD_ROOT

%files
# documentation
/depot/www/kits/%{name}/%{version}/index.html
/depot/www/kits/%{name}/%{version}/readme.html
/depot/www/kits/%{name}/%{version}/LICENSE

# plugins
/opt/kusu/lib/plugins/ngedit/*.py

%exclude /opt/kusu/lib/plugins/ngedit/*.py?

%post

# include Node group creation and component association
echo "POST Start" > /tmp/platform_ofed.log
KID=`/opt/kusu/sbin/sqlrunner -q "SELECT kid FROM kits WHERE rname='platform_ofed'"`
echo "KID = $KID" >> /tmp/platform_ofed.log

# Setup the kit
if [ -z "$KID" ] ; then	
	echo "Adding kit entries to database" >> /tmp/platform_ofed.log
	/opt/kusu/sbin/sqlrunner -q "INSERT INTO kits SET rname='platform_ofed', rdesc='%{summary}', version='%{version}', isOS=0, removeable=1, arch='x86_64'" 2>/dev/null
	KID=`/opt/kusu/sbin/sqlrunner -q "SELECT kid FROM kits WHERE rname='platform_ofed'"`
	echo "KID = $KID" >> /tmp/platform_ofed.log
else
	echo "Updating kit" >> /tmp/platform_ofed.log
	/opt/kusu/sbin/sqlrunner -q "UPDATE kits SET arch='x86_64' WHERE rname='platform_ofed' AND rdesc='%{summary}' AND version='%{version}'"
fi

# Setup the first component
cid_imaged=`/opt/kusu/sbin/sqlrunner -q "SELECT cid FROM components WHERE cname = 'component-Platform-OFED-Diskless-v1_2_5_1'"`
echo "cid_imaged = $cid_imaged" >> /tmp/platform_ofed.log
if [ -z "$cid_imaged" ]; then
        echo "component-Platform-OFED-Diskless-v1_2_5_1 does not exist! creating.." >> /tmp/platform_ofed.log
        /opt/kusu/sbin/sqlrunner -q "INSERT INTO components SET cname='component-Platform-OFED-Diskless-v1_2_5_1', cdesc='Platform OFED component', os='rhel-5-x86_64', kid=$KID"
else
	echo "Updating component component-Platform-OFED-Diskless-v1_2_5_1" >> /tmp/platform_ofed.log
	/opt/kusu/sbin/sqlrunner -q "UPDATE components SET os='rhel-5-x86_64' WHERE cname='component-Platform-OFED-Diskless-v1_2_5_1' AND kid=$KID" >> /tmp/platform_ofed.log
fi

# Setup the second component
cid_full=`/opt/kusu/sbin/sqlrunner -q "SELECT cid FROM components WHERE cname='component-Platform-OFED-v1_2_5_1'"` >> /tmp/platform_ofed.log
echo "cid_full = $cid_full" >> /tmp/platform_ofed.log
if [ -z "$cid_full" ]; then
        echo "component-Platform-OFED-v1_2_5_1 does not exist! creating.." >> /tmp/platform_ofed.log
        /opt/kusu/sbin/sqlrunner -q "INSERT INTO components SET cname='component-Platform-OFED-v1_2_5_1', cdesc='Platform OFED component', os='rhel-5-x86_64', kid=$KID" >> /tmp/platform_ofed.log
else
	echo "Updating component component-Platform-OFED-Diskless-v1_2_5_1" >> /tmp/platform_ofed.log
	/opt/kusu/sbin/sqlrunner -q "UPDATE components SET os='rhel-5-x86_64' WHERE cname='component-Platform-OFED-v1_2_5_1' AND kid=$KID" >> /tmp/platform_ofed.log
fi
echo "Stop  post" >> /tmp/platform_ofed.log
exit 0

%postun
# ------------------  POST UNINSTALL  -------------------------
touch /tmp/platform_ofed.log
echo "Start  postun" >> /tmp/platform_ofed.log
cid_imaged=`/opt/kusu/sbin/sqlrunner -q "SELECT cid FROM components WHERE cname = 'component-Platform-OFED-Diskless-v1_2_5_1'"`
echo "   cid_imaged = $cid_imaged"
if [ -z "$cid_imaged" ]; then
        echo "component-Platform-OFED-Diskless-v1_2_5_1 does not exist" >> /tmp/platform_ofed.log
else
	echo "component-Platform-OFED-Diskless-v1_2_5_1 exists" >> /tmp/platform_ofed.log
	/opt/kusu/sbin/sqlrunner -q "DELETE FROM components WHERE cname='component-Platform-OFED-Diskless-v1_2_5_1' AND os='rhel-5-x86_64'"
fi

cid_full=`/opt/kusu/sbin/sqlrunner -q "SELECT cid FROM components WHERE cname='component-Platform-OFED-v1_2_5_1'"`
echo "   cid_full = $cid_full" >> /tmp/platform_ofed.log
if [ -z "$cid_full" ]; then
        echo "component-Platform-OFED-v1_2_5_1 does not exist" >> /tmp/platform_ofed.log
else
	/opt/kusu/sbin/sqlrunner -q "DELETE FROM components WHERE cname='component-Platform-OFED-v1_2_5_1' AND os='rhel-5-x86_64'" >> /tmp/platform_ofed.log
fi
exit 0
