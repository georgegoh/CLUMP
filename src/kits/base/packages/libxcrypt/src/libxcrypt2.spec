
# norootforbuild

Name:           libxcrypt2
License:        LGPL v2 or later; Public Domain, Freeware
Group:          System/Libraries
AutoReqProv:    on
Version:        3.0.2
Release:        1
Summary:        Crypt Library for DES, MD5, and Blowfish
Source:         libxcrypt-%{version}.tar.bz2
BuildRoot:      %{_tmppath}/%{name}-%{version}-build

%description
Libxcrypt is a replacement for libcrypt, which comes with the GNU C
Library. It supports DES crypt, MD5, and passwords with blowfish
encryption.



%package -n libxcrypt-devel
Summary:        Development Include Files and Libraries for enhanced crypt functionality
Group:          Development/Libraries/C and C++
Requires:       libxcrypt2 = %{version}
AutoReqProv:    on

%description -n libxcrypt-devel
libxcrypt is a replacement for libcrypt, which comes with the GNU C
Library. It supports DES crypt, MD5, and passwords with blowfish
encryption.

This package contains the header files and static libraries necessary
to develop software using libxcrypt.



%prep
%setup -n libxcrypt-%{version}

%build
CFLAGS=$RPM_OPT_FLAGS ./configure
make

%check
make check

%install
make install DESTDIR=$RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/%{_libdir}
mv -v $RPM_BUILD_ROOT/%{_lib}/libxcrypt.a $RPM_BUILD_ROOT/%{_libdir}
ln -sf ../../%{_lib}/libxcrypt.so.2 $RPM_BUILD_ROOT%{_libdir}/libxcrypt.so
rm -rfv $RPM_BUILD_ROOT/%{_lib}/libxcrypt.{la,so}
rm -rfv $RPM_BUILD_ROOT/%{_lib}/xcrypt/libxcrypt_*.{a,la,so}

%clean
rm -rf $RPM_BUILD_ROOT

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%files
%defattr(-,root,root)
%doc COPYING README NEWS README.bcrypt README.ufc-crypt
/%{_lib}/libxcrypt.so.*
%dir /%{_lib}/xcrypt
/%{_lib}/xcrypt/libxcrypt_*.so.1*

%files -n libxcrypt-devel
%defattr(-,root,root)
%{_prefix}/include/*.h
%{_libdir}/libxcrypt.a
%{_libdir}/libxcrypt.so

%changelog
