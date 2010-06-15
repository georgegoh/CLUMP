#
# Copyright (C) 2008-2009 Platform Computing Inc
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

Summary: Tool for appglobals settings of PCM
Name: kusu-appglobals-tool
Version: 2.1
Release: 1
License: GPLv2
Group: System Environment/Base
Vendor: Project Kusu
BuildArch: noarch
Source: %{name}-%{version}.%{release}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-root
URL: http://www.osgdc.org/
BuildRequires: python

%description
This package contains a tool for managing appglobals settings within PCM.

%prep
%setup -q -n %{name}

%build

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT/opt/kusu/sbin
install -d $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/appglobals/
install -d $RPM_BUILD_ROOT/opt/kusu/etc
install -d $RPM_BUILD_ROOT/opt/kusu/man/man8

install -m755 sbin/* $RPM_BUILD_ROOT/opt/kusu/sbin/
install -m644 lib/*.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/appglobals/
install -m644 lib/*.meta.xml $RPM_BUILD_ROOT/opt/kusu/etc/
for i in `ls man/*.8`; do
    gzip -c $i >$RPM_BUILD_ROOT/opt/kusu/man/man8/`basename $i`.gz
done

%pre

%post

%preun

%postun

%files
/opt/kusu/sbin/kusu-appglobals-tool
/opt/kusu/etc/appglobals-tool.meta.xml
/opt/kusu/lib/python/kusu/appglobals/__init__.py*
/opt/kusu/lib/python/kusu/appglobals/app.py*
/opt/kusu/lib/python/kusu/appglobals/metadata.py*
/opt/kusu/lib/python/kusu/appglobals/settings.py*
/opt/kusu/man/man8/kusu-appglobals-tool.8.gz

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Wed Nov 25 2009 Kunal Chowdhury <kunalc@platform.com>
- Initial release
