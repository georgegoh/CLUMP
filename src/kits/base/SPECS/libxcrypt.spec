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

Name:           libxcrypt
License:        LGPL v2.1 or later; Public Domain, Freeware
Group:          System/Libraries
AutoReqProv:    on
Version:        3.0.2
Release:        1
Summary:        Crypt Library for DES, MD5, Blowfish and others
Source:         %{name}-%{version}.%{subversion}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-buildroot

%description
Libxcrypt is a replacement for libcrypt, which comes with the GNU C
Library. It supports DES crypt, MD5, SHA256, SHA512 and passwords with
blowfish encryption.



%package devel
License:        LGPL v2.1 or later; Public Domain, Freeware
Summary:        Development Include Files and Libraries for enhanced crypt functionality
Group:          Development/Libraries/C and C++
Requires:       libxcrypt = %{version}
AutoReqProv:    on

%description devel
libxcrypt is a replacement for libcrypt, which comes with the GNU C
Library. It supports DES crypt, MD5, and passwords with blowfish
encryption.

This package contains the header files and static libraries necessary
to develop software using libxcrypt.



%prep
%setup -n %{name} -q

%build
./configure CFLAGS="$RPM_OPT_FLAGS -Wno-cast-align" \
	--prefix=%{_prefix} \
	--libdir=/%{_lib} --disable-static
make

%install
make install DESTDIR=$RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{_libdir}
rm $RPM_BUILD_ROOT/%{_lib}/libxcrypt.{so,la}
rm $RPM_BUILD_ROOT/%{_lib}/xcrypt/lib*.{so,la}
ln -sf ../../%{_lib}/libxcrypt.so.2 $RPM_BUILD_ROOT%{_libdir}/libxcrypt.so
/sbin/ldconfig -n $RPM_BUILD_ROOT/%{_lib}/

%clean
rm -rf $RPM_BUILD_ROOT

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%files
%defattr(-,root,root)
%doc COPYING README NEWS README.bcrypt README.ufc-crypt
/%{_lib}/libxcrypt.so.*
%dir /%{_lib}/xcrypt
/%{_lib}/xcrypt/lib*.so.*

%files devel
%defattr(-,root,root)
%{_prefix}/include/*.h
%{_libdir}/libxcrypt.so

%changelog
* Mon Jan 21 2009 Hirwan Salleh <hsalleh@platform.com> - 2.6-1
- Initial package.