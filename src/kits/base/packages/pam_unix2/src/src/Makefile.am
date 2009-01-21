#
# Copyright (c) 2002, 2003 SuSE Linux AG, Nürnberg
# Copyright (c) 2001 SuSE GmbH, Nürnberg
#
# Author: Thorsten Kukuk <kukuk@suse.de>
#
EXTRA_DIST = pam_unix2.map

pamdir = $(libdir)/security

AM_CFLAGS = -D_REENTRANT -DPAMDIR=\"$(pamdir)\" \
		-DSYSCONFDIR=\"$(sysconfdir)/security\"

CLEANFILES = *~

noinst_HEADERS = passwd_nss.h public.h yppasswd.h read-files.h \
		getuser.h logindefs.h

pam_PROGRAMS = pam_unix2.so

pam_unix2_so_LDFLAGS = -Wl,-soname,pam_unix2.so \
	-Wl,--version-script=$(srcdir)/pam_unix2.map

pam_unix2_so_SOURCES = passwd_nss.c unix_acct.c get_options.c \
	unix_passwd.c yppasswd_xdr.c support.c \
	unix_auth.c unix_sess.c read-files.c getuser.c copy_xattr.c \
	selinux_utils.c logindefs.c

