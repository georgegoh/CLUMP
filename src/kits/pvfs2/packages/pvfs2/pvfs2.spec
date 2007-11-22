# Name of package
%define name pvfs

# Version
%define version 2.7.0

# Release
%define release 0

# Installation directory base prefix
%define pvfs2_prefix /opt/pvfs2
%define sed_pvfs2_prefix \\/opt\\/pvfs2

Summary: Utilities for the PVFS2 Distributed Filesystem. 
Name: %{name}
Version: %{version}
Release: %{release}
License: GPL/LGPL
Packager: Platform Computing Inc. <http://www.platform.com/>
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
Source0: %{name}-%{version}.tar.gz
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
%setup

%build
echo "Build section called"

# Configure with no karma GUI, to allow building on machines without gtk
%configure --enable-verbose-build

/usr/bin/make clean
/usr/bin/make V=1
# Fix for version 1.1.0 to build the pvfs2-client
/usr/bin/make src/apps/kernel/linux/pvfs2-client
if test $? -ne 0 ; then
   exit 1
fi
/usr/bin/make src/apps/kernel/linux/pvfs2-client-core
if test $? -ne 0 ; then
   exit 1
fi

%install
echo "Install section called"

/usr/bin/make install DESTDIR=$RPM_BUILD_ROOT
/usr/bin/make kmod_install

mkdir -p $RPM_BUILD_ROOT/etc/init.d
mkdir -p $RPM_BUILD_ROOT/opt/pvfs2/sbin
mkdir -p $RPM_BUILD_ROOT/opt/pvfs2/include
mkdir -p $RPM_BUILD_ROOT/opt/pvfs2/
mkdir -p $RPM_BUILD_ROOT/opt/pvfs2/lib
mkdir -p $RPM_BUILD_ROOT/opt/pvfs2/man/man1
mkdir -p $RPM_BUILD_ROOT/opt/pvfs2/bin

sed -e s/@prefix@/"%{sed_pvfs2_prefix}"/g < examples/pvfs2-server.rc.in > $RPM_BUILD_ROOT/etc/init.d/pvfs2-server

# Fix for version 1.1.0 ot install missing bits 
cp src/apps/kernel/linux/pvfs2-client $RPM_BUILD_ROOT/opt/pvfs2/sbin/
cp src/apps/kernel/linux/pvfs2-client-core $RPM_BUILD_ROOT/opt/pvfs2/sbin/

%files 
/etc/init.d/pvfs2-server
/%{pvfs2_prefix}/include/pvfs2-debug.h
/%{pvfs2_prefix}/include/pvfs2-encode-stubs.h
/%{pvfs2_prefix}/include/pvfs2.h
/%{pvfs2_prefix}/include/pvfs2-mgmt.h
/%{pvfs2_prefix}/include/pvfs2-request.h
/%{pvfs2_prefix}/include/pvfs2-sysint.h
/%{pvfs2_prefix}/include/pvfs2-types.h
/%{pvfs2_prefix}/include/pvfs2-util.h
/%{pvfs2_prefix}/lib/libpvfs2.a
/%{pvfs2_prefix}/man/man1/pvfs2.1
/%{pvfs2_prefix}/man/man1/pvfs2-cp.1
/%{pvfs2_prefix}/man/man1/pvfs2-fs-dump.1
/%{pvfs2_prefix}/man/man1/pvfs2-genconfig.1
/%{pvfs2_prefix}/man/man1/pvfs2-ls.1
/%{pvfs2_prefix}/man/man1/pvfs2-ping.1
/%{pvfs2_prefix}/man/man1/pvfs2-server.1
/%{pvfs2_prefix}/man/man1/pvfs2-set-debugmask.1
/%{pvfs2_prefix}/man/man1/pvfs2-set-mode.1
/%{pvfs2_prefix}/man/man1/pvfs2-statfs.1
/%{pvfs2_prefix}/man/man1/pvfs2-set-sync.1
/%{pvfs2_prefix}/man/man5/pvfs2.conf.5
/%{pvfs2_prefix}/man/man5/pvfs2tab.5
/%{pvfs2_prefix}/bin/pvfs2-check-config
/%{pvfs2_prefix}/bin/pvfs2-chmod
/%{pvfs2_prefix}/bin/pvfs2-chown
/%{pvfs2_prefix}/bin/pvfs2-config
/%{pvfs2_prefix}/bin/pvfs2-cp
/%{pvfs2_prefix}/bin/pvfs2-event-mon-example
/%{pvfs2_prefix}/bin/pvfs2-fsck
/%{pvfs2_prefix}/bin/pvfs2-fs-dump
/%{pvfs2_prefix}/bin/pvfs2-genconfig
/%{pvfs2_prefix}/bin/pvfs2-ls
/%{pvfs2_prefix}/bin/pvfs2-mkdir
/%{pvfs2_prefix}/bin/pvfs2-mkspace
/%{pvfs2_prefix}/bin/pvfs2-perf-mon-example
/%{pvfs2_prefix}/bin/pvfs2-ping
/%{pvfs2_prefix}/bin/pvfs2-remove-object
/%{pvfs2_prefix}/bin/pvfs2-rm
/%{pvfs2_prefix}/bin/pvfs2-set-debugmask
/%{pvfs2_prefix}/bin/pvfs2-set-eventmask
/%{pvfs2_prefix}/bin/pvfs2-set-mode
/%{pvfs2_prefix}/bin/pvfs2-showcoll
/%{pvfs2_prefix}/bin/pvfs2-statfs
/%{pvfs2_prefix}/bin/pvfs2-stat
/%{pvfs2_prefix}/bin/pvfs2-set-sync
/%{pvfs2_prefix}/bin/pvfs2-touch
/%{pvfs2_prefix}/bin/pvfs2-ln
/%{pvfs2_prefix}/bin/pvfs2-check-server
/%{pvfs2_prefix}/bin/pvfs2-change-fsid
/%{pvfs2_prefix}/bin/pvfs2-config-convert
/%{pvfs2_prefix}/bin/pvfs2-lsplus
/%{pvfs2_prefix}/bin/pvfs2-migrate-collection
/%{pvfs2_prefix}/bin/pvfs2-perror
/%{pvfs2_prefix}/bin/pvfs2-validate
/%{pvfs2_prefix}/bin/pvfs2-viewdist
/%{pvfs2_prefix}/bin/pvfs2-xattr
#/%{pvfs2_prefix}/bin/karma
/%{pvfs2_prefix}/sbin/pvfs2-client
/%{pvfs2_prefix}/sbin/pvfs2-client-core
/%{pvfs2_prefix}/sbin/pvfs2-server

%post

%clean
if [ -d $RPM_BUILD_ROOT ]; then
	/bin/rm -rf $RPM_BUILD_ROOT
fi

%preun 
if [ -x /etc/init.d/pvfs2-client ]; then
	echo "Stopping PVFS2 daemon"
	chkconfig pvfs2-client off
	/etc/init.d/pvfs2-client stop
fi

if [ -x /etc/init.d/pvfs2-server ]; then
	echo "Stopping PVFS2 server"
	chkconfig pvfs2-server off
	/etc/init.d/pvfs2-server stop
fi 
