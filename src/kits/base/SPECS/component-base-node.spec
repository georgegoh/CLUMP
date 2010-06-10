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
# $Id: component-base-node.spec 3331 2009-12-22 06:54:59Z mxu $
#

Summary: Component for Kusu Node Base
Name: component-base-node
Version: 2.1
Release: 1
License: GPLv2
URL: http://www.platform.com
Group: System Environment/Base
Vendor: Platform Computing Inc
Requires: kusu-base-node >= 0.1

BuildArch: noarch
Buildroot: %{_tmppath}/%{name}-%{version}-buildroot
Source: %{name}-%{version}.%{release}.tar.gz
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
Requires: kusu-primitive 
Requires: xinetd
Requires: rsh-server
Requires: rsh
Requires: vim-enhanced
Requires: chkconfig
Requires: rsyslog

%description
This component provides the nodes with the Kusu tools for the 
nodes (not the installer components).


%prep
%setup -q -n %{name}

%build

%install
rm -rf $RPM_BUILD_ROOT
name_eths_dir=$RPM_BUILD_ROOT/opt/kusu/libexec/name_eths
mkdir -p $name_eths_dir

install -m0755 libexec/name_eths/dump_pirq $name_eths_dir
install -m0755 libexec/name_eths/edit_modprobe_conf $name_eths_dir
install -m0755 libexec/name_eths/hw_eth_order.pl $name_eths_dir
install -m0755 libexec/name_eths/mactab_to_redhat_configfiles $name_eths_dir
install -m0755 libexec/name_eths/name_eths_redhat $name_eths_dir

mkdir -p $RPM_BUILD_ROOT/etc/init.d/
install -m0755 libexec/name_eths/name_eths.init.redhat $RPM_BUILD_ROOT/etc/init.d/name_eths

name_eths_docdir=$RPM_BUILD_ROOT/opt/kusu/share/doc/name_eths-0.4
mkdir -p $name_eths_docdir
install -m0444 doc/name_eths-0.4/* $name_eths_docdir

%files
/etc/init.d/name_eths
/opt/kusu/libexec/name_eths/dump_pirq
/opt/kusu/libexec/name_eths/edit_modprobe_conf
/opt/kusu/libexec/name_eths/hw_eth_order.pl
/opt/kusu/libexec/name_eths/mactab_to_redhat_configfiles
/opt/kusu/libexec/name_eths/name_eths_redhat
/opt/kusu/share/doc/name_eths-0.4/*

%clean
rm -rf $RPM_BUILD_ROOT

%pre

%post
#equivalent of post section for the client

/sbin/chkconfig name_eths on

%preun

%postun
#equivalent of uninstall section for the client

%changelog
* Tue Jun 16 2009 Chew Meng Kuan <mkchew@platform.com> 5.3-1
- Bump version to 5.3 for PCM 1.2.1.

* Thu Nov 7 2008 Mark Black <mblack@platform.com>
- Added dependencies for new primitives

* Thu Jan 10 2008 Platform Computing <support@platform.com>
- Initial release.
