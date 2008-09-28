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
# $Id: base-node.spec 2352 2007-09-25 09:34:34Z mike $
#

Summary: Component for Kusu Node Base
Name: component-base-node
Version: 0.10
Release: 3
License: GPLv2
URL: http://www.osgdc.org
Group: System Environment/Base
Vendor: Platform Computing Inc
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
Requires: xinetd
Requires: rsh-server
Requires: rsh

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
* Thu Jan 10 2008 Platform Computing <support@platform.com>
- Initial release.