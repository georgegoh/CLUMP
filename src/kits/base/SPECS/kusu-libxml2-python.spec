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
# $Id: kusu-libxml2-python.spec 1335 2007-06-14 11:06:48Z najib $
#
%define python_ver %(python -c "import sys; v=sys.version_info[:2]; print '%d.%d'%v")

Summary: kusu-libxml2-python module runtime
Name: kusu-libxml2-python
Version: 2.5.11
Release: 1
License: GPLv2
Group: System Environment/Base
Vendor: Platform Computing Inc.
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
AutoReq: no
Source: %{name}-%{version}.tar.gz
Buildrequires: gcc, python, python-devel, patch, libxml2, libxml2-devel, libxslt, libxslt-devel

%description
This package installs the kusu-libxml2-python module runtime.

%prep
%setup -n %{name} -q
patch src/setup.py custom/%{version}/setup.py.patch

%build
%define _approot /opt/kusu
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/%{_approot}

(cd src; python setup.py install --prefix $RPM_BUILD_ROOT/%{_approot})

if [ -d $RPM_BUILD_ROOT/%{_approot}/lib64 ] ;
then
  mkdir -p $RPM_BUILD_ROOT/%{_approot}/lib64/python ;
  cp -rf $RPM_BUILD_ROOT/%{_approot}/lib64/python%{python_ver}/site-packages/* $RPM_BUILD_ROOT/%{_approot}/lib64/python/. ;
  rm -rf $RPM_BUILD_ROOT/%{_approot}/lib64/python%{python_ver} ;
else
  mkdir -p $RPM_BUILD_ROOT/%{_approot}/lib/python ;
  cp -rf $RPM_BUILD_ROOT/%{_approot}/lib/python%{python_ver}/site-packages/* $RPM_BUILD_ROOT/%{_approot}/lib/python/.
  rm -rf $RPM_BUILD_ROOT/%{_approot}/lib/python%{python_ver} ;
fi

%install
install -d $RPM_BUILD_ROOT/%{_approot}/doc/%{name}-%{version}
install -m755 src/Copyright $RPM_BUILD_ROOT/%{_approot}/doc/%{name}-%{version}
install -m755 src/README $RPM_BUILD_ROOT/%{_approot}/doc/%{name}-%{version}

%pre

%post

%preun

%postun

%clean
rm -rf %{buildroot}

%files
%{_approot}
