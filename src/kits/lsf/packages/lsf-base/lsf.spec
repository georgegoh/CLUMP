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
#  NOTE:  The packageing of LSF is GPL, but LSF is NOT.
#

%define lsftopdir   /opt/lsf
%define lsfversion  7.0
#%define lsflimport  7869
%define lsfclustername XXX_clustername_XXX
%define lsfadmin    lsfadmin

%ifarch i386
%define lsfbintype  linux2.6-glibc2.3-x86
%else 
%define lsfbintype  linux2.6-glibc2.3-x86_64
%endif

%define egotopdir	/opt/lsf/ego
%define egoversion	1.2
%define egowaittime	60
%define ARCH x86_64

Summary: Platform(R) LSF(R) binaries
Name: lsf
Version: 7.0.1
Release: 0
License: Commercial
Group: System Environment/Base
Vendor: Platform Computing Corporation
BuildArch: x86_64
AutoReq: no

%description
This package contains the LSF(R) binaries.

%package master-config
Summary: Platform LSF(R) master configuration
Group: Applications/System
Vendor: Platform Computing Corporation
Prefix: /opt/lsf

%description master-config
Platform(R) LSF(R) Master configuration files

%prep

%install

docdir=$RPM_BUILD_ROOT/depot/www/kits/%{name}/%{version}
plugdir=$RPM_BUILD_ROOT/opt/kusu/lib/plugins

rm -rf $RPM_BUILD_ROOT
mkdir -p $docdir

%clean
rm -rf $RPM_BUILD_ROOT

%files

%attr(755, root, root) %dir %{lsftopdir}

%dir %{lsftopdir}/%{lsfversion}
%{lsftopdir}/%{lsfversion}/COPYRIGHT
%{lsftopdir}/%{lsfversion}/include
%{lsftopdir}/%{lsfversion}/%{lsfbintype}
%{lsftopdir}/%{lsfversion}/lsf_quick_admin.html
%{lsftopdir}/%{lsfversion}/man
%{lsftopdir}/%{lsfversion}/misc
%{lsftopdir}/%{lsfversion}/install
%{lsftopdir}/%{lsfversion}/license_agreement.txt
%{lsftopdir}/%{lsfversion}/lsfBinaryWrapper

%attr(755, %{lsfadmin}, root) %dir %{lsftopdir}/conf
%attr(644, %{lsfadmin}, root) %config %{lsftopdir}/conf/profile.lsf
%attr(644, %{lsfadmin}, root) %config %{lsftopdir}/conf/cshrc.lsf
%attr(644, %{lsfadmin}, root) %config %{lsftopdir}/conf/license.dat
#%attr(644, %{lsfadmin}, root) %config (noreplace) %{lsftopdir}/conf/lsf.conf
#%attr(644, %{lsfadmin}, root) %config (noreplace) %{lsftopdir}/conf/lsf.shared
#%attr(644, %{lsfadmin}, root) %config (noreplace) %{lsftopdir}/conf/lsf.task
#%attr(644, %{lsfadmin}, root) %config (noreplace) %{lsftopdir}/conf/lsf.cluster.%{lsfclustername}

#%attr(755, %{lsfadmin}, root) %dir %{lsftopdir}/conf/lsbatch
#%attr(755, %{lsfadmin}, root) %dir %{lsftopdir}/conf/lsbatch/%{lsfclustername}
#%attr(755, %{lsfadmin}, root) %dir %{lsftopdir}/conf/lsbatch/%{lsfclustername}/configdir
#%attr(644, %{lsfadmin}, root) %config (noreplace) %{lsftopdir}/conf/lsbatch/%{lsfclustername}/configdir/lsb.*

%attr(755, %{lsfadmin}, root) %dir %{lsftopdir}/log
%attr(755, %{lsfadmin}, root) %dir %{lsftopdir}/work
#%attr(755, %{lsfadmin}, root) %dir %{lsftopdir}/work/%{lsfclustername}
#%attr(755, %{lsfadmin}, root) %dir %{lsftopdir}/work/%{lsfclustername}/logdir
#%attr(777, %{lsfadmin}, root) %dir %{lsftopdir}/work/%{lsfclustername}/lsf_cmddir
#%attr(777, %{lsfadmin}, root) %dir %{lsftopdir}/work/%{lsfclustername}/lsf_indir

#all the EGO files will have to be added
%attr(755, %{lsfadmin}, root) %dir %{egotopdir}/kernel/conf
%attr(644, %{lsfadmin}, root) %config %{egotopdir}/kernel/conf/cshrc.ego
%attr(644, %{lsfadmin}, root) %config %{egotopdir}/kernel/conf/profile.ego
%attr(644, %{lsfadmin}, root) %config %{egotopdir}/kernel/conf/ego.conf
%attr(644, %{lsfadmin}, root) %config %{egotopdir}/kernel/conf/ego.shared
%attr(644, %{lsfadmin}, root) %config %{egotopdir}/kernel/conf/ego.cluster.%{lsfclustername}
#%attr(644, %{lsfadmin}, root) %config %{egotopdir}/kernel/conf/license.dat

#unlisted files under %{egotopdir}/kernel/conf/
%{egotopdir}/kernel/conf/*.xml
%{egotopdir}/kernel/conf/*.pem
%{egotopdir}/kernel/conf/wsg.conf
%{egotopdir}/kernel/conf/mibs
#end of unlisted files

%config %{egotopdir}/eservice/esc/conf
%dir %{egotopdir}/eservice/esc/log
%config %{egotopdir}/eservice/esd/conf/egosd_conf.xml
%config %{egotopdir}/eservice/esd/conf/esddefault.xml
%config %{egotopdir}/eservice/esd/conf/named/conf
%config %{egotopdir}/eservice/esd/conf/named/namedb/TMPL.db.EGODOMAIN.CORPDOMAIN
%config %{egotopdir}/eservice/esd/conf/named/namedb/db.ego
%config %{egotopdir}/eservice/esd/conf/named/namedb/localhost.zone
%config %{egotopdir}/eservice/esd/conf/named/namedb/named.ca
%config %{egotopdir}/eservice/esd/conf/named/namedb/named.local
#%dir %{egotopdir}/eservice/wsg/log
#%dir %{egotopdir}/eservice/wsg/tmp
#%dir %{egotopdir}/eservice/wsg/work

%{egotopdir}/%{egoversion}/%{lsfbintype}
%{egotopdir}/%{egoversion}/schema
%{egotopdir}/%{egoversion}/scripts
%{egotopdir}/%{egoversion}/man
%dir %{egotopdir}/%{egoversion}/docs

%attr(755, %{lsfadmin}, root) %dir %{egotopdir}/kernel/log
%dir %{egotopdir}/kernel/work

%files master-config
%defattr(-,lsfadmin,lavaadmin)
%attr(-,lsfadmin,lavaadmin) %{lsftopdir}/conf
%attr(-,lsfadmin,lavaadmin) %{lsftopdir}/work
%attr(644, %{lsfadmin}, root) %config (noreplace) %{lsftopdir}/conf/lsf.shared
%attr(644, %{lsfadmin}, root) %config (noreplace) %{lsftopdir}/conf/lsf.task
%attr(755, %{lsfadmin}, root) %dir %{lsftopdir}/conf/lsbatch
%attr(755, %{lsfadmin}, root) %dir %{lsftopdir}/conf/lsbatch/*
#%attr(644, %{lsfadmin}, root) %config (noreplace) %{lsftopdir}/conf/lsbatch/%{lsfclustername}/configdir/lsb.*

%attr(755, %{lsfadmin}, root) %dir %{lsftopdir}/log
%attr(755, %{lsfadmin}, root) %dir %{lsftopdir}/work/*
#%attr(755, %{lsfadmin}, root) %dir %{lsftopdir}/work/%{lsfclustername}
#%attr(755, %{lsfadmin}, root) %dir %{lsftopdir}/work/%{lsfclustername}/logdir
#%attr(777, %{lsfadmin}, root) %dir %{lsftopdir}/work/%{lsfclustername}/lsf_cmddir
#%attr(777, %{lsfadmin}, root) %dir %{lsftopdir}/work/%{lsfclustername}/lsf_indir

%exclude %{lsftopdir}/conf/cshrc.lsf
%exclude %{lsftopdir}/conf/profile.lsf
%exclude %{lsftopdir}/conf/license.dat
%exclude %{lsftopdir}/conf/lsf.conf
%exclude %{lsftopdir}/conf/lsbatch/%{lsfclustername}/configdir/lsb.hosts
%exclude %{lsftopdir}/conf/lsf.cluster.XXX_clustername_XXX

%preun
# Setup LSF environment
if [ -f %{lsftopdir}/conf/profile.lsf ]; then
    . %{lsftopdir}/conf/profile.lsf
fi

# Check the daemons   
if [ -d $LSF_SERVERDIR ] ; then   
    if [ -x $LSF_SERVERDIR/lsf_daemons ]; then
	$LSF_SERVERDIR/lsf_daemons stop
    fi
fi

## NOTE: EGO conf & work dir addition pending
##       interrelated with config-lsf-master script
# Restore configuration of LSF Master Candidate to suppress an error message
if [ -h %{lsftopdir}/conf -a -d %{lsftopdir}/conf.BAK ]; then
    # Cleanup NFS
    if [ -d %{lsftopdir}/nfs/conf ]; then
      umount %{lsftopdir}/nfs
      grep -v "%{lsftopdir}/nfs" /etc/fstab > /etc/fstab.1
      cp /etc/fstab.1 /etc/fstab
      rm /etc/fstab.1
      rm -f %{lsftopdir}/conf
      if [ -h %{lsftopdir}/work ]; then
          rm -f %{lsftopdir}/work
      fi
    fi
    # Restore Original conf dir
    mv %{lsftopdir}/conf.BAK /conf
fi

# Copy the license.dat file to /root
if [ -f %{lsftopdir}/conf/license.dat ]; then
   echo "Backing up license file to /root"
   cp %{lsftopdir}/conf/license.dat /root
fi


%postun

#Remove LSFHPC from the local machine
if [ -f /etc/rc.d/init.d/lsf ]; then
   echo "Removing init script for LSFHPC..."
   /sbin/chkconfig --del lsf >& /dev/null
   rm -f /etc/rc.d/init.d/lsf
fi
