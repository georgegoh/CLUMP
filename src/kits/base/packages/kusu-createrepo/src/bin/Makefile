SHELL = /bin/sh
top_srcdir = ..
srcdir = ../bin
prefix = /usr
exec_prefix = ${prefix}

bindir = ${exec_prefix}/bin
sbindir = ${exec_prefix}/sbin
libexecdir = ${exec_prefix}/libexec
datadir = ${prefix}/share
sysconfdir = ${prefix}/etc
sharedstatedir = ${prefix}/com
localstatedir = ${prefix}/var
libdir = ${exec_prefix}/lib
infodir = ${prefix}/info
docdir = 
includedir = ${prefix}/include
oldincludedir = /usr/include
mandir = ${prefix}/man

pkgdatadir = $(datadir)/$(PACKAGE)
pkglibdir = $(libdir)/$(PACKAGE)
pkgincludedir = $(includedir)/$(PACKAGE)
top_builddir = ../

# all dirs
DIRS = $(DESTDIR)$(bindir) $(DESTDIR)/etc $(DESTDIR)$(pkgdatadir)


# INSTALL scripts 
INSTALL         = install -p --verbose 
INSTALL_BIN     = $(INSTALL) -m 755 
INSTALL_DIR     = $(INSTALL) -m 755 -d 
INSTALL_DATA    = $(INSTALL) -m 644 
INSTALL_MODULES = $(INSTALL) -m 755 -D 
RM 		= rm -f


all: $(srcdir)/$(PACKAGE)


install: all installdirs
	$(INSTALL_BIN) $(srcdir)/$(PACKAGE) $(DESTDIR)$(bindir)/$(PACKAGE)
	$(INSTALL_BIN) $(srcdir)/modifyrepo $(DESTDIR)$(bindir)/modifyrepo


uninstall:
	$(RM) $(bindir)/$(PACKAGE)



clean:


distclean:
	$(RM) -rf .libs
	$(RM) -f core
	$(RM) -f *~


mostlyclean:
	$(MAKE) clean


maintainer-clean:
	$(MAKE) distclean


distfiles:
	distdir=$(PACKAGE)-$(VERSION); \
	mkdir $(top_srcdir)/.disttmp/$$distdir/bin;\
	cp \
	$(srcdir)/$(PACKAGE) \
	$(srcdir)/Makefile \
	$(srcdir)/modifyrepo \
	$(top_srcdir)/.disttmp/$$distdir/bin

dailyfiles:
	distdir=$(PACKAGE); \
	mkdir $(top_srcdir)/.disttmp/$$distdir/bin;\
	cp \
	$(srcdir)/$(PACKAGE) \
	$(srcdir)/Makefile \
	$(srcdir)/modifyrepo \
	$(top_srcdir)/.disttmp/$$distdir/bin

installdirs:
	$(MAKE) -C $(top_srcdir) installdirs


.PHONY: all install install-strip uninstall clean distclean mostlyclean maintainer-clean info dvi dist distfiles check installcheck installdirs dailyfiles



