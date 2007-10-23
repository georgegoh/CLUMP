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

%define COMP1 component-lava-master-v1_0
%define COMP2 component-lava-compute-v1_0
%define kitname lava

# ignore unpackaged files
%define _unpackaged_files_terminate_build 0

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
docdir=$RPM_BUILD_ROOT/depot/www/kits/%{kitname}/%{version}
plugdir=$RPM_BUILD_ROOT/opt/kusu/lib/plugins

rm -rf $RPM_BUILD_ROOT
mkdir -p $docdir
mkdir -p $RPM_BUILD_ROOT/etc/rc.kusu.d

# Add your own plugins if needed
mkdir -p $plugdir/addhost
mkdir -p $plugdir/genconfig
mkdir -p $plugdir/ngedit

/usr/bin/install -m 755 %{_topdir}/S10lava-genconfig $RPM_BUILD_ROOT/etc/rc.kusu.d/
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
/depot/www/kits/%{kitname}/%{version}/index.html
/depot/www/kits/%{kitname}/%{version}/readme.html
/depot/www/kits/%{kitname}/%{version}/LICENSE
/depot/www/kits/%{kitname}/%{version}/lava_admin_1.0.pdf
/depot/www/kits/%{kitname}/%{version}/lava_using_1.0.pdf

# plugins
/opt/kusu/lib/plugins/addhost/*.py
/opt/kusu/lib/plugins/genconfig/*.py
/opt/kusu/lib/plugins/ngedit/*.py

/etc/rc.kusu.d/S10lava-genconfig
#%exclude /opt/kusu/lib/plugins/addhost/*.py?
#%exclude /opt/kusu/lib/plugins/genconfig/*.py?
#%exclude /opt/kusu/lib/plugins/ngedit/*.py?

%pre
PATH=$PATH:/opt/kusu/sbin
export PATH
if [ -d /opt/kusu/lib ]; then
    PYTHONPATH=/opt/kusu/lib64/python:/opt/kusu/lib/python:
else
    PYTHONPATH=FIX_ME
fi
export PYTHONPATH

if [ ! -e /tmp/kusu/installer_running ]; then
    # Check if MySQL is running if not, start it.
    if [ `service mysqld status | grep -c running` -ne 1 ]; then
       service mysqld start
    fi
fi
KID=`sqlrunner -q "SELECT * FROM kits"`
if [ $? -ne 0 ]; then
   exit 1
fi


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
KID=`sqlrunner -q "SELECT kid FROM kits WHERE rname='lava' and version='%{version}'"`
if [ $? -ne 0 ]; then
   exit 0
fi

sqlrunner -q "DELETE FROM components WHERE kid=$KID"
sqlrunner -q "INSERT into components set cname='%{COMP1}', cdesc='Lava Master Candidate', kid=$KID, os='rhel-5-x86_64'"
sqlrunner -q "INSERT into components set cname='%{COMP1}', cdesc='Lava Master Candidate', kid=$KID, os='centos-5-x86_64'"
sqlrunner -q "INSERT into components set cname='%{COMP1}', cdesc='Lava Master Candidate', kid=$KID, os='fedora-6-x86_64'"
sqlrunner -q "INSERT into components set cname='%{COMP1}', cdesc='Lava Master Candidate', kid=$KID, os='fedora-7-x86_64'"
sqlrunner -q "INSERT into components set cname='%{COMP1}', cdesc='Lava Master Candidate', kid=$KID, os='rhel-5-i386'"
sqlrunner -q "INSERT into components set cname='%{COMP1}', cdesc='Lava Master Candidate', kid=$KID, os='centos-5-i386'"
sqlrunner -q "INSERT into components set cname='%{COMP1}', cdesc='Lava Master Candidate', kid=$KID, os='fedora-6-i386'"
sqlrunner -q "INSERT into components set cname='%{COMP1}', cdesc='Lava Master Candidate', kid=$KID, os='fedora-7-i386'"

sqlrunner -q "INSERT into components set cname='%{COMP2}', cdesc='Lava Compute Node', kid=$KID, os='rhel-5-x86_64'"
sqlrunner -q "INSERT into components set cname='%{COMP2}', cdesc='Lava Compute Node', kid=$KID, os='centos-5-x86_64'"
sqlrunner -q "INSERT into components set cname='%{COMP2}', cdesc='Lava Compute Node', kid=$KID, os='fedora-6-x86_64'"
sqlrunner -q "INSERT into components set cname='%{COMP2}', cdesc='Lava Compute Node', kid=$KID, os='fedora-7-x86_64'"
sqlrunner -q "INSERT into components set cname='%{COMP2}', cdesc='Lava Compute Node', kid=$KID, os='rhel-5-i386'"
sqlrunner -q "INSERT into components set cname='%{COMP2}', cdesc='Lava Compute Node', kid=$KID, os='centos-5-i386'"
sqlrunner -q "INSERT into components set cname='%{COMP2}', cdesc='Lava Compute Node', kid=$KID, os='fedora-6-i386'"
sqlrunner -q "INSERT into components set cname='%{COMP2}', cdesc='Lava Compute Node', kid=$KID, os='fedora-7-i386'"

CID1=`sqlrunner -q "SELECT cid from components where kid=$KID and cname='%{COMP1}' and os=(select repos.ostype from repos, nodegroups WHERE nodegroups.ngid=1 AND nodegroups.repoid=repos.repoid)"`

if [ "x$CID1" = "x" ]; then
   # The kit provides components that are not used with the installers OS#
   exit 0
fi

CID2=`sqlrunner -q "SELECT cid from components where kid=$KID and cname='%{COMP2}' and os=(select repos.ostype from repos, nodegroups WHERE nodegroups.ngid=1 AND nodegroups.repoid=repos.repoid)"`

# SQL/Shell/Python code to update the database.. The updates may optionally
# include Node group creation and component association
sqlrunner -q "INSERT INTO ng_has_comp SET ngid = 1, cid = $CID1"
sqlrunner -q "INSERT INTO ng_has_comp SET ngid = 2, cid = $CID2"
#sqlrunner -q "INSERT INTO ng_has_comp SET ngid = 3, cid = $CID2"
#sqlrunner -q "INSERT INTO ng_has_comp SET ngid = 4, cid = $CID2"

if [ ! -e /tmp/kusu/installer_running ]; then
   # Running outside of Anaconda
   if [ -f /etc/rc.kusu.d/S10lava-genconfig ]; then
       /etc/rc.kusu.d/S10lava-genconfig
   fi
#else
   # Running within Anaconda
fi

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

KID=`sqlrunner -q "SELECT kid FROM kits WHERE rname='lava' and version='%{version}'"`
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

KID=`sqlrunner -q "SELECT kid FROM kits WHERE rname='lava' and version='%{version}'"`

if [ ! -z $KID ]; then
   sqlrunner -q "DELETE FROM ng_has_comp WHERE cid in (select cid from components where kid=$KID)"
fi

# Do not delete the component entries.  Kitops will do this.  It fails otherwise.
rm -rf /opt/lava
rm -rf /opt/kusu/lib/plugins/addhost/10-lava*.py?
rm -rf /opt/kusu/lib/plugins/genconfig/lava*.py?
rm -rf /opt/kusu/lib/plugins/ngedit/lava*.py?

# Remove CFM symlinks
for i in `sqlrunner -q 'SELECT ngname FROM nodegroups WHERE ngid >= 1 AND ngid < 5'`; do
    if [ -d /etc/cfm/$i/opt/lava ]; then
       rm -rf /etc/cfm/$i/opt/lava
    fi
done

for i in `sqlrunner -q 'SELECT ngid FROM nodegroups WHERE ngid >= 1 AND ngid < 5'`; do
    if [ -d /opt/kusu/cfm/$i/opt/lava ]; then
       rm -rf /opt/kusu/cfm/$i/opt/lava
    fi
done

# Remove user/group on removal of kit
if [ `grep -c lavaadmin /etc/passwd ` -eq 1 ]; then
   /usr/sbin/userdel -r lavaadmin
fi
