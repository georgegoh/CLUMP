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
Summary: Base Kit
Name: kit-base
Version: 0.1
Release: 0
License: GPLv2
Group: System Environment/Base
Vendor: Platform Computing Inc
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
BuildArch: noarch
AutoReq: no

%description
This package is destined for the installer node and serves as an 
information container for the database.  

%prep
%define _name base
%define arch noarch

%install
docdir=$RPM_BUILD_ROOT/depot/www/kits/%{_name}/%{version}
plugdir=$RPM_BUILD_ROOT/opt/kusu/lib/plugins
kitinfodir=$RPM_BUILD_ROOT/depot/kits/%{_name}/%{version}/%{arch}

rm -rf $RPM_BUILD_ROOT
mkdir -p $docdir
mkdir -p $docdir/images/border
mkdir -p $docdir/styles
mkdir -p $plugdir/addhost $plugdir/genconfig $plugdir/ngedit
mkdir -p $kitinfodir

/usr/bin/install -m 444 %{_topdir}/docs/*.html    $docdir
/usr/bin/install -m 444 %{_topdir}/docs/images/border/spacer.gif   $docdir/images/border/spacer.gif
/usr/bin/install -m 444 %{_topdir}/docs/styles/site.css   $docdir/styles/site.css
/usr/bin/install -m 444 %{_topdir}/docs/COPYING       $docdir

/usr/bin/install -m 444 %{_topdir}/plugins/addhost/*.py     $plugdir/addhost
/usr/bin/install -m 444 %{_topdir}/plugins/genconfig/*.py    $plugdir/genconfig
/usr/bin/install -m 444 %{_topdir}/plugins/ngedit/*.py      $plugdir/ngedit

/usr/bin/install -m 444 %{_topdir}/kitinfo $kitinfodir

%clean
rm -rf $RPM_BUILD_ROOT

%files
# documentation
/depot/www/kits/%{_name}/%{version}/*.html
/depot/www/kits/%{_name}/%{version}/COPYING
/depot/www/kits/%{_name}/%{version}/images/*/*
/depot/www/kits/%{_name}/%{version}/styles/site.css
/depot/kits/%{_name}/%{version}/%{arch}/kitinfo

# plugins
/opt/kusu/lib/plugins/addhost/00-boothost.py
/opt/kusu/lib/plugins/addhost/01-hosts.py
/opt/kusu/lib/plugins/addhost/02-dnsreverse.py
/opt/kusu/lib/plugins/addhost/03-dnszone.py
/opt/kusu/lib/plugins/addhost/04-dhcp.py
/opt/kusu/lib/plugins/addhost/05-hostspdsh.py
/opt/kusu/lib/plugins/addhost/06-hostsequiv.py
/opt/kusu/lib/plugins/addhost/07-ssh.py
/opt/kusu/lib/plugins/genconfig/__init__.py
/opt/kusu/lib/plugins/genconfig/apache_conf.py
/opt/kusu/lib/plugins/genconfig/debug.py
/opt/kusu/lib/plugins/genconfig/dhcpd.py
/opt/kusu/lib/plugins/genconfig/hostsequiv.py
/opt/kusu/lib/plugins/genconfig/hostspdsh.py
/opt/kusu/lib/plugins/genconfig/hosts.py
/opt/kusu/lib/plugins/genconfig/named.py
/opt/kusu/lib/plugins/genconfig/nodes.py
/opt/kusu/lib/plugins/genconfig/nodegroups.py
/opt/kusu/lib/plugins/genconfig/reverse.py
/opt/kusu/lib/plugins/genconfig/zone.py
/opt/kusu/lib/plugins/genconfig/ssh.py
/opt/kusu/lib/plugins/genconfig/bashrc.py
/opt/kusu/lib/plugins/ngedit/01-component-base-installer.py
/opt/kusu/lib/plugins/ngedit/02-component-base-installer.py
/opt/kusu/lib/plugins/ngedit/03-component-base-node.py
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
