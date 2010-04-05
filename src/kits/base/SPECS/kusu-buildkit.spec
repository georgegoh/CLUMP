# $Id: kusu-buildkit.spec 3135 2009-10-23 05:42:58Z ltsai $
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
#
# 

Summary: Kit building for PCM
Name: kusu-buildkit
Version: 2.0
Release: 1
Epoch: 1
License: GPLv2
Group: System Environment/Base
Vendor: Project Kusu
BuildArch: noarch
Source: %{name}-%{version}.%{release}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-root
URL: http://www.osgdc.org/
BuildRequires: python
Requires: mkisofs
Requires: rpm-build

%description
This package contains a tool to make kits for PCM.

%prep
%setup -q -n %{name}

%build

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/buildkit
install -d $RPM_BUILD_ROOT/opt/kusu/bin
install -d $RPM_BUILD_ROOT/opt/kusu/etc/templates
install -d $RPM_BUILD_ROOT/opt/kusu/share/doc/buildkit-%{version}

install -m755 bin/kusu-buildkit $RPM_BUILD_ROOT/opt/kusu/bin
install -m644 lib/builder.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/buildkit
install -m644 lib/buildkit_makehandlers.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/buildkit
install -m644 lib/buildkit_newhandlers.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/buildkit
install -m644 lib/checker.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/buildkit
install -m644 lib/kitsource01.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/buildkit
install -m644 lib/kitsource02.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/buildkit
install -m644 lib/methods.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/buildkit
install -m644 lib/tool.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/buildkit
install -m644 lib/tool01.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/buildkit
install -m644 lib/tool02.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/buildkit
install -m644 lib/__init__.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/buildkit
install -m644 doc/COPYING $RPM_BUILD_ROOT/opt/kusu/share/doc/buildkit-%{version}
install -m644 doc/buildkit.txt $RPM_BUILD_ROOT/opt/kusu/share/doc/buildkit-%{version}
install -m644 etc/templates/*.tmpl $RPM_BUILD_ROOT/opt/kusu/etc/templates
%pre

%post

%preun

%postun

%files
/opt/kusu/lib/python/kusu/buildkit/*
/opt/kusu/bin/kusu-buildkit
%config(noreplace) /opt/kusu/etc/templates/*.tmpl

%doc /opt/kusu/share/doc/buildkit-%{version}/COPYING
%doc /opt/kusu/share/doc/buildkit-%{version}/buildkit.txt

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Tue Jun 16 2009 Chew Meng Kuan <mkchew@platform.com> 5.3-1
- Bump version to 5.3 for PCM 1.2.1.

* Thu Aug 21 2008 Mark Black <mblack@platform.com> 5.1-5
- Reving tar file for RH

* Thu Mar 27 2008 Mike Frisch <mfrisch@platform.com> 5.1-4
- Remove AutoReq tag at the request of Red Hat

* Thu Mar 20 2008 Mike Frisch <mfrisch@platform.com> 5.1-3
- Change location of Kusu installer lock file in templates

* Mon Jan 2 2008 Shawn Starr <sstarr@platform.com> 5.1-0
- Initial release
