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
# $Id$
# 

Summary: Component for GNOME Desktop
Name: component-gnome-desktop
Version: 1.2
Release: 1
License: GPLv2
URL: http://www.osgdc.org
Group: System Environment/Base
Vendor: Platform Computing Inc
BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
#Requires: libgnome
#Requires: gnome-desktop

%description
This component provides the GNOME Desktop environment for installers.

%prep

%build

%install
rm -rf $RPM_BUILD_ROOT

%clean
rm -rf $RPM_BUILD_ROOT

%files

%pre

%post
#equivalent of post section

%preun

%postun
#equivalent of uninstall section

%changelog
* Mon Oct 13 2008 Tsai Li Ming <ltsai@osgdc.org> 1.0-1
- Sync with OCS (r1609)
- Initial 1.0 release

