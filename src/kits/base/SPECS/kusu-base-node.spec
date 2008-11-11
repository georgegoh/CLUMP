# $Id$
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

%define subversion 6

Summary: Base components for nodes
Name: kusu-base-node
Version: 1.2
Release: 1
License: GPLv2
Group: System Environment/Base
Vendor: Platform Computing Corporation
Source: %{name}-%{version}.%{subversion}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-root
URL: http://www.osgdc.org
Requires: coreutils, chkconfig
BuildRequires: gcc python

%description
This package contains the Kusu Base kit part for nodes.

%prep
%setup -q -n %{name}

%build
cd cfm
make cfmd

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT/opt/kusu/sbin
install -d $RPM_BUILD_ROOT/opt/kusu/etc
install -d $RPM_BUILD_ROOT/etc/init.d
install -d $RPM_BUILD_ROOT/etc/rc.kusu.d
install -d $RPM_BUILD_ROOT/etc/rc.kusu.custom.d
install -d $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu
install -d $RPM_BUILD_ROOT/opt/kusu/lib/plugins/cfmclient
install -d $RPM_BUILD_ROOT/opt/kusu/share/doc/%{name}-%{version}

install -m755 sbin/rc.kusu.sh $RPM_BUILD_ROOT/etc/init.d/kusu
install -m644 lib/kusu/ipfun.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/
install -m755 sbin/cfmclient.py $RPM_BUILD_ROOT/opt/kusu/sbin/cfmclient
install -m755 cfm/cfmd $RPM_BUILD_ROOT/opt/kusu/sbin/cfmd
install -m755 etc/cfmd $RPM_BUILD_ROOT/etc/init.d/cfmd
install -m755 etc/cfmclient $RPM_BUILD_ROOT/etc/init.d/cfmclient
install -m644 sbin/S02KusuNodeNTPD.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S02KusuClientYumSetup.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S02KusuNodeSyslog.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S10NICStartup.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S91KusuAutomountCFM.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m755 sbin/S02KusuAutomount.sh $RPM_BUILD_ROOT/opt/kusu/lib/plugins/cfmclient
install -m755 sbin/S01mountall.sh $RPM_BUILD_ROOT/opt/kusu/lib/plugins/cfmclient
install -m644 sbin/S91KusuHomeFstab.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 doc/COPYING $RPM_BUILD_ROOT/opt/kusu/share/doc/%{name}-%{version}

%pre

%post
/sbin/chkconfig --add kusu
/sbin/chkconfig kusu on
/sbin/chkconfig --add cfmd
/sbin/chkconfig cfmd on
/sbin/chkconfig --add cfmclient
/sbin/chkconfig cfmclient on

%preun
if [ $1 = 0 ]; then # during removal of a pkg
    /sbin/chkconfig --del kusu
    /sbin/chkconfig --del cfmd
    /sbin/chkconfig --del cfmclient
fi

%postun

%files
/etc/init.d/kusu
/etc/init.d/cfmd
/etc/init.d/cfmclient
/etc/rc.kusu.d/
/etc/rc.kusu.custom.d/
/opt/kusu/lib/plugins/cfmclient/S02KusuAutomount.sh
/opt/kusu/lib/plugins/cfmclient/S01mountall.sh
/opt/kusu/lib/python/kusu/ipfun.py*
/opt/kusu/sbin/cfmclient
/opt/kusu/sbin/cfmd

%doc /opt/kusu/share/doc/%{name}-%{version}/COPYING

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Mon Oct 13 2008 Tsai Li Ming <ltsai@osgdc.org> 1.0-1
- Sync with OCS (r1609)
- Initial 1.0 release

