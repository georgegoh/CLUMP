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

%define COMP1 component-ntop-v3_3
%define kitname ntop

# ignore unpackaged files
%define _unpackaged_files_terminate_build 0

Summary: Ntop Kit
Name: kit-ntop
Version: 3.3
Release: 0
License: GPL
Group: System Environment/Base
Vendor: Platform Computing Corporation
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
BuildArch: x86_64
AutoReq: no

%description
This package is destined for the installer node and serves as an 
information container for the database.

%prep

%install
docdir=$RPM_BUILD_ROOT/depot/www/kits/%{kitname}/%{version}
plugdir=$RPM_BUILD_ROOT/opt/kusu/lib/plugins

rm -rf $RPM_BUILD_ROOT
mkdir -p $docdir
mkdir -p $RPM_BUILD_ROOT/etc/rc.kusu.d

# Add your own plugins if needed
mkdir -p $plugdir/ngedit

/usr/bin/install -m 444 %{_topdir}/docs/index.html    $docdir
/usr/bin/install -m 444 %{_topdir}/docs/readme.html   $docdir
/usr/bin/install -m 444 %{_topdir}/docs/COPYING       $docdir

/usr/bin/install -m 444 %{_topdir}/plugins/ngedit/*.py    $plugdir/ngedit

%clean
rm -rf $RPM_BUILD_ROOT

%files
# documentation
/depot/www/kits/%{kitname}/%{version}/index.html
/depot/www/kits/%{kitname}/%{version}/readme.html
/depot/www/kits/%{kitname}/%{version}/COPYING

# plugins
/opt/kusu/lib/plugins/ngedit/*.py

#%exclude /opt/kusu/lib/plugins/ngedit/*.py?

%pre


%post
# POST section
# the following line is needed because kitops will extract
# the %post sections during the kusu installer
if [ -e /tmp/kusu/installer_running ]; then exit 0; fi 

PATH=$PATH:/opt/kusu/sbin
export PATH
if [ -d /opt/kusu/lib ]; then
    PYTHONPATH=/opt/kusu/lib64/python:/opt/kusu/lib/python:
else
    PYTHONPATH=FIX_ME
fi
export PYTHONPATH

# Make the component entries because kitops is broken!!!
KID=`/opt/kusu/sbin/sqlrunner -q "SELECT kid FROM kits WHERE rname='ntop' and version='%{version}'"`
if [ $? -ne 0 ]; then
   exit 0
fi

/opt/kusu/sbin/sqlrunner -q "DELETE FROM components WHERE kid=$KID"
/opt/kusu/sbin/sqlrunner -q "INSERT into components set cname='%{COMP1}', cdesc='Ntop Monitoring', kid=$KID, os='rhel-5-x86_64'"
/opt/kusu/sbin/sqlrunner -q "INSERT into components set cname='%{COMP1}', cdesc='Ntop Monitoring', kid=$KID, os='centos-5-x86_64'"
/opt/kusu/sbin/sqlrunner -q "INSERT into components set cname='%{COMP1}', cdesc='Ntop Monitoring', kid=$KID, os='fedora-6-x86_64'"
/opt/kusu/sbin/sqlrunner -q "INSERT into components set cname='%{COMP1}', cdesc='Ntop Monitoring', kid=$KID, os='fedora-7-x86_64'"
/opt/kusu/sbin/sqlrunner -q "INSERT into components set cname='%{COMP1}', cdesc='Ntop Monitoring', kid=$KID, os='rhel-5-i386'"
/opt/kusu/sbin/sqlrunner -q "INSERT into components set cname='%{COMP1}', cdesc='Ntop Monitoring', kid=$KID, os='centos-5-i386'"
/opt/kusu/sbin/sqlrunner -q "INSERT into components set cname='%{COMP1}', cdesc='Ntop Monitoring', kid=$KID, os='fedora-6-i386'"

CID1=`/opt/kusu/sbin/sqlrunner -q "SELECT cid from components where kid=$KID and cname='%{COMP1}' and os=(select repos.ostype from repos, nodegroups WHERE nodegroups.ngid=1 AND nodegroups.repoid=repos.repoid)"`

if [ "x$CID1" = "x" ]; then
   # The kit provides components that are not used with the installers OS#
   exit 0
fi

# SQL/Shell/Python code to update the database.. The updates may optionally
# include Node group creation and component association
#/opt/kusu/sbin/sqlrunner -q "INSERT INTO ng_has_comp SET ngid = 1, cid = $CID1"
#/opt/kusu/sbin/sqlrunner -q "INSERT INTO ng_has_comp SET ngid = 2, cid = $CID2"
#/opt/kusu/sbin/sqlrunner -q "INSERT INTO ng_has_comp SET ngid = 3, cid = $CID2"
#/opt/kusu/sbin/sqlrunner -q "INSERT INTO ng_has_comp SET ngid = 4, cid = $CID2"

%preun
# PREUN section

# Test the database connection before allowing the package to be removed
PATH=$PATH:/opt/kusu/sbin
export PATH
if [ -d /opt/kusu/lib ]; then
    PYTHONPATH=/opt/kusu/lib64/python:/opt/kusu/lib/python:
else
    PYTHONPATH=FIX_ME
fi
export PYTHONPATH

KID=`/opt/kusu/sbin/sqlrunner -q "SELECT kid FROM kits WHERE rname='ntop' and version='%{version}'"`
if [ $? -ne 0 ]; then
    echo "Database is down.  Unable to remove kit."
    exit 1
fi

%postun
# POSTUN section

# Code necessary to cleanup the database from any entries inserted by the %post
PATH=$PATH:/opt/kusu/sbin
export PATH

if [ -d /opt/kusu/lib ]; then
    PYTHONPATH=/opt/kusu/lib64/python:/opt/kusu/lib/python:
else
    PYTHONPATH=FIX_ME
fi
export PYTHONPATH

KID=`/opt/kusu/sbin/sqlrunner -q "SELECT kid FROM kits WHERE rname='ntop' and version='%{version}'"`

if [ ! -z $KID ]; then
   /opt/kusu/sbin/sqlrunner -q "DELETE FROM ng_has_comp WHERE cid in (select cid from components where kid=$KID)"
fi

# Do not delete the component entries.  Kitops will do this.  It fails otherwise.
rm -rf /opt/ntop
rm -rf /opt/kusu/lib/plugins/ngedit/*ntop*.py?

# Remove CFM symlinks
for i in `/opt/kusu/sbin/sqlrunner -q 'SELECT ngname FROM nodegroups WHERE ngid = 1 AND ngid < 5'`; do
    if [ -d /etc/cfm/$i/opt/ntop ]; then
       rm -rf /etc/cfm/$i/opt/ntop
    fi
done

for i in `/opt/kusu/sbin/sqlrunner -q 'SELECT ngid FROM nodegroups WHERE ngid = 1 AND ngid < 5'`; do
    if [ -d /opt/kusu/cfm/$i/opt/ntop ]; then
       rm -rf /opt/kusu/cfm/$i/opt/ntop
    fi
done

# Remove user/group on removal of kit
if [ `grep -c ntop /etc/passwd ` -eq 1 ]; then
   /usr/sbin/userdel -r ntop
fi
