#
# $Id$
#

%define python_sitepkgs %(python -c 'from distutils import sysconfig; print sysconfig.get_python_lib(1)')
%define subversion 1

Summary: Python bindings for OpenBSD's Blowfish password hashing code
Name: python-bcrypt
Version: 0.1
Release: 1
License: BSD
Group: Development/Libraries
Source: %{name}-%{version}.%{subversion}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot

BuildRequires: python-devel
Requires: python

%description
python-bcrypt is a Python wrapper of OpenBSD's Blowfish password hashing
code, as described in "A Future-Adaptable Password Scheme" by Niels
Provos and David Mazières.

This system hashes passwords using a version of Bruce Schneier's Blowfish
block cipher with modifications designed to raise the cost of off-line
password cracking and frustrate fast hardware implementation. The
computation cost of the algorithm is parametised, so it can be increased
as computers get faster. The intent is to make a compromise of a password
database less likely to result in an attacker gaining knowledge of the
plaintext passwords (e.g. using John the Ripper). 

%prep
%setup -n %{name} -q

%build
#CFLAGS="%{optflags}" %{__python} setup.py build
python setup.py build

%install
rm -rf $RPM_BUILD_ROOT
#%{__python} setup.py install -O1 --skip-build --root="$RPM_BUILD_ROOT" --prefix="%{_prefix}"
python setup.py install -O1 --skip-build --prefix="/usr" --root="$RPM_BUILD_ROOT"

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-, root, root, 0755)
%doc ChangeLog LICENSE MANIFEST README TODO
%{python_sitepkgs}/bcrypt/
%{python_sitepkgs}/bcrypt-0.1-py2.5.egg-info

%changelog
* Mon Jan 19 2009 Hirwan Salleh <hsalleh@platform.com> - 0.1-1
- Initial package.
