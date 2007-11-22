# Name of package
%define name pvfs2-kernel-module
%define srcname pvfs

# Version
%define version 2.7.0

# Release
%define release 0

# Installation directory base prefix
%define pvfs2_prefix /opt/pvfs2
%define sed_pvfs2_prefix \\/opt\\/pvfs2

#%define kernel_version %(uname -r)

Summary: Kernel module or the PVFS2 Distributed Filesystem. 
Name: %{name}
Version: %{version}
Release: %{release}
License: GPL/LGPL
Packager: Platform Computing Inc. <http://www.platform.com/>
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
Source0: pvfs-%{version}.tar.gz
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

%prep
echo "Prep section called"
if [ -d $RPM_BUILD_ROOT ]; then
	rm -rf $RPM_BUILD_ROOT
fi

/bin/mkdir -p $RPM_BUILD_ROOT
%setup -n %{srcname}-%{version}

%build
echo "Build section called"

# Configure with no karma GUI, to allow building on machines without gtk
%ifarch x86_64
%configure --disable-server --enable-verbose-build --with-kernel=/usr/src/kernels/%{kernel_version}-x86_64
%else
%configure --disable-server --enable-verbose-build --with-kernel=/usr/src/kernels/%{kernel_version}-i386
%endif

# Build kernel module
/usr/bin/make just_kmod
/usr/bin/make just_kmod_install DESTDIR=$RPM_BUILD_ROOT

%install
echo "Install section called"

#mkdir -p $RPM_BUILD_ROOT/lib/modules/%{kernel_version}/kernel/fs/pvfs2

# Kernel module
cp src/kernel/linux-2.6/pvfs2.ko $RPM_BUILD_ROOT/lib/modules/%{kernel_version}/kernel/fs/pvfs2

%files 
%defattr(-,root,root)
/lib/modules/%{kernel_version}/kernel/fs/pvfs2/pvfs2.ko

%post

%clean
if [ -d $RPM_BUILD_ROOT ]; then
	/bin/rm -rf $RPM_BUILD_ROOT
fi
