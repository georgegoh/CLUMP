# Copyright (C) 2007 Platform Computing Inc.
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
# $Id: kusu-installer.spec 1335 2007-06-14 11:06:48Z najib $
#

%define subversion 4

Summary: kusu-installer module runtime
Name: kusu-installer
Version: 0.10
Release: 7
License: GPLv2
Group: System Environment/Base
Vendor: Platform Computing Inc.
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Source: %{name}-%{version}.%{subversion}.tar.gz
Buildrequires: gcc, python, python-devel, patch
BuildArch: noarch

%description
This package installs the kusu-installer module runtime.

%prep
%setup -n %{name} -q

%build

%install
%define _approot /opt/kusu
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/%{_approot}

install -d $RPM_BUILD_ROOT/%{_approot}/bin
install -m755 bin/installer $RPM_BUILD_ROOT/%{_approot}/bin
install -m755 bin/test $RPM_BUILD_ROOT/%{_approot}/bin

install -d $RPM_BUILD_ROOT/%{_approot}/etc/templates
install -m644 etc/lang-table $RPM_BUILD_ROOT/%{_approot}/etc
install -m644 etc/lang-names $RPM_BUILD_ROOT/%{_approot}/etc
install -m644 etc/templates/ntp.conf.tmpl $RPM_BUILD_ROOT/%{_approot}/etc/templates

install -d $RPM_BUILD_ROOT/%{_approot}/share/po
install -m644 po/kusuapps.po $RPM_BUILD_ROOT/%{_approot}/share/po

install -d $RPM_BUILD_ROOT/%{_approot}/share/doc/%{name}-%{version}
install -m644 doc/LICENSE $RPM_BUILD_ROOT/%{_approot}/share/doc/%{name}-%{version}

install -d $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/installer
install -m644 lib/network.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/installer
install -m644 lib/kits.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/installer
install -m644 lib/testfactory.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/installer
install -m644 lib/defaults.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/installer
install -m644 lib/language.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/installer
install -m644 lib/welcome.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/installer
install -m644 lib/kits_sourcehandlers.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/installer
install -m644 lib/tzselect.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/installer
install -m644 lib/partition_edit.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/installer
install -m644 lib/confirm.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/installer
install -m644 lib/partition_new.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/installer
install -m644 lib/hostname.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/installer
install -m644 lib/finalactions.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/installer
install -m644 lib/keyboard.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/installer
install -m644 lib/rhel_instnum.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/installer
install -m644 lib/kusufactory.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/installer
install -m644 lib/kitops.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/installer
install -m644 lib/__init__.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/installer
install -m644 lib/partition_delete.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/installer
install -m644 lib/rootpasswd.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/installer
install -m644 lib/partition.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/installer
install -m644 lib/collection.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/installer
install -m644 lib/screen.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/installer
install -m644 lib/gatewaydns.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/installer
install -m644 lib/util.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/installer

%pre

%post

%preun

%postun

%clean
rm -rf %{buildroot}

%files
%{_approot}

%changelog
* Thu Jul 31 2008 Mark Black <mblack@platform.com> 5.1-7
- Reset version/revision after switching build to trunk

* Thu Apr 3 2008 Mike Frisch <mfrisch@platform.com> 5.1-4
- Fixes for partitioning related problems

* Thu Mar 20 2008 Mike Frisch <mfrisch@platform.com> 5.1-3
- Change location of Kusu installer lock file
