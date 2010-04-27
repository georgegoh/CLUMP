Summary: primitive module
name: kusu-primitive
Version: 0.4
Release: 1
License: Unknown
Group: System Environment/Base
Vendor: Platform Computing Inc.
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Source: %{name}-%{version}.%{release}.tar.gz
BuildRequires: gcc
BuildArch: noarch
Requires: e2fsprogs pyparted python-IPy

%description
This package installs the primitive runtime modules.

%prep
%setup -n %{name} -q

%build
make nodeps

%install
%define _approot /opt/primitive
%define _primitive_lib /lib/python2.4/site-packages/primitive

rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/%{_approot}

for d in `find buildout/primitive -type d | grep -v '\.svn' | grep -v '\/test' | cut -c19-`; do \
	install -d $RPM_BUILD_ROOT/%{_approot}/$d; \
done

for f in `find buildout/primitive -type f | grep -v '\.svn' | grep -v '\/test' | cut -c19-`; do \
	install buildout/primitive/$f $RPM_BUILD_ROOT/%{_approot}/$f; \
done

%pre

%post

%preun

%postun

%clean
rm -rf %{buildroot}

%files
%{_approot}

%changelog
* Thu Oct 02 2008 - George Goh <ggoh@osgdc.org>
- Initial spec file for primitive.
