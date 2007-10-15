# Copyright (C) 2007 Platform Computing Corporation
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
# $Id$
# 

%define binaryarch linux2.6-glibc2.3-x86
%define clustername lava

Summary: Lava base package
Name: lava
Version: 1.0
Release: 0
License: Something
Group: Applications/System
Vendor: Platform Computing Corporation
BuildArchitectures: x86_64 i386
Prefix: /opt/lava
#Source: source_for_lava_coming
Buildroot: /var/tmp/%{name}-buildroot

%description
Platform Lava Batch scheduling

%package master-config
Summary: Lava master configuration
Group: Applications/System
Vendor: Platform Computing Corporation
Prefix: /opt/lava

%description master-config
Platform Lava Master configuration files

##
## PREP
##
%prep
rm -rf $RPM_BUILD_ROOT # /var/tmp/lava-buildroot
mkdir -p $RPM_BUILD_ROOT

# Make a bunch of directories
mkdir -p $RPM_BUILD_ROOT/opt/lava/work/%{clustername}/logdir
mkdir -p $RPM_BUILD_ROOT/opt/lava/work/%{clustername}/lsf_cmddir
mkdir -p $RPM_BUILD_ROOT/opt/lava/work/%{clustername}/lsf_indir
mkdir -p $RPM_BUILD_ROOT/opt/lava/log
mkdir -p $RPM_BUILD_ROOT/opt/lava/%{version}/include
mkdir -p $RPM_BUILD_ROOT/opt/lava/conf/lsbatch/%{clustername}/configdir
mkdir -p $RPM_BUILD_ROOT/opt/lava/%{version}/%{binaryarch}/bin
mkdir -p $RPM_BUILD_ROOT/opt/lava/%{version}/%{binaryarch}/etc
mkdir -p $RPM_BUILD_ROOT/opt/lava/%{version}/%{binaryarch}/lib
mkdir -p $RPM_BUILD_ROOT/etc/init.d
mkdir -p $RPM_BUILD_ROOT/etc/profile.d

## 

## Skipping this because we are not starting with a tar file

##
## BUILD
##
%build
tar -zxf %{name}%{version}_linux2.6-glibc2.3-x86.tar.Z -C $RPM_BUILD_ROOT/opt/lava/%{version}
rm -rf $RPM_BUILD_ROOT/opt/lava/%{version}/misc

##
## PRE
##
## %pre

##
## POST
##
%post

##
## PREUN
##
%preun
service lava stop

##
## POSTUN
##
%postun

##
## INSTALL
##
%install

# Install configs
install -m755 cshrc.lsf $RPM_BUILD_ROOT/opt/lava/conf
install -m755 profile.lsf $RPM_BUILD_ROOT/opt/lava/conf
install -m755 profile.lsf $RPM_BUILD_ROOT/etc/profile.d/lava.sh
install -m755 cshrc.lsf $RPM_BUILD_ROOT/etc/profile.d/lava.csh
install -m755 lsf.shared $RPM_BUILD_ROOT/opt/lava/conf
install -m755 lsf.task $RPM_BUILD_ROOT/opt/lava/conf

# Batch configuration
install -m644 lsb.modules $RPM_BUILD_ROOT/opt/lava/conf/lsbatch/%{clustername}/configdir
install -m644 lsb.params $RPM_BUILD_ROOT/opt/lava/conf/lsbatch/%{clustername}/configdir
install -m644 lsb.queues $RPM_BUILD_ROOT/opt/lava/conf/lsbatch/%{clustername}/configdir
install -m644 lsb.users $RPM_BUILD_ROOT/opt/lava/conf/lsbatch/%{clustername}/configdir

# MPI Wrappers
install -m755 mpich-mpirun $RPM_BUILD_ROOT/opt/lava/%{version}/%{binaryarch}/bin
install -m755 openmpi-mpirun $RPM_BUILD_ROOT/opt/lava/%{version}/%{binaryarch}/bin
install -m755 lam-mpirun $RPM_BUILD_ROOT/opt/lava/%{version}/%{binaryarch}/bin
install -m755 mpich-mpirun $RPM_BUILD_ROOT/opt/lava/%{version}/%{binaryarch}/bin

install -m444 license_agreement.txt $RPM_BUILD_ROOT/opt/lava/%{version}
install -m755 lava.init $RPM_BUILD_ROOT/etc/init.d/lava

mkdir -p $RPM_BUILD_ROOT/opt/lava/log

##
## FILES
##
%files
%defattr(-,root,root)
/etc/init.d/lava
/etc/profile.d/*
/opt/lava/%{version}/*
%attr(0755, root, root) /opt/lava/1.0/linux2.6-glibc2.3-x86/etc/eauth
%attr(-,lavaadmin,lavaadmin) /opt/lava/conf
%attr(-,lavaadmin,lavaadmin) /opt/lava/conf/cshrc.lsf
%attr(-,lavaadmin,lavaadmin) /opt/lava/conf/profile.lsf

%files master-config
%defattr(-,lavaadmin,lavaadmin)
%attr(-,lavaadmin,lavaadmin) /opt/lava/conf
%attr(-,lavaadmin,lavaadmin) /opt/lava/work
%exclude /opt/lava/conf/cshrc.lsf
%exclude /opt/lava/conf/profile.lsf

##
## CLEAN
##
%clean
/bin/rm -rf $RPM_BUILD_ROOT
