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

#ifdef WITH_SELINUX


#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <syslog.h>
#include <sys/types.h>
#include <selinux/flask.h>
#include <selinux/selinux.h>
#include <selinux/context.h>

#if defined (HAVE_SECURITY_PAM_EXT_H)
#include <security/pam_ext.h>
#endif

#include "public.h"

int
selinux_check_access (const char *chuser, unsigned int access)
{
  int status = -1;
  security_context_t user_context;

  if (getprevcon (&user_context) == 0)
    {
      context_t c = context_new (user_context);
      const char *user = context_user_get (c);

      if (strcmp (chuser, user) == 0)
	status = 0;
      else
	{
	  struct av_decision avd;
	  int retval = security_compute_av (user_context,
					    user_context,
					    SECCLASS_PASSWD,
					    access,
					    &avd);

	  if ((retval == 0) &&
	      ((access & avd.allowed) == access))
	    status = 0;
	}
      context_free (c);
      freecon (user_context);
    }
  return status;
}

int
set_default_context (pam_handle_t *pamh, const char *filename,
		     char **prev_context)
{
  security_context_t scontext = NULL;

  if (is_selinux_enabled () <= 0)
    return 0;

  if (prev_context == NULL)
    return -1;

  if (getfilecon (filename, &scontext) < 0)
    {
      pam_syslog (pamh, LOG_ERR, "couldn't get security context `%s': %s",
		  filename, strerror (errno));
      return -1;
    }

  if (getfscreatecon (prev_context) < 0)
    {
      freecon (scontext);
      pam_syslog (pamh, LOG_ERR, "couldn't get default security context: %s",
		  strerror (errno));
      return -1;
    }

  if (setfscreatecon (scontext) < 0 )
    {
      freecon (scontext);
      pam_syslog (pamh, LOG_ERR,
		  "couldn't set default security context to `%s': %s",
		  scontext, strerror (errno));
      return -1;
    }

  freecon (scontext);

  return 0;
}

int
restore_default_context (pam_handle_t *pamh,
			 security_context_t prev_context)
{
  int retval = 0;

  if (is_selinux_enabled () <= 0)
    return 0;

  if (setfscreatecon (prev_context) < 0 )
    {
      pam_syslog (pamh, LOG_ERR,
		  "couldn't reset default security context to `%s': %s",
		  prev_context, strerror (errno));
      retval = -1;
    }

  if (prev_context)
    {
      freecon (prev_context);
      prev_context = NULL;
    }

  return retval;
}

#endif
