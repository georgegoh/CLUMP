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

%define version 1.2.5.1
%define OFEDSRC OFED-1.2.5.1.tgz

Summary: OFED Source Code
Name: ofed-src
Version: %{version}
Release: 0
License: Something
Group: System Environment/Base
Vendor: Platform Computing Corporation
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
BuildArch: noarch
AutoReq: no
Source: %{OFEDSRC}

%description
This package contains the OFED source code as provided by
Openfabrics Alliance at http://www.openfabrics.org/

%prep


%install
TARLOC=$OLDPWD
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/opt/ofed/src
cd $RPM_BUILD_ROOT/opt/ofed/src
tar zxvf $TARLOC/%{OFEDSRC}


%clean
rm -rf $RPM_BUILD_ROOT

%files
/opt/ofed/src/OFED-%{version}


%pre
# PRE Install section

%post
# POST Install section

%preun
# PREUN section

%postun
# POSTUN section
