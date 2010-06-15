# $Id: kusu-power.spec 3488 2010-02-04 06:17:32Z mkchew $
#
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

# Definitions :
%define _prefix    /opt/kusu
%define _pmpython_libdir %{_prefix}/lib/python/kusu

%{expand: %%define %dist 1}

Summary: 	Kusu power management utility
Name: 		kusu-power
Version:	2.2.1
Release: 	1
Group:		System
Vendor:		Platform Computing Inc.
URL: 		http://www.platform.com
License: 	GPLv2
Source: 	%{name}-%{version}.%{release}.tar.gz
BuildRoot: 	%{_tmppath}/%{name}-%{version}-buildroot

Requires: OpenIPMI-tools

%description
Kusu power management utility

%prep
%setup -n %{name}

%install
rm -rf $RPM_BUILD_ROOT
python setup.py install --root $RPM_BUILD_ROOT --prefix %{_prefix} --install-lib %{_pmpython_libdir}

# Create symlinks
install -m 755 -d $RPM_BUILD_ROOT%{_prefix}/sbin
ln -s -v ../libexec/kusu-power.py $RPM_BUILD_ROOT%{_prefix}/sbin/kusu-power

%clean
rm -rf $RPM_BUILD_ROOT

%files
# Include all files and directories
%dir %{_prefix}
%{_prefix}/*

%changelog
* Fri Oct 16 2009 Andreas Buck <abuck@platform.com> 2.2.1-1
- Created kusu-power package
- Changed license to GPL v2
