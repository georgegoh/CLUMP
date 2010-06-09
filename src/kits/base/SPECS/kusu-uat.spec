# $Id: kusu-uat.spec 3238 2009-11-17 11:46:38Z mike $
#
# Copyright (C) 2010 Platform Computing Inc.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of version 2 of the GNU General Public License as published by the
# Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

Summary: Kusu UAT
Name: kusu-uat
Version: 2.1
Release: 1
License: GPLv2
Group: System Environment/Base
Vendor: Project Kusu
BuildArch: noarch
Source: %{name}-%{version}.%{release}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-root
Requires: kusu-core
Requires: kusu-shell
BuildRequires: python
URL: http://www.osgdc.org

%description
This package contains the Kusu UAT libraries, plugins and scripts

%prep
%setup -q -n %{name}

%build

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/uat
install -d $RPM_BUILD_ROOT/opt/kusu/lib/plugins/uat
install -d $RPM_BUILD_ROOT/opt/kusu/lib/plugins/shell
install -d $RPM_BUILD_ROOT/opt/kusu/etc/uat/conf.d
install -d $RPM_BUILD_ROOT/opt/kusu/etc/uat/specs

install -m644 lib/__init__.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/uat
install -m644 lib/uat_exceptions.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/uat
install -m644 lib/uat_helper.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/uat
install -m644 plugins/shell/uat_app.py $RPM_BUILD_ROOT/opt/kusu/lib/plugins/shell
install -m644 plugins/uat/check_cfmd.py $RPM_BUILD_ROOT/opt/kusu/lib/plugins/uat
install -m644 plugins/uat/check_disk_info.py $RPM_BUILD_ROOT/opt/kusu/lib/plugins/uat
install -m644 plugins/uat/check_disk_partitions.py $RPM_BUILD_ROOT/opt/kusu/lib/plugins/uat
install -m644 plugins/uat/check_hyper_threading.py $RPM_BUILD_ROOT/opt/kusu/lib/plugins/uat
#install -m644 plugins/uat/check_ibping.py $RPM_BUILD_ROOT/opt/kusu/lib/plugins/uat
install -m644 plugins/uat/check_kusu_services.py $RPM_BUILD_ROOT/opt/kusu/lib/plugins/uat
#install -m644 plugins/uat/check_lava.py $RPM_BUILD_ROOT/opt/kusu/lib/plugins/uat
install -m644 plugins/uat/check_memory_info.py $RPM_BUILD_ROOT/opt/kusu/lib/plugins/uat
install -m644 plugins/uat/check_nfs.py $RPM_BUILD_ROOT/opt/kusu/lib/plugins/uat
install -m644 plugins/uat/check_nics.py $RPM_BUILD_ROOT/opt/kusu/lib/plugins/uat
install -m644 plugins/uat/check_nslookup.py $RPM_BUILD_ROOT/opt/kusu/lib/plugins/uat
install -m644 plugins/uat/check_peripheral_devices.py $RPM_BUILD_ROOT/opt/kusu/lib/plugins/uat
install -m644 plugins/uat/check_ping.py $RPM_BUILD_ROOT/opt/kusu/lib/plugins/uat
install -m644 plugins/uat/check_proc_info.py $RPM_BUILD_ROOT/opt/kusu/lib/plugins/uat
install -m644 plugins/uat/check_speed_step.py $RPM_BUILD_ROOT/opt/kusu/lib/plugins/uat
install -m644 plugins/uat/check_ssh.py $RPM_BUILD_ROOT/opt/kusu/lib/plugins/uat
install -m644 plugins/uat/check_tftpd.py $RPM_BUILD_ROOT/opt/kusu/lib/plugins/uat
install -m644 plugins/uat/check_xserver.py $RPM_BUILD_ROOT/opt/kusu/lib/plugins/uat
install -m644 etc/uat/conf.d/00-default_checks.conf $RPM_BUILD_ROOT/opt/kusu/etc/uat/conf.d
#install -m644 etc/uat/conf.d/00-ofed_checks.conf $RPM_BUILD_ROOT/opt/kusu/etc/uat/conf.d
#install -m644 etc/uat/conf.d/00-lava_check.conf $RPM_BUILD_ROOT/opt/kusu/etc/uat/conf.d
install -m644 etc/uat/specs/example.ini $RPM_BUILD_ROOT/opt/kusu/etc/uat/specs

%files
%dir /opt/kusu/lib/python/kusu/uat
%dir /opt/kusu/lib/plugins/uat
%dir  /opt/kusu/etc/uat/conf.d
%dir  /opt/kusu/etc/uat/specs
/opt/kusu/lib/python/kusu/uat/*.py*
/opt/kusu/lib/plugins/uat/*.py*
/opt/kusu/etc/uat/conf.d/*
/opt/kusu/etc/uat/specs/*
/opt/kusu/lib/plugins/shell/uat_app.py*

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Fri Apr 23 2010 Ankit Agarwal <ankit@platform.com> 2.1-1
- Initial release
