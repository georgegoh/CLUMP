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
# $Id$
#

Summary: Component for Kusu Node Base
Name: component-base-node
Version: 2.0
Release: 1
License: GPLv2
URL: http://www.osgdc.org
Group: System Environment/Base
Vendor: Platform Computing Inc
# The following "Provides" is a workaround for KUSU-1103.
Provides: /etc/localtime
Requires: kusu-base-node >= 0.1

BuildArch: noarch
Buildroot: %{_tmppath}/%{name}-%{version}-buildroot
Requires: python
Requires: pdsh
Requires: pdsh-rcmd-exec
Requires: pdsh-rcmd-rsh
Requires: pdsh-rcmd-ssh
Requires: environment-modules
Requires: kusu-core
Requires: kusu-path
Requires: kusu-util
Requires: kusu-release
Requires: primitive 
Requires: xinetd
Requires: rsh-server
Requires: rsh
#Requires: vim-enhanced

%description
This component provides the nodes with the Kusu tools for the 
nodes (not the installer components).


%prep

%build

%install
rm -rf $RPM_BUILD_ROOT

%files

%clean
rm -rf $RPM_BUILD_ROOT

%pre

%post
#equivalent of post section for the client

%preun

%postun
#equivalent of uninstall section for the client

%changelog
* Mon Oct 13 2008 Tsai Li Ming <ltsai@osgdc.org> 1.0-1
- Sync with OCS (r1609)
- Initial 1.0 release

