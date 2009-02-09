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

docdir=$RPM_BUILD_ROOT/www
plugdir=$RPM_BUILD_ROOT/plugins
kitinfodir=$RPM_BUILD_ROOT/

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
/www/*.html
/www/COPYING
/www/kit_base_doc_source/*
/kitinfo

# plugins
/plugins/addhost/00-boothost.py*
/plugins/addhost/01-hosts.py*
/plugins/addhost/02-dnsreverse.py*
/plugins/addhost/03-dnszone.py*
/plugins/addhost/04-dhcp.py*
/plugins/addhost/05-hostspdsh.py*
/plugins/addhost/06-hostsequiv.py*
/plugins/addhost/07-ssh.py*
/plugins/addhost/09-autofs.py*
/plugins/addhost/10-ssh_knownhosts.py*
/plugins/addhost/99-cfmsync.py*
/plugins/genconfig/__init__.py*
/plugins/genconfig/apache_conf.py*
/plugins/genconfig/debug.py*
/plugins/genconfig/dhcpd.py*
/plugins/genconfig/hostsequiv.py*
/plugins/genconfig/hostspdsh.py*
/plugins/genconfig/hosts.py*
/plugins/genconfig/named.py*
/plugins/genconfig/nodes.py*
/plugins/genconfig/nodegroups.py*
/plugins/genconfig/pam_conf.py*
/plugins/genconfig/pam_conf_rhelfamily.tmpl
/plugins/genconfig/reverse.py*
/plugins/genconfig/resolv.py*
/plugins/genconfig/zone.py*
/plugins/genconfig/ssh.py*
/plugins/genconfig/ssh_config.tmpl*
/plugins/genconfig/apache_conf.tmpl
/plugins/genconfig/bashrc.py*
/plugins/genconfig/kickstart.py*
/plugins/genconfig/autoinst.py*
/plugins/cfmsync/getent-data.sh
/plugins/ngedit/01-component-base-installer.py*
/plugins/ngedit/02-component-base-installer.py*

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

