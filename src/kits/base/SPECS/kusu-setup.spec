# $Id$
#
# Copyright (C) 2010 Platform Computing Inc
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

Summary: Setup module
name: kusu-setup
Version: 2.1
Release: 1
License: GPLv2
Group: System Environment/Base
Vendor: Platform Computing Inc.
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Source: %{name}-%{version}.%{release}.tar.gz
BuildArch: noarch
Requires: python pyparted createrepo yum-utils

%description
This package enables the bootstrap installation of KUSU.

%prep
%setup -n %{name} -q

%build
make nodeps

%install
rm -rf $RPM_BUILD_ROOT

%define _kusu /opt/kusu/bootstrap

# directories for kusu bootstrap
install -d $RPM_BUILD_ROOT/%{_kusu}
install -d $RPM_BUILD_ROOT/%{_kusu}/bin
install -d $RPM_BUILD_ROOT/%{_kusu}/sbin
install -d $RPM_BUILD_ROOT/%{_kusu}/lib64/python
install -d $RPM_BUILD_ROOT/%{_kusu}/libexec
install -d $RPM_BUILD_ROOT/%{_kusu}/share/doc/%{name}-%{version}

# directories for kusu-primitive and 3rdparty packages
%define _site_packages /lib/python2.4/site-packages

# for building purposes only
mkdir -p 3rdparty

# extract rpm package python-IPy
rpm2cpio python-IPy-*.rpm | cpio -dimv ./usr/lib/python2.4/site-packages/*
mkdir -p 3rdparty/python-IPy
mv usr/lib/python2.4/site-packages/* 3rdparty/python-IPy

# repackage python-IPy into kusu-setup
install -d $RPM_BUILD_ROOT/%{_kusu}/%{_site_packages}
for f in `find 3rdparty/python-IPy -type f | grep -v '\.svn' | grep -v '\/test' | cut -c20-`; do
    install 3rdparty/python-IPy/$f $RPM_BUILD_ROOT/%{_kusu}/%{_site_packages}/$f;
done

# package kusu-primitive
for d in `find buildout/primitive -type d | grep -v '\.svn' | grep -v '\/test' | cut -c19-`; do
    install -d $RPM_BUILD_ROOT/%{_kusu}/$d;
done

for f in `find buildout/primitive -type f | grep -v '\.svn' | grep -v '\/test' | cut -c19-`; do
    install buildout/primitive/$f $RPM_BUILD_ROOT/%{_kusu}/$f;
done

# extract rpm package python-sqlalchemy
rpm2cpio python-sqlalchemy-*.rpm | cpio -dimv ./usr/lib/python2.4/site-packages/sqlalchemy/* 
mv usr/lib/python2.4/site-packages/sqlalchemy 3rdparty/

# repackage python-sqlalchemy into kusu-setup
%define _sqlalchemy_lib %{_site_packages}/sqlalchemy
for d in `find 3rdparty/sqlalchemy -type d | grep -v '\.svn' | grep -v '\/test' | cut -c20-`; do
    install -d $RPM_BUILD_ROOT/%{_kusu}/%{_sqlalchemy_lib}/$d;
done

for f in `find 3rdparty/sqlalchemy -type f | grep -v '\.svn' | grep -v '\/test' | cut -c20-`; do
    install 3rdparty/sqlalchemy/$f $RPM_BUILD_ROOT/%{_kusu}/%{_sqlalchemy_lib}/$f;
done

# extract rpm package python-sqlite2
rpm2cpio python-sqlite2-*.rpm | cpio -dimv ./usr/lib64/python2.4/site-packages/pysqlite2/*
mv usr/lib64/python2.4/site-packages/pysqlite2 3rdparty/

# repackage python-sqlite2 into kusu-setup
%define _pysqlite2_lib %{_site_packages}/pysqlite2
install -d $RPM_BUILD_ROOT/%{_kusu}/%{_pysqlite2_lib}

for f in `find 3rdparty/pysqlite2 -type f | grep -v '\.svn' | grep -v '\/test' | cut -c20-`; do
    install 3rdparty/pysqlite2/$f $RPM_BUILD_ROOT/%{_kusu}/%{_pysqlite2_lib}/$f;
done

# extract rpm package python-psycopg2
rpm2cpio python-psycopg2-*.rpm | cpio -dimv ./usr/lib64/python2.4/site-packages/psycopg2/* 
mv usr/lib64/python2.4/site-packages/psycopg2 3rdparty/

# repackage python-psycopg2 into kusu-setup
%define _psycopg2_lib %{_site_packages}/psycopg2
install -d $RPM_BUILD_ROOT/%{_kusu}/%{_psycopg2_lib}

for f in `find 3rdparty/psycopg2 -type f | grep -v '\.svn' | grep -v '\/test' | cut -c19-`; do
    install 3rdparty/psycopg2/$f $RPM_BUILD_ROOT/%{_kusu}/%{_psycopg2_lib}/$f;
done

# extract rpm package python-cheetah
rpm2cpio python-cheetah*.rpm | cpio -dimv ./usr/lib64/python2.4/site-packages/Cheetah/* 
mv usr/lib64/python2.4/site-packages/Cheetah 3rdparty/

# repackage python-cheetah into kusu-setup
%define _cheetah_lib %{_site_packages}/Cheetah
for d in `find 3rdparty/Cheetah -type d | grep -v '\.svn' | grep -v '\/test' | cut -c18-`; do
    install -d $RPM_BUILD_ROOT/%{_kusu}/%{_cheetah_lib}/$d;
done

for f in `find 3rdparty/Cheetah -type f | grep -v '\.svn' | grep -v '\/test' | cut -c18-`; do
    install 3rdparty/Cheetah/$f $RPM_BUILD_ROOT/%{_kusu}/%{_cheetah_lib}/$f;
done

# kusu-setup files
install -d $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m755 bin/kusu-setup $RPM_BUILD_ROOT/%{_kusu}/bin/kusu-setup
install -m644 lib/command.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/message.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/cleanupcommand.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/cleanupreceiver.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/createosrepocommand.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/createosreporeceiver.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/dhcpcheckcommand.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/diskspacecheckcommand.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/diskspacecheckreceiver.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/envcheckcommand.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/fqdnreceiver.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/initkusudbcommand.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/initkusudbreceiver.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/installerinitreceiver.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/installextrakitcommand.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/installextrakitreceiver.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/installoskitcommand.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/installoskitreceiver.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/niccheckcommand.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/networkreceiver.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/keyboardreceiver.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/languagereceiver.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/ramcheckcommand.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/ramcheckreceiver.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/rpmcheckcommand.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/rpminstallcommand.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/rpminstallreceiver.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/sanitizeinstallcommand.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/selinuxcheckcommand.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/setup_errors.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/systemsettingscommand.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/systemsettingsreceiver.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/timezonereceiver.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m644 lib/__init__.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap
install -m644 lib/__init__.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/bootstrap/setup
install -m755 doc/COPYING $RPM_BUILD_ROOT/%{_kusu}/share/doc/%{name}-%{version}

# for pulling in kusu-core
install -d $RPM_BUILD_ROOT/%{_kusu}/lib/python/kusu/core
install -m644 kusu-core/src/lib/__init__.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/kusu
install -m644 kusu-core/src/lib/*.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/kusu/core

# for pulling in kusu-util
install -d $RPM_BUILD_ROOT/%{_kusu}/lib/python/kusu/util
install -d $RPM_BUILD_ROOT/%{_kusu}/lib/python/kusu/util/distro
install kusu-util/src/lib/*.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/kusu/util/
install kusu-util/src/lib/distro/*.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/kusu/util/distro/

# for pulling in kusu-path
install -d $RPM_BUILD_ROOT/%{_kusu}/lib/python
install -m644 kusu-path/src/path.py $RPM_BUILD_ROOT/%{_kusu}/lib/python

# for pulling in kusu-buildkit
install -d $RPM_BUILD_ROOT/%{_kusu}/lib/python/kusu/buildkit
install -m644 kusu-buildkit/src/lib/*.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/kusu/buildkit

# for pulling in kusu-kitops
install -d $RPM_BUILD_ROOT/%{_kusu}/lib/python/kusu/kitops
install -m644 kusu-kitops/src/lib/*.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/kusu/kitops

# for pulling in kusu-boot
install -d $RPM_BUILD_ROOT/%{_kusu}/lib/python/kusu/boot
install -m644 kusu-boot/src/lib/*.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/kusu/boot

# for pulling in ipfun.py
install -m644 kusu-base-node/lib/kusu/ipfun.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/kusu

# for pulling in kusu-repoman
install -d $RPM_BUILD_ROOT/%{_kusu}/lib/python/kusu/repoman
install -m644 kusu-repoman/src/lib/*.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/kusu/repoman

# for pulling in kusu-driverpatch
install -d $RPM_BUILD_ROOT/%{_kusu}/lib/python/kusu/driverpatch
install -m644 kusu-driverpatch/src/lib/*.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/kusu/driverpatch

#for pulling in nodeinstaller-patchfiles
install -d $RPM_BUILD_ROOT/%{_kusu}/lib/python/kusu/genupdates
install -d $RPM_BUILD_ROOT/%{_kusu}/lib/nodeinstaller/bin
install -m644 kusu-nodeinstaller-patchfiles/bin/downloader $RPM_BUILD_ROOT/%{_kusu}/lib/nodeinstaller/bin
install -m644 kusu-nodeinstaller-patchfiles/lib/*.py $RPM_BUILD_ROOT/%{_kusu}/lib/python/kusu/genupdates

cd kusu-nodeinstaller-patchfiles/; find src/ | cpio -mpdu $RPM_BUILD_ROOT/%{_kusu}/lib/nodeinstaller/; cd ../
install -m755 kusu-nodeinstaller-patchfiles/sbin/genupdatesimg.py $RPM_BUILD_ROOT/%{_kusu}/sbin/genupdatesimg

%pre

%post

%preun

%postun

%clean
rm -rf %{buildroot}

%files

# for kusu-setup
%dir %{_kusu}
%dir %{_kusu}/bin
%dir %{_kusu}/lib
%dir %{_kusu}/lib64
%dir %{_kusu}/lib64/python
%dir %{_kusu}/libexec
%dir %{_kusu}/share
%{_kusu}/bin/kusu-setup
%{_kusu}/lib/python/bootstrap/__init__.py*
%{_kusu}/lib/python/bootstrap/setup/*
%doc %{_kusu}/share/doc/%{name}-%{version}/COPYING

# for kusu-primitive and 3rdparty RPMS
%{_kusu}/%{_site_packages}/*
%{_kusu}/libexec/*

# for kusu-path
%{_kusu}/lib/python/path.py*

# for node-installer-patchfiles
%{_kusu}/lib/nodeinstaller/bin/*
%{_kusu}/lib/nodeinstaller/src/*
%{_kusu}/sbin/genupdatesimg

# for other kusu packages that were included in kusu-setup
%{_kusu}/lib/python/kusu/*

%changelog
* Wed May 19 2010 - Ang Yun Quan <yqang@osgdc.org>
- Initial spec file for kusu-setup.

