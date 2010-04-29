# Copyright (C) 2007 Platform Computing Inc.
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
# $Id: kusu-nodeinstaller-patchfiles.spec 3135 2009-10-23 05:42:58Z ltsai $
#

Summary: kusu-nodeinstaller-patchfiles 
Name: kusu-nodeinstaller-patchfiles
Version: 2.1
Release: 1
Epoch: 1
License: GPLv2
Group: System Environment/Base
Vendor: Platform Computing Inc.
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
AutoReq: no
Source: %{name}-%{version}.%{release}.tar.gz
BuildRequires: python
Requires: yum-utils
BuildArch: noarch


%description
Kusu NodeInstaller patchfiles contains distro-specific os installer
patches that contain the Kusu NodeInstaller runtime.

%prep
%setup -n %{name} -q

%build

%install
rm -rf $RPM_BUILD_ROOT

mkdir -p $RPM_BUILD_ROOT/opt/kusu/man/man8
mkdir -p $RPM_BUILD_ROOT/opt/kusu/lib/nodeinstaller/bin
mkdir -p $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/genupdates

install -m755 bin/* $RPM_BUILD_ROOT/opt/kusu/lib/nodeinstaller/bin
install -m755 lib/* $RPM_BUILD_ROOT/opt/kusu/lib/python/kusu/genupdates

find src/ | cpio -mpdu $RPM_BUILD_ROOT/opt/kusu/lib/nodeinstaller/

install -d $RPM_BUILD_ROOT/opt/kusu/sbin
install -m755 sbin/genupdatesimg.py $RPM_BUILD_ROOT/opt/kusu/sbin/genupdatesimg

install -d $RPM_BUILD_ROOT/opt/kusu/man/man8
install -m444 man/genupdatesimg.8 $RPM_BUILD_ROOT/opt/kusu/man/man8

%pre

%post
rm -rf /opt/kusu/lib/nodeinstaller/{rhel,centos,fedora,sles,opensuse}

%preun

%postun
if [ $1 -eq 0 ]; then
    # Remove files created by genupdatesimg
    rm -rf /opt/kusu/lib/nodeinstaller/{rhel,centos,fedora,sles,opensuse}
fi

%clean
rm -rf $RPM_BUILD_ROOT

%files
/opt/kusu/lib/nodeinstaller/bin
/opt/kusu/lib/nodeinstaller/src
/opt/kusu/lib/python/kusu/genupdates
/opt/kusu/sbin/genupdatesimg
/opt/kusu/man/man8/genupdatesimg.8

%changelog
* Tue Jun 16 2009 Chew Meng Kuan <mkchew@platform.com> 5.3-1
- Bump version to 5.3 for PCM 1.2.1.

* Fri Sep 5 2008 Kailash Sethuraman <hsaliak@platform.com> 5.1-9
- Introduce patch for anaconda's yum installer to improve scalability (#114909)

* Thu Sep 4 2008 Mike Frisch <mfrisch@platform.com> 5.1-8
- Remove reboot message displayed in %post section (#114782)

* Thu Aug 21 2008 Mark Black <mblack@platform.com> 5.1-7
- Reving tar file for RH

* Wed Aug 20 2008 Mike Frisch <mfrisch@platform.com> 5.1-6
- Implemented standalone app to generate updates.img files (#111489)

* Thu Jul 31 2008 Mark Black <mblack@platform.com> 5.1-5
- Reset version/revision after switching build to trunk

* Fri Jul 4 2008 Mike Frisch <mfrisch@platform.com>
- Merged fix for removing kusu-ipy (replaced with python-IPy) (#108341)

* Fri May 23 2008 Najib Ninaba <najib@platform.com>
- Moved updates.img generation to post install

* Wed May 21 2008 Najib Ninaba <najib@platform.com>
- Revamped updates.img generation

* Fri Apr 4 2008 Mike Frisch <mfrisch@platform.com>
- Incorporate kusu-autoinstall updates

* Fri Feb 1 2008 Najib Ninaba <najib@platform.com>
- Fix path to nodeinstaller patchfiles directory

* Mon Jan 2 2008 Shawn Starr <sstarr@platform.com>
- Initial release
