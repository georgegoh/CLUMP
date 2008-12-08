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
# $Id$
# 

%define subversion 17

Summary: Kusu Base Installer
Name: kusu-base-installer
Version: 1.2
Release: 2
License: GPLv2
Group: System Environment/Base
Vendor: Platform Computing Inc
BuildArchitectures: noarch
Source: %{name}-%{version}.%{subversion}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Requires: openssl, httpd
BuildRequires: python
BuildArch: noarch

%description
This package contains the Kusu installer node tools.

%prep
%setup -q -n kusu-base-installer

%build

%pre

##
## POST
##
%post
if [ ! -f /etc/cfm/.cfmsecret ] ; then
    # Contact Mark prior to touching this!
    if [ ! -d /etc/cfm ] ; then
        mkdir /etc/cfm
    fi
    umask 077
    openssl rand -base64 32 > /etc/cfm/.cfmsecret
    chmod 400 /etc/cfm/.cfmsecret
    chown apache /etc/cfm/.cfmsecret
fi

##
## PREUN
##
%preun

##
## POSTUN
##
%postun
if [ "$1" -eq 0 ] ; then
    if [ -f /etc/cfm/.cfmsecret ] ; then
        rm -rf /etc/cfm/.cfmsecret
    fi
fi


##
## INSTALL
##
%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT/etc/cfm
install -d $RPM_BUILD_ROOT/etc/rc.kusu.d
install -d $RPM_BUILD_ROOT/tftpboot/kusu/pxelinux.cfg
install -d $RPM_BUILD_ROOT/opt/kusu/sbin
install -d $RPM_BUILD_ROOT/opt/kusu/bin
install -d $RPM_BUILD_ROOT/opt/kusu/cfm
install -d $RPM_BUILD_ROOT/opt/kusu/etc/templates
install -d $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/ui/text
install -d $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/ngedit
install -d $RPM_BUILD_ROOT/opt/kusu/share/locale/en/LC_MESSAGES
install -d $RPM_BUILD_ROOT/opt/kusu/sql
install -d $RPM_BUILD_ROOT/opt/kusu/man/man8
install -d $RPM_BUILD_ROOT/depot/repos/custom_scripts
install -d $RPM_BUILD_ROOT/depot/repos/post_scripts
install -d $RPM_BUILD_ROOT/depot/kits
install -d $RPM_BUILD_ROOT/depot/images

# Just for development
#echo "Letmein" > $RPM_BUILD_ROOT/opt/kusu/etc/db.passwd
touch $RPM_BUILD_ROOT/depot/repos/custom_scripts/bogus.sh
install -m644 sbin/S01KusuDB.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S90KusuCFM.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S02KusuDHCPD.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S02KusuRepo.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S02KusuSSH.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S02KusuSSHHosts.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S02KusuSyslog.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S02KusuApache.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S02KusuNfsExport.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S03KusuImage.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S02KusuIptables.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S02KusuNtp.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S02KusuXinetd.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S02KusuMotd.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S02KusuYumSetup.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S02KusuGenconfig.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S02KusuNamed.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S02KusuUsrSkel.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S90KusuFirefox.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S99KusuCFMSync.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S99KusuMigrateAppGlobals.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S99KusuNoPreservePartition.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m755 sbin/boothost.py $RPM_BUILD_ROOT/opt/kusu/sbin/boothost
install -m755 sbin/buildimage.py $RPM_BUILD_ROOT/opt/kusu/sbin/buildimage
install -m755 sbin/buildinitrd.py $RPM_BUILD_ROOT/opt/kusu/sbin/buildinitrd
install -m755 sbin/addhost.py $RPM_BUILD_ROOT/opt/kusu/sbin/addhost
install -m755 sbin/cfmsync.py $RPM_BUILD_ROOT/opt/kusu/sbin/cfmsync
install -m755 sbin/netedit.py $RPM_BUILD_ROOT/opt/kusu/sbin/netedit
install -m755 sbin/ngedit $RPM_BUILD_ROOT/opt/kusu/sbin/ngedit
install -m755 sbin/nghosts.py $RPM_BUILD_ROOT/opt/kusu/sbin/nghosts
install -m755 sbin/nodeboot.cgi.py $RPM_BUILD_ROOT/depot/repos/nodeboot.cgi
install -m755 sbin/sqlrunner.py $RPM_BUILD_ROOT/opt/kusu/sbin/sqlrunner
install -m755 sbin/listavailmodules.py $RPM_BUILD_ROOT/opt/kusu/sbin/listavailmodules
install -m755 sbin/listavailpkgs.py $RPM_BUILD_ROOT/opt/kusu/sbin/listavailpkgs
install -m755 sbin/listcomps.py $RPM_BUILD_ROOT/opt/kusu/sbin/listcomps
install -m755 bin/genconfig.py $RPM_BUILD_ROOT/opt/kusu/bin/genconfig
install -m644 lib/kusu/nodefun.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu
install -m644 lib/kusu/syncfun.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu
install -m644 lib/kusu/addhost.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu
install -m644 lib/kusu/cfms.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu
install -m644 lib/kusu/cfmnet.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu
install -m644 lib/kusu/genconfig.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu
install -m644 lib/kusu/niifun.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu
install -m644 lib/kusu/ngedit/ngedit.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/ngedit
install -m644 lib/kusu/ngedit/partition.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/ngedit
install -m644 lib/kusu/ngedit/__init__.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/ngedit
install -m644 lib/kusu/ui/text/USXkusuwidgets.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/ui/text
install -m644 lib/kusu/ui/text/USXnavigator.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/ui/text
install -m644 lib/kusu/ui/text/USXscreenfactory.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/ui/text
install -m644 sql/kusu_createdb.sql $RPM_BUILD_ROOT/opt/kusu/sql
install -m644 sql/kusu_dbperms.sql $RPM_BUILD_ROOT/opt/kusu/sql
install -m644 sql/kusu_alterdb.sql $RPM_BUILD_ROOT/opt/kusu/sql
install -m644 locale/en/LC_MESSAGES/kusuapps.mo $RPM_BUILD_ROOT/opt/kusu/share/locale/en/LC_MESSAGES/
install -m644 sql/kusu_primedb_sample.sql $RPM_BUILD_ROOT/opt/kusu/sql
install -m644 etc/templates/kickstart.tmpl $RPM_BUILD_ROOT/opt/kusu/etc/templates
install -m644 etc/templates/autoinst.tmpl $RPM_BUILD_ROOT/opt/kusu/etc/templates
install -m644 etc/templates/dhcpd.tmpl $RPM_BUILD_ROOT/opt/kusu/etc/templates

for i in `ls man/*.8`; do
    gzip -c $i >$RPM_BUILD_ROOT/opt/kusu/man/man8/`basename $i`.gz
done

echo "# CFM changed file list.  Generated automatically" > $RPM_BUILD_ROOT/opt/kusu/cfm/changedfiles.lst

%files
/etc/rc.kusu.d/S01KusuDB.rc.py*
/etc/rc.kusu.d/S02KusuApache.rc.py*
/etc/rc.kusu.d/S02KusuDHCPD.rc.py*
/etc/rc.kusu.d/S02KusuGenconfig.rc.py*
/etc/rc.kusu.d/S02KusuIptables.rc.py*
/etc/rc.kusu.d/S02KusuMotd.rc.py*
/etc/rc.kusu.d/S02KusuNamed.rc.py*
/etc/rc.kusu.d/S02KusuNfsExport.rc.py*
/etc/rc.kusu.d/S02KusuNtp.rc.py*
/etc/rc.kusu.d/S02KusuRepo.rc.py*
/etc/rc.kusu.d/S02KusuSSH.rc.py*
/etc/rc.kusu.d/S02KusuSSHHosts.rc.py*
/etc/rc.kusu.d/S02KusuSyslog.rc.py*
/etc/rc.kusu.d/S02KusuUsrSkel.rc.py*
/etc/rc.kusu.d/S02KusuXinetd.rc.py*
/etc/rc.kusu.d/S02KusuYumSetup.rc.py*
/etc/rc.kusu.d/S03KusuImage.rc.py*
/etc/rc.kusu.d/S90KusuCFM.rc.py*
/etc/rc.kusu.d/S90KusuFirefox.rc.py*
/etc/rc.kusu.d/S99KusuCFMSync.rc.py*
/etc/rc.kusu.d/S99KusuMigrateAppGlobals.rc.py*
/etc/rc.kusu.d/S99KusuNoPreservePartition.rc.py*
/opt/kusu/bin/genconfig
/opt/kusu/lib/python/kusu/addhost.py*
/opt/kusu/lib/python/kusu/cfmnet.py*
/opt/kusu/lib/python/kusu/cfms.py*
/opt/kusu/lib/python/kusu/genconfig.py*
/opt/kusu/lib/python/kusu/ngedit/__init__.py*
/opt/kusu/lib/python/kusu/ngedit/ngedit.py*
/opt/kusu/lib/python/kusu/ngedit/partition.py*
/opt/kusu/lib/python/kusu/niifun.py*
/opt/kusu/lib/python/kusu/nodefun.py*
/opt/kusu/lib/python/kusu/syncfun.py*
/opt/kusu/lib/python/kusu/ui/text/USXkusuwidgets.py*
/opt/kusu/lib/python/kusu/ui/text/USXnavigator.py*
/opt/kusu/lib/python/kusu/ui/text/USXscreenfactory.py*
/opt/kusu/sbin/addhost
/opt/kusu/sbin/boothost
/opt/kusu/sbin/buildimage
/opt/kusu/sbin/buildinitrd
/opt/kusu/sbin/cfmsync
/opt/kusu/sbin/netedit
/opt/kusu/sbin/ngedit
/opt/kusu/sbin/nghosts
/opt/kusu/sbin/sqlrunner
/opt/kusu/sbin/listavailmodules
/opt/kusu/sbin/listavailpkgs
/opt/kusu/sbin/listcomps
/opt/kusu/share/locale/en/LC_MESSAGES/kusuapps.mo
/opt/kusu/sql/kusu_alterdb.sql
/opt/kusu/sql/kusu_createdb.sql
/opt/kusu/sql/kusu_dbperms.sql
/opt/kusu/sql/kusu_primedb_sample.sql
/opt/kusu/man/man8/addhost.8.gz
/opt/kusu/man/man8/boothost.8.gz
/opt/kusu/man/man8/buildimage.8.gz
/opt/kusu/man/man8/buildinitrd.8.gz
/opt/kusu/man/man8/cfmclient.8.gz
/opt/kusu/man/man8/cfmd.8.gz
/opt/kusu/man/man8/cfmsync.8.gz
/opt/kusu/man/man8/genconfig.8.gz
/opt/kusu/man/man8/kitops.8.gz
/opt/kusu/man/man8/netedit.8.gz
/opt/kusu/man/man8/ngedit.8.gz
/opt/kusu/man/man8/nghosts.8.gz
/opt/kusu/man/man8/repoman.8.gz
/opt/kusu/man/man8/repopatch.8.gz
/opt/kusu/man/man8/sqlrunner.8.gz
/opt/kusu/etc/templates/kickstart.tmpl
/opt/kusu/etc/templates/autoinst.tmpl
/opt/kusu/etc/templates/dhcpd.tmpl
/depot/repos/post_scripts
%defattr(-,apache,apache)
/depot/repos/nodeboot.cgi
/depot/kits
/depot/images
/depot/repos/custom_scripts
/opt/kusu/cfm/changedfiles.lst

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Mon Oct 13 2008 Tsai Li Ming <ltsai@osgdc.org> 1.0-1
- Sync with OCS (r1609)
- Initial 1.0 release

