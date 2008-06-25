AC_INIT(genhdlist.c)
AM_INIT_AUTOMAKE(genhdlist, 0.1)

AC_PROG_CC
AC_HEADER_STDC

AC_LANG(C)

AC_CHECK_LIB(rpm, rpmtsCreate)
AC_CHECK_LIB(rpmdb, rpmdbInit)
AC_CHECK_LIB(popt, poptGetContext)
#AC_CHECK_LIB(pthread)

LIBS="-lrpm -lrpmdb -lpopt"
CFLAGS="-I/usr/include/rpm"

AC_OUTPUT(Makefile)
