/* Copyright (C) 2003, 2004, 2006 Thorsten Kukuk
   Author: Thorsten Kukuk <kukuk@suse.de>

   This program is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License version 2 as
   published by the Free Software Foundation.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software Foundation,
   Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.  */


#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <syslog.h>

#if defined HAVE_SYS_XATTR_H
#include <sys/xattr.h>
#elif defined HAVE_ATTR_XATTR_H
#include <sys/types.h>
#include <attr/xattr.h>
#elif defined WITH_SELINUX
#include <selinux/selinux.h>
#endif

#include <security/pam_modules.h>
#if defined (HAVE_SECURITY_PAM_EXT_H)
#include <security/pam_ext.h>
#endif

#include "public.h"

int
copy_xattr (pam_handle_t *pamh, const char *from, const char *to)
{
#if defined(HAVE_LLISTXATTR) && defined(HAVE_LGETXATTR) && defined(HAVE_LSETXATTR)
  ssize_t size = llistxattr (from, NULL, 0);
  if (size < 0)
    {
      if (errno != ENOSYS && errno != ENOTSUP)
	{
	  pam_syslog (pamh, LOG_ERR, "listing attributes of %s", from);
	  return 1;
	}
    }
  else
    {
      char *name = NULL, *end_names = NULL, *value = NULL;
      char *names = malloc (size + 1);

      if (names == NULL)
	{
	  pam_syslog (pamh, LOG_ERR, "running out of memory!");
	  return 1;
	}

      size = llistxattr (from, names, size);
      if (size < 0)
	{
	  pam_syslog (pamh, LOG_ERR, "listing attributes of %s", from);
	  if (value)
	    free (value);
	  free (names);
	  return 1;
	}
      else
	{
	  names[size] = '\0';
	  end_names = names + size;
	}

      for (name = names; name != end_names;
	   name = strchr (name, '\0') + 1)
	{
	  char *old_value;

	  /* check if this attribute shall be preserved */
	  if (!*name)
	    continue;

	  size = lgetxattr (from, name, NULL, 0);
	  if (size < 0)
	    {
	      pam_syslog (pamh, LOG_ERR, "getting attribute %s of %s",
			 name, from);
	      if (value)
		free (value);
	      free (names);
	      return 1;
	    }

	  value = realloc (old_value = value, size);
	  if (size != 0 && value == NULL)
	    {
	      pam_syslog (pamh, LOG_ERR, "running out of memory!");
	      free (old_value);
	      free (names);
	      return 1;
	    }

	  size = lgetxattr (from, name, value, size);
	  if (size < 0)
	    {
	      pam_syslog (pamh, LOG_ERR, "getting attribute %s of %s",
			  name, from);
	      if (value)
		free (value);
	      free (names);
	      return 1;
	    }

	  if (lsetxattr (to, name, value, size, 0) != 0)
	    {
	      if (errno == ENOSYS)
		pam_syslog (pamh, LOG_ERR, "setting attributes for %s", to);
	      else
		pam_syslog (pamh, LOG_ERR, "setting attribute %s for %s",
			    name, to);
	      if (value)
		free (value);
	      free (names);
	      return 1;
	    }
	}
      free (value);
      free (names);
    }
#elif defined(WITH_SELINUX)
  if (is_selinux_enabled () > 0)
    {
      security_context_t passwd_context = NULL;
      int ret;

      if (getfilecon (file, &passwd_context) < 0)
	{
	  pam_syslog (pamh, LOG_ERR,
		      "%s: Can't get context for %s", program, file);
	  return 1;
	}
      ret = setfilecon (tmpname, passwd_context);
      freecon (passwd_context);
      if (ret != 0)
	{
	  pam_syslog (pamh, LOG_ERR, "%s: Can't set context for %s",
		      progname, tmpname);
	  return 1;
	}
    }
#endif

  return 0;
}
