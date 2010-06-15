# $Id: kusu-license-tool.spec 3539 2010-02-23 05:02:34Z qguan $
#
# Copyright (C) 2010 Platform Computing Inc
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

Summary: PCM License Support Tool
Name: kusu-license-tool
Version: 2.1
Release: 1
License: GPLv2
Group: System Environment/Base
Vendor: Project Kusu
BuildArch: noarch
Source: %{name}-%{version}.%{release}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-root
URL: http://www.osgdc.org
BuildRequires: python

%description
This package contains a plug-in based FLEXlm license support tool.

%prep
%setup -q -n %{name}

%build

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT/opt/kusu/sbin
install -d $RPM_BUILD_ROOT/opt/kusu/libexec
install -d $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/license
install -d $RPM_BUILD_ROOT/opt/kusu/lib/plugins/licensetool
install -d $RPM_BUILD_ROOT/opt/kusu/man/man8
install -m755 lib/kusu-license-support.py $RPM_BUILD_ROOT/opt/kusu/libexec
install -m755 sbin/kusu-license-tool.py $RPM_BUILD_ROOT/opt/kusu/sbin/kusu-license-tool
install -m644 lib/__init__.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/license
install -m644 lib/license_manager.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/license
install -m644 lib/license_plugin.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/license
gzip -c man/kusu-license-tool.8 > $RPM_BUILD_ROOT/opt/kusu/man/man8/kusu-license-tool.8.gz

%pre

%post
if [ $1 -eq 1 ]; then
    PROFILE=/root/.bash_profile
    MESSAGE_FILE=/opt/kusu/libexec/kusu-license-support.py
    RESULT=`grep $MESSAGE_FILE $PROFILE`
    if [ "x$RESULT" == "x" ]; then
        echo "[ -f $MESSAGE_FILE ] && python $MESSAGE_FILE" >> $PROFILE
    fi
fi

%preun

%postun

%files
/opt/kusu/sbin/kusu-license-tool*
/opt/kusu/libexec/kusu-license-support.py*
/opt/kusu/lib/python/kusu/license
/opt/kusu/man/man8/kusu-license-tool.8.gz

%doc

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Thu Jan 28 2010 Bin Xu <binxu@platform.com> 2.0-1
- Initial release


