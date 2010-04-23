# $Id: kusu-base-node.sles.spec 3419 2010-01-25 09:41:40Z mkchew $
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

Summary: Base components for nodes
Name: kusu-base-node
Version: 2.0
Release: 1
Epoch: 1
License: GPLv2
Group: System Environment/Base
Vendor: Platform Computing Corporation
Source: %{name}-%{version}.%{release}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-root
URL: http://www.osgdc.org
BuildRequires: gcc python
Requires: coreutils
#for chkconfig
Requires: aaa_base

Requires: python
Requires: pdsh
Requires: pdsh-rcmd-exec
Requires: pdsh-rcmd-rsh
Requires: pdsh-rcmd-ssh
#Requires: environment-modules
Requires: kusu-core
Requires: kusu-path
Requires: kusu-util
Requires: kusu-release
Requires: kusu-primitive 
Requires: python-cheetah
Requires: xinetd
Requires: rsh-server
Requires: rsh
Requires: ipmitool
Requires: python-xml

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
install -d $RPM_BUILD_ROOT/opt/kusu/etc/ipmi-vendor
install -d $RPM_BUILD_ROOT/opt/kusu/man/man8
install -d $RPM_BUILD_ROOT/etc/init.d
install -d $RPM_BUILD_ROOT/etc/rc.kusu.d
install -d $RPM_BUILD_ROOT/opt/kusu/etc/templates/
install -d $RPM_BUILD_ROOT/etc/rc.kusu.custom.d
install -d $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu
install -d $RPM_BUILD_ROOT/opt/kusu/lib/plugins/cfmclient
install -d $RPM_BUILD_ROOT/opt/kusu/share/doc/%{name}-%{version}

install -m755 sbin/rc.kusu.sh $RPM_BUILD_ROOT/etc/init.d/kusu
install -m644 lib/kusu/ipfun.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/
install -m755 sbin/cfmclient.py $RPM_BUILD_ROOT/opt/kusu/sbin/cfmclient
install -m755 sbin/updatenic.py $RPM_BUILD_ROOT/opt/kusu/sbin/updatenic
install -m755 cfm/cfmd $RPM_BUILD_ROOT/opt/kusu/sbin/cfmd
install -m755 etc/cfmd $RPM_BUILD_ROOT/etc/init.d/cfmd
install -m644 etc/templates/syslog-ng.conf.in.tmpl $RPM_BUILD_ROOT/opt/kusu/etc/templates/
install -m755 etc/cfmclient $RPM_BUILD_ROOT/etc/init.d/cfmclient
install -m644 sbin/S03KusuNodeNTPD.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S03KusuClientYumSetup.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S03KusuSSHDConfig.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S10NICStartup.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S91KusuAutomountCFM.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m755 sbin/S03KusuAutomount.sh $RPM_BUILD_ROOT/opt/kusu/lib/plugins/cfmclient
install -m755 sbin/S01mountall.sh $RPM_BUILD_ROOT/opt/kusu/lib/plugins/cfmclient
install -m644 sbin/S91KusuHomeFstab.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S90KusuMinUidGid.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S95KusuIpmiSetup.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S99KusuNodeResolvConf.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S99KusuServicesManager.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 doc/COPYING $RPM_BUILD_ROOT/opt/kusu/share/doc/%{name}-%{version}
install -m755 lib/cfmclient-plugins/00-updateNICs.sh $RPM_BUILD_ROOT/opt/kusu/lib/plugins/cfmclient
install -m755 lib/cfmclient-plugins/S99-updateSyslog.py $RPM_BUILD_ROOT/opt/kusu/lib/plugins/cfmclient
install -m644 lib/kusu/servicefun.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/

for i in `ls man/*.8`; do
    gzip -c $i >$RPM_BUILD_ROOT/opt/kusu/man/man8/`basename $i`.gz
done

%pre

%post
/sbin/chkconfig -f --add kusu
/sbin/chkconfig -f --add cfmd
/sbin/chkconfig -f --add cfmclient

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
/opt/kusu/etc/templates/
/opt/kusu/lib/plugins/cfmclient/S03KusuAutomount.sh
/opt/kusu/lib/plugins/cfmclient/S01mountall.sh
/opt/kusu/lib/python/kusu/ipfun.py*
/opt/kusu/lib/python/kusu/servicefun.py*
/opt/kusu/sbin/cfmclient
/opt/kusu/sbin/cfmd
/opt/kusu/sbin/updatenic
/opt/kusu/man/man8/updatenic.8.gz
/opt/kusu/lib/plugins/cfmclient/00-updateNICs.sh
/opt/kusu/lib/plugins/cfmclient/S99-updateSyslog.py*
/opt/kusu/etc/ipmi-vendor/

%doc /opt/kusu/share/doc/%{name}-%{version}/COPYING

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Thu Oct 8 2009 Ankit Agarwal <ankit@platform.com> 5.3-2
- Merged fix #132086 from pcm-1_2 branch, added servicefun.py

* Tue Jun 16 2009 Chew Meng Kuan <mkchew@platform.com> 5.3-1
- Bump version to 5.3 for PCM 1.2.1.

* Mon Oct 13 2008 Tsai Li Ming <ltsai@osgdc.org> 1.0-1
- Sync with OCS (r1609)
- Initial 1.0 release

