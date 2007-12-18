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

%define __find_requires %{nil}
%define __find_provides %{nil}

%define lsf_major_version  7.0
%define lsfversion 7.0.2
%define lsfadmin    lsfadmin

%ifarch i386
%define lsfbintype  linux2.6-glibc2.3-x86
%else 
%define lsfbintype  linux2.6-glibc2.3-x86_64
%endif

Summary: Platform(R) LSF(R) binaries
Name: lsf
Version: %{lsfversion}
Release: 0
License: Commercial
Group: System Environment/Base
Vendor: Platform Computing Corporation
BuildArch: x86_64
Requires: coreutils, chkconfig, shadow-utils

%description
This package contains the LSF(R) binaries.

# %package master-config
# Summary: Platform LSF(R) master configuration
# Group: Applications/System
# Vendor: Platform Computing Corporation
# Prefix: /opt/lsf
# Requires: lsf

# %description master-config
# Platform(R) LSF(R) Master configuration files

%prep

%pre
if [ `grep -c lsfadmin /etc/group` -eq 0 ]; then \
	groupadd -g 495 lsfadmin; \
fi

if [ `grep -c lsfadmin /etc/passwd` -eq 0 ]; then \
	adduser -u 495 -d "/home/lsfadmin" -g lsfadmin -m lsfadmin ;\
fi

%install
rm -rf $RPM_BUILD_ROOT

%clean
rm -rf $RPM_BUILD_ROOT

%files
%dir /opt/lsf
/opt/lsf/%{lsf_major_version}/*
%attr(-, %{lsfadmin}, -) %dir /opt/lsf/log
%attr(-, %{lsfadmin}, -) %dir /opt/lsf/conf
%attr(-, %{lsfadmin}, -) %dir /opt/lsf/conf/ego
%attr(-, %{lsfadmin}, -) %dir /opt/lsf/conf/lsbatch
%attr(-, %{lsfadmin}, %{lsfadmin}) %dir /opt/lsf/patch
%attr(-, %{lsfadmin}, %{lsfadmin}) %dir /opt/lsf/patch/backup
%attr(-, %{lsfadmin}, %{lsfadmin}) %dir /opt/lsf/patch/lock
%attr(-, %{lsfadmin}, %{lsfadmin}) %dir /opt/lsf/patch/patchdb/*
%attr(-, %{lsfadmin}, -) %dir /opt/lsf/work
%attr(-, %{lsfadmin}, -) /opt/lsf/patch.conf
%attr(-, %{lsfadmin}, -) /opt/lsf/conf/lsf.task
%attr(-, %{lsfadmin}, -) /opt/lsf/conf/profile.lsf
%attr(-, %{lsfadmin}, -) /opt/lsf/conf/cshrc.lsf

%post
/bin/ln -s /opt/lsf/conf/profile.lsf /etc/profile.d/lsf.sh
/bin/ln -s /opt/lsf/conf/cshrc.lsf /etc/profile.d/lsf.csh
/bin/ln -s /opt/lsf/%{lsf_major_version}/%{lsfbintype}/etc/lsf_daemons /etc/init.d/lsf_daemons
/sbin/chkconfig --add lsf_daemons

%preun
# Setup LSF environment
if [ -f /opt/lsf/conf/profile.lsf ]; then
    . /opt/lsf/conf/profile.lsf
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
if [ -h /opt/lsf/conf -a -d /opt/lsf/conf.BAK ]; then
    # Cleanup NFS
    if [ -d /opt/lsf/nfs/conf ]; then
      umount /opt/lsf/nfs
      grep -v "/opt/lsf/nfs" /etc/fstab > /etc/fstab.1
      cp /etc/fstab.1 /etc/fstab
      rm /etc/fstab.1
      rm -f /opt/lsf/conf
      if [ -h /opt/lsf/work ]; then
          rm -f /opt/lsf/work
      fi
    fi

    # Restore Original conf dir
    mv /opt/lsf/conf.BAK /conf
fi

# Copy the license.dat file to /root
if [ -f /opt/lsf/conf/license.dat ]; then
   echo "Backing up license file to /root"
   cp /opt/lsf/conf/license.dat /root
fi

%postun
# Remove initscript
/sbin/chkconfig --del lsf_daemons >& /dev/null || :
rm -f /etc/rc.d/init.d/lsf_daemons

# Remove symlinks
rm -f /etc/profile.d/lsf.sh /etc/profile.d/lsf.csh
