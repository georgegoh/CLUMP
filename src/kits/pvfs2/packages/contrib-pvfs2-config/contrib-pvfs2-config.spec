# Name of package
%define name contrib-pvfs2-config
%define srcname pvfs2-kernel-module

# Version
%define version 2.7.0

# Release
%define release 0

# Installation directory base prefix
%define package_prefix /usr/src/redhat/SRPMS

Name: %{name}
Version: %{version}
Release: %{release}
Packager: Platform Computing Corporation. <http://www.platform.com/>
#BuildRoot: /tmp/pvfs2
Summary: OCS Installation for kernel module for the PVFS2 Distributed Filesystem. 
License: GPL/LGPL
Vendor: None 
URL: http://www.pvfs.org/pvfs2
Group: System Environment/Base
BuildRequires: db4 >= 4.1
Requires: db4 >= 4.1
#BuildRequires: gtk2 >= 2.0
#Requires: gtk2 >= 2.0

%description
PVFS2 is a next generation parallel file system for Linux clusters. It
harnesses commodity storage and network technology to provide concurrent
access to data that is distributed across a (possibly large) collection
of servers.  PVFS2 serves as both a testbed for parallel I/O research
and as a freely available production-level tool for the cluster community.

This package contains the pvfs2 source distribution from which the kernel 
module will be built automatically.  The package is for use with OCS
as it will unpack on first boot, and install the module. 

%prep
echo "Prep Section"

%build

%install
if [ ! -d $RPM_BUILD_ROOT ]; then
	echo "The $(RPM_BUILD_ROOT) does not exist!"
	exit 1
fi

%files 
%defattr(-,root,root)
/usr/src/redhat/SRPMS/%{srcname}-%{version}-%{release}.src.rpm
%clean
