%define approot /opt/ntop
%define debug_package %{nil}

Summary: C interface to CGI (common gateway interface)
Name: cgilib
Version: 0.5
Release: 1
License: GPL
Group: Development/Libraries
URL: http://www.infodrom.north.de/cgilib/

Packager: Shawn Starr <sstarr@platform.com>

Source: http://www.infodrom.org/projects/cgilib/download/cgilib-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

%description
cgilib is a simple library that provides an easy interface to the
common gateway interface, known as CGI. The purpose is to provide an
easy to use interface to CGI if you need to write your program in C
instead of perl.

%package devel
Summary: Header files, libraries and development documentation for %{name}.
Group: Development/Libraries
#Requires: %{name} = %{version}-%{release}

%description devel
This package contains the header files, static libraries and development
documentation for %{name}. If you like to develop programs using %{name},
you will need to install %{name}-devel.

%prep
%setup

%build
%{__make} CFLAGS="%{optflags} -I." libcgi.a

%install
%{__rm} -rf %{buildoot}
mkdir -p $RPM_BUILD_ROOT%{approot}

%{__install} -Dp -m0644 cgi.h $RPM_BUILD_ROOT%{approot}%{_includedir}/cgi.h
%{__install} -Dp -m0644 libcgi.a $RPM_BUILD_ROOT%{approot}%{_libdir}/libcgi.a
%{__install} -Dp -m0644 cgi.5 $RPM_BUILD_ROOT%{approot}%{_mandir}/man5/cgi.5

for man in cgi*.3; do
	%{__install} -Dp -m0644 $man $RPM_BUILD_ROOT%{approot}%{_mandir}/man3/$man
done

%clean
%{__rm} -rf %{buildroot}

%files devel
%defattr(-, root, root, 0755)
%{approot}

%changelog
* Fri Nov 16 2007 Shawn Starr <sstarr@platform.com>
- Modified Dag package - Initial Packaging for Kusu
