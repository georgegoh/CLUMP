# Upstream: Tobi Oetiker <oetiker$ee,ethz,ch>

%{?fc1:%define _without_python 1}
%{?el3:%define _without_python 1}

%{?rh9:%define _without_python 1}
%{?rh9:%define _without_ruby 1}
%{?rh9:%define _without_tcltk_devel 1}

%{?rh7:%define _without_python 1}
%{?rh7:%define _without_ruby 1}
%{?rh7:%define _without_tcltk_devel 1}

%{?el2:%define _without_python 1}
%{?el2:%define _without_ruby 1}
%{?el2:%define _without_tcltk_devel 1}

%define approot /opt/ntop

%define perl_vendorarch %(eval "`perl -V:installvendorarch`"; echo "$installvendorarch" | cut -d'/' -f3-)
%define perl_vendorlib %(eval "`perl -V:installvendorlib`"; echo "$installvendorlib" | cut -d'/' -f3-)
%define python_sitearch %(%{__python} -c 'from distutils import sysconfig; print "%s" % sysconfig.get_python_lib(1)' | cut -d'/' -f3-)

%define python_version %(%{__python} -c 'import string, sys; print string.split(sys.version, " ")[0]')
%define ruby_sitearch %(ruby -rrbconfig -e "puts Config::CONFIG['sitearchdir']" | cut -d'/' -f3-)
%define ruby_archdir %(ruby -rrbconfig -e "puts Config::CONFIG['archdir']" | cut -d'/' -f3-)

Summary: Round Robin Database Tool to store and display time-series data
Name: rrdtool
Version: 1.2.23
Release: 1
License: GPL
Group: Applications/Databases
URL: http://people.ee.ethz.ch/~oetiker/webtools/rrdtool/

Packager: Shawn Starr <sstarr@platform.com>

Source0: http://oss.oetiker.ch/rrdtool/pub/rrdtool-%{version}.tar.gz
Patch0: rrdtool-1.2.13-php.patch
Patch1: rrdtool-1.2.19-python.patch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

BuildRequires: gcc-c++, openssl-devel, cgilib-devel, libart_lgpl-devel >= 2.0
BuildRequires: libpng-devel, zlib-devel, freetype-devel
%{!?_without_python:BuildRequires: python-devel >= 2.3}
%{!?_without_ruby:BuildRequires: ruby, ruby-devel}
%{!?_without_tcltk_devel:BuildRequires: tcl-devel, tk-devel}
%{?_without_tcltk_devel:BuildRequires: tcl, tk}
Requires: perl >= %(rpm -q --qf '%%{epoch}:%%{version}' perl)

%description
RRD is the Acronym for Round Robin Database. RRD is a system to store and
display time-series data (i.e. network bandwidth, machine-room temperature,
server load average). It stores the data in a very compact way that will not
expand over time, and it presents useful graphs by processing the data to
enforce a certain data density. It can be used either via simple wrapper
scripts (from shell or Perl) or via frontends that poll network devices and
put a friendly user interface on it.

%package devel
Summary: RRDtool static libraries and header files
Group: Development/Libraries
Requires: %{name} = %{version}

%description devel
RRD is the Acronym for Round Robin Database. RRD is a system to store and
display time-series data (i.e. network bandwidth, machine-room temperature,
server load average). This package allow you to use directly this library.

%package -n perl-rrdtool
Summary: Perl RRDtool bindings
Group: Development/Languages
Requires: %{name} = %{version}
Obsoletes: rrdtool-perl <= %{version}-%{release}
Provides: rrdtool-perl = %{version}-%{release}

%description -n perl-rrdtool
The Perl RRDtool bindings

%package -n tcl-rrdtool
Summary: TCL bindings
Group: Development/Languages
Requires: %{name} = %{version}
Obsoletes: rrdtool-tcl <= %{version}-%{release}
Provides: rrdtool-tcl = %{version}-%{release}

%description -n tcl-rrdtool
The TCL RRDtool bindings

%package -n python-rrdtool
Summary: Python RRDtool bindings
Group: Development/Languages
BuildRequires: python
Requires: python >= %{python_version}
Requires: %{name} = %{version}
Obsoletes: rrdtool-python <= %{version}-%{release}
Provides: rrdtool-python = %{version}-%{release}

%description -n python-rrdtool
Python RRDtool bindings.

%package -n php-rrdtool
Summary: RRDtool module for PHP
Group: Development/Languages
Requires: %{name} = %{version}, php >= 4.0
Obsoletes: rrdtool-php <= %{version}-%{release}
Provides: rrdtool-php = %{version}-%{release}

%description -n php-rrdtool
The php-%{name} package includes a dynamic shared object (DSO) that adds
RRDtool bindings to the PHP HTML-embedded scripting language.

%package -n ruby-rrdtool
Summary: RRDtool module for Ruby
Group: Development/Languages
Requires: %{name} = %{version}, ruby-devel
Obsoletes: rrdtool-ruby <= %{version}-%{release}
Provides: rrdtool-ruby = %{version}-%{release}

%description -n ruby-rrdtool
The ruby-%{name} package includes a library that implements RRDtool bindings
for the Ruby language.

%prep
%setup
#if %{!?_without_php:1}0
#patch0 -p0 -b .php
#%{__perl} -pi.orig -e 's|../config.h|../rrd_config.h|g' php4/rrdtool.c
#endif
#patch1 -p0 -b .python

### FIXME: Fixes to /usr/lib(64) for x86_64. (Fix upstream)
%{__perl} -pi.orig -e 's|/lib\b|/%{_lib}|g' configure Makefile.in php4/configure php4/ltconfig*

### Fix to find correct python dir on lib64
%{__perl} -pi.orig -e 's|get_python_lib\(0,0,prefix|get_python_lib\(1,0,prefix|g' configure

%build
%configure \
%{?_without_python:--disable-python} \
%{?_without_ruby:--disable-ruby} \
	--disable-static \
%{?_without_tcl:--disable-tcl} \
	--enable-perl-site-install \
%{!?_without_python:--enable-python} \
%{!?_without_ruby:--enable-ruby} \
	--enable-ruby-site-install \
%{!?_without_tcl:--enable-tcl} \
	--enable-tcl-site \
	--with-perl-options='INSTALLDIRS="vendor" DESTDIR="" PREFIX="%{approot}"' \
	--with-pic \
	--with-tcllib="%{_libdir}"
%{__make} %{?_smp_mflags}

%install
%{__rm} -rf %{buildroot}
%{__make} install DESTDIR="%{buildroot}"

### FIXME: Another dirty hack to install perl modules with old and new perl-ExtUtils-MakeMaker (Fix upstream)
%{__rm} -rf %{buildroot}%{buildroot}
%{__make} -C bindings/perl-piped install INSTALLDIRS="vendor" DESTDIR="" PREFIX="%{buildroot}%{approot}"
%{__make} -C bindings/perl-shared install INSTALLDIRS="vendor" DESTDIR="" PREFIX="%{buildroot}%{approot}"

### FIXME: Another dirty hack to install ruby files if they're available
if [ -f bindings/ruby/RRD.so ]; then
	%{__install} -Dp -m0755 bindings/ruby/RRD.so %{buildroot}%{approot}/%{ruby_sitearch}/RRD.so
	%{__rm} -rf %{buildroot}%{approot}/%{ruby_archdir}
	%{__rm} -rf %{buildroot}/usr
fi

### We only want .txt and .html files for the main documentation
%{__mkdir_p} rpm-doc/docs/
%{__cp} -ap doc/*.txt doc/*.html rpm-doc/docs/

### Clean up examples dir
%{__rm} -f examples/Makefile* examples/*.in
find examples/ -type f -exec chmod 0644 {} \;
find examples/ -type f -exec %{__perl} -pi -e 's|^#! \@perl\@|#!%{__perl}|gi' {} \;
find examples/ -name "*.pl" -exec %{__perl} -pi -e 's|\015||gi' {} \;

### Clean up buildroot
%{__rm} -rf %{buildroot}%{approot}%{perl_archlib} %{buildroot}%{approot}/%{perl_vendorarch}/auto/*{,/*{,/*}}/.packlist
%{__rm} -f %{buildroot}%{approot}/%{perl_vendorarch}/ntmake.pl

# Find files to get rid of
find %{buildroot}%{approot}/%{perl_archlib} -name '*.packlist' | xargs -n1 /bin/rm -rfv $1
find %{buildroot}%{approot}/%{perl_vendorarch} -name 'ntmake.pl' | xargs -n1 /bin/rm -rfv $1
find %{buildroot}%{approot} -name 'perllocal.pod' | xargs -n1 /bin/rm -rfv $1

%clean
%{__rm} -rf %{buildroot}

%files
%defattr(-, root, root, 0755)
%doc CHANGES CONTRIBUTORS COPYING COPYRIGHT NEWS README THREADS TODO
%doc examples/ rpm-doc/docs/
%doc %{_mandir}/man1/*.1*
%{_bindir}/rrdcgi
%{_bindir}/rrdtool
%{_bindir}/rrdupdate
%{_libdir}/librrd.so.*
%{_libdir}/librrd_th.so.*
%{_datadir}/rrdtool/

%files devel
%defattr(-, root, root, 0755)
%{approot}/share/man/man3/*.3*
%{_includedir}/rrd.h
%{_libdir}/librrd.so
%{_libdir}/librrd_th.so
%{_libdir}/librrd.la
%exclude %{_libdir}/librrd_th.la
%{approot}/share/doc/

%files -n perl-rrdtool
%defattr(-, root, root, 0755)
%doc bindings/perl-shared/MANIFEST bindings/perl-shared/README
%{approot}/%{perl_vendorlib}/RRDp.pm
%{approot}/%{perl_vendorarch}/RRDs.pm
%{approot}/%{perl_vendorarch}/auto/RRDs/

%files -n tcl-rrdtool
%defattr(-, root, root, 0755)
%doc bindings/tcl/README
%{_libdir}/tclrrd%{version}.so
%{_libdir}/rrdtool/ifOctets.tcl
%{_libdir}/rrdtool/pkgIndex.tcl

%if %{!?_without_python:1}0
%files -n python-rrdtool
%defattr(-, root, root, 0755)
%doc bindings/python/ACKNOWLEDGEMENT bindings/python/AUTHORS bindings/python/COPYING bindings/python/README
%{approot}/%{python_sitearch}/rrdtoolmodule.so
%endif

%if %{!?_without_ruby:1}0
%files -n ruby-rrdtool
%defattr(-, root, root, 0755)
%doc bindings/ruby/CHANGES bindings/ruby/README
%{approot}/%{ruby_sitearch}/RRD.so
%endif

%changelog
* Fri Nov 16 2007 Shawn Starr <sstarr@platform.com>
- Modified Dag package - Initial packaging for Kusu
