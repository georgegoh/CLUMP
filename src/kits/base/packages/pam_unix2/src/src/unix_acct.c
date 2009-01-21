/*
 * Copyright (c) 2006 SuSE Linux Products GmbH Nuernberg, Germany.
 * Copyright (c) 1999, 2000, 2002, 2003 SuSE GmbH Nuernberg, Germany.
 *               2004 SUSE LINUX AG, Germany.
 *               2005 SUSE LINUX Products GmbH, Germany.
 * Author: Thorsten Kukuk <kukuk@suse.de>
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, and the entire permission notice in its entirety,
 *    including the disclaimer of warranties.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. The name of the author may not be used to endorse or promote
 *    products derived from this software without specific prior
 *    written permission.
 *
 * ALTERNATIVELY, this product may be distributed under the terms of
 * the GNU Public License, in which case the provisions of the GPL are
 * required INSTEAD OF the above restrictions.  (This clause is
 * necessary due to a potential bad interaction between the GPL and
 * the restrictions contained in a BSD-style copyright.)
 *
 * THIS SOFTWARE IS PROVIDED ``AS IS'' AND ANY EXPRESS OR IMPLIED
 * WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
 * OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT,
 * INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
 * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <pwd.h>
#include <grp.h>
#include <time.h>
#include <errno.h>
#include <dlfcn.h>
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <shadow.h>
#include <syslog.h>
#include <sys/types.h>

#define PAM_SM_ACCOUNT
#include <security/pam_modules.h>
#if defined (HAVE_SECURITY_PAM_EXT_H)
#include <security/pam_ext.h>
#endif

#include "public.h"

#define SCALE (24L*3600L)

static int
hp_expire (pam_handle_t *pamh, int flags, const struct passwd *pw)
{
  long min, max;
  char *age;

  age = strchr (pw->pw_passwd, ',');
  if (age == NULL)
    return PAM_SUCCESS;
  ++age;

  max = c2n (age[0]);
  if (max < 0)
    {
    error_state:
      pam_syslog (pamh, LOG_ERR, "Age field for %s is wrong", pw->pw_name);
      return PAM_ACCT_EXPIRED;
    }
  ++age;

  if (age == NULL)
    goto error_state;

  min = c2n (age[0]);
  if (min < 0)
    goto error_state;
  ++age;

  if (age == NULL)
    goto error_state;

  if ((max == 0 && min == 0) ||
      ((time(0)/(SCALE*7) > str2week (age) + max) && (max >= min)))
    {
      __write_message (pamh, flags, PAM_TEXT_INFO,
		       _("Your password has expired. Choose a new password."));
      return PAM_NEW_AUTHTOK_REQD;
    }

  return PAM_SUCCESS;
}

/* Only the password changing requested is not ignored for root, all
   other shadow account informations will be ignored for root, or root
   will not be able to login.  */
static int
expire (pam_handle_t *pamh, int flags, const struct spwd *sp, uid_t uid)
{
  long now;

  now = time (NULL) / SCALE;

  if (sp->sp_expire > 0 && now >= sp->sp_expire && uid != 0)
    {
      /* __write_message (pamh, flags,
	 _("Your login has expired.  Contact the system administrator.")); */
      return PAM_ACCT_EXPIRED;
    }

  if (sp->sp_lstchg == 0)
    {
      __write_message (pamh, flags, PAM_TEXT_INFO,
                       _("Password change requested. Choose a new password."));
      return PAM_NEW_AUTHTOK_REQD;
    }

  if (sp->sp_lstchg > 0 && sp->sp_max >= 0 &&
      (now > sp->sp_lstchg + sp->sp_max) && uid != 0)
    {
      if (sp->sp_inact >= 0 &&
	  now >= sp->sp_lstchg + sp->sp_max + sp->sp_inact)
	{
	  /*__write_message (pamh, flags,
	    _("Your password is inactive.  Contact the system administrator."));*/
	  return PAM_ACCT_EXPIRED;
	}
      if (sp->sp_max < sp->sp_min)
	{
	  /*__write_message (pamh, flags,
	    _("Your password has expired.  Contact the system administrator."));*/
	  return PAM_ACCT_EXPIRED;
	}
      __write_message (pamh, flags, PAM_TEXT_INFO,
		       _("Your password has expired. Choose a new password."));
      return PAM_NEW_AUTHTOK_REQD;
    }

  return PAM_SUCCESS;
}


int
pam_sm_acct_mgmt (pam_handle_t *pamh, int flags, int argc, const char **argv)
{
  int retval;
  int sp_buflen = 256;
  char *sp_buffer = alloca (sp_buflen);
  struct spwd sp_resultbuf;
  struct spwd *sp;
  int pw_buflen = 256;
  char *pw_buffer = alloca (pw_buflen);
  struct passwd pw_resultbuf;
  struct passwd *pw;
  const char *name;
  options_t options;

  memset (&options, 0, sizeof (options));

  if (get_options (pamh, &options, "account", argc, argv) < 0)
    {
      pam_syslog (pamh, LOG_ERR, "cannot get options");
      return PAM_SYSTEM_ERR;
    }

  if (options.debug)
    pam_syslog (pamh, LOG_DEBUG, "pam_sm_acct_mgmt() called");

  /* get the user name */
  if ((retval = pam_get_user (pamh, &name, NULL)) != PAM_SUCCESS)
    return retval;

  /* Check, if we got a valid user name */
  if (name == NULL || name[0] == '\0')
    {
      if (name)
	{
	  pam_syslog (pamh, LOG_ERR, "bad username [%s]", name);
	  return PAM_USER_UNKNOWN;
	}
      else if (options.debug)
	pam_syslog (pamh, LOG_DEBUG, "name == NULL, return PAM_SERVICE_ERR");
      return PAM_SERVICE_ERR;
    }
  else if (options.debug)
    pam_syslog (pamh, LOG_DEBUG, "username=[%s]", name);

  while (getpwnam_r (name, &pw_resultbuf, pw_buffer, pw_buflen, &pw) != 0
         && errno == ERANGE)
    {
      errno = 0;
      pw_buflen += 256;
      pw_buffer = alloca (pw_buflen);
    }

  if (pw == NULL)
    {
      if (options.debug)
	pam_syslog (pamh, LOG_DEBUG, "Cannot find passwd entry for %s", name);
      return PAM_USER_UNKNOWN;
    }

  /* If we use ldap, handle pam_ldap like "sufficient". If it returns
     success, we should also return success. Else ignore the call.  */
  if (options.use_other_modules && pw->pw_uid != 0)
    {
      unsigned int i;

      for (i = 0; options.use_other_modules[i] != NULL; i++)
	{
	  int retval;

	  retval = __call_other_module(pamh, flags,
	  			options.use_other_modules[i],
				"pam_sm_acct_mgmt",
				&options);

	  if (retval == PAM_SUCCESS ||
	      retval == PAM_PERM_DENIED ||
	      retval == PAM_ACCT_EXPIRED ||
	      retval == PAM_NEW_AUTHTOK_REQD)
	    return retval;
	}
    }

  if (pw->pw_passwd == NULL || pw->pw_passwd[0] == '!')
    {
      if (options.debug)
	{
	  if (pw->pw_passwd == NULL)
	    pam_syslog (pamh, LOG_DEBUG, "Password entry is empty for %s", name);
	  else
	    pam_syslog (pamh, LOG_DEBUG, "Account is locked for %s", name);
	}
      return PAM_PERM_DENIED;
    }

  if (strchr (pw->pw_passwd, ',') != NULL)
    return hp_expire (pamh, flags, pw);

  while (getspnam_r (pw->pw_name, &sp_resultbuf, sp_buffer,
		     sp_buflen, &sp) != 0 && errno == ERANGE)
    {
      errno = 0;
      sp_buflen += 256;
      sp_buffer = alloca (sp_buflen);
    }

  if (sp == NULL) /* We have no shadow */
    return PAM_SUCCESS;

  /* Always call expire, could be that root is enforced to change
     root password.  */
  retval = expire (pamh, flags, sp, pw->pw_uid);
  if (options.debug)
    pam_syslog (pamh, LOG_DEBUG, "expire() returned with %d", retval);
  if (retval != PAM_SUCCESS)
    return retval;

  if (sp)
    {
      /* Print when the user has to change his password the next time ! */
      long now, remain;

      now = time (NULL) / SCALE;

      if (sp->sp_lstchg != -1 && sp->sp_max != -1 && sp->sp_warn != -1)
	{
	  if ((remain = (sp->sp_lstchg + sp->sp_max) - now) <= sp->sp_warn)
	    {
	      if (remain > 1)
		__write_message (pamh, flags, PAM_TEXT_INFO,
				 _("Your password will expire in %ld days."),
				 remain);
	      else if (remain == 1)
		__write_message (pamh, flags, PAM_TEXT_INFO,
				 _("Your password will expire tomorrow."));
	      else if (remain == 0)
		__write_message (pamh, flags, PAM_TEXT_INFO,
				 _("Your password will expire within 24 hours."));
	    }
	}
    }
  return PAM_SUCCESS;
}
