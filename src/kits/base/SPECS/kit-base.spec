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
%define _unpackaged_files_terminate_build 0
%define _name base

Summary: kit-base package
Name: kit-base
Version: 1.2
Release: 1
License: GPLv2
Group: System Environment/Base
Vendor: Platform Computing Inc
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
#BuildArch: noarch
AutoReq: no
Source: %{name}-%{version}.12.tar.gz
URL: http://www.osgdc.org

%description
This package is destined for the installer node and serves as an 
information container for the database.  

%prep
%setup -q -n %{name}

%build

%install
rm -rf $RPM_BUILD_ROOT

docdir=$RPM_BUILD_ROOT/depot/www/kits/%{_name}/%{version}
plugdir=$RPM_BUILD_ROOT/opt/kusu/lib/plugins
kitinfodir=$RPM_BUILD_ROOT/depot/kits/%{_name}/%{version}/%{_arch}

mkdir -p $docdir
mkdir -p $docdir/kit_base_doc_source
mkdir -p $plugdir/addhost $plugdir/genconfig $plugdir/ngedit $plugdir/cfmsync
mkdir -p $kitinfodir


/usr/bin/install -m 444 docs/*.html    $docdir
/usr/bin/install -m 444 docs/COPYING       $docdir
/usr/bin/install -m 444 docs/kit_base_doc_source/* -t $docdir/kit_base_doc_source

/usr/bin/install -m 444 plugins/addhost/*.py     $plugdir/addhost
/usr/bin/install -m 444 plugins/genconfig/*.py    $plugdir/genconfig
/usr/bin/install -m 444 plugins/genconfig/*.tmpl    $plugdir/genconfig
/usr/bin/install -m 444 plugins/ngedit/*.py      $plugdir/ngedit
/usr/bin/install -m 444 plugins/cfmsync/*.sh      $plugdir/cfmsync

/usr/bin/install -m 444 kitinfo $kitinfodir

%clean
rm -rf $RPM_BUILD_ROOT

%files
# documentation
/depot/www/kits/%{_name}/%{version}/*.html
/depot/www/kits/%{_name}/%{version}/COPYING
/depot/www/kits/%{_name}/%{version}/kit_base_doc_source/*
/depot/kits/%{_name}/%{version}/%{_arch}/kitinfo

# plugins
/opt/kusu/lib/plugins/addhost/00-boothost.py*
/opt/kusu/lib/plugins/addhost/01-hosts.py*
/opt/kusu/lib/plugins/addhost/02-dnsreverse.py*
/opt/kusu/lib/plugins/addhost/03-dnszone.py*
/opt/kusu/lib/plugins/addhost/04-dhcp.py*
/opt/kusu/lib/plugins/addhost/05-hostspdsh.py*
/opt/kusu/lib/plugins/addhost/06-hostsequiv.py*
/opt/kusu/lib/plugins/addhost/07-ssh.py*
/opt/kusu/lib/plugins/addhost/09-autofs.py*
/opt/kusu/lib/plugins/addhost/10-ssh_knownhosts.py*
/opt/kusu/lib/plugins/addhost/99-cfmsync.py*
/opt/kusu/lib/plugins/genconfig/__init__.py*
/opt/kusu/lib/plugins/genconfig/apache_conf.py*
/opt/kusu/lib/plugins/genconfig/debug.py*
/opt/kusu/lib/plugins/genconfig/dhcpd.py*
/opt/kusu/lib/plugins/genconfig/hostsequiv.py*
/opt/kusu/lib/plugins/genconfig/hostspdsh.py*
/opt/kusu/lib/plugins/genconfig/hosts.py*
/opt/kusu/lib/plugins/genconfig/named.py*
/opt/kusu/lib/plugins/genconfig/nodes.py*
/opt/kusu/lib/plugins/genconfig/nodegroups.py*
/opt/kusu/lib/plugins/genconfig/reverse.py*
/opt/kusu/lib/plugins/genconfig/resolv.py*
/opt/kusu/lib/plugins/genconfig/zone.py*
/opt/kusu/lib/plugins/genconfig/ssh.py*
/opt/kusu/lib/plugins/genconfig/ssh_config.tmpl*
/opt/kusu/lib/plugins/genconfig/apache_conf.tmpl
/opt/kusu/lib/plugins/genconfig/bashrc.py*
/opt/kusu/lib/plugins/genconfig/kickstart.py*
/opt/kusu/lib/plugins/genconfig/autoinst.py*
/opt/kusu/lib/plugins/cfmsync/getent-data.sh
/opt/kusu/lib/plugins/ngedit/01-component-base-installer.py*
/opt/kusu/lib/plugins/ngedit/02-component-base-installer.py*
/opt/kusu/lib/plugins/ngedit/03-component-base-node.py*

%pre

%post
# SQL/Shell/Python code to update the database.. The updates may optionally
# include Node group creation and component association

%preun

%postun
# Code necessary to cleanup the database from any entries inserted by the %post

%changelog
* Mon Oct 13 2008 Tsai Li Ming <ltsai@osgdc.org> 1.0-1
- Sync with OCS (r1609)
- Initial 1.0 release

