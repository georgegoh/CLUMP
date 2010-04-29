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
# $Id: kusu-base-installer.sles.spec 3499 2010-02-09 10:28:36Z mkchew $
# 

Summary: Kusu Base Installer
Name: kusu-base-installer
Version: 2.1
Release: 1
Epoch: 1
License: GPLv2
Group: System Environment/Base
Vendor: Platform Computing Inc
BuildArchitectures: noarch
Source: %{name}-%{version}.%{release}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
BuildRequires: python
BuildArch: noarch
# kusu-base-installer dependencies
Requires: openssl
Requires: apache2
# these should be in component-base-installer spec
Requires: kusu-primitive
Requires: python-sqlalchemy
Requires: postgresql
Requires: postgresql-server
Requires: sqlite >= 3.3.6-2
Requires: python-sqlite2
Requires: aaa_base

%description
This package contains the Kusu installer node tools.

%prep
%setup -q -n kusu-base-installer

%build
cd po
msgfmt -o kusuapps.mo en_US.po
mkdir -p ../locale/en/LC_MESSAGES
cp kusuapps.mo ../locale/en/LC_MESSAGES

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
    chown wwwrun /etc/cfm/.cfmsecret
fi

/sbin/chkconfig --add lmgrd

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


/sbin/chkconfig --del lmgrd

##
## INSTALL
##
%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT/etc/cfm
install -d $RPM_BUILD_ROOT/etc/rc.kusu.d
install -d $RPM_BUILD_ROOT/etc/init.d
install -d $RPM_BUILD_ROOT/tftpboot/kusu/pxelinux.cfg
install -d $RPM_BUILD_ROOT/opt/kusu/sbin
install -d $RPM_BUILD_ROOT/opt/kusu/bin
install -d $RPM_BUILD_ROOT/opt/kusu/cfm
install -d $RPM_BUILD_ROOT/opt/kusu/libexec
install -d $RPM_BUILD_ROOT/opt/kusu/etc/templates
install -d $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/ui/text
install -d $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/ngedit
install -d $RPM_BUILD_ROOT/opt/kusu/share/locale/en/LC_MESSAGES
install -d $RPM_BUILD_ROOT/tftpboot/kusu
install -d $RPM_BUILD_ROOT/opt/kusu/man/man8
install -d $RPM_BUILD_ROOT/opt/kusu/firstboot
install -d $RPM_BUILD_ROOT/depot/repos/custom_scripts
install -d $RPM_BUILD_ROOT/depot/repos/post_scripts
install -d $RPM_BUILD_ROOT/depot/kits
install -d $RPM_BUILD_ROOT/depot/www/kits
install -d $RPM_BUILD_ROOT/depot/images
install -d $RPM_BUILD_ROOT/srv/www/htdocs
install -d $RPM_BUILD_ROOT/srv/www/htdocs/portal
install -d $RPM_BUILD_ROOT/srv/www/htdocs/portal/images
install -d $RPM_BUILD_ROOT/srv/www/htdocs/portal/styles
install -d $RPM_BUILD_ROOT/srv/www/html/portal/htdocs
install -d $RPM_BUILD_ROOT/srv/www/htdocs
install -d $RPM_BUILD_ROOT/srv/www/cgi-bin
install -d $RPM_BUILD_ROOT/srv/www/htdocs/portal/images
install -d $RPM_BUILD_ROOT/srv/www/htdocs/cgi-bin

# Just for development
#echo "Letmein" > $RPM_BUILD_ROOT/opt/kusu/etc/db.passwd
touch $RPM_BUILD_ROOT/depot/repos/custom_scripts/bogus.sh
install -m644 sbin/S01KusuDB.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S02KusuFirstBootConfig.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S90KusuCFM.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S03KusuDHCPD.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S03KusuRepo.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S03KusuSSH.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S03KusuSSHHosts.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S03KusuApache.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S03KusuIptables.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S03KusuNtp.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S03KusuXinetd.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S03KusuMotd.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S03KusuYumSetup.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S03KusuGenconfig.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S03KusuNamed.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S03KusuUsrSkel.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S04KusuImage.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S04KusuNetworkRoutes.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S04KusuNfsExport.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S04KusuSyslogMaster.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S90KusuFirefox.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S99KusuCFMSync.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S99KusuMigrateAppGlobals.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S999KusuFirstBootConfig.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m644 sbin/S99KusuXorg.rc.py $RPM_BUILD_ROOT/etc/rc.kusu.d/
install -m755 sbin/kusu-boothost.py $RPM_BUILD_ROOT/opt/kusu/sbin/kusu-boothost
install -m755 sbin/kusu-buildimage.py $RPM_BUILD_ROOT/opt/kusu/sbin/kusu-buildimage
install -m755 sbin/kusu-buildinitrd.py $RPM_BUILD_ROOT/opt/kusu/sbin/kusu-buildinitrd
install -m755 sbin/kusu-addhost.py $RPM_BUILD_ROOT/opt/kusu/sbin/kusu-addhost
install -m755 sbin/kusu-cfmsync.py $RPM_BUILD_ROOT/opt/kusu/sbin/kusu-cfmsync
install -m755 sbin/kusu-netedit.py $RPM_BUILD_ROOT/opt/kusu/sbin/kusu-netedit
install -m755 sbin/kusu-ngedit $RPM_BUILD_ROOT/opt/kusu/sbin/kusu-ngedit
install -m755 sbin/kusu-nghosts.py $RPM_BUILD_ROOT/opt/kusu/sbin/kusu-nghosts
install -m755 sbin/nodeboot.cgi.py $RPM_BUILD_ROOT/depot/repos/nodeboot.cgi
install -m755 sbin/sqlrunner.py $RPM_BUILD_ROOT/opt/kusu/sbin/sqlrunner
install -m755 sbin/listavailmodules.py $RPM_BUILD_ROOT/opt/kusu/sbin/listavailmodules
install -m755 sbin/listavailpkgs.py $RPM_BUILD_ROOT/opt/kusu/sbin/listavailpkgs
install -m755 sbin/listcomps.py $RPM_BUILD_ROOT/opt/kusu/sbin/listcomps
install -m755 sbin/lmgrd_safe $RPM_BUILD_ROOT/opt/kusu/sbin/lmgrd_safe
install -m755 sbin/lmgrd.init $RPM_BUILD_ROOT/opt/kusu/sbin/lmgrd.init
install -m755 sbin/lmgrd.init $RPM_BUILD_ROOT/etc/init.d/lmgrd
install -m755 bin/kusu-genconfig.py $RPM_BUILD_ROOT/opt/kusu/bin/kusu-genconfig
install -m644 lib/kusu/nodefun.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu
install -m644 lib/kusu/syncfun.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu
install -m644 lib/kusu/addhost.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu
install -m644 lib/kusu/cfms.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu
install -m644 lib/kusu/cfmnet.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu
install -m644 lib/kusu/genconfig.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu
install -m644 lib/kusu/ngedit/ngedit.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/ngedit
install -m644 lib/kusu/ngedit/constants.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/ngedit
install -m644 lib/kusu/ngedit/partition.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/ngedit
install -m644 lib/kusu/ngedit/__init__.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/ngedit
install -m644 lib/kusu/ui/text/USXkusuwidgets.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/ui/text
install -m644 lib/kusu/ui/text/USXnavigator.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/ui/text
install -m644 lib/kusu/ui/text/USXscreenfactory.py $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/ui/text
install -m644 locale/en/LC_MESSAGES/kusuapps.mo $RPM_BUILD_ROOT/opt/kusu/share/locale/en/LC_MESSAGES/
install -m644 etc/templates/kickstart.tmpl $RPM_BUILD_ROOT/opt/kusu/etc/templates
install -m644 etc/templates/autoinst.tmpl $RPM_BUILD_ROOT/opt/kusu/etc/templates
install -m644 etc/templates/dhcpd.tmpl $RPM_BUILD_ROOT/opt/kusu/etc/templates
install -m644 etc/templates/pxefile.tmpl $RPM_BUILD_ROOT/opt/kusu/etc/templates
install -m400 etc/power_defaults $RPM_BUILD_ROOT/opt/kusu/etc

install -m755 libexec/kusu-lmgrd-support.py $RPM_BUILD_ROOT/opt/kusu/libexec/kusu-lmgrd-support
install -m755 libexec/kusu-secure-mysql.py $RPM_BUILD_ROOT/opt/kusu/libexec/kusu-secure-mysql

install -m755 firstboot/kusuNetToolConfig.py $RPM_BUILD_ROOT/opt/kusu/firstboot/kusuNetToolConfig.py.disable

install -m644 portal/index.html $RPM_BUILD_ROOT/srv/www/htdocs
install -m644 portal/index.html $RPM_BUILD_ROOT/srv/www/htdocs/portal
install -m644 portal/images/* $RPM_BUILD_ROOT/srv/www/htdocs/portal/images
install -m644 portal/styles/portal.css $RPM_BUILD_ROOT/srv/www/htdocs/portal/styles
install -m755 portal/cgi-bin/* $RPM_BUILD_ROOT/srv/www/cgi-bin

install -m644 tftpboot/kusu/chain.c32 $RPM_BUILD_ROOT/tftpboot/kusu
install -m644 tftpboot/kusu/menu.c32 $RPM_BUILD_ROOT/tftpboot/kusu

for i in `ls man/*.8`; do
    gzip -c $i >$RPM_BUILD_ROOT/opt/kusu/man/man8/`basename $i`.gz
done

pushd $RPM_BUILD_ROOT/opt/kusu/man/man8
ln -s /opt/kusu/man/man8/kusu-addhost.8.gz addhost.8.gz
ln -s /opt/kusu/man/man8/kusu-boothost.8.gz boothost.8.gz
ln -s /opt/kusu/man/man8/kusu-buildimage.8.gz buildimage.8.gz
ln -s /opt/kusu/man/man8/kusu-buildinitrd.8.gz buildinitrd.8.gz
ln -s /opt/kusu/man/man8/kusu-cfmsync.8.gz cfmsync.8.gz
ln -s /opt/kusu/man/man8/kusu-genconfig.8.gz genconfig.8.gz
ln -s /opt/kusu/man/man8/kusu-kitops.8.gz kitops.8.gz
ln -s /opt/kusu/man/man8/kusu-netedit.8.gz netedit.8.gz
ln -s /opt/kusu/man/man8/kusu-ngedit.8.gz ngedit.8.gz
ln -s /opt/kusu/man/man8/kusu-nghosts.8.gz nghosts.8.gz
ln -s /opt/kusu/man/man8/kusu-repoman.8.gz repoman.8.gz
ln -s /opt/kusu/man/man8/kusu-repopatch.8.gz repopatch.8.gz
popd

pushd $RPM_BUILD_ROOT/opt/kusu/sbin
ln -s /opt/kusu/sbin/kusu-cfmsync cfmsync
ln -s /opt/kusu/sbin/kusu-ngedit ngedit
ln -s /opt/kusu/sbin/kusu-addhost addhost
ln -s /opt/kusu/sbin/kusu-boothost boothost
ln -s /opt/kusu/sbin/kusu-buildimage buildimage
ln -s /opt/kusu/sbin/kusu-buildinitrd buildinitrd
ln -s /opt/kusu/sbin/kusu-netedit netedit
ln -s /opt/kusu/sbin/kusu-nghosts nghosts
popd

pushd $RPM_BUILD_ROOT/opt/kusu/bin
ln -s /opt/kusu/bin/kusu-genconfig genconfig
popd

echo "# CFM changed file list.  Generated automatically" > $RPM_BUILD_ROOT/opt/kusu/cfm/changedfiles.lst

%files
/etc/rc.kusu.d/S01KusuDB.rc.py*
/etc/rc.kusu.d/S02KusuFirstBootConfig.rc.py*
/etc/rc.kusu.d/S03KusuApache.rc.py*
/etc/rc.kusu.d/S03KusuDHCPD.rc.py*
/etc/rc.kusu.d/S03KusuGenconfig.rc.py*
/etc/rc.kusu.d/S03KusuIptables.rc.py*
/etc/rc.kusu.d/S03KusuMotd.rc.py*
/etc/rc.kusu.d/S03KusuNamed.rc.py*
/etc/rc.kusu.d/S03KusuNtp.rc.py*
/etc/rc.kusu.d/S03KusuRepo.rc.py*
/etc/rc.kusu.d/S03KusuSSH.rc.py*
/etc/rc.kusu.d/S03KusuSSHHosts.rc.py*
/etc/rc.kusu.d/S03KusuUsrSkel.rc.py*
/etc/rc.kusu.d/S03KusuXinetd.rc.py*
/etc/rc.kusu.d/S03KusuYumSetup.rc.py*
/etc/rc.kusu.d/S04KusuImage.rc.py*
/etc/rc.kusu.d/S04KusuNetworkRoutes.rc.py*
/etc/rc.kusu.d/S04KusuNfsExport.rc.py*
/etc/rc.kusu.d/S04KusuSyslogMaster.rc.py*
/etc/rc.kusu.d/S90KusuCFM.rc.py*
/etc/rc.kusu.d/S90KusuFirefox.rc.py*
/etc/rc.kusu.d/S99KusuCFMSync.rc.py*
/etc/rc.kusu.d/S99KusuMigrateAppGlobals.rc.py*
/etc/rc.kusu.d/S99KusuXorg.rc.py*
/etc/rc.kusu.d/S999KusuFirstBootConfig.rc.py*
/etc/init.d/lmgrd
/tftpboot/kusu/chain.c32
/tftpboot/kusu/menu.c32
/opt/kusu/bin/genconfig
/opt/kusu/bin/kusu-genconfig
/opt/kusu/firstboot/kusuNetToolConfig.py*
/opt/kusu/lib/python/kusu/addhost.py*
/opt/kusu/lib/python/kusu/cfmnet.py*
/opt/kusu/lib/python/kusu/cfms.py*
/opt/kusu/lib/python/kusu/genconfig.py*
/opt/kusu/lib/python/kusu/ngedit/__init__.py*
/opt/kusu/lib/python/kusu/ngedit/ngedit.py*
/opt/kusu/lib/python/kusu/ngedit/constants.py*
/opt/kusu/lib/python/kusu/ngedit/partition.py*
/opt/kusu/lib/python/kusu/nodefun.py*
/opt/kusu/lib/python/kusu/syncfun.py*
/opt/kusu/lib/python/kusu/ui/text/USXkusuwidgets.py*
/opt/kusu/lib/python/kusu/ui/text/USXnavigator.py*
/opt/kusu/lib/python/kusu/ui/text/USXscreenfactory.py*
/opt/kusu/libexec/kusu-lmgrd-support
/opt/kusu/libexec/kusu-secure-mysql
/opt/kusu/sbin/addhost
/opt/kusu/sbin/kusu-addhost
/opt/kusu/sbin/boothost
/opt/kusu/sbin/kusu-boothost
/opt/kusu/sbin/buildimage
/opt/kusu/sbin/kusu-buildimage
/opt/kusu/sbin/buildinitrd
/opt/kusu/sbin/kusu-buildinitrd
/opt/kusu/sbin/cfmsync
/opt/kusu/sbin/kusu-cfmsync
/opt/kusu/sbin/netedit
/opt/kusu/sbin/kusu-netedit
/opt/kusu/sbin/ngedit
/opt/kusu/sbin/kusu-ngedit
/opt/kusu/sbin/nghosts
/opt/kusu/sbin/kusu-nghosts
/opt/kusu/sbin/sqlrunner
/opt/kusu/sbin/listavailmodules
/opt/kusu/sbin/listavailpkgs
/opt/kusu/sbin/listcomps
/opt/kusu/sbin/lmgrd_safe
/opt/kusu/sbin/lmgrd.init
/opt/kusu/share/locale/en/LC_MESSAGES/kusuapps.mo
/opt/kusu/man/man8/addhost.8.gz
/opt/kusu/man/man8/kusu-addhost.8.gz
/opt/kusu/man/man8/boothost.8.gz
/opt/kusu/man/man8/kusu-boothost.8.gz
/opt/kusu/man/man8/buildimage.8.gz
/opt/kusu/man/man8/kusu-buildimage.8.gz
/opt/kusu/man/man8/buildinitrd.8.gz
/opt/kusu/man/man8/kusu-buildinitrd.8.gz
/opt/kusu/man/man8/cfmclient.8.gz
/opt/kusu/man/man8/cfmd.8.gz
/opt/kusu/man/man8/cfmsync.8.gz
/opt/kusu/man/man8/kusu-cfmsync.8.gz
/opt/kusu/man/man8/genconfig.8.gz
/opt/kusu/man/man8/kusu-genconfig.8.gz
/opt/kusu/man/man8/kitops.8.gz
/opt/kusu/man/man8/kusu-kitops.8.gz
/opt/kusu/man/man8/netedit.8.gz
/opt/kusu/man/man8/kusu-netedit.8.gz
/opt/kusu/man/man8/ngedit.8.gz
/opt/kusu/man/man8/kusu-ngedit.8.gz
/opt/kusu/man/man8/nghosts.8.gz
/opt/kusu/man/man8/kusu-nghosts.8.gz
/opt/kusu/man/man8/repoman.8.gz
/opt/kusu/man/man8/kusu-repoman.8.gz
/opt/kusu/man/man8/repopatch.8.gz
/opt/kusu/man/man8/kusu-repopatch.8.gz
/opt/kusu/man/man8/sqlrunner.8.gz
%config(noreplace) /opt/kusu/etc/templates/kickstart.tmpl
%config(noreplace) /opt/kusu/etc/templates/autoinst.tmpl
%config(noreplace) /opt/kusu/etc/templates/dhcpd.tmpl
%config(noreplace) /opt/kusu/etc/templates/pxefile.tmpl
%config(noreplace) /opt/kusu/etc/power_defaults
/depot/repos/post_scripts
/depot/www/kits
%defattr(-,wwwrun,www)
/depot/repos/nodeboot.cgi
/depot/kits
/depot/images
/depot/repos/custom_scripts
/opt/kusu/cfm/changedfiles.lst
/srv/www/htdocs/index.html
/srv/www/htdocs/portal/index.html
/srv/www/htdocs/portal/images/*
#/srv/www/htdocs/portal/styles/*
/srv/www/htdocs/portal/styles
/srv/www/cgi-bin/*

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Tue Jun 16 2009 Chew Meng Kuan <mkchew@platform.com> 5.3-1
- Bump version to 5.3 for PCM 1.2.1.

* Mon Oct 13 2008 Tsai Li Ming <ltsai@osgdc.org> 1.0-1
- Sync with OCS (r1609)
- Initial 1.0 release

