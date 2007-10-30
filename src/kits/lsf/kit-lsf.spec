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

%define COMP1 component-LSF-Master-v7_0_1
%define COMP2 component-LSF-Compute-v7_0_1

Summary: LSF Kit
Name: kit-lsf
Version: 7.0.1
Release: 0
License: Commercial
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
mkdir -p $RPM_BUILD_ROOT/etc/rc.kusu.d

# Add your own plugins if needed
mkdir -p $plugdir/addhost
mkdir -p $plugdir/genconfig
mkdir -p $plugdir/ngedit

/usr/bin/install -m 755 %{_topdir}/S11lsf-genconfig $RPM_BUILD_ROOT/etc/rc.kusu.d/
cp -r %{_topdir}/docs/LICENSE $docdir
cp -r %{_topdir}/docs/readme.html $docdir
cp -r %{_topdir}/docs/files/* $docdir
find $docdir -exec chmod 444 {} \;

/usr/bin/install -m 444 %{_topdir}/plugins/addhost/*.py    $plugdir/addhost
/usr/bin/install -m 444 %{_topdir}/plugins/genconfig/*.py   $plugdir/genconfig
/usr/bin/install -m 444 %{_topdir}/plugins/ngedit/*.py    $plugdir/ngedit

%clean
rm -rf $RPM_BUILD_ROOT

%files
# documentation
/depot/www/kits/%{name}/%{version}/*

# plugins
/opt/kusu/lib/plugins/addhost/*.py
/opt/kusu/lib/plugins/genconfig/*.py
/opt/kusu/lib/plugins/ngedit/*.py

/etc/rc.kusu.d/S11lsf-genconfig
#%exclude /opt/kusu/lib/plugins/addhost/*.py?
#%exclude /opt/kusu/lib/plugins/genconfig/*.py?
#%exclude /opt/kusu/lib/plugins/ngedit/*.py?

%pre
PATH=$PATH:/opt/kusu/sbin
export PATH

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
PATH=$PATH:/opt/kusu/sbin
export PATH
if [ -d /opt/kusu/lib ]; then
    PYTHONPATH=/opt/kusu/lib64/python:/opt/kusu/lib/python:
else
    PYTHONPATH=FIX_ME
fi
export PYTHONPATH

# Make the component entries
KID=`sqlrunner -q "SELECT kid FROM kits WHERE rname='lsf' and version='%{version}'"`
if [ $? -ne 0 ]; then
   exit 0
fi

sqlrunner -q "DELETE FROM components WHERE kid=$KID"
sqlrunner -q "INSERT into components set cname='%{COMP1}', cdesc='LSF Master Candidate', kid=$KID, os='rhel-5-x86_64'"
sqlrunner -q "INSERT into components set cname='%{COMP1}', cdesc='LSF Master Candidate', kid=$KID, os='centos-5-x86_64'"

sqlrunner -q "INSERT into components set cname='%{COMP2}', cdesc='LSF Compute Node', kid=$KID, os='rhel-5-x86_64'"
sqlrunner -q "INSERT into components set cname='%{COMP2}', cdesc='LSF Compute Node', kid=$KID, os='centos-5-x86_64'"

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
# sqlrunner -q "INSERT INTO ng_has_comp SET ngid = 3, cid = $CID2"
# sqlrunner -q "INSERT INTO ng_has_comp SET ngid = 4, cid = $CID2"

# Assign the nodes to the default clustername
CNAME=`sqlrunner -q "SELECT kvalue FROM appglobals WHERE kname='PrimaryInstaller'"`
sqlrunner -q "INSERT INTO appglobals SET kname='LSF7_0_1_ClusterName', kvalue=\"$CNAME\", ngid=1"
sqlrunner -q "INSERT INTO appglobals SET kname='LSF7_0_1_ClusterName', kvalue=\"$CNAME\", ngid=2"

NGNAME=`sqlrunner -q "SELECT ngname FROM nodegroups WHERE ngid=2"`

OSTYPE=`sqlrunner -q "SELECT ostype FROM repos WHERE repoid=1000"`

ngedit -c $NGNAME -n lsf-master-candidate

NEW_NGID=`sqlrunner -q "SELECT ngid FROM nodegroups where ngname = \"lsf-master-candidate\""`

sqlrunner -q "INSERT INTO appglobals SET kname='LSF7_0_1_ClusterName', kvalue=\"$CNAME\", ngid=$NEW_NGID"

NEW_CID=`sqlrunner -q "SELECT cid from components where kid=$KID and cname='%{COMP1}' and os=(select repos.ostype from repos, nodegroups WHERE nodegroups.ngid=2 AND nodegroups.repoid=repos.repoid)"`

OLD_CID=`sqlrunner -q "SELECT cid from components where kid=$KID and cname='%{COMP2}' and os=(select repos.ostype from repos, nodegroups WHERE nodegroups.ngid=2 AND nodegroups.repoid=repos.repoid)"`

sqlrunner -q "UPDATE ng_has_comp SET cid=$NEW_CID WHERE ngid=$NEW_NGID AND cid=$OLD_CID"

if [ ! -e /tmp/kusu/installer_running ]; then
    # Running outside of Anaconda
    if [ -f /etc/rc.kusu.d/S11lsf-genconfig ]; then
	/etc/rc.kusu.d/S11lsf-genconfig
    fi
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

KID=`sqlrunner -q "SELECT kid FROM kits WHERE rname='lsf' AND version='%{version}'"`
if [ $? -ne 0 ]; then
    echo "Database is down.  Unable to remove kit."
    exit 1
fi
if [ ! -z $KID ]; then
    # Purge all the CFM entries for this kit
    for i in `sqlrunner -q "SELECT ngname FROM nodegroups, repos_have_kits WHERE nodegroups.repoid=repos_have_kits.repoid and repos_have_kits.kid=$KID"`; do
	if [ -d /etc/cfm/$i ]; then
		cd /etc/cfm/$i
		if [ -d /etc/cfm/$i/opt/lsf/conf ]; then
	    		rm -rf /etc/cfm/$i/opt/lsf
		fi
	fi
    done
    for i in `sqlrunner -q "SELECT ngid FROM nodegroups, repos_have_kits WHERE nodegroups.repoid=repos_have_kits.repoid and repos_have_kits.kid=$KID"`; do
	if [ -d /opt/kusu/cfm/$i ]; then
		cd /opt/kusu/cfm/$i
		if [ -d /opt/kusu/cfm/$i/opt/lsf/conf ]; then
	    		rm -rf /opt/kusu/cfm/$i/opt/lsf
		fi
	fi
    done
    # Remove associations if they exist
    sqlrunner -q "DELETE FROM ng_has_comp WHERE cid in (select cid from components where kid=$KID)"

fi

ngedit -d lsf-master-candidate

sqlrunner -q "DELETE FROM appglobals WHERE kname='LSF7_0_1_ClusterName'"

%postun
# POSTUN section
rm -rf /opt/lsf
rm -rf /opt/kusu/lib/plugins/addhost/10-lsf*7_0_1.py?
rm -rf /opt/kusu/lib/plugins/genconfig/lsf*7_0_1.py?
rm -rf /opt/kusu/lib/plugins/ngedit/lsf*7_0_1.py?
