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

%define LSF_VERSION 7_0_1
%define EGO_VERSION 1_2
%define LSF_MASTER_COMP component-LSF-Master-v%{LSF_VERSION}
%define LSF_COMPUTE_COMP component-LSF-Compute-v%{LSF_VERSION}
%define KNAME_CLUSTERNAME LSF%{LSF_VERSION}_ClusterName
%define LSF_MASTER_NODEGROUP lsf-master-candidate

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
tmpldir=$RPM_BUILD_ROOT/etc/cfm/templates

rm -rf $RPM_BUILD_ROOT

mkdir -p $tmpldir
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

/usr/bin/install -m 444 %{_topdir}/templates/default.* $tmpldir

/usr/bin/install -d $tmpldir/lsbatch/default/configdir
/usr/bin/install -m 444 %{_topdir}/templates/lsbatch/default/configdir/* $tmpldir/lsbatch/default/configdir

%clean
rm -rf $RPM_BUILD_ROOT

%files
%dir /etc/cfm/templates
/etc/cfm/templates/default.*
%dir /etc/cfm/templates/lsbatch
%dir /etc/cfm/templates/lsbatch/default
%dir /etc/cfm/templates/lsbatch/default/configdir
/etc/cfm/templates/lsbatch/default/configdir/*

# documentation
/depot/www/kits/%{name}/%{version}/*

# plugins
/opt/kusu/lib/plugins/addhost/*.py
/opt/kusu/lib/plugins/genconfig/*.py
/opt/kusu/lib/plugins/ngedit/*.py
/etc/rc.kusu.d/S11lsf-genconfig

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

KID=`sqlrunner -q "SELECT kid FROM kits WHERE rname = \"lsf\" AND version = \"%{version}\""`

if [ -z "$KID" ]; then
	echo "Error: LSF kit does not appear to be installed"
	exit 1
fi

# Insert this kit into all repos
# for repoid in `sqlrunner -q "SELECT repoid FROM repos"`; do
	# sqlrunner -q "INSERT INTO repos_have_kits (repoid, kid) VALUES ($repoid, $KID)"
# done

# Attempt to get NGID for "lsf-master-candidate" nodegroup.  This will
# not succeed on a 'clean' install.
MASTER_NGID=`sqlrunner -q "SELECT ngid FROM nodegroups WHERE ngname = \"%{LSF_MASTER_NODEGROUP}\""`

for cid in `sqlrunner -q "SELECT cid FROM components WHERE kid = $KID"`; do
	# Remove association to 'lsf-master-candidate' nodegroup
	if [ -n "$MASTER_NGID" ]; then
		sqlrunner -q "DELETE FROM ng_has_comp WHERE ngid = $MASTER_NGID AND cid = $cid"
	fi
	
	# Remove association to compute nodegroup
	sqlrunner -q "DELETE FROM ng_has_comp WHERE ngid = 2 AND cid = $cid"
done

# Remove components entries
sqlrunner -q "DELETE FROM components WHERE kid = $KID"

for os in `sqlrunner -q "SELECT DISTINCT ostype FROM repos"`; do
        # Add master component
        sqlrunner -q "INSERT INTO components SET cname = \"%{LSF_MASTER_COMP}\", cdesc = \"LSF Master Candidate\", kid = $KID, os = \"$os\""

        # Add compute component
        sqlrunner -q "INSERT INTO components SET cname = \"%{LSF_COMPUTE_COMP}\", cdesc = \"LSF Compute Node\", kid = $KID, os = \"$os\""
done

# Create duplicate nodegroup
if [ -z "$MASTER_NGID" ]; then
	# lsf-master-candidate nodegroup does not previously exist (good!)

	# Use the compute nodegroup as a template for the 
	# 'lsf-master-candidate' nodegroup
	NGNAME=`sqlrunner -q "SELECT ngname FROM nodegroups WHERE ngid = 2"`

	ngedit -c $NGNAME -n %{LSF_MASTER_NODEGROUP}

	MASTER_NGID=`sqlrunner -q "SELECT ngid FROM nodegroups WHERE ngname = \"%{LSF_MASTER_NODEGROUP}\""`

	sqlrunner -q "UPDATE nodegroups SET nameformat = \"lsfmaster-#RR-#NN\" WHERE ngid = $MASTER_NGID"
fi

# Get CID for LSF compute component
CID=`sqlrunner -q "SELECT cid FROM components WHERE kid = $KID AND cname = \"%{LSF_COMPUTE_COMP}\" AND os=(SELECT repos.ostype FROM repos, nodegroups WHERE nodegroups.ngid = 2 AND nodegroups.repoid = repos.repoid)"`

if [ -z "$CID" ]; then
        echo "Error: unable to get CID of LSF compute compoent"
        exit 1
fi

# Create association from compute nodegroup to LSF compute component
sqlrunner -q "INSERT INTO ng_has_comp SET ngid = 2, cid = $CID"

# Create association from 'lsf-master-candidate' nodegroup to LSF master
# component
NEW_CID=`sqlrunner -q "SELECT cid FROM components WHERE kid = $KID AND cname = \"%{LSF_MASTER_COMP}\" AND os=(SELECT repos.ostype FROM repos, nodegroups WHERE nodegroups.ngid = $MASTER_NGID and nodegroups.repoid = repos.repoid)"`

sqlrunner -q "INSERT INTO ng_has_comp SET cid = $NEW_CID, ngid = $MASTER_NGID"

# Assign the nodes to the default clustername
CNAME=`sqlrunner -q "SELECT kvalue FROM appglobals WHERE kname = \"PrimaryInstaller\""`
sqlrunner -q "INSERT INTO appglobals SET kname = \"%{KNAME_CLUSTERNAME}\", kvalue=\"$CNAME\", ngid = $MASTER_NGID"
sqlrunner -q "INSERT INTO appglobals SET kname = \"%{KNAME_CLUSTERNAME}\", kvalue=\"$CNAME\", ngid = 2"

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

ngedit -d %{LSF_MASTER_NODEGROUP}

sqlrunner -q "DELETE FROM appglobals WHERE kname='%{KNAME_CLUSTERNAME}'"

%postun
rm -rf /opt/lsf
rm -rf /opt/kusu/lib/plugins/addhost/10-lsf*%{LSF_VERSION}.py?
rm -rf /opt/kusu/lib/plugins/addhost/11-lsf*%{LSF_VERSION}.py?
rm -rf /opt/kusu/lib/plugins/genconfig/lsf*%{LSF_VERSION}.py?
rm -rf /opt/kusu/lib/plugins/genconfig/ego*%{EGO_VERSION}.py?
rm -rf /opt/kusu/lib/plugins/ngedit/lsf*%{LSF_VERSION}.py?
