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
Version: 2.1
Release: 1
Epoch: 1
License: GPLv2
Group: System Environment/Base
Vendor: Platform Computing Inc
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
#BuildArch: noarch
AutoReq: no
Source: %{name}-%{version}.%{release}.tar.gz
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
mkdir -p $docdir/images/border
mkdir -p $docdir/styles
#mkdir -p $docdir/guides/pcm_user_guide_files
#mkdir -p $docdir/guides/pcm_installation_guide
#mkdir -p $docdir/guides/pcm_release_notes
mkdir -p $plugdir/addhost $plugdir/genconfig $plugdir/ngedit $plugdir/cfmsync
mkdir -p $kitinfodir


/usr/bin/install -m 444 docs/*.html    $docdir
/usr/bin/install -m 444 docs/images/border/spacer.gif   $docdir/images/border/spacer.gif
/usr/bin/install -m 444 docs/styles/site.css   $docdir/styles/site.css
/usr/bin/install -m 444 docs/COPYING       $docdir
#/usr/bin/install -m 444 docs/guides/*.html $docdir/guides
#/usr/bin/install -m 444 docs/guides/pcm_user_guide_files/* $docdir/guides/pcm_user_guide_files
#/usr/bin/install -m 444 docs/guides/pcm_installation_guide/* $docdir/guides/pcm_installation_guide
#/usr/bin/install -m 444 docs/guides/pcm_release_notes/* $docdir/guides/pcm_release_notes
#/usr/bin/install -m 444 docs/guides/upgrading_from_pcm_1.2_to_pcm_2.0.pdf $docdir/guides
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
#/www/guides/*.html
#/www/guides/*.pdf
#/www/guides/pcm_user_guide_files/*
#/www/guides/pcm_installation_guide/*
#/www/guides/pcm_release_notes/*
/www/images/*/*
/www/styles/site.css
/kitinfo


# plugins
/plugins/addhost/00-boothost.py*
/plugins/addhost/01-hosts.py*
/plugins/addhost/02-dns.py*
/plugins/addhost/04-dhcp.py*
/plugins/addhost/05-hostspdsh.py*
/plugins/addhost/06-hostsequiv.py*
/plugins/addhost/07-ssh.py*
/plugins/addhost/09-autofs.py*
/plugins/addhost/08-alterego.py*
/plugins/addhost/10-ssh_knownhosts.py*
/plugins/addhost/20-kusupower.py*
/plugins/addhost/99-cfmsync.py*
/plugins/genconfig/__init__.py*
/plugins/genconfig/apache_conf.py*
/plugins/genconfig/debug.py*
/plugins/genconfig/dhcpd.py*
/plugins/genconfig/hostsequiv.py*
/plugins/genconfig/hostspdsh.py*
/plugins/genconfig/hosts.py*
/plugins/genconfig/kusupower_conf.py*
/plugins/genconfig/named.py*
/plugins/genconfig/nodes.py*
/plugins/genconfig/nodegroups.py*
/plugins/genconfig/reverse.py*
/plugins/genconfig/resolv.py*
/plugins/genconfig/zone.py*
/plugins/genconfig/ssh.py*
%config(noreplace) /plugins/genconfig/ssh_config.tmpl*
%config(noreplace) /plugins/genconfig/apache_conf.tmpl
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
* Fri Nov 27 2009 Meng Xu <mxu@platform.com> 5.3-1
- Merge fix to problem #131877 for PCM 2.0.

* Tue Jun 16 2009 Chew Meng Kuan <mkchew@platform.com> 5.3-1
- Bump version to 5.3 for PCM 1.2.1.

* Wed Feb 11 2009 Mike Frisch <mfrisch@platform.com> 5.2-2
- Change comment marker when no nodes exist in zone (#123146)

* Wed Oct 15 2008 Shawn Starr <sstarr@platform.com> 5.1-19
- Fix dhcp genconfig plugin, now supports Etherboot for QEMU/KVM

* Thu Sep 15 2008 Mark Black <mblack@platform.com> 5.1-18
- Remove offensive words

* Thu Aug 21 2008 Mark Black <mblack@platform.com> 5.1-17
- Fixing revisions for RH

* Fri Jul 18 2008 Shawn Starr <sstarr@platform.com> 5.1.1-4
- Fix addhost boothost plugin, ignore unmanaged nodes

* Wed Jun 18 2008 Shawn Starr <sstarr@platform.com> 5.1.1-2
- Fix genconfig plugins when two devices share same network range

* Mon Jun 2 2008 Mike Frisch <mfrisch@platform.com> 5.1-13
- Add missing copyright messages

* Thu May 29 2008 Mike Frisch <mfrisch@platform.com> 5.1-12
- Added cfmsync addhost plugin (#109560)

* Tue Apr 8 2008 Mike Frisch <mfrisch@platform.com> 5.1-10
- Fixed problem with modules initialization in .bashrc (#106511)

* Fri Apr 4 2008 Mike Frisch <mfrisch@platform.com> 5.1-9
- Fix for DHCP plugin (#106308)

* Thu Jan 10 2008 Platform Computing <support@platform.com>
- Initial release.
