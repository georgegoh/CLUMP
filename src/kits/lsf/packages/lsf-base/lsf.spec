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
#  NOTE:  The packaging of LSF is GPL, but LSF is NOT.
#

%define lsftopdir   /opt/lsf
%define lsfconfdir  %{lsftopdir}/conf
%define lsfversion  7.0
%define lsfadmin    lsfadmin

%ifarch i386
%define lsfbintype  linux2.6-glibc2.3-x86
%else 
%define lsfbintype  linux2.6-glibc2.3-x86_64
%endif

%define egotopdir	/opt/lsf/ego
%define egoconfdir  %{egotopdir}/kernel/conf
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
Requires: coreutils, chkconfig, shadow-utils

%description
This package contains the LSF(R) binaries.

%package master-config
Summary: Platform LSF(R) master configuration
Group: Applications/System
Vendor: Platform Computing Corporation
Prefix: /opt/lsf
Requires: lsf

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

%{lsftopdir}/cshrc.platform
%{lsftopdir}/profile.platform

%attr(755, %{lsfadmin}, root) %dir %{lsfconfdir}
%attr(644, %{lsfadmin}, root) %{lsfconfdir}/profile.lsf
%attr(644, %{lsfadmin}, root) %{lsfconfdir}/cshrc.lsf
%attr(644, %{lsfadmin}, root) %config %{lsfconfdir}/license.dat

%attr(755, %{lsfadmin}, root) %dir %{lsftopdir}/log
%attr(755, %{lsfadmin}, root) %dir %{lsftopdir}/work

%dir %{egotopdir}
%dir %{egotopdir}/kernel
%attr(-, %{lsfadmin}, lsfadmin) %dir %{egoconfdir}

%config %{egoconfdir}/users.xml
%config %{egoconfdir}/cshrc.ego
%config %{egoconfdir}/profile.ego

#unlisted files under %{egoconfdir}/
%{egoconfdir}/*.pem
%{egoconfdir}/mibs
#end of unlisted files

%dir %{egotopdir}/eservice
%dir %{egotopdir}/eservice/esc
%dir %{egotopdir}/eservice/esc/log
%dir %{egotopdir}/eservice/esd
%dir %{egotopdir}/eservice/esd/conf/
%dir %{egotopdir}/eservice/esd/conf/named/
%config %{egotopdir}/eservice/esd/conf/egosd_conf.xml
%config %{egotopdir}/eservice/esd/conf/esddefault.xml
%config %{egotopdir}/eservice/esd/conf/named/conf
%dir %{egotopdir}/eservice/esd/conf/named/namedb
%config %{egotopdir}/eservice/esd/conf/named/namedb/TMPL.db.EGODOMAIN.CORPDOMAIN
%config %{egotopdir}/eservice/esd/conf/named/namedb/db.ego
%config %{egotopdir}/eservice/esd/conf/named/namedb/localhost.zone
%config %{egotopdir}/eservice/esd/conf/named/namedb/named.ca
%config %{egotopdir}/eservice/esd/conf/named/namedb/named.local

%{egotopdir}/%{egoversion}/%{lsfbintype}
%{egotopdir}/%{egoversion}/schema
%{egotopdir}/%{egoversion}/scripts
%{egotopdir}/%{egoversion}/man
%dir %{egotopdir}/%{egoversion}/docs
%dir %{egotopdir}/%{egoversion}

%attr(755, %{lsfadmin}, root) %dir %{egotopdir}/kernel/log
%attr(755, %{lsfadmin}, root) %dir %{egotopdir}/kernel/work

%files master-config
%defattr(-,lsfadmin,lsfadmin)
%config %{egoconfdir}/ResourceGroups.xml
%config %{egoconfdir}/ConsumerTrees.xml
%config %{egoconfdir}/wsg.conf

%post
/bin/ln -s %{lsfconfdir}/profile.lsf /etc/profile.d/lsf.sh
/bin/ln -s %{lsfconfdir}/cshrc.lsf /etc/profile.d/lsf.csh
/bin/ln -s %{lsftopdir}/%{lsfversion}/%{lsfbintype}/etc/lsf_daemons /etc/init.d/lsf_daemons
/sbin/chkconfig --add lsf_daemons

%preun
# Setup LSF environment
if [ -f %{lsfconfdir}/profile.lsf ]; then
    . %{lsfconfdir}/profile.lsf
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
if [ -h %{lsfconfdir} -a -d %{lsfconfdir}.BAK ]; then
    # Cleanup NFS
    if [ -d %{lsftopdir}/nfs/conf ]; then
      umount %{lsftopdir}/nfs
      grep -v "%{lsftopdir}/nfs" /etc/fstab > /etc/fstab.1
      cp /etc/fstab.1 /etc/fstab
      rm /etc/fstab.1
      rm -f %{lsfconfdir}
      if [ -h %{lsftopdir}/work ]; then
          rm -f %{lsftopdir}/work
      fi
    fi
    # Restore Original conf dir
    mv %{lsfconfdir}.BAK /conf
fi

# Copy the license.dat file to /root
if [ -f %{lsfconfdir}/license.dat ]; then
   echo "Backing up license file to /root"
   cp %{lsfconfdir}/license.dat /root
fi

%postun
# Remove initscript
/sbin/chkconfig --del lsf_daemons >& /dev/null || :
rm -f /etc/rc.d/init.d/lsf_daemons

# Remove symlinks
rm -f /etc/profile.d/lsf.sh /etc/profile.d/lsf.csh
