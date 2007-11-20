# Upstream: Luca Deri <deri$ntop,org>

%{?dist: %{expand: %%define %dist 1}}

%{!?dist:%define _with_tcpwrappersdevel 1}
%{!?dist:%define _with_libpcapdevel 1}

%{?fc7:%define _with_libpcapdevel 1}
%{?fc7:%define _with_tcpwrappersdevel 1}

%{?el5:%define _with_libpcapdevel 1}
%{?fc6:%define _with_libpcapdevel 1}

%define logmsg logger -t %{name}/rpm

Summary: Network traffic probe that shows the network usage
Name: ntop
Version: 3.3
Release: 1
License: GPL
Group: Applications/System
URL: http://www.ntop.org/

Packager: Shawn Starr <sstarr@platform.com>

Source: http://dl.sf.net/ntop/ntop-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

BuildRequires: openssl-devel, gdbm-devel, libpcap, rrdtool-devel, zlib-devel, glib-devel
BuildRequires: gd-devel, gcc-c++, automake, autoconf, gettext
%{?_with_libpcapdevel:BuildRequires: libpcap-devel}
%{?_with_tcpwrappersdevel:BuildRequires: tcp_wrappers-devel}
%{!?_without_tcpwrappers:BuildRequires: tcp_wrappers}
Requires: /sbin/chkconfig, /sbin/ldconfig

%description
ntop is a network and traffic analyzer that provides a wealth of information on
various networking hosts and protocols. ntop is primarily accessed via a built-in
web interface. Optionally, data may be stored into a database for analysis or
extracted from the web server in formats suitable for manipulation in perl or php.

%prep
%setup

%{__perl} -pi.orig -e 's|^NTOP_VERSION_EXTRA=.*$|NTOP_VERSION_EXTRA="(Dag Apt RPM Repository)"|;' configure configure.in

%{__perl} -pi.orig -e '
		s|\@CFG_CONFIGFILE_DIR\@|\$(sysconfdir)/ntop|;
		s|(\$\(CFG_DBFILE_DIR\))|\$(DESTDIR)$1|;
	' Makefile.in

%{__perl} -pi.orig -e '
		s|user = "nobody"|user = "ntop"|;
		s|user = "anonymous"|user = "nobody"|;
	' main.c

%{__cat} <<EOF >ntop.logrotate
%{_localstatedir}/log/ntop.access.log {
	missingok
	postrotate
		/sbin/service ntop condrestart >/dev/null 2>&1
	endscript
}
EOF

%{__cat} <<'EOF' >ntop.sysv
#!/bin/bash
#
# Init file for the NTOP network monitor
#
# chkconfig: - 93 83
#
# description: NTOP Network Monitor
#
# processname: ntop
# config: %{_sysconfdir}/ntop.conf
# pidfile: %{_localstatedir}/run/ntop

# Source function library.
. %{_initrddir}/functions

# Source networking configuration.
. %{_sysconfdir}/sysconfig/network

# Check that networking is up.
[ "${NETWORKING}" == "no" ] && exit 0
[ -x "%{_bindir}/ntop" ] || exit 1
[ -r "%{_sysconfdir}/ntop.conf" ] || exit 1
[ -r "%{_localstatedir}/ntop/ntop_pw.db" ] || exit 1

RETVAL=0
prog="ntop"

start () {
	echo -n $"Starting $prog: "
	daemon %{_prefix}/bin/$prog -d -L @%{_sysconfdir}/ntop.conf
	RETVAL=$?
	echo
	[ $RETVAL -eq 0 ] && touch %{_localstatedir}/lock/subsys/$prog
	return $RETVAL
}

stop () {
	echo -n $"Stopping $prog: "
	killproc $prog
	RETVAL=$?
	echo
	[ $RETVAL -eq 0 ] && rm -f %{_localstatedir}/lock/subsys/$prog
	return $RETVAL
}

restart () {
	stop
	start
}

case "$1" in
  start)
	start
	;;
  stop)
	stop
	;;
  restart|reload)
	restart
	;;
  condrestart)
	[ -e %{_localstatedir}/lock/subsys/$prog ] && restart
	RETVAL=$?
	;;
  status)
	status $prog
	RETVAL=$?
	;;
  *)
	echo $"Usage: $0 {start|stop|restart|condrestart|status}"
	RETVAL=1
esac

exit $RETVAL
EOF

%{__cat} <<EOF >ntop.conf.sample
###  You should copy this file to it's normal location, %{_sysconfdir}/etc/ntop.conf
###  and edit it to fit your needs.
###
###       ntop is easily launched with options by referencing this file from
###       a command line like this:
###
###       ntop @%{_sysconfdir}/ntop.conf
###
###  Remember, options may also be listed directly on the command line, both
###  before and  after the @%{_sysconfdir}/ntop.conf.
###
###  For switches that provide values, e.g. -i, the last one matters.
###  For switches just say 'do things', e..g -M, if it's ANYWHERE in the
###  commands, it will be set.  There's no unset option.
###
###  You can use this to your advantage, for example:
###       ntop @%{_sysconfdir}/ntop.conf -i none
###  Overrides the -i in the file.

### Sets the user that ntop runs as.
###  NOTE: This should not be root unless you really understand the security risks.
--user ntop

### Sets the directory that ntop runs from.
--db-file-path %{_localstatedir}/ntop

### Interface(s) that ntop will capture on (default: eth0)
#--interface eth0

### Configures ntop not to trust MAC addrs.  This is used when port mirroring or SPAN
#--no-mac

### Logging messages to syslog (instead of the console):
###  NOTE: To log to a specific facility, use --use-syslog=local3
###  NOTE: The = is REQUIRED and no spaces are permitted.
--use-syslog

### Tells ntop to track only local hosts as specified by the --local-subnets option
#--track-local-hosts

### Sets the port that the HTTP webserver listens on
###  NOTE: --http-server 3000 is the default
#--http-server 3000

### Sets the port that the optional HTTPS webserver listens on
#--https-server 3001

### Sets the networks that ntop should consider as local.
###  NOTE: Uses dotted decimal and CIDR notation. Example: 192.168.0.0/24
###        The addresses of the interfaces are always local and don't need to be specified.
#--local-subnets xx.xx.xx.xx/yy

### Sets the domain.  ntop should be able to determine this automatically.
#--domain mydomain.com

### Sets program to run as a daemon
###  NOTE: For more than casual use, you probably want this.
#--daemon
EOF

%build
%{__rm} -f libtool.m4.in
./autogen.sh --noconfig
%configure \
	--program-prefix="%{?_program_prefix}" \
	--enable-i18n \
	--enable-largerrdpop \
	--enable-optimize \
	--enable-sslv3 \
	--enable-jumbo-frames \
	--with-rrd-home=/opt/ntop \
%{!?_without_tcpwrappers:--with-tcpwrap}
#	--with-pcap-include="%{_includedir}/pcap" \
#	--enable-xmldump \
%{__make} %{?_smp_mflags} faq.html ntop.txt ntop.html all

%install
%{__rm} -rf %{buildroot}
%{__install} -d -m0755 %{buildroot}%{_bindir} \
			%{buildroot}%{_datadir}/ntop/ \
			%{buildroot}%{_localstatedir}/ntop/ #/rrd/{flows,graphics,interfaces/eth0}
%{__make} install install-data-local \
	DESTDIR="%{buildroot}"

%{__install} -Dp -m0755 ntop.sysv %{buildroot}%{_initrddir}/ntop
%{__install} -Dp -m0644 ntop.logrotate %{buildroot}%{_sysconfdir}/logrotate.d/ntop
#%{__install} -Dp -m0600 ntop.conf.sample %{buildroot}%{_sysconfdir}/ntop.conf

%pre
if ! /usr/bin/id ntop &>/dev/null; then
	/usr/sbin/useradd -M -s /sbin/nologin -r ntop &>/dev/null || \
		%logmsg "Unexpected error adding user \"ntop\". Abort installation."
fi

%post
/sbin/chkconfig --add ntop
/sbin/ldconfig 2>/dev/null

if /usr/bin/id ntop &>/dev/null; then
	/usr/sbin/usermod -s /sbin/nologin -c "ntop user" -g ntop \
		-d %{_localstatedir}/ntop ntop &>/dev/null || \
		%logmsg "Unexpected error modifying user \"ntop\". Abort installation."
fi

%preun
if [ $1 -eq 0 ]; then
	/sbin/service ntop stop &>/dev/null || :
	/sbin/chkconfig --del ntop
fi

%postun
if [ $1 -eq 0 ]; then
	/usr/sbin/userdel ntop || %logmsg "User \"ntop\" could not be deleted."
	/usr/sbin/groupdel ntop || %logmsg "Group \"ntop\" could not be deleted."
fi

if [ $1 -ge 1 ]; then
	/sbin/service ntop condrestart &>/dev/null || :
fi
/sbin/ldconfig 2>/dev/null

%clean
%{__rm} -rf %{buildroot}

%files
%defattr(-, root, root, 0755)
%doc AUTHORS ChangeLog CONTENTS COPYING INSTALL MANIFESTO NEWS PORTING THANKS
%doc *.txt docs/* ntop.conf.sample
%doc %{_mandir}/man8/ntop.8*
#%config(noreplace) %{_sysconfdir}/ntop.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/ntop
%config %{_sysconfdir}/ntop/
%config %{_initrddir}/ntop
%{_bindir}/ntop
%{_datadir}/ntop/
%{_libdir}/*.so
%{_libdir}/ntop/

%defattr(-, ntop, nobody, 0775)
%{_localstatedir}/ntop/

%exclude %{_libdir}/*.a
%exclude %{_libdir}/*.la
#%exclude %{_libdir}/plugins/

%changelog
* Fri Nov 16 2007 Shawn Starr <sstarr@platform.com>
- Modified Dag package - Initial packaging for Kusu
