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
# $Id: kusu-autoinstall.spec 3135 2009-10-23 05:42:58Z ltsai $
#

Summary: Kusu Autoinstall module runtime
Name: kusu-autoinstall
Version: 2.0
Release: 1
Epoch: 1
License: GPLv2
Group: System Environment/Base
Vendor: Platform Computing Inc.
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
AutoReq: no
Source: %{name}-%{version}.%{release}.tar.gz
Buildrequires: gcc, python, python-devel, patch
BuildArch: noarch

%description
This package installs the kusu-autoinstall module runtime.

%prep
%setup -n %{name} -q

%build

%install
%define _approot /opt/kusu
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/%{_approot}

install -d $RPM_BUILD_ROOT/%{_approot}/etc/templates
install -m644 etc/templates/kickstart.tmpl $RPM_BUILD_ROOT/%{_approot}/etc/templates
install -m644 etc/templates/autoinst.tmpl $RPM_BUILD_ROOT/%{_approot}/etc/templates

install -d $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/autoinstall
install -m755 lib/autoinstall.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/autoinstall
install -m755 lib/scriptfactory.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/autoinstall
install -m755 lib/__init__.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/autoinstall
install -m755 lib/installprofile.py $RPM_BUILD_ROOT/%{_approot}/lib/python/kusu/autoinstall

install -d $RPM_BUILD_ROOT/%{_approot}/share/doc/%{name}-%{version}/samples
install -m644 doc/samples/genkickstart $RPM_BUILD_ROOT/%{_approot}/share/doc/%{name}-%{version}/samples

%pre

%post

%preun

%postun

%clean
rm -rf %{buildroot}

%files
%{_approot}

%changelog
* Tue Jun 16 2009 Chew Meng Kuan <mkchew@platform.com> 5.3-1
- Bump version to 5.3 for PCM 1.2.1.

* Thu Aug 21 2008 Mark Black <mblack@platform.com> 5.1-4
- Reving tar file for RH

* Thu Jul 17 2008 Mike Frisch <mfrisch@platform.com> 5.1-3
- Change method of initializing swap space (#111560)
