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
# $Id$
#
Summary: Base Kit
Name: kit-base
Version: 0.1
Release: 0
License: GPLv2
Group: System Environment/Base
Vendor: Platform Computing Corporation
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
BuildArch: noarch
AutoReq: no

%description
This package is destined for the installer node and serves as an 
information container for the database.  

%prep

%install
docdir=$RPM_BUILD_ROOT/depot/www/kits/%{name}/%{version}
plugdir=$RPM_BUILD_ROOT/opt/kusu/lib/plugins

rm -rf $RPM_BUILD_ROOT
mkdir -p $docdir
mkdir -p $plugdir/addhost $plugdir/genconfig $plugdir/ngedit

/usr/bin/install -m 444 %{_topdir}/docs/index.html    $docdir
/usr/bin/install -m 444 %{_topdir}/docs/readme.html   $docdir
/usr/bin/install -m 444 %{_topdir}/docs/COPYING       $docdir

/usr/bin/install -m 444 %{_topdir}/plugins/addhost/*.py     $plugdir/addhost
/usr/bin/install -m 444 %{_topdir}/plugins/genconfig/*.py    $plugdir/genconfig
/usr/bin/install -m 444 %{_topdir}/plugins/ngedit/*.py      $plugdir/ngedit


%clean
rm -rf $RPM_BUILD_ROOT

%files
# documentation
/depot/www/kits/%{name}/%{version}/index.html
/depot/www/kits/%{name}/%{version}/readme.html
/depot/www/kits/%{name}/%{version}/COPYING

# plugins
/opt/kusu/lib/plugins/addhost/*.py
/opt/kusu/lib/plugins/genconfig/*.py
/opt/kusu/lib/plugins/ngedit/*.py
%exclude /opt/kusu/lib/plugins/addhost/*.py?
%exclude /opt/kusu/lib/plugins/genconfig/*.py?
%exclude /opt/kusu/lib/plugins/ngedit/*.py?

%pre

%post
# SQL/Shell/Python code to update the database.. The updates may optionally
# include Node group creation and component association

%preun

%postun
# Code necessary to cleanup the database from any entries inserted by the %post
