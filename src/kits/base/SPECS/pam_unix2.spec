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
# $Id$
#

%define subversion 1

Name:           pam_unix2
BuildRequires:  libxcrypt-devel pam-devel
BuildRequires:  cracklib
BuildRequires:  libselinux-devel
License:        BSD 3-Clause
Group:          System/Libraries
AutoReqProv:    on
Version:        2.6
Release:        1
Summary:        pam_unix2 authentication module with strong encryption
Source:         %{name}-%{version}.%{subversion}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-buildroot

%description
pam_unix2 authentication module with strong encryption
* Allows global configuration file for all options
* Can get passwords from secure NIS+ servers
* Sets secureRPC credentials
* Supports HP-UX password aging.
* Support of passwords with DES, bigcrypt, MD5 and blowfish encryption
* Usage of glibc NSS modules for flexible location of user data
* Allows changing of passwords in local files, NIS, NIS+ and LDAP (if pam_ldap is installed)
* On a NIS master server, passwords could be changed in the source files of NIS maps. 

%prep
%setup -n %{name} -q

%build
CFLAGS="$RPM_OPT_FLAGS" ./configure --enable-selinux \
	--libdir=/%{_lib} --mandir=%{_mandir}
make

%install
mkdir -p $RPM_BUILD_ROOT/sbin
install -d -m 755 $RPM_BUILD_ROOT%{_libdir}
make DESTDIR=$RPM_BUILD_ROOT install
#
# Remove stuff we don't wish to have now:
#
#rm -rf $RPM_BUILD_ROOT/usr/{include,lib}
#rm -rf $RPM_BUILD_ROOT/%{_lib}/security/*.la
#
# Install READMEs of PAM modules
#
DOC=$RPM_BUILD_ROOT%{_defaultdocdir}/pam
mkdir -p $DOC/modules
cp -fpv README $DOC/modules/README.pam_unix2
# Find lang files
%{find_lang} pam_unix2

%post

%clean
rm -rf $RPM_BUILD_ROOT
%verifyscript

%files -f pam_unix2.lang
%defattr(-,root,root,755)
%doc %{_defaultdocdir}/pam
%attr(755,root,root) /%{_lib}/security/pam_unix2.so
%attr(644,root,root) %doc %{_mandir}/man8/pam_unix2.8.gz
%attr(644,root,root) /etc/default/passwd

%changelog
* Mon Jan 21 2009 Hirwan Salleh <hsalleh@platform.com> - 2.6-1
- Initial package.
